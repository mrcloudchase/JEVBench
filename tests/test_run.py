import os

import pytest

from conftest import Fake
from tdm.data import Cache, load_dataset
from tdm.run import Belief, load_env, run


def test_belief_returns_the_answers(fake, questions):
    assert Belief(questions, fake)("I want a refund")["refund"]["noul"] == 0.9


def test_run_sends_only_state_and_copies_the_rest(fake, records, questions):
    out = {r["id"]: r for r in run(records, questions, fake)}
    assert out["a"]["label"] == 1 and out["a"]["source"] == "x" and out["a"]["repeat"] == 0
    assert "state" not in out["a"] and out["a"]["answers"]["refund"]["noul"] == 0.9


def test_repeats_skips_and_errors(records, questions):
    fake = Fake(fail_on={"Where is my order?"})
    out = list(run(records, questions, fake, repeats=2, done={("a", 0)}))
    assert len(out) == 5 and fake.calls == 5
    assert sum("error" in r for r in out) == 2                     # a failure is recorded, not raised


def test_cache_answers_a_repeated_request(tmp_path, fake, records, questions):
    cache = Cache(tmp_path / "cache.jsonl")
    list(run(records, questions, fake, cache=cache))
    again = list(run(records, questions, fake, cache=Cache(tmp_path / "cache.jsonl")))
    assert fake.calls == 3 and all(r["cached"] for r in again)


def test_dataset_needs_unique_ids_and_state(tmp_path):
    (tmp_path / "d.jsonl").write_text('{"id": "a", "state": "x"}\n{"id": "a", "state": "y"}\n')
    with pytest.raises(ValueError, match="duplicate"):
        load_dataset(tmp_path / "d.jsonl")
    (tmp_path / "d.jsonl").write_text('{"id": "a"}\n')
    with pytest.raises(ValueError, match="state"):
        load_dataset(tmp_path / "d.jsonl")


def test_load_env_keeps_quotes_drops_comments_and_does_not_override(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text('A_Q="x # y"\nA_C=plain  # comment\nA_SET=file\n')
    monkeypatch.setenv("A_SET", "env")
    for k in ("A_Q", "A_C"):
        monkeypatch.delenv(k, raising=False)
    load_env(tmp_path / ".env")
    assert (os.environ["A_Q"], os.environ["A_C"], os.environ["A_SET"]) == ("x # y", "plain", "env")
