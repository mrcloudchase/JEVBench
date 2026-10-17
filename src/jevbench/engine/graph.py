"""Dependency resolution and scheduling order for a framework's node graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from jevbench.errors import SchemaError


@dataclass
class Graph:
    dependencies: dict[str, set[str]]
    levels: list[list[str]] = field(default_factory=list)

    @classmethod
    def build(cls, dependencies: dict[str, set[str]]) -> "Graph":
        graph = cls({k: set(v) for k, v in dependencies.items()})
        graph._check_references()
        graph.levels = graph._topological_levels()
        return graph

    def dependents(self, node_id: str) -> set[str]:
        return {other for other, deps in self.dependencies.items() if node_id in deps}

    def _check_references(self) -> None:
        problems = []
        for node_id, deps in self.dependencies.items():
            for dep in sorted(deps):
                if dep not in self.dependencies:
                    problems.append(f"nodes.{node_id}: references unknown node {dep!r}")
                if dep == node_id:
                    problems.append(f"nodes.{node_id}: a node cannot depend on itself (use a loop node for iteration)")
        if problems:
            raise SchemaError(problems)

    def _topological_levels(self) -> list[list[str]]:
        remaining = {k: set(v) for k, v in self.dependencies.items()}
        levels: list[list[str]] = []
        while remaining:
            ready = sorted(n for n, deps in remaining.items() if not deps)
            if not ready:
                raise SchemaError(f"cycle detected among nodes {sorted(remaining)}; feedback needs an explicit loop node")
            levels.append(ready)
            for n in ready:
                del remaining[n]
            for deps in remaining.values():
                deps.difference_update(ready)
        return levels
