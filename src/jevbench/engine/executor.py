"""Runs a framework graph: level-parallel scheduling, conditional skips, tracing."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jevbench.engine.context import Context, MockBook, Scope
from jevbench.engine.nodes.base import Node
from jevbench.engine.trace import NodeTrace, RunTrace
from jevbench.errors import ExecutionError, JevBenchError, SchemaError
from jevbench.providers.config import ProviderRegistry
from jevbench.schema.models import Framework
from jevbench.schema.validator import analyze


@dataclass
class RunResult:
    judgment: Any
    trace: RunTrace

    def to_dict(self) -> dict[str, Any]:
        return self.trace.to_dict()


def prepare_input(framework: Framework, input: dict[str, Any] | None) -> dict[str, Any]:
    """Apply declared defaults and check required inputs."""
    data = dict(input or {})
    missing = []
    for name, spec in framework.inputs.items():
        if name not in data:
            if spec.required and spec.default is None:
                missing.append(name)
            else:
                data[name] = spec.default
    if missing:
        raise ExecutionError(f"missing required input(s): {', '.join(missing)}")
    return data


def run(framework: Framework, input: dict[str, Any] | None = None, *, providers: ProviderRegistry | None = None,
        mocks: dict[str, Any] | None = None, mock_all: bool = False, max_workers: int = 8,
        base_dir: str | Path | None = None, store=None) -> RunResult:
    """Execute a framework end to end and return the judgment with its trace."""
    problems = analyze(framework, base_dir, store).all_problems()
    if problems:
        raise SchemaError(problems)
    data = prepare_input(framework, input)
    ctx = Context(
        framework=framework,
        scope=Scope(input=data),
        providers=providers or ProviderRegistry.load(),
        mocks=MockBook(mocks),
        base_dir=Path(base_dir or ".").resolve(),
        store=store,
        max_workers=max_workers,
        mock_all=mock_all,
    )
    trace = RunTrace(framework=framework.name, version=framework.version, input=data)
    try:
        judgment = execute_graph(ctx)
    except JevBenchError as exc:
        trace.nodes = ctx.traces
        trace.finish("error", error=str(exc))
        raise ExecutionError(str(exc), getattr(exc, "node_path", None), trace) from exc
    trace.nodes = ctx.traces
    trace.finish("ok", judgment=judgment)
    return RunResult(judgment, trace)


def execute_graph(ctx: Context) -> Any:
    """Run every node of ``ctx.framework`` in dependency order and resolve its output."""
    analysis = analyze(ctx.framework, ctx.base_dir, ctx.store)
    if analysis.problems:
        raise SchemaError(analysis.problems)
    for level in analysis.graph.levels:
        nodes = [analysis.nodes[node_id] for node_id in level]
        if len(nodes) == 1 or ctx.max_workers <= 1:
            for node in nodes:
                _run_node(node, ctx)
        else:
            with ThreadPoolExecutor(max_workers=min(ctx.max_workers, len(nodes))) as pool:
                for result in pool.map(lambda n: _run_node(n, ctx), nodes):
                    pass
    try:
        return ctx.resolve_output(ctx.framework.output)
    except JevBenchError as exc:
        raise ExecutionError(f"output: {exc}", ctx.path or None) from exc


def _run_node(node: Node, ctx: Context) -> None:
    path = ctx.node_path(node.id)
    trace = NodeTrace(id=node.id, path=path, type=node.type_name)
    with ctx._lock:
        ctx.traces.append(trace)
    node_ctx = ctx.for_node(trace)
    try:
        if node.spec.when is not None and not node_ctx.eval(node.spec.when):
            ctx.set_output(node.id, None)
            trace.finish("skipped")
            return
        output = node.execute(node_ctx)
    except JevBenchError as exc:
        trace.finish("error", error=str(exc))
        raise ExecutionError(f"node {path!r} ({node.type_name}): {exc}", path) from exc
    except Exception as exc:  # defensive: never lose the trace on an unexpected bug
        trace.finish("error", error=f"{type(exc).__name__}: {exc}")
        raise ExecutionError(f"node {path!r} ({node.type_name}): {type(exc).__name__}: {exc}", path) from exc
    if isinstance(output, dict) and "_issue" in output:
        output = dict(output)
        trace.issue = output.pop("_issue")
        trace.provider = output.get("provider")
        trace.model = output.get("model")
        trace.usage = output.get("usage") or {}
        trace.mocked = output.get("provider") == "mock"
    ctx.set_output(node.id, output)
    trace.finish("ok", output=output)
