"""Node base class and the typed node registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from jevbench.engine.expressions import is_template, node_references, parse, template_expressions
from jevbench.errors import ExecutionError, SchemaError

Numeric = float | str
"""A number, or a string holding a bare expression / ``${template}`` that yields one at run time."""

if TYPE_CHECKING:
    from jevbench.engine.context import Context
    from jevbench.schema.models import Framework, NodeSpec


class NodeConfig(BaseModel):
    """Base for type-specific node fields. Subclasses declare their fields."""

    model_config = ConfigDict(extra="forbid")


class Node:
    """A unit of a framework graph.

    Subclasses set ``type_name`` and ``Config`` and implement ``execute``. The default
    dependency analysis scans ``when``, ``depends_on`` and the fields named in
    ``expression_fields`` (bare expressions) and ``template_fields`` (``${...}`` templates).
    """

    type_name: ClassVar[str]
    Config: ClassVar[type[NodeConfig]] = NodeConfig
    expression_fields: ClassVar[tuple[str, ...]] = ()
    template_fields: ClassVar[tuple[str, ...]] = ()
    numeric_fields: ClassVar[tuple[str, ...]] = ()
    makes_api_calls: ClassVar[bool] = False

    def __init__(self, node_id: str, spec: "NodeSpec", framework: "Framework"):
        self.id = node_id
        self.spec = spec
        self.framework = framework
        try:
            self.config = self.Config(**spec.extra)
        except ValidationError as exc:
            problems = [f"nodes.{node_id}.{'.'.join(str(p) for p in e['loc']) or '-'}: {e['msg']}" for e in exc.errors()]
            raise SchemaError(problems) from None

    # -- static analysis -------------------------------------------------------------------

    def expressions(self) -> list[str]:
        """Every bare expression this node evaluates (used for dependency analysis)."""
        found: list[str] = []
        if self.spec.when:
            found.append(self.spec.when)
        for name in self.expression_fields:
            found.extend(_flatten_expressions(getattr(self.config, name, None)))
        for name in self.template_fields:
            found.extend(template_expressions(getattr(self.config, name, None)))
        for name in self.numeric_fields:
            value = getattr(self.config, name, None)
            if isinstance(value, str):
                if is_template(value):
                    found.extend(template_expressions(value))
                else:
                    parse(value)
                    found.append(value)
        return found

    def number(self, ctx: "Context", name: str) -> float | None:
        """Resolve a ``Numeric`` config field: numbers pass through, strings are evaluated."""
        value = getattr(self.config, name)
        if value is None or isinstance(value, (int, float)):
            return value
        resolved = ctx.resolve_output(value)
        if not isinstance(resolved, (int, float)) or isinstance(resolved, bool):
            raise ExecutionError(f"{name} {value!r} is not numeric: {resolved!r}", ctx.node_path(self.id))
        return resolved

    def dependencies(self) -> set[str]:
        deps = set(self.spec.depends_on)
        for expression in self.expressions():
            static, _ = node_references(expression)
            deps |= static
        return deps

    def validate(self) -> list[str]:
        """Return semantic problems (bad expressions, dynamic references without depends_on)."""
        problems: list[str] = []
        for expression in self.expressions():
            try:
                _, dynamic = node_references(expression)
            except SchemaError as exc:
                problems.extend(f"nodes.{self.id}: {p}" for p in exc.problems)
                continue
            except Exception as exc:
                problems.append(f"nodes.{self.id}: {exc}")
                continue
            if dynamic and not self.spec.depends_on:
                problems.append(f"nodes.{self.id}: dynamic node reference in {expression!r} requires depends_on")
        return problems

    # -- execution ---------------------------------------------------------------------------

    def execute(self, ctx: "Context") -> Any:  # pragma: no cover - abstract
        raise NotImplementedError

    def summary(self) -> dict[str, Any]:
        """Short description for ``inspect``."""
        return {}


def _flatten_expressions(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parse(value)
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for v in value.values():
            out.extend(_flatten_expressions(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(_flatten_expressions(v))
        return out
    return []


class NodeRegistry:
    def __init__(self) -> None:
        self._types: dict[str, type[Node]] = {}

    def register(self, cls: type[Node]) -> type[Node]:
        self._types[cls.type_name] = cls
        return cls

    def get(self, type_name: str) -> type[Node]:
        try:
            return self._types[type_name]
        except KeyError:
            raise SchemaError(f"unknown node type {type_name!r}; known: {sorted(self._types)}") from None

    def names(self) -> list[str]:
        return sorted(self._types)

    def build(self, node_id: str, spec: "NodeSpec", framework: "Framework") -> Node:
        return self.get(spec.type)(node_id, spec, framework)


registry = NodeRegistry()
