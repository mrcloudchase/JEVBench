"""Experiment 1: beliefs. Every provider on every dataset, then scored against the labels.

    python experiments/beliefs.py                         # run what is missing, then score everything
    python experiments/beliefs.py --dataset appstore_app --provider openai
    python experiments/beliefs.py --score                 # score the committed results only; no API calls

Hosted providers are asked three times per record (they need not be deterministic); local models
once. Runs resume: answered (record, repeat) pairs are skipped, and responses are cached, so a rerun
costs nothing. Results go to results/beliefs/<dataset>/<provider>.jsonl, scores to scores.json there.
"""

import argparse
import json
import sys
from pathlib import Path

from tdm import evaluate, load_env, load_provider
from tdm.score import Run, report

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ["steam_recommend", "appstore_stars", "appstore_app"]
PROVIDERS = {                                  # name: (repeats, concurrent calls)
    "typesafe": (3, 8), "openai": (3, 8), "deepseek": (3, 8),
    "von": (1, 2), "opendecider": (1, 2), "openjev": (1, 2),            # local servers: see servers/README.md
}


def run(dataset: str, provider: str) -> dict:
    repeats, workers = PROVIDERS[provider]
    data, out = ROOT / "datasets" / dataset, ROOT / "results" / "beliefs" / dataset
    out.mkdir(parents=True, exist_ok=True)
    return evaluate(data / "questions.yaml", data / "dataset.jsonl", out / f"{provider}.jsonl", load_provider(provider),
                    repeats, out / f"cache.{provider}.jsonl", workers)


def score(dataset: str) -> str:
    out = ROOT / "results" / "beliefs" / dataset
    runs = [Run(out / f"{p}.jsonl", None, "label", 0.5) for p in PROVIDERS if (out / f"{p}.jsonl").exists()]
    summaries = [{**r.summary(), "file": str(r.path.relative_to(ROOT))} for r in runs]
    (out / "scores.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return report(runs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", choices=DATASETS, action="append", help="default: all")
    parser.add_argument("--provider", choices=list(PROVIDERS), action="append", help="default: all")
    parser.add_argument("--score", action="store_true", help="only score the existing results")
    args = parser.parse_args()
    load_env(ROOT / ".env")
    for dataset in args.dataset or DATASETS:
        if not args.score:
            for provider in args.provider or PROVIDERS:
                r = run(dataset, provider)
                print(f"[{dataset}] {r['provider']} {r['model']}: {r['run']} run ({r['cached']} cached), "
                      f"{r['done_before']} already done, {r['errors']} errors", file=sys.stderr, flush=True)
        print(f"\n## {dataset}\n\n{score(dataset)}")
