"""Execution history: one record per executed node, nested for composite nodes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class NodeTrace:
    id: str
    path: str
    type: str
    status: str = "pending"  # pending | ok | skipped | error
    started_at: str = field(default_factory=_now)
    finished_at: str | None = None
    duration_ms: float | None = None
    output: Any = None
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    issue: dict[str, Any] | None = None
    mocked: bool = False
    iteration: int | None = None
    children: list["NodeTrace"] = field(default_factory=list)

    def finish(self, status: str, output: Any = None, error: str | None = None) -> None:
        self.status = status
        self.output = output
        self.error = error
        self.finished_at = _now()
        self.duration_ms = round((datetime.fromisoformat(self.finished_at) - datetime.fromisoformat(self.started_at)).total_seconds() * 1000, 1)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def to_dict(self, include_output: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "path": self.path,
            "type": self.type,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
        }
        if self.iteration is not None:
            data["iteration"] = self.iteration
        if self.provider:
            data.update(provider=self.provider, model=self.model, usage=self.usage, mocked=self.mocked)
        if self.issue is not None:
            data["issue"] = self.issue
        if include_output:
            data["output"] = self.output
        if self.error:
            data["error"] = self.error
        if self.children:
            data["children"] = [c.to_dict(include_output) for c in self.children]
        return data


@dataclass
class RunTrace:
    framework: str
    version: str
    input: dict[str, Any]
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str = field(default_factory=_now)
    finished_at: str | None = None
    duration_ms: float | None = None
    status: str = "running"
    judgment: Any = None
    error: str | None = None
    nodes: list[NodeTrace] = field(default_factory=list)

    def finish(self, status: str, judgment: Any = None, error: str | None = None) -> None:
        self.status = status
        self.judgment = judgment
        self.error = error
        self.finished_at = _now()
        self.duration_ms = round((datetime.fromisoformat(self.finished_at) - datetime.fromisoformat(self.started_at)).total_seconds() * 1000, 1)

    def all_nodes(self):
        for node in self.nodes:
            yield from node.walk()

    def totals(self) -> dict[str, Any]:
        calls = [n for n in self.all_nodes() if n.provider]
        return {
            "nodes": sum(1 for _ in self.all_nodes()),
            "api_calls": sum(1 for n in calls if not n.mocked),
            "mocked_calls": sum(1 for n in calls if n.mocked),
            "input_tokens": sum(int(n.usage.get("input_tokens") or 0) for n in calls),
            "output_tokens": sum(int(n.usage.get("output_tokens") or 0) for n in calls),
            "skipped": sum(1 for n in self.all_nodes() if n.status == "skipped"),
        }

    def to_dict(self, include_output: bool = True) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "framework": self.framework,
            "version": self.version,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "input": self.input,
            "judgment": self.judgment,
            "error": self.error,
            "totals": self.totals(),
            "nodes": [n.to_dict(include_output) for n in self.nodes],
        }
