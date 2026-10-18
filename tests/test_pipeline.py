import json

import pytest
import yaml

from conftest import Fake
from tdm import Project, execute, report_experiment, score_experiment


@pytest.fixture
def project(tmp_path, records, questions):
    """A tiny project on disk: one task, two models, one experiment."""
    (tmp_path / "configs" / "models").mkdir(parents=True)
    (tmp_path / "configs" / "experiments").mkdir()
    for name in ("a", "b"):
        (tmp_path / "configs" / "models" / f"{name}.yaml").write_text(yaml.safe_dump({"provider": "von", "model": "m", "repeats": 2}))
    (tmp_path / "configs" / "experiments" / "e.yaml").write_text(yaml.safe_dump({"tasks": ["t"], "models": ["a", "b"]}))
    task = tmp_path / "tasks" / "t"
    task.mkdir(parents=True)
    (task / "questions.yaml").write_text(yaml.safe_dump(questions))
    (task / "manifest.jsonl").write_text("".join(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in records))
    (task / "data.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    return Project(tmp_path)


def test_a_run_is_a_folder_with_a_manifest_and_resumes(project):
    first = execute(project, "t", "a", "2026-01-01", Fake(fail_on={"refund please"}))
    meta = first.meta
    assert first.dir.name == f"2026-01-01_a_t_{project.task('t').version[:8]}"
    assert meta["status"] == "incomplete" and meta["rows"] == 4 and meta["expected_rows"] == 6
    again = execute(project, "t", "a", "2026-01-01", Fake())
    assert again.complete and again.meta["rows"] == 6 and again.meta["served"] == ["fake-1"]
    untouched = Fake()
    execute(project, "t", "a", "2026-01-01", untouched)
    assert untouched.calls == 0                                   # a complete run is never run again
    assert execute(project, "t", "a", "2026-01-02", Fake()).dir != again.dir


def test_data_must_match_the_manifest(project):
    path = project.task("t").dir / "data.jsonl"
    path.write_text(path.read_text().replace('"label": 0', '"label": 1'))
    with pytest.raises(ValueError, match="does not match"):
        project.task("t").records()


def test_score_and_report_read_only_the_stage_before(project):
    execute(project, "t", "a", "2026-01-01", Fake())
    execute(project, "t", "b", "2026-01-01", Fake(answer=lambda s: {"refund": {"type": "noul", "noul": 0.6}}))
    scores = score_experiment(project, "e")["tasks"]["t"]
    a, b = scores["runs"]
    assert (a["model"], a["accuracy"], b["accuracy"]) == ("a", 1.0, pytest.approx(2 / 3))
    assert scores["paired"][0]["delta"] == pytest.approx(-1 / 3)
    text = report_experiment(project, "e")
    assert "| a | fake-1 | 3 | 2 |" in text and (project.root / "reports" / "e.t.csv").exists()


def test_a_task_change_needs_a_new_run(project):
    execute(project, "t", "a", "2026-01-01", Fake())
    (project.task("t").dir / "questions.yaml").write_text(yaml.safe_dump({"refund": {"type": "noul", "instructions": "Refund?"}}))
    assert project.latest("t", "a") is None
