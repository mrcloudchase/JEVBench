"""Stage 2, run: a task and a model make a run. A provider turns evidence and questions into beliefs.

    belief = Belief(questions, provider)(state)          # one belief
    execute(project, "steam_recommend", "typesafe")      # every record of a task -> runs/<id>/

A run folder holds run.json (what ran: task version, model config, the model versions the API served,
git commit, times, counts) and beliefs.jsonl (one line per record and repeat). An incomplete run
resumes; a complete run is never touched again, and running the same task and model on another day
makes a new run.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, Iterator

from .data import Results, read_jsonl
from .providers import Provider


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider):
        self.questions, self.provider = questions, provider

    def __call__(self, state) -> dict:
        return self.provider(state, self.questions)["answers"]


def run(dataset: Iterable[dict], questions: dict, provider: Provider, workers: int = 8, repeats: int = 1,
        cache=None, done: set = frozenset()) -> Iterator[dict]:
    """Form a belief for every record, `repeats` times each, concurrently.

    Only `state` and the questions go to the provider; every other field is copied to the result,
    with `repeat`. A record's own `questions` replace the shared ones. Pairs in `done` are skipped.
    With a cache, a request seen before is answered from it and marked `cached`."""
    jobs = [(record, r) for record in dataset for r in range(repeats) if (record["id"], r) not in done]

    def one(job):
        record, repeat = job
        qs = record.get("questions") or questions
        result = {k: v for k, v in record.items() if k not in ("state", "questions")}
        result["repeat"] = repeat
        try:
            key = cache and provider.key(record["state"], qs, repeat)
            response = cache and cache.get(key)
            if response:
                return {**result, **response, "cached": True}
            response = provider(record["state"], qs)
            if cache:
                cache.put(key, response)
            return {**result, **response}
        except Exception as exc:                       # a failed record is reported, not fatal
            return {**result, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(one, jobs)


def execute(project, task_name: str, model_name: str, date: str | None = None, provider: Provider | None = None):
    """Run a model on a task into runs/<date>_<model>_<task>_<version>/. Returns the RunDir."""
    task, model = project.task(task_name), project.model(model_name)
    date = date or dt.date.today().isoformat()
    out = project.run_dir(date, model_name, task)
    if out.complete:
        return out
    out.dir.mkdir(parents=True, exist_ok=True)
    meta = out.meta if (out.dir / "run.json").exists() else {
        "id": out.dir.name, "task": task.name, "task_version": task.version, "model": model,
        "git_commit": git_commit(project.root), "started": now(), "status": "running"}
    write_meta(out, meta)
    provider = provider or project.provider(model)
    records, repeats = task.records(), model.get("repeats", 1)
    with Results(out.beliefs) as results:
        for result in run(records, task.questions, provider, model.get("workers", 8), repeats, done=results.done):
            results.write(result)
    rows = [r for r in read_jsonl(out.beliefs) if "answers" in r]
    meta.update({"finished": now(), "records": len(records), "rows": len(rows), "expected_rows": len(records) * repeats,
                 "served": sorted({r.get("model") or "?" for r in rows}),
                 "cost_usd": round(sum(r.get("cost_usd") or 0 for r in rows), 6),
                 "status": "complete" if len(rows) == len(records) * repeats else "incomplete"})
    write_meta(out, meta)
    return out


def write_meta(run_dir, meta: dict) -> None:
    (run_dir.dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def git_commit(root: Path) -> str | None:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "configs", "tasks"], cwd=root,
                               capture_output=True, text=True).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


def load_env(*paths: str | Path) -> None:
    """Set variables from .env files without overriding ones already in the environment."""
    for path in map(Path, paths):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = (part.strip() for part in line.split("=", 1))
                    if value[:1] in "'\"" and value[:1] and value.count(value[0]) >= 2:
                        value = value[1:value.index(value[0], 1)]          # quoted: keep everything inside
                    else:
                        value = value.split(" #", 1)[0].strip()            # unquoted: drop an inline comment
                    os.environ.setdefault(key, value)
