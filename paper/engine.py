"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions, provider)(state)

Three inputs, three places:

    .env             which provider: PROVIDER_URL, PROVIDER_API_KEY, PROVIDER_MODEL, PROVIDER_HANDLER
    questions.yaml   the task: questions in the wire format, keyed by question id
    dataset.jsonl    the data: one record per line, {"id", "state", "label"?, "questions"?, ...}

The engine speaks raw HTTP. A Handler translates between the engine and one provider's payloads:
headers(api_key), request(state, questions, model) -> payload, response(body) -> {model, answers, usage}.
The default handler speaks the TypeSafe wire format. Any other provider is a Handler subclass,
selected by PROVIDER_HANDLER as a registered name or "module:attribute".

    python engine.py questions.yaml dataset.jsonl [--out results.jsonl] [--workers 8]
"""

from __future__ import annotations

import importlib
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, Iterator

import yaml


def load_env(*paths: str | Path) -> None:
    """Set variables from .env files without overriding ones already in the environment."""
    for path in map(Path, paths):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))


# ====================================================================== provider
class Handler:
    """Translates between the engine and one provider. This default speaks the TypeSafe wire format."""

    def headers(self, api_key: str) -> dict:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def request(self, state, questions: dict, model: str) -> dict:
        return {"model": model, "state": state, "questions": questions}

    def response(self, body: dict) -> dict:
        return {"model": body.get("model"), "answers": body["answers"], "usage": body.get("usage", {})}


HANDLERS = {"typesafe": Handler()}


def load_handler(name: str) -> Handler:
    """A registered handler name, or "module:attribute" naming a Handler instance or class."""
    if name in HANDLERS:
        return HANDLERS[name]
    module, _, attr = name.partition(":")
    handler = getattr(importlib.import_module(module), attr)
    return handler() if isinstance(handler, type) else handler


class Provider:
    """state + questions -> {model, answers, usage}, over raw HTTP, configured by the environment."""

    RETRY = {408, 429, 500, 502, 503, 504, 529}

    def __init__(self, url=None, api_key=None, model=None, handler=None, timeout=30.0, retries=3):
        env = os.environ
        try:
            self.url = url or env["PROVIDER_URL"]
            self.api_key = api_key or env["PROVIDER_API_KEY"]
            self.model = model or env["PROVIDER_MODEL"]
        except KeyError as missing:
            raise RuntimeError(f"set {missing.args[0]} in .env or the environment") from None
        self.handler = handler or load_handler(env.get("PROVIDER_HANDLER", "typesafe"))
        self.timeout, self.retries = timeout, retries

    def __call__(self, state, questions: dict) -> dict:
        payload = json.dumps(self.handler.request(state, questions, self.model)).encode("utf-8")
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(self.url, data=payload, headers=self.handler.headers(self.api_key), method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return self.handler.response(json.loads(resp.read()))
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "replace")[:300]
                if err.code not in self.RETRY or attempt == self.retries:
                    raise RuntimeError(f"HTTP {err.code} from {self.url}: {detail}") from None
                time.sleep(float(err.headers.get("Retry-After") or 2 ** attempt))
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt == self.retries:
                    raise RuntimeError(f"{self.url}: {err}") from None
                time.sleep(2 ** attempt)


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider | None = None):
        self.questions, self.provider = questions, provider or Provider()

    def __call__(self, state) -> dict:
        return self.provider(state, self.questions)["answers"]


# ====================================================================== data
def load_questions(path: str | Path) -> dict:
    """The task: questions in the wire format, keyed by question id."""
    questions = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(questions, dict) or not questions:
        raise ValueError(f"{path}: expected a mapping of question id -> question")
    return questions


def load_dataset(path: str | Path) -> list[dict]:
    """The data: JSONL, one record per line, or a YAML list of the same records."""
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


def run(dataset: Iterable[dict], questions: dict, provider: Provider | None = None, workers: int = 8) -> Iterator[dict]:
    """Form a belief for every record, concurrently. Only `state` and the questions go to the provider;
    every other field is copied to the result. A record's own `questions` replace the shared ones."""
    provider = provider or Provider()

    def one(record):
        result = {k: v for k, v in record.items() if k not in ("state", "questions")}
        try:
            return {**result, **provider(record["state"], record.get("questions") or questions)}
        except Exception as exc:                       # a failed record is reported, not fatal
            return {**result, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(one, dataset)


if __name__ == "__main__":
    import argparse
    import sys

    load_env(Path.cwd() / ".env", Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Form a belief for every record of a dataset.")
    parser.add_argument("questions", help="YAML: question id -> question, in the wire format")
    parser.add_argument("dataset", help="JSONL (or a YAML list): records with id, state, optional label and questions")
    parser.add_argument("--out", help="JSONL results; records whose id is already there are skipped")
    parser.add_argument("--workers", type=int, default=8, help="concurrent provider calls")
    args = parser.parse_args()

    questions, dataset = load_questions(args.questions), load_dataset(args.dataset)
    done = set()
    if args.out and Path(args.out).exists():
        done = {json.loads(line)["id"] for line in Path(args.out).read_text(encoding="utf-8").splitlines() if line.strip()}
    todo = [r for r in dataset if r["id"] not in done]

    out = open(args.out, "a", encoding="utf-8") if args.out else sys.stdout
    errors = 0
    for result in run(todo, questions, workers=args.workers):
        errors += "error" in result
        out.write(json.dumps(result) + "\n")
        out.flush()
    if args.out:
        out.close()
        print(f"{len(todo)} run, {len(done)} already done, {errors} errors -> {args.out}", file=sys.stderr)
