"""Composite nodes: reusable subgraphs and bounded loops."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from jevbench.engine.context import Context
from jevbench.engine.expressions import parse
from jevbench.engine.nodes.base import Node, NodeConfig, registry
from jevbench.engine.trace import NodeTrace
from jevbench.errors import ExecutionError
from jevbench.schema.models import Framework, SubFramework


class _NestedConfig(NodeConfig):
    framework: str | None = Field(default=None, description="Path to a framework file, or name@version from the store.")
    body: SubFramework | None = Field(default=None, description="Inline nodes/output.")
    inputs: dict[str, str] | None = Field(default=None, description="name -> expression; the nested framework's input.")

    @model_validator(mode="after")
    def _one_body(self) -> "_NestedConfig":
        if (self.framework is None) == (self.body is None):
            raise ValueError("give exactly one of 'framework' or 'body'")
        return self


class NestedNode(Node):
    expression_fields = ("inputs",)
    config: _NestedConfig
    _resolved: tuple[Framework, Path] | None = None

    def resolve(self, base_dir: Path, store=None) -> tuple[Framework, Path]:
        """Load the nested framework (cached per node instance)."""
        if self._resolved is None:
            if self.config.body is not None:
                self._resolved = (self.config.body.as_framework(self.framework, f"{self.framework.name}.{self.id}"), base_dir)
            else:
                from jevbench.store import resolve_reference

                self._resolved = resolve_reference(self.config.framework, base_dir, store)
        return self._resolved

    def nested_input(self, ctx: Context) -> dict[str, Any]:
        if self.config.inputs is None:
            return ctx.scope.input
        return {name: ctx.eval(expr) for name, expr in self.config.inputs.items()}

    def summary(self) -> dict[str, Any]:
        return {"framework": self.config.framework or "(inline)"}


@registry.register
class SubgraphNode(NestedNode):
    """Run another framework as one node. Its judgment is this node's output."""

    type_name = "subgraph"
    Config = _NestedConfig

    def execute(self, ctx: Context) -> Any:
        framework, base_dir = self.resolve(ctx.base_dir, ctx.store)
        judgment, traces = ctx.run_nested(framework, self.nested_input(ctx), self.id, base_dir=base_dir)
        ctx.current_trace.children.extend(traces)
        return judgment


class LoopConfig(_NestedConfig):
    max_iterations: int = Field(ge=1, le=1000)
    until: str | None = Field(default=None, description="Expression over the body's nodes; stops the loop when true.")


@registry.register
class LoopNode(NestedNode):
    """Bounded iteration of a nested framework.

    Inside the body, ``loop.iteration`` (1-based), ``loop.previous`` (previous iteration's output,
    null on the first) and ``loop.history`` are available. ``until`` is evaluated after each
    iteration in the body's scope.
    """

    type_name = "loop"
    Config = LoopConfig
    config: LoopConfig

    def validate(self) -> list[str]:
        problems = super().validate()
        if self.config.until:
            try:
                parse(self.config.until)
            except Exception as exc:
                problems.append(f"nodes.{self.id}.until: {exc}")
        return problems

    def summary(self) -> dict[str, Any]:
        return {**super().summary(), "max_iterations": self.config.max_iterations, "until": self.config.until}

    def execute(self, ctx: Context) -> dict[str, Any]:
        framework, base_dir = self.resolve(ctx.base_dir, ctx.store)
        nested_input = self.nested_input(ctx)
        history: list[Any] = []
        previous: Any = None
        converged = False
        for iteration in range(1, self.config.max_iterations + 1):
            loop_scope = {"iteration": iteration, "previous": previous, "history": list(history)}
            child = ctx.child(framework, nested_input, self.id, base_dir=base_dir, loop=loop_scope)
            from jevbench.engine.executor import execute_graph

            value = execute_graph(child)
            for trace in child.traces:
                trace.iteration = iteration
            ctx.current_trace.children.extend(child.traces)
            history.append(value)
            previous = value
            if self.config.until and child.eval(self.config.until):
                converged = True
                break
        return {"value": previous, "iterations": len(history), "converged": converged, "history": history}
