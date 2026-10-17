"""Run every architecture over every item of a task through the JEVBench engine, recording the judgment
and the trace totals (calls, tokens, latency). Results are append-only JSONL so runs can resume."""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tasks import TASKS  # noqa: E402

from jevbench import api  # noqa: E402
from jevbench.errors import JevBenchError  # noqa: E402
from jevbench.providers.config import ProviderRegistry  # noqa: E402

HERE = Path(__file__).resolve().parent
ARCH = HERE / "architectures"
RESULTS = HERE / "results"
ARCHITECTURES = ["single", "gated", "panel", "escalation", "chain", "contrastive", "iterative"]


def build_input(task: dict, item: dict, arch: str) -> dict:
    data = {"text": item["text"], "instructions": task["instructions"], "criteria": task["criteria"]}
    if arch == "panel":
        data["frames"] = task["frames"]
    if arch == "chain":
        data["aux"] = task["aux"]
    if arch == "contrastive":
        data["stance_for"], data["stance_against"] = task["stance_for"], task["stance_against"]
    return data


def run_one(framework, base_dir, registry, task, item, idx, arch, mock):
    data = build_input(task, item, arch)
    started = time.perf_counter()
    for attempt in range(3):
        try:
            result = api.run_framework(framework, data, providers=registry, base_dir=base_dir, mock_all=mock)
            totals = result.trace.totals()
            return {"idx": idx, "label": item["label"], "judgment": result.judgment, "calls": totals["api_calls"] + totals["mocked_calls"],
                    "input_tokens": totals["input_tokens"], "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
        except JevBenchError as exc:
            error = str(exc)
            time.sleep(1.5 * (attempt + 1))
    return {"idx": idx, "label": item["label"], "judgment": None, "error": error, "calls": 0, "input_tokens": 0, "latency_ms": None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=list(TASKS))
    parser.add_argument("--arch", action="append", help="architecture(s) to run; default all applicable")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--suffix", default="", help="results directory suffix, e.g. _rep1 for a replicate run")
    args = parser.parse_args()

    task = TASKS[args.task]()
    items = task["items"][: args.limit] if args.limit else task["items"]
    archs = args.arch or ARCHITECTURES
    registry = ProviderRegistry.load()
    out_dir = RESULTS / (("mock_" + task["name"] if args.mock else task["name"]) + args.suffix)
    out_dir.mkdir(parents=True, exist_ok=True)

    for arch in archs:
        if arch == "contrastive" and not task.get("stance_for"):
            print(f"[{task['name']}] skip {arch}: task has no stances")
            continue
        framework, base_dir = api.load_framework(ARCH / f"{arch}.yaml")
        out = out_dir / f"{arch}.jsonl"
        done = set()
        if out.exists():
            done = {json.loads(line)["idx"] for line in out.read_text().splitlines() if line.strip()}
        todo = [(i, it) for i, it in enumerate(items) if i not in done]
        print(f"[{task['name']}] {arch}: {len(done)} done, {len(todo)} to run", flush=True)
        t0 = time.perf_counter()
        with out.open("a") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_one, framework, base_dir, registry, task, it, i, arch, args.mock) for i, it in todo]
            for n, fut in enumerate(as_completed(futures), 1):
                fh.write(json.dumps(fut.result()) + "\n"); fh.flush()
                if n % 50 == 0:
                    print(f"  {n}/{len(todo)} ({time.perf_counter() - t0:.0f}s)", flush=True)
        print(f"[{task['name']}] {arch}: finished in {time.perf_counter() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
