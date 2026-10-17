"""JEV wire-format value objects.

An ``Issue`` is exactly one request body for ``POST /v1/systemone``; a ``Ruling`` is exactly
one response. Both are kept as plain JSON-compatible data so they round-trip through traces,
mocks and any JEV-compatible provider unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

IMAGES_HEADER = "TypeSafe-Danger-Zone-Images"
LONG_CONTEXT_HEADER = "TypeSafe-Danger-Zone-Long-Context"

QUESTION_TYPES = ("noul", "choice", "score", "box")
IMAGE_QUESTION_TYPES = ("box",)


@dataclass
class Issue:
    """Shared state plus one or more questions: the payload of one provider call."""

    state: Any
    questions: dict[str, dict[str, Any]]
    model: str | None = None
    assets: dict[str, dict[str, Any]] | None = None
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def needs_images(self) -> bool:
        return bool(self.assets) or any(q.get("type") in IMAGE_QUESTION_TYPES for q in self.questions.values())

    def to_wire(self) -> dict[str, Any]:
        body: dict[str, Any] = {"state": self.state, "questions": self.questions}
        if self.model:
            body["model"] = self.model
        if self.assets:
            body["assets"] = self.assets
        return body

    def redacted(self) -> dict[str, Any]:
        """Wire form with image payloads replaced by their size, for traces."""
        body = self.to_wire()
        if self.assets:
            body["assets"] = {
                ref: {**spec, "data_base64": f"<{len(spec['data_base64'])} base64 chars>"} if "data_base64" in spec else spec
                for ref, spec in self.assets.items()
            }
        return body


@dataclass
class Ruling:
    """The answers to every question of one Issue, from one provider call."""

    answers: dict[str, dict[str, Any]]
    model: str | None = None
    provider: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None

    def to_wire(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "answers": self.answers,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }

    @classmethod
    def from_wire(cls, body: dict[str, Any], provider: str | None = None, latency_ms: float | None = None) -> "Ruling":
        return cls(
            answers=_normalize_answers(body.get("answers") or {}),
            model=body.get("model"),
            provider=provider,
            usage=dict(body.get("usage") or {}),
            latency_ms=latency_ms,
        )


def _normalize_answers(answers: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Make answers uniform across clients: plain dicts, score maps keyed by string level."""
    out: dict[str, dict[str, Any]] = {}
    for qid, answer in answers.items():
        answer = dict(answer)
        if answer.get("type") == "score":
            for key in ("legend", "probabilities"):
                if isinstance(answer.get(key), dict):
                    answer[key] = {str(k): v for k, v in answer[key].items()}
        out[qid] = answer
    return out
