import json

import pytest

from conftest import Fake
from tdm.decision import (ABSTAIN, Chained, Decision, EvaluatorOptimizer, Live, OrchestratorWorker, Parallel, Recorded,
                          Single, compare, confidence, decide_all, score_decisions, top)

threshold = Decision(lambda b, theta: int(b["refund"]["noul"] >= theta), theta=0.5)


def recorded(tmp_path, name, probs, cost=0.0):
    rows = [{"id": i, "repeat": 0, "label": label, "answers": {"refund": {"type": "noul", "noul": p}}, "cost_usd": cost}
            for i, (p, label) in probs.items()]
    (tmp_path / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return Recorded(tmp_path / f"{name}.jsonl")


def test_values_are_named_and_replaceable():
    b = {"refund": {"type": "noul", "noul": 0.6}}
    assert threshold(b) == 1 and threshold.given(theta=0.7)(b) == 0 and threshold.values == {"theta": 0.5}


def test_top_and_confidence_for_every_type():
    assert (top({"type": "noul", "noul": 0.3}), confidence({"type": "noul", "noul": 0.3})) == (0, 0.7)
    choice = {"type": "choice", "probabilities": {"x": 0.2, "y": 0.8}}
    score = {"type": "score", "probabilities": {"0": 0.1, "1": 0.3, "2": 0.6}}
    assert (top(choice), confidence(choice), top(score)) == ("y", 0.8, 2)
    assert top({"type": "refusal"}) is None and confidence({"type": "refusal"}) == 0.0


def test_single_over_recorded_beliefs_and_scoring(tmp_path):
    src = recorded(tmp_path, "m", {"a": (0.9, 1), "b": (0.4, 1), "c": (0.2, 0)})
    out = decide_all(Single(src, threshold), src.records())
    s = score_decisions(out, loss=lambda a, y: 0 if a == y else 1)
    assert s["accuracy"] == pytest.approx(2 / 3) and s["coverage"] == 1.0 and s["risk"] == pytest.approx(1 / 3)
    assert compare(out, decide_all(Single(src, threshold.given(theta=0.3)), src.records()))["delta"] == pytest.approx(1 / 3)


def test_abstain_counts_against_accuracy_not_selective_accuracy(tmp_path):
    src = recorded(tmp_path, "m", {"a": (0.95, 1), "b": (0.55, 0)})
    gate = Decision(lambda b, tau: top(b["refund"]) if confidence(b["refund"]) >= tau else ABSTAIN, tau=0.9)
    s = score_decisions(decide_all(Single(src, gate), src.records()))
    assert (s["accuracy"], s["coverage"], s["selective_accuracy"]) == (0.5, 0.5, 1.0)


def test_parallel_and_orchestrator_worker(tmp_path):
    cheap = recorded(tmp_path, "cheap", {"a": (0.55, 1), "b": (0.05, 0)}, cost=0.0)
    hosted = recorded(tmp_path, "hosted", {"a": (0.9, 1), "b": (0.6, 0)}, cost=0.01)
    vote = Decision(lambda *bs: int(sum(top(b["refund"]) for b in bs) * 2 > len(bs)))
    assert [o["calls"] for o in decide_all(Parallel([cheap, hosted], vote), cheap.records())] == [2, 2]
    gate = Decision(lambda b, tau: top(b["refund"]) if confidence(b["refund"]) >= tau else "escalate", tau=0.8)
    out = {o["id"]: o for o in decide_all(OrchestratorWorker(Single(cheap, gate), {"escalate": Single(hosted, threshold)}), cheap.records())}
    assert out["a"]["routed"] == "escalate" and out["a"]["action"] == 1 and out["a"]["cost_usd"] == 0.01
    assert out["b"]["routed"] is None and out["b"]["action"] == 0 and out["b"]["calls"] == 1


def test_chained_passes_the_first_belief_as_evidence(questions):
    seen = []
    fake = Fake(answer=lambda state: (seen.append(state), {"refund": {"type": "noul", "noul": 0.8}})[1])
    first = Live(questions, fake)
    then = Live(questions, fake, evidence=lambda r, formed: {"text": r["state"], "earlier": formed[0]["refund"]["noul"]})
    out = Chained([first, then], Decision(lambda b1, b2: top(b2["refund"])))({"id": "a", "state": "refund"})
    assert seen == ["refund", {"text": "refund", "earlier": 0.8}] and out["action"] == 1 and out["calls"] == 2


def test_evaluator_optimizer_stops_when_done_or_out_of_rounds(questions):
    probs = iter([0.6, 0.65, 0.95])
    fake = Fake(answer=lambda state: {"refund": {"type": "noul", "noul": next(probs)}})
    done = Decision(lambda b: confidence(b["refund"]) >= 0.9)
    out = EvaluatorOptimizer(Live(questions, fake, evidence=lambda r, formed: (r["state"], len(formed))), done,
                             Decision(lambda b: top(b["refund"])), rounds=3)({"id": "a", "state": "x"})
    assert out["rounds"] == 3 and out["action"] == 1 and fake.calls == 3
