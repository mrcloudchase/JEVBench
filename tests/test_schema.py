import pytest

from jevbench.errors import SchemaError
from jevbench.schema.models import Question
from jevbench.schema.validator import analyze
from jevbench.store import framework_from_data


def fw(nodes, **extra):
    return framework_from_data({"jevbench": 1, "name": "t", "nodes": nodes, **extra})


def test_single_node_output_defaults():
    framework = fw({"j": {"type": "expr", "value": "1"}})
    assert framework.output == "nodes.j"


def test_multi_node_requires_output():
    with pytest.raises(SchemaError, match="output"):
        fw({"a": {"type": "expr", "value": "1"}, "b": {"type": "expr", "value": "2"}})


def test_schema_version_enforced():
    with pytest.raises(SchemaError, match="schema version"):
        framework_from_data({"jevbench": 2, "nodes": {"a": {"type": "expr", "value": "1"}}})


@pytest.mark.parametrize(
    "question",
    [
        {"type": "choice", "criteria": {}},
        {"type": "choice", "criteria": {str(i): None for i in range(256)}},
        {"type": "score", "criteria": ["one"]},
        {"type": "score", "criteria": [str(i) for i in range(11)]},
        {"type": "noul"},
        {"type": "noul", "instructions": "x", "criteria": {"yes": "y"}},
        {"type": "box", "instructions": "x", "criteria": ["no"]},
    ],
)
def test_question_constraints(question):
    with pytest.raises(Exception):
        Question(**question)


def test_question_wire_form_drops_none():
    assert Question(type="noul", instructions="q").to_wire() == {"type": "noul", "instructions": "q"}


def test_unknown_node_type_and_bad_fields():
    assert any("unknown node type 'nope'" in p for p in analyze(fw({"a": {"type": "nope"}})).problems)
    analysis = analyze(fw({"a": {"type": "threshold", "value": "1"}}))
    assert any("min and/or max" in p for p in analysis.problems)


def test_unknown_reference_and_cycle_detected():
    analysis = analyze(fw({"a": {"type": "expr", "value": "nodes.zzz"}}))
    assert any("unknown node 'zzz'" in p for p in analysis.problems)
    analysis = analyze(fw({"a": {"type": "expr", "value": "nodes.b"}, "b": {"type": "expr", "value": "nodes.a"}}, output="nodes.a"))
    assert any("cycle" in p for p in analysis.problems)


def test_dynamic_reference_requires_depends_on():
    analysis = analyze(fw({"a": {"type": "expr", "value": "1"}, "b": {"type": "expr", "value": "nodes[input.k]"}}, output="nodes.b"))
    assert any("depends_on" in p for p in analysis.problems)
    analysis = analyze(fw({"a": {"type": "expr", "value": "1"}, "b": {"type": "expr", "value": "nodes[input.k]", "depends_on": ["a"]}}, output="nodes.b"))
    assert analysis.ok and analysis.graph.levels == [["a"], ["b"]]


def test_levels_and_api_bound():
    nodes = {
        "j1": {"type": "judge", "state": "x", "questions": {"q": {"type": "noul", "instructions": "?"}}},
        "j2": {"type": "judge", "state": "x", "questions": {"q": {"type": "noul", "instructions": "?"}}},
        "agg": {"type": "aggregate", "values": ["nodes.j1.answers.q.noul", "nodes.j2.answers.q.noul"]},
        "loop": {"type": "loop", "max_iterations": 4, "inputs": {"x": "nodes.agg"},
                 "body": {"nodes": {"j": {"type": "judge", "state": "${input.x}", "questions": {"q": {"type": "noul", "instructions": "?"}}}}}},
    }
    analysis = analyze(fw(nodes, output="nodes.loop"))
    assert analysis.ok, analysis.all_problems()
    assert analysis.graph.levels == [["j1", "j2"], ["agg"], ["loop"]]
    assert analysis.api_call_bound() == 2 + 4
