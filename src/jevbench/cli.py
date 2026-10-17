"""``jevbench`` command line: validate, run, inspect, test, save, list, providers, schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jevbench import api
from jevbench.errors import ExecutionError, JevBenchError
from jevbench.loader import dump_yaml
from jevbench.store import FrameworkStore


def _print(data: Any, fmt: str) -> None:
    if fmt == "yaml":
        sys.stdout.write(dump_yaml(data))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def _parse_set(pairs: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        if not sep:
            raise JevBenchError(f"--set expects key=value, got {pair!r}")
        try:
            out[key] = json.loads(raw)
        except json.JSONDecodeError:
            out[key] = raw
    return out


def _load(args) -> tuple:
    framework, base_dir = api.load_framework(args.framework)
    return framework, base_dir


def _providers(args):
    from jevbench.providers.config import ProviderRegistry

    return ProviderRegistry.load(getattr(args, "providers", None))


# -- commands --------------------------------------------------------------------------------

def cmd_validate(args) -> int:
    framework, base_dir = _load(args)
    problems = api.validate_framework(framework, base_dir, FrameworkStore(args.store))
    if problems:
        print(f"INVALID: {framework.name}@{framework.version}")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"OK: {framework.name}@{framework.version} ({len(framework.nodes)} nodes)")
    return 0


def cmd_inspect(args) -> int:
    framework, base_dir = _load(args)
    info = api.inspect_framework(framework, base_dir, FrameworkStore(args.store))
    if args.format != "pretty":
        _print(info, args.format)
        return 0 if info["valid"] else 1
    print(f"{info['name']}@{info['version']}  valid={info['valid']}  max_api_calls={info['max_api_calls']}")
    if info["description"]:
        print(f"  {info['description']}")
    if info["inputs"]:
        print("inputs: " + ", ".join(f"{k}{'' if v.get('required', True) else '?'}" for k, v in info["inputs"].items()))
    print("execution levels:")
    for i, level in enumerate(info["levels"], 1):
        print(f"  {i}. {', '.join(level)}")
    print("nodes:")
    _print_nodes(info["nodes"], "  ")
    print(f"output: {json.dumps(info['output'])}")
    for problem in info["problems"]:
        print(f"PROBLEM: {problem}")
    return 0 if info["valid"] else 1


def _print_nodes(nodes: dict[str, Any], indent: str) -> None:
    for node_id, node in nodes.items():
        extras = {k: v for k, v in node.items() if k not in ("type", "depends_on", "when", "nested") and v is not None}
        deps = f" <- {', '.join(node['depends_on'])}" if node["depends_on"] else ""
        cond = f"  when: {node['when']}" if node.get("when") else ""
        detail = f"  {json.dumps(extras, default=str)}" if extras else ""
        print(f"{indent}{node_id} [{node['type']}]{deps}{cond}{detail}")
        if "nested" in node:
            _print_nodes(node["nested"]["nodes"], indent + "    ")


def cmd_run(args) -> int:
    framework, base_dir = _load(args)
    input_data = api.load_input(args.input, _parse_set(args.set))
    mocks = json.loads(Path(args.mocks).read_text()) if args.mocks else None
    try:
        result = api.run_framework(framework, input_data, providers=_providers(args), mocks=mocks, mock_all=args.mock,
                                   max_workers=args.workers, base_dir=base_dir, store=FrameworkStore(args.store))
    except ExecutionError as exc:
        if args.trace and exc.trace is not None:
            Path(args.trace).write_text(json.dumps(exc.trace.to_dict(), indent=2, default=str))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.trace:
        Path(args.trace).write_text(json.dumps(result.trace.to_dict(), indent=2, default=str))
    if args.format == "pretty":
        print(json.dumps(result.judgment, indent=2, ensure_ascii=False, default=str))
        totals = result.trace.totals()
        print(f"-- {framework.name}@{framework.version} run {result.trace.run_id}: {result.trace.duration_ms} ms, "
              f"{totals['api_calls']} api calls ({totals['mocked_calls']} mocked), {totals['input_tokens']} input tokens, "
              f"{totals['skipped']} skipped", file=sys.stderr)
        if args.verbose:
            for node in result.trace.all_nodes():
                tag = f"#{node.iteration}" if node.iteration else ""
                extra = f" {node.provider}/{node.model} {node.usage.get('input_tokens', 0)} tok" if node.provider else ""
                print(f"   {node.path}{tag} [{node.type}] {node.status} {node.duration_ms} ms{extra}", file=sys.stderr)
                if args.verbose > 1 and node.status == "ok":
                    print(f"      -> {json.dumps(node.output, default=str)[:300]}", file=sys.stderr)
    elif args.format == "trace":
        _print(result.trace.to_dict(), "json")
    else:
        _print({"judgment": result.judgment, "run_id": result.trace.run_id, "totals": result.trace.totals()}, args.format)
    return 0


def cmd_test(args) -> int:
    framework, base_dir = _load(args)
    cases = api.load_test_cases(args.cases) if args.cases else None
    if cases is None and not framework.tests:
        print("no test cases: add a 'tests:' section or pass --cases file")
        return 1
    report = api.run_tests(framework, cases, providers=_providers(args) if args.live else None, base_dir=base_dir,
                           store=FrameworkStore(args.store), mock_all=args.mock, live=args.live, max_workers=args.workers)
    if args.format != "pretty":
        _print(report.to_dict(), args.format)
        return 0 if report.passed else 1
    for result in report.results:
        if result.error and result.passed:
            print(f"SKIP {result.name}: {result.error}")
            continue
        status = "PASS" if result.passed else "FAIL"
        calls = f" ({result.api_calls} api calls)" if result.api_calls else ""
        print(f"{status} {result.name}{calls}")
        if result.error:
            print(f"     error: {result.error}")
        for failure in result.failures:
            print(f"     expect: {failure}")
        if not result.passed and result.judgment is not None:
            print(f"     judgment: {json.dumps(result.judgment, default=str)[:400]}")
    ok, failed = report.counts
    print(f"-- {ok} passed, {failed} failed")
    return 0 if report.passed else 1


def cmd_save(args) -> int:
    framework, base_dir = _load(args)
    problems = api.validate_framework(framework, base_dir, FrameworkStore(args.store))
    if problems and not args.force:
        print("refusing to save an invalid framework:\n  - " + "\n  - ".join(problems))
        return 1
    path = FrameworkStore(args.store).save(framework, overwrite=args.force)
    print(f"saved {framework.name}@{framework.version} -> {path}")
    return 0


def cmd_list(args) -> int:
    entries = FrameworkStore(args.store).list()
    if args.format != "pretty":
        _print(entries, args.format)
        return 0
    if not entries:
        print(f"store is empty ({FrameworkStore(args.store).root})")
    for entry in entries:
        print(f"{entry['name']}  latest={entry['latest']}  versions={', '.join(entry['versions'])}")
    return 0


def cmd_providers(args) -> int:
    registry = _providers(args)
    data = {name: registry.get(name).redacted() for name in registry.names()}
    if args.format != "pretty":
        _print({"default": registry.default_name, "providers": data}, args.format)
        return 0
    for name, cfg in data.items():
        star = "*" if name == registry.default_name else " "
        key = "key set" if cfg["api_key"] else "NO KEY"
        print(f"{star} {name}: {cfg['client']} {cfg['base_url']}{cfg['path']} model={cfg['default_model']} [{key}] caps={','.join(cfg['capabilities'])}")
    return 0


def cmd_schema(args) -> int:
    if args.what == "framework":
        _print(api.framework_schema(), args.format)
    else:
        _print(api.node_types(), args.format)
    return 0


# -- parser ----------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jevbench", description="Compose, run and test judging frameworks on JEV decision models.")
    parser.add_argument("--store", help="framework store directory (default: $JEVBENCH_STORE or ~/.jevbench/frameworks)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p, fmt_choices=("pretty", "json", "yaml")):
        p.add_argument("framework", help="framework file (.yaml/.json) or store reference name[@version]")
        p.add_argument("--format", "-f", choices=fmt_choices, default="pretty")

    p = sub.add_parser("validate", help="check a framework file")
    add_common(p)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("inspect", help="show nodes, dependencies and execution order")
    add_common(p)
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("run", help="execute a framework with runtime input")
    add_common(p, ("pretty", "json", "yaml", "trace"))
    p.add_argument("--input", "-i", help="input file (.json/.yaml) mapping input names to values")
    p.add_argument("--set", "-s", action="append", default=[], metavar="KEY=VALUE", help="set an input (JSON value or string)")
    p.add_argument("--providers", "-p", help="providers file")
    p.add_argument("--mock", action="store_true", help="answer every judge offline with synthetic rulings")
    p.add_argument("--mocks", help="JSON file of node path -> answers to pin")
    p.add_argument("--trace", "-t", help="write the full execution trace to this JSON file")
    p.add_argument("--workers", "-w", type=int, default=8, help="max parallel judges per level")
    p.add_argument("--verbose", "-v", action="count", default=0)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("test", help="run a framework's declarative test cases")
    add_common(p)
    p.add_argument("--cases", "-c", help="test cases file (default: the framework's 'tests' section)")
    p.add_argument("--providers", "-p")
    p.add_argument("--live", action="store_true", help="run cases without mocks against real providers")
    p.add_argument("--mock", action="store_true", help="force every case offline")
    p.add_argument("--workers", "-w", type=int, default=8)
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("save", help="save a framework version into the store")
    add_common(p)
    p.add_argument("--force", action="store_true", help="overwrite an existing version / skip validation")
    p.set_defaults(func=cmd_save)

    p = sub.add_parser("list", help="list stored frameworks and versions")
    p.add_argument("--format", "-f", choices=("pretty", "json", "yaml"), default="pretty")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("providers", help="show configured providers (keys redacted)")
    p.add_argument("--providers", "-p")
    p.add_argument("--format", "-f", choices=("pretty", "json", "yaml"), default="pretty")
    p.set_defaults(func=cmd_providers)

    p = sub.add_parser("schema", help="print the framework JSON schema or the node type catalogue")
    p.add_argument("what", choices=("framework", "nodes"), nargs="?", default="framework")
    p.add_argument("--format", "-f", choices=("json", "yaml"), default="json")
    p.set_defaults(func=cmd_schema)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except JevBenchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
