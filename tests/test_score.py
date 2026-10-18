import json

import pytest

from tdm.score import ChoiceScorer, NoulScorer, ScoreScorer, ScoredRun, paired


def noul(p):
    return {"type": "noul", "noul": p}


def test_noul_metrics():
    pairs = [(noul(0.9), 1), (noul(0.6), 0), (noul(0.4), 1), (noul(0.1), 0)]
    m = NoulScorer(0.5).metrics(pairs)
    assert m["accuracy"] == 0.5 and m["precision"] == 0.5 and m["recall"] == 0.5
    assert m["auroc"] == pytest.approx(0.75)                     # 3 of 4 positive-negative pairs ranked right
    assert m["brier"] == pytest.approx((0.01 + 0.36 + 0.36 + 0.01) / 4)


def test_choice_and_score_metrics():
    a = {"type": "choice", "choice": "x", "probabilities": {"x": 0.8, "y": 0.2}}
    assert ChoiceScorer().metrics([(a, "x"), (a, "y")])["accuracy"] == 0.5
    s = {"type": "score", "score": 1.2, "probabilities": {"0": 0.1, "1": 0.6, "2": 0.3}}
    m = ScoreScorer().metrics([(s, 1), (s, 2)])
    assert m["accuracy"] == 0.5 and m["within_one"] == 1.0 and m["mae"] == pytest.approx((0.2 + 0.8) / 2)


def test_refusal_is_wrong_not_an_error(tmp_path):
    rows = [{"id": "a", "repeat": 0, "label": "x", "answers": {"q": {"type": "refusal"}}},
            {"id": "b", "repeat": 0, "label": "x", "answers": {"q": {"type": "choice", "choice": "x", "probabilities": {"x": 1.0}}}}]
    (tmp_path / "r.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    s = ScoredRun(tmp_path / "r.jsonl", None, "label", 0.5).summary()
    assert s["accuracy"] == 0.5 and s["refusals"] == 1 and s["errors"] == 0


def test_paired_bootstrap():
    d = paired({"a": True, "b": False, "c": True}, {"a": True, "b": True, "c": True, "z": False})
    assert d["n"] == 3 and d["delta"] == pytest.approx(1 / 3) and d["only_other_right"] == 1
    assert d["ci95"][0] <= d["delta"] <= d["ci95"][1]
