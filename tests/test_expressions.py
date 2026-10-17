import pytest

from jevbench.engine.expressions import evaluate, node_references, render, template_expressions
from jevbench.errors import ExpressionError

SCOPE = {
    "input": {"text": "hi", "n": 3},
    "nodes": {"a": {"answers": {"q": {"choice": "x", "probabilities": {"x": 0.7, "y": 0.3}, "confidence": 0.55}}}, "b": None},
    "loop": None,
}


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("nodes.a.answers.q.choice == 'x'", True),
        ("nodes.a.answers.q.confidence > 0.5 and input.n == 3", True),
        ("argmax(nodes.a.answers.q.probabilities)", "x"),
        ("[k for k, v in nodes.a.answers.q.probabilities.items() if v > 0.5]", ["x"]),
        ("nodes.b is None", True),
        ("nodes['a'].answers.q.probabilities['y']", 0.3),
        ("mean([1, 2, 3])", 2.0),
        ("'yes' if nodes.a.answers.q.confidence > 0.5 else 'no'", "yes"),
        ("input.text.upper()", "HI"),
        ("nodes.a.answers.q.probabilities.get('z', 0)", 0),
        ("clamp(5, 0, 1)", 1),
        ("round(0.456, 1)", 0.5),
    ],
)
def test_evaluate(expression, expected):
    assert evaluate(expression, SCOPE) == expected


@pytest.mark.parametrize(
    "expression",
    ["__import__('os')", "open('x')", "nodes.a._private", "(lambda: 1)()", "nodes.b.answers", "nodes.a.answers.missing", "input.text.__class__", "x := 1"],
)
def test_unsafe_or_bad_expressions_raise(expression):
    with pytest.raises(ExpressionError):
        evaluate(expression, SCOPE)


def test_render_templates():
    out = render({"whole": "${nodes.a.answers.q}", "text": "Hi ${input.text}! n=${input.n}", "list": ["${input.n}"]}, SCOPE)
    assert out["whole"] == SCOPE["nodes"]["a"]["answers"]["q"]
    assert out["text"] == "Hi hi! n=3"
    assert out["list"] == [3]


def test_template_expressions_and_references():
    assert template_expressions({"a": "${nodes.x.y} and ${input.z}", "b": ["${nodes.w}"]}) == ["nodes.x.y", "input.z", "nodes.w"]
    assert node_references("nodes.a.answers.q.choice == nodes['b']") == ({"a", "b"}, False)
    assert node_references("nodes[name]")[1] is True
    assert node_references("input.x")[0] == set()
