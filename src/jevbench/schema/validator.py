"""Semantic validation: node types, expressions, references, cycles, nested frameworks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from jevbench.engine.graph import Graph
from jevbench.engine.nodes import registry
from jevbench.engine.nodes.base import Node
from jevbench.errors import JevBenchError, SchemaError
from jevbench.schema.models import Framework

if TYPE_CHECKING:
    from jevbench.store import FrameworkStore


@dataclass
class Analysis:
    framework: Framework
    nodes: dict[str, Node]
    graph: Graph
    problems: list[str] = field(default_factory=list)
    nested: dict[str, "Analysis"] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.problems and all(n.ok for n in self.nested.values())

    def all_problems(self, prefix: str = "") -> list[str]:
        out = [f"{prefix}{p}" for p in self.problems]
        for node_id, nested in self.nested.items():
            out.extend(nested.all_problems(f"{prefix}nodes.{node_id} -> "))
        return out

    def api_call_bound(self) -> int:
        """Upper bound on provider calls for one run (loops count max_iterations)."""
        from jevbench.engine.nodes.composite import LoopNode

        total = 0
        for node_id, node in self.nodes.items():
            if node.makes_api_calls:
                total += 1
            elif node_id in self.nested:
                inner = self.nested[node_id].api_call_bound()
                total += inner * (node.config.max_iterations if isinstance(node, LoopNode) else 1)
        return total


def build_nodes(framework: Framework) -> dict[str, Node]:
    """Instantiate typed nodes; raises SchemaError listing every bad node."""
    nodes: dict[str, Node] = {}
    problems: list[str] = []
    for node_id, spec in framework.nodes.items():
        try:
            nodes[node_id] = registry.build(node_id, spec, framework)
        except SchemaError as exc:
            problems.extend(exc.problems)
    if problems:
        raise SchemaError(problems)
    return nodes


def analyze(framework: Framework, base_dir: Path | None = None, store: "FrameworkStore | None" = None,
            _stack: tuple[str, ...] = ()) -> Analysis:
    """Build nodes and graph, collecting problems instead of raising where possible."""
    base_dir = Path(base_dir or ".").resolve()
    try:
        nodes = build_nodes(framework)
    except SchemaError as exc:
        return Analysis(framework, {}, Graph({}), list(exc.problems))

    problems: list[str] = []
    deps: dict[str, set[str]] = {}
    for node_id, node in nodes.items():
        try:
            problems.extend(node.validate())
            deps[node_id] = node.dependencies()
        except JevBenchError as exc:
            problems.append(f"nodes.{node_id}: {exc}")
            deps[node_id] = set(node.spec.depends_on)

    try:
        graph = Graph.build(deps)
    except SchemaError as exc:
        problems.extend(exc.problems)
        graph = Graph(deps)

    problems.extend(_check_output(framework, nodes))

    analysis = Analysis(framework, nodes, graph, problems)
    from jevbench.engine.nodes.composite import NestedNode

    key = f"{framework.name}@{framework.version}"
    for node_id, node in nodes.items():
        if isinstance(node, NestedNode):
            try:
                nested_fw, nested_dir = node.resolve(base_dir, store)
            except JevBenchError as exc:
                analysis.problems.append(f"nodes.{node_id}: {exc}")
                continue
            nested_key = f"{nested_fw.name}@{nested_fw.version}"
            if node.config.framework and nested_key in (*_stack, key):
                analysis.problems.append(f"nodes.{node_id}: recursive framework reference {nested_key}")
                continue
            analysis.nested[node_id] = analyze(nested_fw, nested_dir, store, (*_stack, key))
    return analysis


def _check_output(framework: Framework, nodes: dict[str, Node]) -> list[str]:
    from jevbench.engine.expressions import is_template, node_references, template_expressions

    output = framework.output
    expressions = template_expressions(output) if not isinstance(output, str) or is_template(output) else [output]
    problems = []
    for expression in expressions:
        try:
            refs, _ = node_references(expression)
        except JevBenchError as exc:
            problems.append(f"output: {exc}")
            continue
        for ref in sorted(refs):
            if ref not in nodes:
                problems.append(f"output: references unknown node {ref!r}")
    return problems


def validate(framework: Framework, base_dir: Path | None = None, store: "FrameworkStore | None" = None) -> list[str]:
    """Return a list of problems (empty when valid)."""
    return analyze(framework, base_dir, store).all_problems()
