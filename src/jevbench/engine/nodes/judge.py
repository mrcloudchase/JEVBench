"""JudgeJEV: one node, one Issue, one API call, one Ruling."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field, ValidationError

from jevbench.engine.context import Context
from jevbench.engine.nodes.base import Node, NodeConfig, registry
from jevbench.errors import ExecutionError, ProviderError, SchemaError
from jevbench.providers.clients import synthesize_answer
from jevbench.providers.wire import Issue, Ruling
from jevbench.schema.models import Question


class JudgeConfig(NodeConfig):
    state: Any = Field(description="Shared state; any JSON value, templates allowed.")
    questions: dict[str, Question] = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    assets: dict[str, dict[str, Any]] | None = Field(default=None, description="ref -> {path | data_base64, format}")


@registry.register
class JudgeNode(Node):
    type_name = "judge"
    Config = JudgeConfig
    template_fields = ("state", "questions", "assets")
    makes_api_calls = True

    config: JudgeConfig

    def expressions(self) -> list[str]:
        found = super().expressions()
        # Question content is a pydantic model; scan its wire form for templates.
        from jevbench.engine.expressions import template_expressions

        for question in self.config.questions.values():
            found.extend(template_expressions(question.to_wire()))
        return found

    def provider_name(self) -> str | None:
        return self.config.provider or self.framework.defaults.provider

    def model_name(self) -> str | None:
        return self.config.model or self.framework.defaults.model

    def summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name() or "(default)",
            "model": self.model_name() or "(provider default)",
            "questions": {qid: q.type for qid, q in self.config.questions.items()},
        }

    # -- execution --------------------------------------------------------------------------

    def build_issue(self, ctx: Context) -> Issue:
        state = ctx.render(self.config.state)
        questions: dict[str, dict[str, Any]] = {}
        for qid, question in self.config.questions.items():
            rendered = ctx.render(question.to_wire())
            try:
                questions[qid] = Question(**rendered).to_wire()
            except ValidationError as exc:
                raise ExecutionError(f"question {qid!r} invalid after templating: {exc.errors()[0]['msg']}", ctx.node_path(self.id)) from None
        assets = self._load_assets(ctx.render(self.config.assets), ctx.base_dir) if self.config.assets else None
        headers = {**self.framework.defaults.headers, **self.config.headers}
        return Issue(state=state, questions=questions, model=self.model_name(), assets=assets, headers=headers)

    def execute(self, ctx: Context) -> dict[str, Any]:
        issue = self.build_issue(ctx)
        path = ctx.node_path(self.id)
        mocked = ctx.mocks.take(path)
        if mocked is not None or ctx.mock_all:
            ruling = self._mock_ruling(issue, mocked)
        else:
            ruling = self._call_provider(ctx, issue)
        return {"_issue": issue.redacted(), **ruling.to_wire()}

    def _call_provider(self, ctx: Context, issue: Issue) -> Ruling:
        provider = ctx.providers.get(self.provider_name())
        if issue.needs_images and not provider.has("images"):
            raise ProviderError(f"provider {provider.name!r} does not declare the 'images' capability needed by node {self.id!r}")
        return ctx.providers.client(provider.name).evaluate(issue)

    @staticmethod
    def _mock_ruling(issue: Issue, mocked: Any) -> Ruling:
        pinned = mocked if isinstance(mocked, dict) else {}
        if "answers" in pinned and isinstance(pinned["answers"], dict):
            pinned = pinned["answers"]
        answers = {qid: synthesize_answer(q, pinned.get(qid)) for qid, q in issue.questions.items()}
        return Ruling(answers=answers, model=f"mock:{issue.model or 'default'}", provider="mock",
                      usage={"input_tokens": 0, "output_tokens": 0}, latency_ms=0.0)

    @staticmethod
    def _load_assets(assets: dict[str, dict[str, Any]], base_dir: Path) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for ref, spec in assets.items():
            spec = dict(spec)
            path = spec.pop("path", None)
            if path:
                file = Path(path)
                if not file.is_absolute():
                    file = base_dir / file
                try:
                    spec["data_base64"] = base64.b64encode(file.read_bytes()).decode("ascii")
                except OSError as exc:
                    raise ExecutionError(f"asset {ref!r}: cannot read {file}: {exc}") from None
                spec.setdefault("format", file.suffix.lstrip(".").lower().replace("jpeg", "jpg"))
            spec.setdefault("type", "image")
            out[ref] = spec
        return out
