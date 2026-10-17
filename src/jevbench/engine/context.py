"""Execution context shared by nodes while a graph runs."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jevbench.engine.expressions import evaluate, is_template, render
from jevbench.engine.trace import NodeTrace

if TYPE_CHECKING:
    from jevbench.providers.config import ProviderRegistry
    from jevbench.schema.models import Framework
    from jevbench.store import FrameworkStore


@dataclass
class Scope:
    """Names visible to expressions: ``input``, ``nodes`` and (inside loops) ``loop``."""

    input: dict[str, Any]
    nodes: dict[str, Any] = field(default_factory=dict)
    loop: dict[str, Any] | None = None

    def mapping(self) -> dict[str, Any]:
        return {"input": self.input, "nodes": self.nodes, "loop": self.loop}


class MockBook:
    """Mocked rulings keyed by node path. A list value is consumed one entry per call."""

    def __init__(self, mocks: dict[str, Any] | None = None):
        self._mocks = dict(mocks or {})
        self._cursor: dict[str, int] = {}
        self._lock = threading.Lock()

    def __bool__(self) -> bool:
        return bool(self._mocks)

    def take(self, path: str) -> Any | None:
        with self._lock:
            if path not in self._mocks:
                return None
            value = self._mocks[path]
            if isinstance(value, list):
                index = self._cursor.get(path, 0)
                self._cursor[path] = index + 1
                return value[min(index, len(value) - 1)]
            return value


@dataclass
class Context:
    framework: "Framework"
    scope: Scope
    providers: "ProviderRegistry"
    mocks: MockBook
    base_dir: Path
    store: "FrameworkStore | None" = None
    path: str = ""
    max_workers: int = 8
    mock_all: bool = False
    traces: list[NodeTrace] = field(default_factory=list)
    current_trace: NodeTrace = field(default_factory=lambda: NodeTrace(id="", path="", type=""))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def for_node(self, trace: NodeTrace) -> "Context":
        """A view of this context bound to one node's trace record (shares scope, mocks and lock)."""
        return replace(self, current_trace=trace)

    def node_path(self, node_id: str) -> str:
        return f"{self.path}.{node_id}" if self.path else node_id

    def eval(self, expression: str) -> Any:
        return evaluate(expression, self.scope.mapping())

    def render(self, value: Any) -> Any:
        return render(value, self.scope.mapping())

    def resolve_output(self, value: Any) -> Any:
        """``output``-style values: a bare expression string, or a value with ``${}`` templates."""
        if isinstance(value, str) and not is_template(value):
            return self.eval(value)
        return self.render(value)

    def set_output(self, node_id: str, value: Any) -> None:
        with self._lock:
            self.scope.nodes[node_id] = value

    def child(self, framework: "Framework", input: dict[str, Any], node_id: str, *, base_dir: Path | None = None,
              loop: dict[str, Any] | None = None) -> "Context":
        """A context for a nested framework (subgraph body or loop iteration)."""
        from jevbench.engine.executor import prepare_input

        return Context(
            framework=framework,
            scope=Scope(input=prepare_input(framework, input), loop=loop),
            providers=self.providers,
            mocks=self.mocks,
            base_dir=base_dir or self.base_dir,
            store=self.store,
            path=self.node_path(node_id),
            max_workers=self.max_workers,
            mock_all=self.mock_all,
        )

    def run_nested(self, framework: "Framework", input: dict[str, Any], node_id: str, *, base_dir: Path | None = None,
                   loop: dict[str, Any] | None = None) -> tuple[Any, list[NodeTrace]]:
        from jevbench.engine.executor import execute_graph

        child = self.child(framework, input, node_id, base_dir=base_dir, loop=loop)
        judgment = execute_graph(child)
        return judgment, child.traces
