"""Data: the questions file, the dataset, the results file and the response cache."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import yaml


def read_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    records = read_jsonl(path) if path.suffix == ".jsonl" else yaml.safe_load(path.read_text(encoding="utf-8"))
    seen = set()
    for n, record in enumerate(records, 1):
        if "id" not in record or "state" not in record:
            raise ValueError(f"{path}: record {n} needs `id` and `state`")
        if record["id"] in seen:
            raise ValueError(f"{path}: duplicate id {record['id']!r}")
        seen.add(record["id"])
    return records


class Results:
    """An append-only JSONL file of results, one line per (id, repeat).
    Answered (id, repeat) pairs are done; failed ones are dropped from the file and retried."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        previous = read_jsonl(self.path)
        kept = [r for r in previous if "answers" in r]
        if len(kept) != len(previous):
            self.path.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
        self.done = {(r["id"], r.get("repeat", 0)) for r in kept}
        self.retried = len(previous) - len(kept)

    def __enter__(self):
        self.file = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self.file.close()

    def write(self, result: dict) -> None:
        self.file.write(json.dumps(result) + "\n")
        self.file.flush()


class Cache:
    """Provider responses keyed by request hash, in a JSONL file, so a repeated request costs nothing.
    The same request with a different repeat index is a different key."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.entries = {e["key"]: e["response"] for e in read_jsonl(self.path)}
        self.lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        return self.entries.get(key)

    def put(self, key: str, response: dict) -> None:
        with self.lock:
            self.entries[key] = response
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "response": response}) + "\n")
