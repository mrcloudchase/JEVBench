"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions, provider)(state)

    .env             which provider              -> providers.py
    questions.yaml   the task                    -> data.py
    dataset.jsonl    the data, one record a line -> data.py

    python engine.py questions.yaml dataset.jsonl --out results.jsonl
                     [--provider openai] [--repeats 3] [--cache cache.jsonl] [--workers 8]
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


def run(dataset: Iterable[dict], questions: dict, provider: Provider | None = None, workers: int = 8,
        repeats: int = 1, cache=None, done: set = frozenset()) -> Iterator[dict]:
    """Form a belief for every record, `repeats` times each, concurrently.

    Only `state` and the questions go to the provider; every other field is copied to the result,
    with `repeat`. A record's own `questions` replace the shared ones. Pairs in `done` are skipped.
    With a cache, a request seen before is answered from it and marked `cached`."""
    provider = provider or load_provider()
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

    from data import Cache, Results, load_dataset, load_questions

    load_env(Path.cwd() / ".env", Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Form a belief for every record of a dataset.")
    parser.add_argument("questions", help="YAML: question id -> question, in the wire format")
    parser.add_argument("dataset", help="JSONL (or a YAML list): records with id, state, optional label and questions")
    parser.add_argument("--out", help="JSONL results; answered (id, repeat) pairs are skipped, failed ones retried")
    parser.add_argument("--provider", help="registered name or module:Class; overrides PROVIDER")
    parser.add_argument("--repeats", type=int, default=1, help="ask every record this many times")
    parser.add_argument("--cache", help="JSONL response cache; a request seen before costs nothing")
    parser.add_argument("--workers", type=int, default=8, help="concurrent provider calls")
    args = parser.parse_args()

    questions, dataset = load_questions(args.questions), load_dataset(args.dataset)
    provider, cache = load_provider(args.provider), Cache(args.cache) if args.cache else None

    if not args.out:
        for result in run(dataset, questions, provider, args.workers, args.repeats, cache):
            print(json.dumps(result), flush=True)
        sys.exit(0)

    with Results(args.out) as results:
        n = errors = cached = 0
        for result in run(dataset, questions, provider, args.workers, args.repeats, cache, results.done):
            n, errors, cached = n + 1, errors + ("error" in result), cached + bool(result.get("cached"))
            results.write(result)
    print(f"{provider.name} {provider.model}: {n} run ({cached} from cache, {results.retried} retried), "
          f"{len(results.done)} already done, {errors} errors -> {args.out}", file=sys.stderr)
