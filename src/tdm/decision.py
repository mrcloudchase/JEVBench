"""The second primitive: a decision rule applied to beliefs with explicit values.

    action = Decision(rule, **values)(*beliefs)

A rule is a pure expression over beliefs (providers' answers, in the wire format's shapes) and values
(thresholds, costs, labels) that returns an action or ABSTAIN. An action is a label; acting on it is
ordinary code, e.g. `handlers[action](record)`. Values are named, so `decision.given(theta=0.7)` is the
same rule with other values, and recorded beliefs can be decided again without calling a model.

A unit is a belief and a decision. An architecture is units wired one of five ways:

    Single(belief, decision)                          one unit
    Chained([b1, b2, ...], decision)                  each belief is evidence for the next
    Parallel([b1, b2, ...], decision)                 independent beliefs, one decision over all of them
    OrchestratorWorker(unit, {action: architecture})  a unit's action picks the architecture that runs next
    EvaluatorOptimizer(belief, done, decision)        re-ask with the last belief until `done`, at most n rounds

Beliefs come from a Source: Live (a provider call) or Recorded (a results file from tdm.belief, by record id),
so the same architecture runs live or offline. Each architecture returns an outcome: the action and what
it cost (calls, dollars, latency, rounds).
"""

from __future__ import annotations

import json
import statistics
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterable

from .data import read_jsonl
from .score import paired

ABSTAIN = "abstain"


class Decision:
    """A rule and its values. Calling it with beliefs returns an action."""

    def __init__(self, rule: Callable, **values):
        self.rule, self.values = rule, values

    def __call__(self, *beliefs):
        return self.rule(*beliefs, **self.values)

    def given(self, **values) -> "Decision":
        return Decision(self.rule, **{**self.values, **values})


# ====================================================================== where beliefs come from
class Source(ABC):
    """A record (and what earlier steps believed) -> a provider response: answers, cost_usd, latency_ms."""

    @abstractmethod
    def __call__(self, record: dict, context=None) -> dict | None: ...


class Live(Source):
    """Ask a provider. `evidence(record, context)` builds the state; by default it is the record's own."""

    def __init__(self, questions: dict, provider, evidence: Callable = None, cache=None):
        self.questions, self.provider, self.cache = questions, provider, cache
        self.evidence = evidence or (lambda record, context: record["state"])

    def __call__(self, record, context=None):
        state = self.evidence(record, context)
        key = self.cache and self.provider.key(state, self.questions)
        response = self.cache and self.cache.get(key)
        if not response:
            try:
                response = self.provider(state, self.questions)
            except Exception as exc:                       # a failed call is an empty belief, not a crash
                return {"error": str(exc)}
            if self.cache:
                self.cache.put(key, response)
        return response


class Recorded(Source):
    """Beliefs already formed: a results file from tdm.belief, read back by record id. Costs nothing to ask."""

    def __init__(self, path: str | Path, repeat: int = 0):
        self.path = Path(path)
        self.rows = {r["id"]: r for r in read_jsonl(self.path) if r.get("repeat", 0) == repeat and "answers" in r}

    def __call__(self, record, context=None):
        return self.rows.get(record["id"])

    def records(self) -> list[dict]:
        """The recorded rows themselves: id, label and the other fields tdm.belief copied through."""
        return list(self.rows.values())


def answers(response):
    return response.get("answers") if response else None


def top(answer):
    """The answer's most probable option: 1/0 for noul, the option for choice, the level index for score."""
    if not answer or answer.get("type") == "refusal":
        return None
    if answer["type"] == "noul":
        return int(answer["noul"] >= 0.5)
    best = max(answer["probabilities"], key=answer["probabilities"].get)
    return int(best) if answer["type"] == "score" else best


def confidence(answer) -> float:
    """The top option's probability, the same statistic for every provider: max(p, 1 - p) for noul."""
    if not answer or answer.get("type") == "refusal":
        return 0.0
    if answer["type"] == "noul":
        return max(answer["noul"], 1 - answer["noul"])
    return max(answer["probabilities"].values())


def outcome(action, responses: list, parallel: bool = False, **extra) -> dict:
    """The action and what forming its beliefs cost. Parallel calls cost their sum but take the longest one's time."""
    made = [r for r in responses if r]
    latencies = [r.get("latency_ms") or 0 for r in made]
    return {"action": action, "calls": len(made), "cost_usd": sum(r.get("cost_usd") or 0 for r in made),
            "latency_ms": (max(latencies, default=0) if parallel else sum(latencies)),
            "beliefs": [answers(r) for r in responses], **extra}


# ====================================================================== the five structures
class Architecture(ABC):
    @abstractmethod
    def __call__(self, record: dict) -> dict: ...


class Single(Architecture):
    def __init__(self, belief: Source, decision: Decision):
        self.belief, self.decision = belief, decision

    def __call__(self, record):
        response = self.belief(record)
        b = answers(response)
        return outcome(self.decision(b) if b else ABSTAIN, [response])


class Chained(Architecture):
    """Each belief after the first gets the previous beliefs as context for its evidence."""

    def __init__(self, beliefs: list[Source], decision: Decision):
        self.beliefs, self.decision = beliefs, decision

    def __call__(self, record):
        responses, formed = [], []
        for belief in self.beliefs:
            response = belief(record, formed)
            responses.append(response)
            if not answers(response):
                return outcome(ABSTAIN, responses)
            formed.append(answers(response))
        return outcome(self.decision(*formed), responses)


class Parallel(Architecture):
    """Independent beliefs, formed concurrently; the decision sees all of them (missing ones as None)."""

    def __init__(self, beliefs: list[Source], decision: Decision):
        self.beliefs, self.decision = beliefs, decision

    def __call__(self, record):
        with ThreadPoolExecutor(max_workers=len(self.beliefs)) as pool:
            responses = list(pool.map(lambda b: b(record), self.beliefs))
        return outcome(self.decision(*map(answers, responses)), responses, parallel=True)


class OrchestratorWorker(Architecture):
    """The orchestrator unit's action names a worker architecture to run, or is the final action itself."""

    def __init__(self, orchestrator: Single, workers: dict[str, Architecture]):
        self.orchestrator, self.workers = orchestrator, workers

    def __call__(self, record):
        first = self.orchestrator(record)
        worker = self.workers.get(first["action"])
        if worker is None:
            return {**first, "routed": None}
        second = worker(record)
        return {**second, "calls": first["calls"] + second["calls"], "cost_usd": first["cost_usd"] + second["cost_usd"],
                "latency_ms": first["latency_ms"] + second["latency_ms"], "beliefs": first["beliefs"] + second["beliefs"],
                "routed": first["action"]}


class EvaluatorOptimizer(Architecture):
    """Ask; while `done(belief)` is false and rounds remain, ask again with the beliefs so far as context."""

    def __init__(self, belief: Source, done: Decision, decision: Decision, rounds: int = 3):
        self.belief, self.done, self.decision, self.rounds = belief, done, decision, rounds

    def __call__(self, record):
        responses, formed = [], []
        for _ in range(self.rounds):
            response = self.belief(record, formed)
            responses.append(response)
            if not answers(response):
                break
            formed.append(answers(response))
            if self.done(formed[-1]):
                break
        return outcome(self.decision(formed[-1]) if formed else ABSTAIN, responses, rounds=len(formed))


def decide_all(architecture: Architecture, records: Iterable[dict], workers: int = 8, keep=("id", "label")) -> list[dict]:
    """Run an architecture over records; each outcome keeps the record's `keep` fields."""
    def one(record):
        return {**{k: record[k] for k in keep if k in record}, **architecture(record)}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, records))


# ====================================================================== scoring decisions
def correct(action, label) -> bool:
    return action != ABSTAIN and str(action) == str(label)


def score_decisions(outcomes: list[dict], loss: Callable | None = None) -> dict:
    """Accuracy counts an abstention as wrong; selective accuracy is over the decisions made.
    With `loss(action, label)`, also the expected loss per decision (the empirical risk)."""
    acted = [o for o in outcomes if o["action"] != ABSTAIN]
    out = {"n": len(outcomes),
           "accuracy": statistics.fmean(correct(o["action"], o["label"]) for o in outcomes),
           "coverage": len(acted) / len(outcomes),
           "selective_accuracy": statistics.fmean(correct(o["action"], o["label"]) for o in acted) if acted else None,
           "calls_per_item": statistics.fmean(o["calls"] for o in outcomes),
           "usd_per_1k": 1000 * statistics.fmean(o["cost_usd"] for o in outcomes),
           "latency_ms_mean": statistics.fmean(o["latency_ms"] for o in outcomes)}
    if loss:
        out["risk"] = statistics.fmean(loss(o["action"], o["label"]) for o in outcomes)
    return out


def compare(base: list[dict], other: list[dict]) -> dict:
    """Accuracy of `other` minus `base` on the same records, with a 95% bootstrap interval."""
    return paired({o["id"]: correct(o["action"], o["label"]) for o in base},
                  {o["id"]: correct(o["action"], o["label"]) for o in other})


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
