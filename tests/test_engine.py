import pytest

from jevbench.engine.executor import run
from jevbench.errors import ExecutionError
from jevbench.store import framework_from_data

Q = {"label": {"type": "choice", "instructions": "?", "criteria": {"a": None, "b": None, "c": None}},
     "score": {"type": "score", "instructions": "?", "criteria": ["lo", "mid", "hi"]},
     "flag": {"type": "noul", "instructions": "?"}}


def fw(nodes, **extra):
    return framework_from_data({"jevbench": 1, "name": "t", "nodes": nodes, **extra})


def judge(state="${input.text}", **kw):
    return {"type": "judge", "state": state, "questions": Q, **kw}


def test_judge_mock_all_and_pinned_mocks(mock_registry):
    framework = fw({"j": judge()})
    result = run(framework, {"text": "x"}, providers=mock_registry, mock_all=True)
    assert result.judgment["answers"]["label"]["choice"] == "a"
    assert result.trace.nodes[0].mocked and result.trace.nodes[0].issue["state"] == "x"
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"j": {"label": "c", "score": 1.5, "flag": 0.9}})
    answers = result.judgment["answers"]
    assert answers["label"]["choice"] == "c" and answers["score"]["score"] == 1.5 and answers["flag"]["noul"] == 0.9
    assert answers["score"]["probabilities"] == {"0": 0.0, "1": 0.5, "2": 0.5}


def test_mock_provider_from_registry(mock_registry):
    framework = fw({"j": {"type": "judge", "provider": "mock", "state": "s",
                          "questions": {"department": {"type": "choice", "instructions": "?", "criteria": {"billing": None, "technical": None}}}}})
    result = run(framework, {}, providers=mock_registry)
    assert result.judgment["answers"]["department"]["choice"] == "billing"
    assert result.trace.totals()["api_calls"] == 0 and result.trace.nodes[0].provider == "mock"


def test_policy_nodes(mock_registry):
    nodes = {
        "a": judge(), "b": judge(), "c": judge(),
        "vote": {"type": "vote", "values": ["nodes.a.answers.label.choice", "nodes.b.answers.label.choice", "nodes.c.answers.label.choice"], "method": "majority"},
        "mean": {"type": "aggregate", "values": ["nodes.a.answers.score.score", "nodes.b.answers.score.score"], "weights": [3, 1]},
        "spread": {"type": "aggregate", "method": "spread", "from": "[nodes.a.answers.score.score, nodes.b.answers.score.score]"},
        "cons": {"type": "consensus", "values": ["nodes.a.answers.flag.noul", "nodes.b.answers.flag.noul"], "tolerance": 0.2},
        "thr": {"type": "threshold", "value": "nodes.mean", "min": 1, "max": 2},
        "guard": {"type": "constraint", "rules": [{"name": "r1", "require": "nodes.thr"}, {"name": "r2", "require": "nodes.cons.agreed"}]},
        "expr": {"type": "expr", "value": "sorted(nodes.vote.tally.keys())"},
        "dec": {"type": "decide", "cases": [{"when": "not nodes.guard.satisfied", "then": "review"}, {"when": "nodes.vote.winner == 'a'", "then": "${nodes.vote.winner}!"}], "default": "none"},
    }
    framework = fw(nodes, output={"d": "${nodes.dec}", "v": "${nodes.vote}", "m": "${nodes.mean}", "s": "${nodes.spread}", "c": "${nodes.cons}", "g": "${nodes.guard}", "e": "${nodes.expr}"})
    mocks = {"a": {"label": "a", "score": 2, "flag": 0.9}, "b": {"label": "a", "score": 0, "flag": 0.8}, "c": {"label": "b", "score": 1, "flag": 0.1}}
    j = run(framework, {"text": "x"}, providers=mock_registry, mocks=mocks).judgment
    assert j["v"]["winner"] == "a" and j["v"]["tally"] == {"a": 2.0, "b": 1.0} and not j["v"]["unanimous"]
    assert j["m"] == 1.5 and j["s"] == 2.0
    assert j["c"] == {"agreed": True, "value": pytest.approx(0.85), "spread": pytest.approx(0.1)}
    assert j["g"] == {"satisfied": True, "violations": []}
    assert j["e"] == ["a", "b"] and j["d"] == "a!"


def test_vote_tie_and_unanimous(mock_registry):
    nodes = {"v": {"type": "vote", "from": "input.labels", "method": "unanimous"}, "p": {"type": "vote", "from": "input.labels", "tie": "first"}}
    framework = fw(nodes, output={"v": "${nodes.v.winner}", "p": "${nodes.p}"})
    j = run(framework, {"labels": ["x", "y"]}, providers=mock_registry).judgment
    assert j["v"] is None and j["p"]["tied"] and j["p"]["winner"] == "x"
    j = run(framework, {"labels": ["x", "x"]}, providers=mock_registry).judgment
    assert j["v"] == "x"


def test_when_skips_node_and_downstream_sees_null(mock_registry):
    nodes = {"j": judge(), "esc": judge(when="nodes.j.answers.label.confidence < 0.5"),
             "out": {"type": "decide", "cases": [{"when": "nodes.esc is None", "then": "first"}], "default": "escalated"}}
    framework = fw(nodes, output="nodes.out")
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"j": {"label": "a"}})
    assert result.judgment == "first" and result.trace.totals()["skipped"] == 1
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"j": {"label": {"a": 0.4, "b": 0.3, "c": 0.3}}, "esc": {"label": "b"}})
    assert result.judgment == "escalated"


def test_loop_bounded_and_until(mock_registry):
    body = {"nodes": {"j": judge(state="${input.text} ${loop.iteration} ${loop.previous}")}, "output": "nodes.j.answers.flag.noul"}
    framework = fw({"l": {"type": "loop", "max_iterations": 3, "until": "nodes.j.answers.flag.noul > 0.8", "body": body}})
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"l.j": [{"flag": 0.2}, {"flag": 0.9}]})
    assert result.judgment == {"value": 0.9, "iterations": 2, "converged": True, "history": [0.2, 0.9]}
    iterations = [n.iteration for n in result.trace.all_nodes() if n.path == "l.j"]
    assert iterations == [1, 2]
    assert result.trace.nodes[0].children[1].issue["state"] == "x 2 0.2"
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"l.j": {"flag": 0.1}})
    assert result.judgment["iterations"] == 3 and not result.judgment["converged"]


def test_subgraph_inline_and_file(tmp_path, mock_registry):
    (tmp_path / "policy.yaml").write_text(
        "jevbench: 1\nname: p\nnodes:\n  d: {type: decide, cases: [{when: 'input.x > 1', then: big}], default: small}\n")
    nodes = {"j": judge(), "inline": {"type": "subgraph", "inputs": {"x": "nodes.j.answers.score.score"},
                                      "body": {"nodes": {"e": {"type": "expr", "value": "input.x * 10"}}}},
             "file": {"type": "subgraph", "framework": "policy.yaml", "inputs": {"x": "nodes.j.answers.score.score"}}}
    framework = fw(nodes, output={"i": "${nodes.inline}", "f": "${nodes.file}"})
    result = run(framework, {"text": "x"}, providers=mock_registry, mocks={"j": {"score": 2}}, base_dir=tmp_path)
    assert result.judgment == {"i": 20.0, "f": "big"}
    by_id = {n.id: n for n in result.trace.nodes}
    assert [c.path for c in by_id["file"].children] == ["file.d"] and [c.path for c in by_id["inline"].children] == ["inline.e"]


def test_missing_input_and_node_error_keep_trace(mock_registry):
    framework = framework_from_data({"jevbench": 1, "inputs": {"text": {}}, "nodes": {"j": judge()}})
    with pytest.raises(ExecutionError, match="missing required input"):
        run(framework, {}, providers=mock_registry)
    framework = fw({"j": judge(), "bad": {"type": "expr", "value": "nodes.j.answers.nope"}}, output="nodes.bad")
    with pytest.raises(ExecutionError) as info:
        run(framework, {"text": "x"}, providers=mock_registry, mock_all=True)
    assert info.value.node_path == "bad" and info.value.trace.status == "error"
    assert [n.status for n in info.value.trace.nodes] == ["ok", "error"]


def test_parallel_level_runs_concurrently(mock_registry):
    nodes = {f"j{i}": judge() for i in range(6)}
    framework = fw(nodes, output="[nodes.j0, nodes.j5]")
    result = run(framework, {"text": "x"}, providers=mock_registry, mock_all=True, max_workers=4)
    assert len(result.judgment) == 2 and result.trace.totals()["mocked_calls"] == 6
