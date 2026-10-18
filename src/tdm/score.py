"""Stage 3, score: runs -> scores. Beliefs against labels, for any question type, compared across models.

    score_experiment(project, "fresh-reviews")      # -> scores/fresh-reviews.json; no model is called

The answer's type picks the scorer:

    noul     predict yes when noul >= threshold; label is 1/0, true/false or yes/no
             accuracy, precision, recall, F1 at the threshold; AUROC, Brier and ECE use the probability itself
    choice   predict the chosen option; label is the option name
             accuracy, macro-F1; Brier over all options; ECE of the top probability
    score    predict the most probable level; label is the level index
             accuracy, within-one accuracy, mean absolute error of the expected score; ECE of the top probability

With several repeats, metrics are averaged over repeats (with their range) and `agree` is the share
of records whose prediction was the same on every repeat. A refusal counts as wrong. Cost and latency
come from the run. Each model is compared with the experiment's first model on the same records.
"""

from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .data import read_jsonl


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
class ScoredRun:
    """One run's beliefs file: its rows grouped by repeat, scored for one question against one label field."""

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


def paired(a: dict, b: dict, iters: int = 2000, seed: int = 1) -> dict:
    """Mean of b minus a over the keys both have (bools or numbers), with a 95% bootstrap interval."""
    ids = sorted(set(a) & set(b), key=str)
    diffs = [float(b[i]) - float(a[i]) for i in ids]
    rng = random.Random(seed)
    boots = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(iters))
    return {"n": len(ids), "delta": statistics.fmean(diffs), "ci95": (boots[int(0.025 * iters)], boots[int(0.975 * iters)]),
            "only_base_right": diffs.count(-1), "only_other_right": diffs.count(1)}


def paired_delta(base: "ScoredRun", other: "ScoredRun", iters: int = 2000, seed: int = 1) -> dict:
    """Accuracy of `other` minus `base` on records both answered (first repeat), with a 95% bootstrap interval."""
    return paired(base.correct_by_id(), other.correct_by_id(), iters, seed)


# ====================================================================== an experiment
def score_experiment(project, name: str, threshold: float = 0.5) -> dict:
    """Score the latest complete run of each model on each task, and write scores/<name>.json."""
    exp = project.experiment(name)
    out = {"experiment": name, "tasks": {}}
    for task in exp["tasks"]:
        found = [(m, project.latest(task, m)) for m in exp["models"]]
        scored = [(m, r, ScoredRun(r.beliefs, None, "label", threshold)) for m, r in found if r]
        entry = {"task_version": project.task(task).version, "missing": [m for m, r in found if not r], "runs": [], "paired": []}
        for model, run_dir, s in scored:
            entry["runs"].append({"model": model, "run": run_dir.dir.name, **s.summary(), "file": str(run_dir.beliefs.relative_to(project.root))})
        if scored:
            entry.update(question=scored[0][2].question, type=entry["runs"][0]["type"], threshold=threshold, base=scored[0][0])
            for model, _, s in scored[1:]:
                entry["paired"].append({"model": model, **paired_delta(scored[0][2], s)})
        out["tasks"][task] = entry
    path = project.root / "scores" / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out
