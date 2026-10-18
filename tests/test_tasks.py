"""Every committed task loads: its questions parse, its data matches its manifest, and every label is an option."""
from pathlib import Path

import pytest

from tdm import Project

ROOT = Path(__file__).resolve().parents[1]
TASKS = sorted(p.parent.name for p in (ROOT / "tasks").glob("*/questions.yaml"))


@pytest.mark.parametrize("name", TASKS)
def test_task_is_well_formed(name):
    task = Project(ROOT).task(name)
    (qid, question), = task.questions.items()
    records = task.records()
    assert records and len({r["id"] for r in records}) == len(records)
    if question["type"] == "choice":
        assert {str(r["label"]) for r in records} <= set(question["criteria"])
    assert all(r["state"] for r in records)
