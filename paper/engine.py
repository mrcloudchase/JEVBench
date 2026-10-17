"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions, provider)(state)

    .env             which provider              -> providers.py
    questions.yaml   the task                    -> data.py
    dataset.jsonl    the data, one record a line -> data.py

    python engine.py questions.yaml dataset.jsonl [--out results.jsonl] [--workers 8]
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, Iterator

from providers import Provider, load_provider


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider | None = None):
        self.questions, self.provider = questions, provider or load_provider()

    def __call__(self, state) -> dict:
        return self.provider(state, self.questions)["answers"]


def run(dataset: Iterable[dict], questions: dict, provider: Provider | None = None, workers: int = 8) -> Iterator[dict]:
    """Form a belief for every record, concurrently. Only `state` and the questions go to the provider;
    every other field is copied to the result. A record's own `questions` replace the shared ones."""
    provider = provider or load_provider()

    def one(record):
        result = {k: v for k, v in record.items() if k not in ("state", "questions")}
        try:
            return {**result, **provider(record["state"], record.get("questions") or questions)}
        except Exception as exc:                       # a failed record is reported, not fatal
            return {**result, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(one, dataset)


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


if __name__ == "__main__":
    import argparse
    import json
    import sys

    from data import Results, load_dataset, load_questions

    load_env(Path.cwd() / ".env", Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Form a belief for every record of a dataset.")
    parser.add_argument("questions", help="YAML: question id -> question, in the wire format")
    parser.add_argument("dataset", help="JSONL (or a YAML list): records with id, state, optional label and questions")
    parser.add_argument("--out", help="JSONL results; ids already answered are skipped, failed ids are retried")
    parser.add_argument("--workers", type=int, default=8, help="concurrent provider calls")
    args = parser.parse_args()

    questions, dataset, provider = load_questions(args.questions), load_dataset(args.dataset), load_provider()

    if not args.out:
        for result in run(dataset, questions, provider, args.workers):
            print(json.dumps(result), flush=True)
        sys.exit(0)

    with Results(args.out) as results:
        todo = [r for r in dataset if r["id"] not in results.done]
        errors = 0
        for result in run(todo, questions, provider, args.workers):
            errors += "error" in result
            results.write(result)
    print(f"{type(provider).__name__} {provider.model}: {len(todo)} run ({results.retried} retried), "
          f"{len(results.done)} already done, {errors} errors -> {args.out}", file=sys.stderr)
