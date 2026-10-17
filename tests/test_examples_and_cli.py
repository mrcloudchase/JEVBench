import json

import pytest

from jevbench import api
from jevbench.cli import main
from jevbench.store import FrameworkStore

EXAMPLE_FILES = ["single_judge", "parallel_council", "hierarchical_council", "adversarial", "escalation_cascade",
                 "composed", "iterative_review", "image_box", "policies/majority_vote"]


@pytest.mark.parametrize("name", EXAMPLE_FILES)
def test_examples_validate_and_pass_offline_tests(examples, name):
    framework, base_dir = api.load_framework(examples / f"{name}.yaml")
    assert api.validate_framework(framework, base_dir) == []
    report = api.run_tests(framework, base_dir=base_dir)
    failures = [(r.name, r.failures, r.error) for r in report.results if not r.passed]
    assert not failures, failures


def test_examples_run_fully_mocked(examples, mock_registry):
    framework, base_dir = api.load_framework(examples / "parallel_council.yaml")
    result = api.run_framework(framework, {"message": "hi"}, providers=mock_registry, mock_all=True, base_dir=base_dir)
    assert result.judgment["decision"] in {"allow", "abstain", "human_review", "remove"}
    assert result.trace.totals()["mocked_calls"] == 3


def test_cli_validate_inspect_run_test(examples, capsys, tmp_path):
    assert main(["validate", str(examples / "adversarial.yaml")]) == 0
    assert "OK: adversarial@1.0.0" in capsys.readouterr().out
    assert main(["inspect", str(examples / "composed.yaml")]) == 0
    out = capsys.readouterr().out
    assert "policy [subgraph]" in out and "tally [vote]" in out
    trace = tmp_path / "trace.json"
    assert main(["run", str(examples / "single_judge.yaml"), "-i", str(examples / "inputs/ticket.json"), "--mock", "-f", "json", "--trace", str(trace)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["judgment"]["department"] == "billing" and data["totals"]["mocked_calls"] == 1
    assert json.loads(trace.read_text())["nodes"][0]["mocked"] is True
    assert main(["run", str(examples / "policies/majority_vote.yaml"), "-s", 'labels=["a","a","b"]']) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "a"
    assert main(["test", str(examples / "escalation_cascade.yaml")]) == 0
    assert "3 passed, 0 failed" in capsys.readouterr().out


def test_cli_reports_invalid_framework(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("jevbench: 1\nnodes:\n  a: {type: expr, value: 'nodes.zzz'}\n")
    assert main(["validate", str(bad)]) == 1
    assert "unknown node 'zzz'" in capsys.readouterr().out
    assert main(["inspect", str(bad), "-f", "json"]) == 1


def test_store_save_list_and_reference(examples, store_root, capsys, mock_registry):
    assert main(["save", str(examples / "policies/majority_vote.yaml")]) == 0
    assert main(["save", str(examples / "policies/majority_vote.yaml")]) == 2  # duplicate version refused
    assert main(["list"]) == 0
    assert "majority_vote  latest=1.0.0" in capsys.readouterr().out
    framework, base_dir = api.load_framework("majority_vote@1.0.0")
    assert framework.name == "majority_vote"
    composed = {"jevbench": 1, "nodes": {"p": {"type": "subgraph", "framework": "majority_vote", "inputs": {"labels": "input.labels"}}}}
    fw, _ = api.load_framework(composed)
    result = api.run_framework(fw, {"labels": ["x", "x", "y"]}, providers=mock_registry, store=FrameworkStore())
    assert result.judgment["decision"] == "x"


def test_schema_and_node_catalogue():
    assert set(api.node_types()) >= {"judge", "expr", "threshold", "decide", "vote", "aggregate", "consensus", "constraint", "subgraph", "loop"}
    assert "nodes" in api.framework_schema()["properties"]
    assert main(["schema", "nodes"]) == 0
