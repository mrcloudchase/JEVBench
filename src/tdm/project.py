"""The project on disk: what the files are, where they live, and how they tie together.

    configs/models/<model>.yaml            provider, pinned model, repeats, concurrency
    configs/experiments/<experiment>.yaml  the tasks and models to compare
    tasks/<task>/                          questions.yaml, manifest.jsonl (committed), data.jsonl (the text; may be git-ignored)
    runs/<date>_<model>_<task>_<version>/  run.json and beliefs.jsonl: one run, never edited once complete
    scores/<experiment>.json               derived from runs
    reports/<experiment>.md                derived from scores

A task's version is a hash of its questions and manifest, so a run always names the exact sample and
wording it saw. Each stage reads only the previous stage's files.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from .data import load_dataset, load_questions, read_jsonl
from .providers import PROVIDERS, Provider


@dataclass
class Task:
    name: str
    dir: Path

    @property
    def questions(self) -> dict:
        return load_questions(self.dir / "questions.yaml")

    @property
    def manifest(self) -> list[dict]:
        return read_jsonl(self.dir / "manifest.jsonl")

    @property
    def version(self) -> str:
        digest = hashlib.sha256()
        for name in ("questions.yaml", "manifest.jsonl"):
            digest.update((self.dir / name).read_bytes())
        return digest.hexdigest()[:12]

    def records(self) -> list[dict]:
        """The records with their text, checked against the manifest: same ids, same labels."""
        records = load_dataset(self.dir / "data.jsonl")
        expected = {m["id"]: m.get("label") for m in self.manifest}
        if {r["id"]: r.get("label") for r in records} != expected:
            raise ValueError(f"{self.dir}/data.jsonl does not match manifest.jsonl; rebuild the task or restore its data")
        return records


@dataclass
class RunDir:
    dir: Path

    @property
    def meta(self) -> dict:
        return json.loads((self.dir / "run.json").read_text())

    @property
    def beliefs(self) -> Path:
        return self.dir / "beliefs.jsonl"

    @property
    def complete(self) -> bool:
        return (self.dir / "run.json").exists() and self.meta.get("status") == "complete"


class Project:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()

    def _yaml(self, kind: str, name: str) -> dict:
        path = self.root / "configs" / kind / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"no {kind[:-1]} config {path.relative_to(self.root)}")
        return {"name": name, **yaml.safe_load(path.read_text())}

    def model(self, name: str) -> dict:
        return self._yaml("models", name)

    def experiment(self, name: str) -> dict:
        return self._yaml("experiments", name)

    def task_version(self, experiment: dict, task: str) -> str:
        """The task version an experiment scores: pinned in its `task_versions`, or else the current one."""
        return (experiment.get("task_versions") or {}).get(task) or self.task(task).version

    def task(self, name: str) -> Task:
        task = Task(name, self.root / "tasks" / name)
        if not (task.dir / "questions.yaml").exists():
            raise FileNotFoundError(f"no task tasks/{name}")
        return task

    def provider(self, model: dict, env=os.environ) -> Provider:
        """A provider from a model config. The key comes from the provider's own variable (TYPESAFE_API_KEY, ...);
        `timeout` (seconds per call, default 30) can be raised for slow local models."""
        cls = PROVIDERS[model["provider"]]
        return cls(url=model.get("url"), api_key=env.get(cls.key_env) if cls.key_env else None, model=model["model"],
                   timeout=model.get("timeout", 30.0))

    def run_dir(self, date: str, model: str, task: Task) -> RunDir:
        return RunDir(self.root / "runs" / f"{date}_{model}_{task.name}_{task.version[:8]}")

    def runs(self, task: str | None = None, model: str | None = None) -> list[RunDir]:
        found = [RunDir(p.parent) for p in sorted((self.root / "runs").glob("*/run.json"))]
        return [r for r in found if (task is None or r.meta["task"] == task) and (model is None or r.meta["model"]["name"] == model)]

    def latest(self, task: str, model: str, version: str | None = None) -> RunDir | None:
        """The most recent complete run of a model on a version of the task (default: the current one)."""
        version = version or self.task(task).version
        done = [r for r in self.runs(task, model) if r.complete and r.meta["task_version"] == version]
        return max(done, key=lambda r: r.meta["started"]) if done else None
