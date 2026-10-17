"""Clients that turn an Issue into a Ruling.

* ``SdkClient``: the official ``typesafe-sdk`` (default for TypeSafe and any provider that speaks
  the exact wire format at ``/v1/systemone``).
* ``HttpClient``: a dependency-free raw wire client for gateways that mount the same body at a
  different path (for example an AI gateway's ``/v1/evaluate``).
* ``MockClient``: deterministic offline answers for tests, dry runs and framework development.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from jevbench.errors import ProviderError
from jevbench.providers.config import ProviderConfig
from jevbench.providers.wire import IMAGES_HEADER, Issue, Ruling


class JevClient(ABC):
    """One provider connection. ``evaluate`` performs exactly one API call."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def evaluate(self, issue: Issue) -> Ruling: ...

    def resolve_model(self, issue: Issue) -> str:
        return issue.model or self.config.default_model

    def request_headers(self, issue: Issue) -> dict[str, str]:
        headers = {**self.config.headers, **issue.headers}
        if issue.needs_images:
            headers.setdefault(IMAGES_HEADER, "true")
        return headers


class SdkClient(JevClient):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        try:
            from typesafe_sdk import RetryPolicy, TypeSafeClient
        except ImportError as exc:  # pragma: no cover
            raise ProviderError("typesafe-sdk is not installed; pip install typesafe-sdk") from exc
        if not config.api_key:
            raise ProviderError(f"provider {config.name!r} has no API key (set TYPESAFE_API_KEY or api_key in the providers file)")
        self._sdk = TypeSafeClient(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.default_model,
            headers=config.headers or None,
            timeout=config.timeout,
            retry=RetryPolicy(max_retries=config.max_retries),
        )

    def evaluate(self, issue: Issue) -> Ruling:
        from typesafe_sdk import Image, TypeSafeError

        assets = None
        if issue.assets:
            assets = {ref: Image.from_base64(spec["data_base64"]) for ref, spec in issue.assets.items()}
        extra_headers = {k: v for k, v in self.request_headers(issue).items() if k not in self.config.headers}
        started = time.perf_counter()
        try:
            response = self._sdk.system_one(
                issue.state,
                issue.questions,
                model=self.resolve_model(issue),
                assets=assets,
                extra_headers=extra_headers or None,
            )
        except TypeSafeError as exc:
            raise ProviderError(f"{self.config.name}: {exc}") from exc
        latency = (time.perf_counter() - started) * 1000
        body = response.model_dump(mode="json")
        return Ruling.from_wire(body, provider=self.config.name, latency_ms=round(latency, 1))


class HttpClient(JevClient):
    def evaluate(self, issue: Issue) -> Ruling:
        body = issue.to_wire()
        body["model"] = self.resolve_model(issue)
        headers = {"Content-Type": "application/json", **self.request_headers(issue)}
        if self.config.api_key:
            headers.setdefault("Authorization", f"Bearer {self.config.api_key}")
        url = self.config.base_url.rstrip("/") + self.config.path
        request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        started = time.perf_counter()
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                if exc.code in (408, 429, 529) or exc.code >= 500:
                    if attempt < self.config.max_retries:
                        attempt += 1
                        time.sleep(min(5.0, 0.5 * 2**attempt))
                        continue
                raise ProviderError(f"{self.config.name}: HTTP {exc.code}: {detail}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                raise ProviderError(f"{self.config.name}: {exc}") from None
        latency = (time.perf_counter() - started) * 1000
        return Ruling.from_wire(payload, provider=self.config.name, latency_ms=round(latency, 1))


class MockClient(JevClient):
    """Answers every question deterministically without any network access.

    ``config.mock_answers`` may pin answers by question id; everything else gets a neutral
    synthetic answer (first choice option, lowest score level, noul 0.5, centred box).
    """

    def evaluate(self, issue: Issue) -> Ruling:
        answers = {qid: self._answer(qid, question) for qid, question in issue.questions.items()}
        tokens = len(json.dumps(issue.to_wire())) // 4
        return Ruling(answers=answers, model=f"mock:{self.resolve_model(issue)}", provider=self.config.name,
                      usage={"input_tokens": tokens, "output_tokens": 0}, latency_ms=0.0)

    def _answer(self, qid: str, question: dict[str, Any]) -> dict[str, Any]:
        pinned = self.config.mock_answers.get(qid)
        if pinned is not None:
            return synthesize_answer(question, pinned)
        return synthesize_answer(question)


def synthesize_answer(question: dict[str, Any], value: Any = None) -> dict[str, Any]:
    """Build a complete wire answer for ``question``.

    ``value`` may be a full answer dict (returned as-is), or a shorthand: the option label for a
    choice, a level index or float for a score, a probability for a noul, a dict of edges for a box.
    """
    qtype = question.get("type")
    if isinstance(value, dict) and value.get("type") == qtype:
        return value
    if qtype == "noul":
        p = 0.5 if value is None else float(value)
        return {"type": "noul", "noul": p}
    if qtype == "choice":
        options = list(question.get("criteria") or {})
        if isinstance(value, dict):
            probs = {o: float(value.get(o, 0.0)) for o in options}
        else:
            pick = options[0] if value is None else str(value)
            probs = {o: (1.0 if o == pick else 0.0) for o in options}
        winner = max(probs, key=probs.get) if probs else None
        n = len(probs)
        p_max = probs.get(winner, 0.0)
        confidence = (p_max - 1 / n) / (1 - 1 / n) if n > 1 else 1.0
        return {"type": "choice", "choice": winner, "probabilities": probs, "confidence": round(confidence, 4)}
    if qtype == "score":
        levels = list(question.get("criteria") or [])
        n = len(levels)
        if isinstance(value, dict):
            probs = {str(i): float(value.get(str(i), value.get(i, 0.0))) for i in range(n)}
        else:
            target = 0.0 if value is None else float(value)
            lo = int(max(0, min(n - 1, target // 1)))
            hi = min(n - 1, lo + 1)
            frac = target - lo
            probs = {str(i): 0.0 for i in range(n)}
            probs[str(lo)] = round(1 - frac, 4)
            probs[str(hi)] = round(probs[str(hi)] + frac, 4)
        score = sum(int(k) * v for k, v in probs.items())
        mode = int(max(probs, key=probs.get)) if probs else 0
        mad_unif = sum(abs(i - (n - 1) / 2) for i in range(n)) / n if n else 1
        spread = sum(v * abs(int(k) - mode) for k, v in probs.items())
        confidence = max(0.0, 1 - spread / mad_unif) if mad_unif else 1.0
        legend = {str(i): (lvl if isinstance(lvl, str) else json.dumps(lvl)) for i, lvl in enumerate(levels)}
        return {"type": "score", "score": round(score, 4), "legend": legend, "probabilities": probs,
                "confidence": round(confidence, 4)}
    if qtype == "box":
        box = value if isinstance(value, dict) else {"top": 0.25, "bottom": 0.75, "left": 0.25, "right": 0.75}
        return {"type": "box", "box": box, "confidence": 1.0 if value is not None else 0.5}
    raise ProviderError(f"cannot synthesize an answer for question type {qtype!r}")


_CLIENTS: dict[str, type[JevClient]] = {"sdk": SdkClient, "http": HttpClient, "mock": MockClient}


def build_client(config: ProviderConfig) -> JevClient:
    try:
        return _CLIENTS[config.client](config)
    except KeyError:
        raise ProviderError(f"unknown client kind {config.client!r}") from None
