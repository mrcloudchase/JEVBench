"""Score beliefs against labels, for any results file and any question type, and compare providers.

    python score.py results_a.jsonl [results_b.jsonl ...] [--question ID] [--label FIELD] [--threshold 0.5]

The answer's type picks the scorer:

    noul     predict yes when noul >= threshold; label is 1/0, true/false or yes/no
             accuracy, precision, recall, F1 at the threshold; AUROC, Brier and ECE use the probability itself
    choice   predict the chosen option; label is the option name
             accuracy, macro-F1; Brier over all options; ECE of the top probability
    score    predict the most probable level; label is the level index
             accuracy, within-one accuracy, mean absolute error of the expected score; ECE of the top probability

With several repeats, metrics are averaged over repeats (with their range) and `agree` is the share
of records whose prediction was the same on every repeat. Cost and latency come from the results.
With two or more files, each is compared with the first on the records both answered.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from data import read_jsonl


# ====================================================================== scorers, one per answer type
class Scorer:
    """Turns an answer into a prediction and a list of (answer, label) pairs into metrics."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def predict(self, answer: dict): raise NotImplementedError
    def metrics(self, pairs: list[tuple[dict, object]]) -> dict: raise NotImplementedError

    def correct(self, answer, label) -> bool:
        return answer is not None and answer.get("type") not in ("refusal",) and self.predict(answer) == self.gold(label)

    def gold(self, label):
        return label

    @staticmethod
    def ece(points: list[tuple[float, bool]], bins: int = 10) -> float:
        """Expected calibration error: |confidence - accuracy|, weighted over equal-width bins."""
        total, err = len(points), 0.0
        for b in range(bins):
            lo, hi = b / bins, (b + 1) / bins
            bucket = [(p, ok) for p, ok in points if lo <= p < hi or (b == bins - 1 and p == 1.0)]
            if bucket:
                err += len(bucket) / total * abs(statistics.fmean(p for p, _ in bucket) - statistics.fmean(ok for _, ok in bucket))
        return err


class NoulScorer(Scorer):
    def gold(self, label):
        return label in (1, True) or str(label).strip().lower() in ("1", "true", "yes")

    def predict(self, answer):
        return answer["noul"] >= self.threshold

    def metrics(self, pairs):
        scored = [(a["noul"], self.gold(y)) for a, y in pairs if a and "noul" in a]
        tp = sum(p >= self.threshold and y for p, y in scored)
        fp = sum(p >= self.threshold and not y for p, y in scored)
        fn = sum(p < self.threshold and y for p, y in scored)
        precision, recall = tp / (tp + fp) if tp + fp else 0.0, tp / (tp + fn) if tp + fn else 0.0
        return {
            "accuracy": statistics.fmean(self.correct(a, y) for a, y in pairs),
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "auroc": self.auroc(scored),
            "brier": statistics.fmean((p - y) ** 2 for p, y in scored) if scored else None,
            "ece": self.ece([(p, y) for p, y in scored]) if scored else None,
        }

    @staticmethod
    def auroc(scored: list[tuple[float, bool]]) -> float | None:
        """Probability that a random positive outranks a random negative; ties count half."""
        pos, neg = [p for p, y in scored if y], [p for p, y in scored if not y]
        if not pos or not neg:
            return None
        wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
        return wins / (len(pos) * len(neg))


class ChoiceScorer(Scorer):
    def gold(self, label):
        return str(label)

    def predict(self, answer):
        return str(answer["choice"])

    def metrics(self, pairs):
        answered = [(a, self.gold(y)) for a, y in pairs if a and "probabilities" in a]
        labels = {self.gold(y) for _, y in pairs}
        f1s = []
        for c in labels:
            tp = sum(self.predict(a) == c and y == c for a, y in answered)
            fp = sum(self.predict(a) == c and y != c for a, y in answered)
            fn = sum(y == c for _, y in pairs) - tp
            precision, recall = tp / (tp + fp) if tp + fp else 0.0, tp / (tp + fn) if tp + fn else 0.0
            f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
        brier = [sum((p - (str(k) == y)) ** 2 for k, p in a["probabilities"].items()) for a, y in answered]
        return {
            "accuracy": statistics.fmean(self.correct(a, y) for a, y in pairs),
            "macro_f1": statistics.fmean(f1s) if f1s else None,
            "brier": statistics.fmean(brier) if brier else None,
            "ece": self.ece([(max(a["probabilities"].values()), self.predict(a) == y) for a, y in answered]) if answered else None,
        }


class ScoreScorer(Scorer):
    def gold(self, label):
        return int(label)

    def predict(self, answer):
        return int(max(answer["probabilities"], key=answer["probabilities"].get))

    def metrics(self, pairs):
        answered = [(a, self.gold(y)) for a, y in pairs if a and "probabilities" in a]
        return {
            "accuracy": statistics.fmean(self.correct(a, y) for a, y in pairs),
            "within_one": statistics.fmean(abs(self.predict(a) - y) <= 1 for a, y in answered) if answered else None,
            "mae": statistics.fmean(abs(a["score"] - y) for a, y in answered) if answered else None,
            "ece": self.ece([(max(a["probabilities"].values()), self.predict(a) == y) for a, y in answered]) if answered else None,
        }


SCORERS = {"noul": NoulScorer, "choice": ChoiceScorer, "score": ScoreScorer}


# ====================================================================== one results file
class Run:
    """One results file: its rows grouped by repeat, scored for one question against one label field."""

    def __init__(self, path: str | Path, question: str | None, label: str, threshold: float):
        self.path = Path(path)
        rows = read_jsonl(self.path)
        self.errors = sum("error" in r for r in rows)
        self.rows = [r for r in rows if "answers" in r and r.get(label) is not None]
        if not self.rows:
            raise ValueError(f"{path}: no answered rows with a `{label}` field")
        ids = {qid for r in self.rows for qid in r["answers"]}
        if question is None:
            if len(ids) != 1:
                raise ValueError(f"{path}: several questions {sorted(ids)}; pick one with --question")
            question = next(iter(ids))
        self.question, self.label = question, label
        kinds = {r["answers"][question]["type"] for r in self.rows if question in r["answers"]} - {"refusal"}
        self.scorer = SCORERS[kinds.pop()](threshold)
        self.by_repeat = defaultdict(dict)
        for r in self.rows:
            self.by_repeat[r.get("repeat", 0)][r["id"]] = r

    def answer(self, row):
        return row["answers"].get(self.question)

    def name(self):
        r = self.rows[0]
        return f"{r.get('provider', '?')} {r.get('model', '?')}"

    def summary(self) -> dict:
        per_repeat = [self.scorer.metrics([(self.answer(r), r[self.label]) for r in rep.values()]) for rep in self.by_repeat.values()]
        out = {"file": str(self.path), "name": self.name(), "type": type(self.scorer).__name__.removesuffix("Scorer").lower(),
               "n": len(next(iter(self.by_repeat.values()))), "repeats": len(self.by_repeat), "errors": self.errors,
               "refusals": sum((self.answer(r) or {}).get("type") == "refusal" for r in self.rows)}
        for key in per_repeat[0]:
            values = [m[key] for m in per_repeat if m[key] is not None]
            out[key] = statistics.fmean(values) if values else None
            out[key + "_range"] = (min(values), max(values)) if len(values) > 1 else None
        out["agree"] = None                                 # one repeat: nothing to agree with
        if len(self.by_repeat) > 1:
            common = set.intersection(*(set(rep) for rep in self.by_repeat.values()))
            same = [len({self.prediction(rep[i]) for rep in self.by_repeat.values()}) == 1 for i in common]
            out["agree"] = statistics.fmean(same) if same else None
        costs = [r.get("cost_usd") or 0 for r in self.rows]
        latencies = sorted(r["latency_ms"] for r in self.rows if r.get("latency_ms") is not None)
        out["usd_per_1k"] = 1000 * statistics.fmean(costs) if costs else None
        out["tokens_per_item"] = statistics.fmean((r.get("usage") or {}).get("input_tokens") or 0 for r in self.rows)
        out["latency_p50_ms"] = latencies[len(latencies) // 2] if latencies else None
        out["latency_p95_ms"] = latencies[int(len(latencies) * 0.95)] if latencies else None
        return out

    def prediction(self, row):
        a = self.answer(row)
        return None if not a or a.get("type") == "refusal" else self.scorer.predict(a)

    def correct_by_id(self, repeat: int = 0) -> dict:
        rep = self.by_repeat.get(repeat) or next(iter(self.by_repeat.values()))
        return {i: self.scorer.correct(self.answer(r), r[self.label]) for i, r in rep.items()}


def paired_delta(base: Run, other: Run, iters: int = 2000, seed: int = 1) -> dict:
    """Accuracy of `other` minus `base` on records both answered (first repeat), with a 95% bootstrap interval."""
    a, b = base.correct_by_id(), other.correct_by_id()
    ids = sorted(set(a) & set(b), key=str)
    diffs = [int(b[i]) - int(a[i]) for i in ids]
    rng = random.Random(seed)
    boots = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(iters))
    return {"n": len(ids), "delta": statistics.fmean(diffs), "ci95": (boots[int(0.025 * iters)], boots[int(0.975 * iters)]),
            "only_base_right": diffs.count(-1), "only_other_right": diffs.count(1)}


# ====================================================================== report
def fmt(value, digits=3):
    if value is None:
        return "-"
    if isinstance(value, tuple):
        return f"{value[0]:.{digits}f}–{value[1]:.{digits}f}"
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def report(runs: list[Run]) -> str:
    summaries = [run.summary() for run in runs]
    metric_keys = [k for k in summaries[0] if k in ("accuracy", "precision", "recall", "f1", "auroc", "macro_f1",
                                                     "within_one", "mae", "brier", "ece", "agree")]
    head = ["provider / model", "n", "repeats"] + metric_keys + ["$ per 1k", "tokens", "p50 ms", "p95 ms", "errors", "refusals"]
    lines = [f"question `{runs[0].question}`, label `{runs[0].label}`, scorer {summaries[0]['type']}"
             + (f", threshold {runs[0].scorer.threshold}" if summaries[0]["type"] == "noul" else ""), "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for s in summaries:
        cells = [s["name"], s["n"], s["repeats"]]
        for k in metric_keys:
            cells.append(fmt(s[k]) + (f" ({fmt(s[k + '_range'])})" if s.get(k + "_range") else ""))
        cells += [fmt(s["usd_per_1k"], 4), f"{s['tokens_per_item']:.0f}", fmt(s["latency_p50_ms"], 0),
                  fmt(s["latency_p95_ms"], 0), s["errors"], s["refusals"]]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    if len(runs) > 1:
        lines += ["", f"Accuracy versus {runs[0].name()} on the same records (first repeat; 95% bootstrap interval):", "",
                  "| provider / model | n | delta | ci95 | only base right | only other right |", "|---|---|---|---|---|---|"]
        for run in runs[1:]:
            d = paired_delta(runs[0], run)
            lines.append(f"| {run.name()} | {d['n']} | {d['delta']:+.3f} | {fmt(d['ci95'])} | {d['only_base_right']} | {d['only_other_right']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score beliefs against labels and compare results files.")
    parser.add_argument("results", nargs="+", help="results JSONL files from engine.py")
    parser.add_argument("--question", help="question id to score (default: the only one)")
    parser.add_argument("--label", default="label", help="record field holding the ground truth")
    parser.add_argument("--threshold", type=float, default=0.5, help="noul: predict yes at or above this")
    parser.add_argument("--json", help="also write the summaries as JSON to this file")
    args = parser.parse_args()
    runs = [Run(path, args.question, args.label, args.threshold) for path in args.results]
    print(report(runs))
    if args.json:
        Path(args.json).write_text(json.dumps([r.summary() for r in runs], indent=2), encoding="utf-8")
