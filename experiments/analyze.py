"""Compute the comparison table from results/<task>/<arch>.jsonl and write results/<task>.md and .json."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PRICE_PER_MTOK = 0.042


def load(task: str) -> dict[str, list[dict]]:
    runs = {}
    for path in sorted((RESULTS / task).glob("*.jsonl")):
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        runs[path.stem] = rows
    return runs


def variants(arch: str, rows: list[dict]):
    """Yield (name, answer_key, confidence_key). The panel yields vote and pool from the same calls."""
    yield arch, "answer", "confidence"
    if arch == "panel":
        yield "panel_pool", "pool_answer", "pool_confidence"


def ece(pairs: list[tuple[float, bool]], bins: int = 10) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(c, ok) for c, ok in pairs if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if bucket:
            conf = sum(c for c, _ in bucket) / len(bucket)
            acc = sum(1 for _, ok in bucket if ok) / len(bucket)
            err += len(bucket) / total * abs(conf - acc)
    return round(err, 3)


def macro_f1(pairs: list[tuple[str, str]], labels: set[str]) -> float:
    f1s = []
    for lab in labels:
        tp = sum(1 for p, t in pairs if p == lab and t == lab)
        fp = sum(1 for p, t in pairs if p == lab and t != lab)
        fn = sum(1 for p, t in pairs if p != lab and t == lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return round(sum(f1s) / len(f1s), 3) if f1s else 0.0


def summarize(name: str, rows: list[dict], akey: str, ckey: str) -> dict:
    ok_rows = [r for r in rows if r.get("judgment")]
    n = len(rows)
    labels = {r["label"] for r in rows}
    preds = [(r["judgment"][akey], r["label"]) for r in ok_rows]
    acted = [(p, t) for p, t in preds if p != "abstain"]
    correct_all = sum(1 for p, t in preds if p == t)
    correct_acted = sum(1 for p, t in acted if p == t)
    conf_pairs = [(float(r["judgment"][ckey]), r["judgment"][akey] == r["label"]) for r in ok_rows
                  if r["judgment"][akey] != "abstain" and r["judgment"].get(ckey) is not None]
    calls = sum(r["calls"] for r in ok_rows)
    tokens = sum(r["input_tokens"] for r in ok_rows)
    latencies = [r["latency_ms"] for r in ok_rows if r.get("latency_ms")]
    return {
        "architecture": name,
        "n": n,
        "errors": n - len(ok_rows),
        "accuracy": round(correct_all / n, 3) if n else None,
        "accuracy_ci95": bootstrap_ci([p == t for p, t in preds]),
        "coverage": round(len(acted) / n, 3) if n else None,
        "selective_accuracy": round(correct_acted / len(acted), 3) if acted else None,
        "selective_accuracy_ci95": bootstrap_ci([p == t for p, t in acted]),
        "macro_f1_acted": macro_f1(acted, labels),
        "ece": ece(conf_pairs),
        "calls_per_item": round(calls / len(ok_rows), 2) if ok_rows else None,
        "tokens_per_item": round(tokens / len(ok_rows)) if ok_rows else None,
        "usd_per_1k_items": round(tokens / len(ok_rows) * 1000 / 1e6 * PRICE_PER_MTOK, 4) if ok_rows else None,
        "latency_ms_p50": round(sorted(latencies)[len(latencies) // 2]) if latencies else None,
    }


def bootstrap_ci(flags: list[bool], iters: int = 2000, seed: int = 1) -> tuple[float, float] | None:
    """95% bootstrap interval for a proportion."""
    if not flags:
        return None
    rng = random.Random(seed)
    n = len(flags)
    means = sorted(sum(rng.choice(flags) for _ in range(n)) / n for _ in range(iters))
    return round(means[int(0.025 * iters)], 3), round(means[int(0.975 * iters)], 3)


def paired_delta(base: list[dict], other: list[dict], akey: str, iters: int = 2000, seed: int = 2) -> dict:
    """Accuracy difference other - single on the same items, with a bootstrap interval over items.
    Abstentions count as wrong, so this is the all-items accuracy delta."""
    b = {r["idx"]: r for r in base if r.get("judgment")}
    o = {r["idx"]: r for r in other if r.get("judgment")}
    idx = sorted(set(b) & set(o))
    if not idx:
        return {}
    diffs = [(1 if o[i]["judgment"][akey] == o[i]["label"] else 0) - (1 if b[i]["judgment"]["answer"] == b[i]["label"] else 0) for i in idx]
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(n)) / n for _ in range(iters))
    return {"delta_accuracy": round(sum(diffs) / n, 3), "ci95": (round(means[int(0.025 * iters)], 3), round(means[int(0.975 * iters)], 3)),
            "changed_items": sum(1 for d in diffs if d)}


def replicate_noise(task: str) -> dict | None:
    """If replicate runs of the single decision exist (results/<task>_rep*/single.jsonl), report agreement and spread."""
    reps = sorted(RESULTS.glob(f"{task}_rep*/single.jsonl"))
    base = RESULTS / task / "single.jsonl"
    if not reps or not base.exists():
        return None
    runs = [base] + reps
    answers = []
    for path in runs:
        rows = {json.loads(l)["idx"]: json.loads(l) for l in path.read_text().splitlines() if l.strip()}
        answers.append(rows)
    idx = sorted(set.intersection(*[set(a) for a in answers]))
    accs = [round(sum(1 for i in idx if a[i]["judgment"]["answer"] == a[i]["label"]) / len(idx), 3) for a in answers]
    agree_all = sum(1 for i in idx if len({a[i]["judgment"]["answer"] for a in answers}) == 1) / len(idx)
    conf_spread = sum(max(float(a[i]["judgment"]["confidence"]) for a in answers) - min(float(a[i]["judgment"]["confidence"]) for a in answers) for i in idx) / len(idx)
    return {"runs": len(runs), "accuracies": accs, "accuracy_range": round(max(accs) - min(accs), 3),
            "items_agreeing_across_runs": round(agree_all, 3), "mean_confidence_spread": round(conf_spread, 3)}


def selective_curve(rows: list[dict]) -> list[dict]:
    """Coverage and selective accuracy of the single decision at increasing confidence floors."""
    out = []
    ok = [r for r in rows if r.get("judgment")]
    for tau in [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        acted = [r for r in ok if float(r["judgment"]["confidence"]) >= tau]
        correct = sum(1 for r in acted if r["judgment"]["answer"] == r["label"])
        out.append({"tau": tau, "coverage": round(len(acted) / len(ok), 3) if ok else None,
                    "selective_accuracy": round(correct / len(acted), 3) if acted else None})
    return out


def main(task: str) -> None:
    runs = load(task)
    table = []
    for arch, rows in runs.items():
        for name, akey, ckey in variants(arch, rows):
            row = summarize(name, rows, akey, ckey)
            if "single" in runs and name != "single":
                row["vs_single"] = paired_delta(runs["single"], rows, akey)
            table.append(row)
    order = ["single", "gated", "panel", "panel_pool", "escalation", "chain", "contrastive", "iterative"]
    table.sort(key=lambda r: order.index(r["architecture"]) if r["architecture"] in order else 99)
    curve = selective_curve(runs["single"]) if "single" in runs else []
    extras = {}
    if "escalation" in runs:
        esc = [r for r in runs["escalation"] if r.get("judgment")]
        extras["escalation_rate"] = round(sum(1 for r in esc if r["judgment"].get("escalated")) / len(esc), 3) if esc else None
    if "contrastive" in runs:
        con = [r for r in runs["contrastive"] if r.get("judgment")]
        extras["contested_rate"] = round(sum(1 for r in con if r["judgment"].get("contested")) / len(con), 3) if con else None
    if "iterative" in runs:
        it = [r for r in runs["iterative"] if r.get("judgment")]
        extras["mean_rounds"] = round(sum(r["judgment"].get("rounds", 1) for r in it) / len(it), 2) if it else None
    if "panel" in runs:
        pan = [r for r in runs["panel"] if r.get("judgment")]
        extras["panel_unanimous_rate"] = round(sum(1 for r in pan if r["judgment"].get("unanimous")) / len(pan), 3) if pan else None
    noise = replicate_noise(task)
    if noise:
        extras["single_replicates"] = noise

    (RESULTS / f"{task}.json").write_text(json.dumps({"task": task, "table": table, "selective_curve": curve, "extras": extras}, indent=2))
    cols = ["architecture", "accuracy", "accuracy_ci95", "coverage", "selective_accuracy", "selective_accuracy_ci95", "macro_f1_acted", "ece", "calls_per_item", "tokens_per_item", "usd_per_1k_items", "latency_ms_p50"]
    lines = [f"# {task}", "", f"n = {table[0]['n']} items per architecture, one run each.", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in table:
        lines.append("| " + " | ".join("" if r.get(c) is None else str(r[c]) for c in cols) + " |")
    lines += ["", "Paired accuracy delta versus the single decision on the same items (abstentions count as wrong):", "",
              "| architecture | delta | ci95 | items changed |", "|---|---|---|---|"]
    for r in table:
        d = r.get("vs_single")
        if d:
            lines.append(f"| {r['architecture']} | {d['delta_accuracy']:+.3f} | {d['ci95']} | {d['changed_items']} |")
    lines += ["", "Selective prediction curve of the single decision (confidence floor tau):", "",
              "| tau | coverage | selective_accuracy |", "|---|---|---|"]
    lines += [f"| {c['tau']} | {c['coverage']} | {c['selective_accuracy']} |" for c in curve]
    lines += ["", "Extras: " + json.dumps(extras)]
    (RESULTS / f"{task}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
