"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions)(state)

Configuration lives in .env (or the environment) and is read by the official typesafe-sdk:

    TYPESAFE_API_KEY        required
    TYPESAFE_BASE_URL       any endpoint that speaks the typed-decision wire format
    TYPESAFE_DEFAULT_MODEL  e.g. jev-latest

Data lives in YAML: states and questions, nothing else. One file is one case or a dataset of cases.

    # one case
    questions: {...}
    state: "..."

    # a dataset: shared questions, many states; any other keys (id, label, ...) pass through
    questions: {...}
    cases:
      - {id: t1, state: "...", label: technical}
      - {id: t2, state: "...", questions: {...}}      # a case may bring its own questions

    python engine.py data.yaml [--workers 8] [--out results.jsonl]
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator

import yaml


def load_env(*paths: str | Path) -> None:
    """Set variables from .env files without overriding ones already in the environment."""
    for path in paths:
        path = Path(path)
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


class Provider:
    """state + questions -> response, through the SDK configured by the environment."""

    def __init__(self):
        from typesafe_sdk import TypeSafeClient
        self.client = TypeSafeClient()

    def __call__(self, state, questions: dict) -> dict:
        return self.client.system_one(state, questions).model_dump(mode="json")


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider | None = None):
        self.questions, self.provider = questions, provider or Provider()

    def __call__(self, state) -> dict:
        return self.provider(state, self.questions)["answers"]


def load_cases(path: str | Path) -> list[dict]:
    """Read one case or a dataset of cases from YAML. Each case has `state` and `questions`."""
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    shared = spec.get("questions")
    raw = spec["cases"] if "cases" in spec else [{"state": spec.get("state")}]
    cases = []
    for i, case in enumerate(raw):
        case = dict(case)
        case.setdefault("id", i)
        case["questions"] = case.get("questions") or shared
        if case.get("state") is None or not case["questions"]:
            raise ValueError(f"{path}: case {case['id']} needs `state` and `questions`")
        cases.append(case)
    return cases


def run(cases: list[dict], provider: Provider | None = None, workers: int = 8) -> Iterator[dict]:
    """Form a belief for every case, concurrently. Yields each case with the provider's response."""
    provider = provider or Provider()

    def one(case):
        try:
            response = provider(case["state"], case["questions"])
            return {**{k: v for k, v in case.items() if k != "questions"}, **response}
        except Exception as exc:                       # a failed case is recorded, not fatal
            return {**{k: v for k, v in case.items() if k != "questions"}, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(one, cases)


if __name__ == "__main__":
    import argparse
    import json
    import sys

    load_env(Path.cwd() / ".env", Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Form beliefs for one case or a dataset of cases in YAML.")
    parser.add_argument("data", help="YAML with `questions` and `state`, or `questions` and `cases`")
    parser.add_argument("--workers", type=int, default=8, help="concurrent provider calls")
    parser.add_argument("--out", help="write one JSON record per case to this file instead of stdout")
    args = parser.parse_args()

    cases = load_cases(args.data)
    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    for record in run(cases, workers=args.workers):
        out.write(json.dumps(record) + "\n")
    if args.out:
        out.close()
        print(f"{len(cases)} cases -> {args.out}", file=sys.stderr)
