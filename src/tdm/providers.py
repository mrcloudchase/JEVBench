"""Providers: anything that turns state and questions into a belief over HTTP.

Provider is the generic HTTP client. It owns transport, configuration, retries, timing, cost and
errors, and leaves three things to subclasses: headers(), payload() and parse(). A provider with a
different API is one subclass that overrides what differs. parse() returns {"model", "answers",
"usage"} with answers in the TypeSafe wire format's shapes, so nothing downstream changes when the
provider does.

Configuration comes from the environment (usually .env):

    PROVIDER           registered name (typesafe, openai, deepseek, von, opendecider, openjev) or "module:Class"; default typesafe
    PROVIDER_URL       endpoint; optional when the class has a default
    PROVIDER_API_KEY   optional when the class's own variable is set (TYPESAFE_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY);
                       local servers (von, opendecider, openjev) need none
    PROVIDER_MODEL     optional when the class has a default
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

PROVIDERS: dict[str, type["Provider"]] = {}


def register(name: str):
    """Class decorator: make a provider selectable by name."""
    def add(cls):
        cls.name = name
        PROVIDERS[name] = cls
        return cls
    return add


class Provider(ABC):
    """Generic HTTP provider: state + questions -> {provider, model, answers, usage, latency_ms, cost_usd}."""

    name: str = "provider"
    url: str | None = None                 # class defaults; the environment overrides them
    model: str | None = None
    key_env: str | None = None             # the vendor's usual key variable, used when PROVIDER_API_KEY is unset
    usd_per_mtok_input: float = 0.0        # list price, for cost reporting
    required = ("url", "api_key", "model")  # a local server needs no key
    retry_statuses = {408, 429, 500, 502, 503, 504, 529}

    def __init__(self, url=None, api_key=None, model=None, timeout=30.0, retries=3):
        self.url, self.api_key, self.model = url or self.url, api_key, model or self.model
        self.timeout, self.retries = timeout, retries
        for field in self.required:
            if not getattr(self, field):
                raise RuntimeError(f"{type(self).__name__}: set PROVIDER_{field.upper()} in .env or the environment")

    @classmethod
    def from_env(cls, env=os.environ) -> "Provider":
        api_key = env.get("PROVIDER_API_KEY") or (env.get(cls.key_env) if cls.key_env else None)
        return cls(url=env.get("PROVIDER_URL"), api_key=api_key, model=env.get("PROVIDER_MODEL"))

    # ---- what a provider defines
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @abstractmethod
    def payload(self, state, questions: dict) -> dict:
        """The request body for one belief."""

    @abstractmethod
    def parse(self, body: dict, questions: dict) -> dict:
        """The response body -> {"model", "answers", "usage"}, answers in the wire format's shapes."""

    # ---- what every provider shares
    def key(self, state, questions: dict, repeat: int = 0) -> str:
        """A stable hash of one request, for caching. Repeats are distinct requests."""
        request = {"url": self.url, "payload": self.payload(state, questions), "repeat": repeat}
        return hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def __call__(self, state, questions: dict) -> dict:
        data = json.dumps(self.payload(state, questions)).encode("utf-8")
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(self.url, data=data, headers=self.headers(), method="POST")
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = json.loads(response.read())
                latency_ms = round((time.perf_counter() - started) * 1000, 1)
                result = self.parse(body, questions)
                tokens = (result.get("usage") or {}).get("input_tokens") or 0
                return {"provider": self.name, **result, "latency_ms": latency_ms,
                        "cost_usd": round(tokens * self.usd_per_mtok_input / 1e6, 8)}
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "replace")[:300]
                if err.code not in self.retry_statuses or attempt == self.retries:
                    raise RuntimeError(f"HTTP {err.code} from {self.url}: {detail}") from None
                time.sleep(float(err.headers.get("Retry-After") or 2 ** attempt))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as err:   # resets and refusals are transient too
                if attempt == self.retries:
                    raise RuntimeError(f"{self.url}: {err}") from None
                time.sleep(2 ** attempt)


def text(value) -> str:
    """Content as a string: strings pass through, structured content becomes JSON."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


@register("typesafe")
class TypeSafe(Provider):
    """The TypeSafe wire format, which is also the engine's own. Any gateway serving it works too."""

    url = "https://api.typesafe.ai/v1/systemone"
    model = "jev-latest"
    key_env = "TYPESAFE_API_KEY"
    usd_per_mtok_input = 0.042

    def payload(self, state, questions):
        return {"model": self.model, "state": state, "questions": questions}

    def parse(self, body, questions):
        return {"model": body.get("model"), "answers": body["answers"], "usage": body.get("usage", {})}


class Local(TypeSafe):
    """An open model served on this machine in the wire format: no key, no price."""

    key_env = None
    usd_per_mtok_input = 0.0
    required = ("url", "model")


@register("von")
class Von(Local):
    """Von 1.3 (wfzyx/von, 395M ModernBERT, Apache-2.0): `von serve --port 8101 --noul-decision raw`."""

    url = "http://127.0.0.1:8101/v1/systemone"
    model = "von-1.3"


@register("opendecider")
class OpenDecider(Local):
    """OpenDecider nano (manjunathshiva/opendecider-nano, ~0.4B): `opendecider serve --port 8102`."""

    url = "http://127.0.0.1:8102/v1/systemone"
    model = "opendecider-nano"


@register("openjev")
class OpenJev(Local):
    """open-jev-deberta-v3-large (com-kotobalabs, 0.4B, Apache-2.0): `python servers/openjev.py --port 8103`."""

    url = "http://127.0.0.1:8103/v1/systemone"
    model = "open-jev-deberta-v3-large"


@register("openai")
class OpenAI(Provider):
    """OpenAI's Decisions API (POST /v1/decisions, public beta since October 2026).

    Questions translate one to one: noul -> predicate (yes/no criteria are appended to the
    instructions, since predicates take none), choice criteria -> choices, score criteria -> levels.
    Answers translate back to the wire format's shapes; a refusal becomes {"type": "refusal"}."""

    url = "https://api.openai.com/v1/decisions"
    model = "gpt-6-luna"
    key_env = "OPENAI_API_KEY"
    usd_per_mtok_input = 0.10

    def payload(self, state, questions):
        return {"model": self.model, "input": text(state),
                "questions": [self.question(qid, q) for qid, q in questions.items()]}

    @staticmethod
    def question(qid: str, q: dict) -> dict:
        kind, instructions = q["type"], text(q.get("instructions") or "")
        if kind == "noul":
            criteria = q.get("criteria") or {}
            notes = [f"{side.capitalize()} means: {text(criteria[side])}." for side in ("true", "false") if criteria.get(side)]
            return {"type": "predicate", "name": qid, "instructions": " ".join([instructions, *notes]).strip()}
        if kind == "choice":
            choices = [{"value": k, **({"description": text(d)} if d is not None else {})} for k, d in q["criteria"].items()]
            return {"type": "choice", "name": qid, "instructions": instructions, "choices": choices}
        if kind == "score":
            return {"type": "score", "name": qid, "instructions": instructions, "levels": [{"label": text(level)} for level in q["criteria"]]}
        raise ValueError(f"OpenAI Decisions has no {kind!r} question type")

    def parse(self, body, questions):
        answers = {}
        for a in body.get("answers", []):
            name, kind = a.get("name"), a["type"]
            if kind == "predicate":
                answers[name] = {"type": "noul", "noul": a["probability"]}
            elif kind == "choice":
                answers[name] = {"type": "choice", "choice": a["choice"], "confidence": a["confidence"],
                                 "probabilities": {p["value"]: p["probability"] for p in a["probabilities"]}}
            elif kind == "score":
                answers[name] = {"type": "score", "score": a["score"], "confidence": a["confidence"],
                                 "legend": {str(p["value"]): p.get("label") for p in a["probabilities"]},
                                 "probabilities": {str(p["value"]): p["probability"] for p in a["probabilities"]}}
            else:
                answers[name] = {"type": kind}                     # refusal, or a type this parser doesn't know yet
        return {"model": body.get("model"), "answers": answers, "usage": body.get("usage", {})}


@register("deepseek")
class DeepSeek(Provider):
    """A chat model read as a typed decision model. Each question is its own request: the options
    get one-token labels (yes/no, 1..N, A..Z) and the belief is the next-token distribution over
    them, from top_logprobs (at most 20, so at most 20 options), renormalized over the labels."""

    url = "https://api.deepseek.com/chat/completions"
    model = "deepseek-chat"
    key_env = "DEEPSEEK_API_KEY"
    usd_per_mtok_input = 0.30              # V4.1 Flash, cache miss, peak hours

    def __call__(self, state, questions):
        results = [super(DeepSeek, self).__call__(state, {qid: q}) for qid, q in questions.items()]
        merged = {**results[0], "answers": {}, "usage": {"input_tokens": 0, "output_tokens": 0}}
        for r in results:
            merged["answers"].update(r["answers"])
            for k in merged["usage"]:
                merged["usage"][k] += r["usage"].get(k, 0)
        merged["latency_ms"] = round(sum(r["latency_ms"] for r in results), 1)
        merged["cost_usd"] = round(sum(r["cost_usd"] for r in results), 8)
        return merged

    def key(self, state, questions, repeat=0):
        return "+".join(super(DeepSeek, self).key(state, {qid: q}, repeat) for qid, q in questions.items())

    @staticmethod
    def options(q: dict) -> list[tuple[str, str, str]]:
        """(label, key, description) for each option, in order."""
        kind, criteria = q["type"], q.get("criteria") or {}
        if kind == "noul":
            return [("yes", "true", text(criteria.get("true") or "true")), ("no", "false", text(criteria.get("false") or "false"))]
        if kind == "score":
            return [(str(i + 1), str(i), text(level)) for i, level in enumerate(criteria)]
        if kind == "choice":
            return [(chr(65 + i), k, text(d if d is not None else k)) for i, (k, d) in enumerate(criteria.items())]
        raise ValueError(f"DeepSeek provider has no {kind!r} question type")

    def payload(self, state, questions):
        (q,) = questions.values()
        options = self.options(q)
        if len(options) > 20:
            raise ValueError("top_logprobs reads at most 20 options")
        if q["type"] == "noul":
            ask = f"Statement: {text(q.get('instructions') or '')}\nIs the statement true of the state? Answer yes or no."
        else:
            lines = "\n".join(f"{label}: {description}" for label, _, description in options)
            ask = f"Question: {text(q.get('instructions') or '')}\n{lines}\nAnswer with one label."
        return {"model": self.model, "max_tokens": 1, "logprobs": True, "top_logprobs": 20,
                "messages": [{"role": "system", "content": "Answer with the label only."},
                             {"role": "user", "content": f"State:\n{text(state)}\n\n{ask}"}]}

    def parse(self, body, questions):
        ((qid, q),) = questions.items()
        mass = {}
        for t in body["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
            token = t["token"].strip().lower()
            mass[token] = mass.get(token, 0.0) + math.exp(t["logprob"])
        options = self.options(q)
        p = [mass.get(label.lower(), 0.0) for label, _, _ in options]
        total = sum(p)
        usage = {"input_tokens": body["usage"]["prompt_tokens"], "output_tokens": body["usage"]["completion_tokens"]}
        if not total:
            return {"model": body.get("model"), "answers": {qid: {"type": "refusal"}}, "usage": usage}
        p = [x / total for x in p]
        best = max(range(len(p)), key=p.__getitem__)
        if q["type"] == "noul":
            answer = {"type": "noul", "noul": p[0]}
        elif q["type"] == "choice":
            answer = {"type": "choice", "choice": options[best][1], "confidence": p[best],
                      "probabilities": {key: x for (_, key, _), x in zip(options, p)}}
        else:
            answer = {"type": "score", "score": sum(i * x for i, x in enumerate(p)), "confidence": p[best],
                      "legend": {key: d for _, key, d in options}, "probabilities": {key: x for (_, key, _), x in zip(options, p)}}
        return {"model": body.get("model"), "answers": {qid: answer}, "usage": usage}


def load_provider(name: str | None = None, env=os.environ) -> Provider:
    """The provider named here or by PROVIDER (a registered name or "module:Class"), configured from env."""
    name = name or env.get("PROVIDER", "typesafe")
    if name in PROVIDERS:
        cls = PROVIDERS[name]
    else:
        module, _, attr = name.partition(":")
        cls = getattr(importlib.import_module(module), attr)
    return cls.from_env(env)
