"""Data: the questions file, the dataset, and the results file."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def load_questions(path: str | Path) -> dict:
    """The task: questions in the wire format, keyed by question id."""
    questions = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(questions, dict) or not questions:
        raise ValueError(f"{path}: expected a mapping of question id -> question")
    return questions


def load_dataset(path: str | Path) -> list[dict]:
    """The data: JSONL, one record per line, or a YAML list of the same records.
    Each record has `id` and `state`; `label`, its own `questions` and any other fields are optional."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    records = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else yaml.safe_load(text)
    seen = set()
    for n, record in enumerate(records, 1):
        if "id" not in record or "state" not in record:
            raise ValueError(f"{path}: record {n} needs `id` and `state`")
        if record["id"] in seen:
            raise ValueError(f"{path}: duplicate id {record['id']!r}")
        seen.add(record["id"])
    return records


class Results:
    """An append-only JSONL file of results. Ids with answers are done; failed ids are dropped and retried."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        previous = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()] if self.path.exists() else []
        kept = [r for r in previous if "answers" in r]
        if len(kept) != len(previous):
            self.path.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
        self.done = {r["id"] for r in kept}
        self.retried = len(previous) - len(kept)

    def __enter__(self):
        self.file = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self.file.close()

    def write(self, result: dict) -> None:
        self.file.write(json.dumps(result) + "\n")
        self.file.flush()
