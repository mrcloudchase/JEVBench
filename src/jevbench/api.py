"""Frontend-independent API. The CLI (and any future UI or server) is a thin layer over this."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jevbench.engine.executor import RunResult, run
from jevbench.engine.nodes import registry
from jevbench.engine.trace import RunTrace
from jevbench.loader import parse_data, read_data_file
from jevbench.providers.config import ProviderRegistry
from jevbench.schema.models import SCHEMA_VERSION, Framework, TestCase
from jevbench.schema.validator import Analysis, analyze
from jevbench.store import FrameworkStore, framework_from_data, load_framework_file, resolve_reference
from jevbench.testing import TestReport, run_tests as _run_tests

__all__ = [
    "Analysis",
    "Framework",
    "FrameworkStore",
    "ProviderRegistry",
    "RunResult",
    "RunTrace",
    "SCHEMA_VERSION",
    "TestReport",
    "framework_from_data",
    "framework_schema",
    "inspect_framework",
    "load_framework",
    "load_input",
    "node_types",
    "run_framework",
    "run_tests",
    "validate_framework",
]


def load_framework(source: str | Path | dict[str, Any], base_dir: str | Path | None = None) -> tuple[Framework, Path]:
    """Load from a path, a ``name@version`` store reference, or an already-parsed mapping."""
    if isinstance(source, dict):
        return framework_from_data(source), Path(base_dir or ".").resolve()
    return resolve_reference(str(source), Path(base_dir or ".").resolve())


def load_input(source: str | Path | None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if source:
        loaded = read_data_file(source)
        if not isinstance(loaded, dict):
            raise ValueError(f"{source}: input must be a mapping")
        data.update(loaded)
    data.update(overrides or {})
    return data


def validate_framework(framework: Framework, base_dir: str | Path | None = None, store: FrameworkStore | None = None) -> list[str]:
    return analyze(framework, Path(base_dir or "."), store).all_problems()


def inspect_framework(framework: Framework, base_dir: str | Path | None = None, store: FrameworkStore | None = None) -> dict[str, Any]:
    analysis = analyze(framework, Path(base_dir or "."), store)
    return _describe(analysis)


def _describe(analysis: Analysis) -> dict[str, Any]:
    nodes = {}
    for node_id, node in analysis.nodes.items():
        nodes[node_id] = {
            "type": node.type_name,
            "depends_on": sorted(node.dependencies()),
            "when": node.spec.when,
            **node.summary(),
        }
        if node_id in analysis.nested:
            nodes[node_id]["nested"] = _describe(analysis.nested[node_id])
    return {
        "name": analysis.framework.name,
        "version": analysis.framework.version,
        "description": analysis.framework.description,
        "inputs": {k: v.model_dump(exclude_none=True) for k, v in analysis.framework.inputs.items()},
        "valid": analysis.ok,
        "problems": analysis.all_problems(),
        "levels": analysis.graph.levels,
        "max_api_calls": analysis.api_call_bound(),
        "output": analysis.framework.output,
        "nodes": nodes,
    }


def run_framework(framework: Framework, input: dict[str, Any] | None = None, *, providers: ProviderRegistry | None = None,
                  mocks: dict[str, Any] | None = None, mock_all: bool = False, max_workers: int = 8,
                  base_dir: str | Path | None = None, store: FrameworkStore | None = None) -> RunResult:
    return run(framework, input, providers=providers, mocks=mocks, mock_all=mock_all, max_workers=max_workers,
               base_dir=base_dir, store=store)


def run_tests(framework: Framework, cases: list[TestCase] | None = None, **kwargs: Any) -> TestReport:
    return _run_tests(framework, cases, **kwargs)


def load_test_cases(path: str | Path) -> list[TestCase]:
    data = read_data_file(path)
    if isinstance(data, dict):
        data = data.get("tests", [])
    return [TestCase(**case) for case in data]


def node_types() -> dict[str, dict[str, Any]]:
    """Registered node types with their field schemas (for docs, validation UIs, canvases)."""
    out = {}
    for name in registry.names():
        cls = registry.get(name)
        out[name] = {"doc": (cls.__doc__ or "").strip(), "fields": cls.Config.model_json_schema()}
    return out


def framework_schema() -> dict[str, Any]:
    return Framework.model_json_schema()


def parse_framework_text(text: str, suffix: str = ".yaml") -> Framework:
    return framework_from_data(parse_data(text, suffix))
