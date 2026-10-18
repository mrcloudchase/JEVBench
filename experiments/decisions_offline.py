"""Experiment 2: decisions over recorded beliefs (E1-E5). No model is called.

    python experiments/decisions_offline.py      # writes results/decisions/offline.json, about 40 seconds

Every belief comes from results/beliefs/<dataset>/<provider>.jsonl (first repeat). Each experiment changes only
the decision rule, its values, or how units are wired, so differences are the decision layer's alone.
"""

import hashlib
import json
import random
import statistics
from pathlib import Path

from tdm.decision import (ABSTAIN, Decision, OrchestratorWorker, Parallel, Recorded, Single, compare, confidence,
                          correct, decide_all, score_decisions, top)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "decisions"

EVALS = {"steam_recommend": "recommends", "appstore_stars": "stars", "appstore_app": "app"}
PROVIDERS = ["typesafe", "openai", "deepseek", "von", "opendecider", "openjev"]
HOSTED, LOCAL = PROVIDERS[:3], PROVIDERS[3:]


def beliefs(task):
    return {p: Recorded(ROOT / "results" / "beliefs" / task / f"{p}.jsonl") for p in PROVIDERS}


def half(record) -> int:
    """A fixed split of the records into two halves, for fitting values on one and testing on the other."""
    return int(hashlib.md5(record["id"].encode()).hexdigest(), 16) % 2


# ---------------------------------------------------------------------- rules: pure expressions over beliefs and values
def threshold(q):
    """noul: act yes when P(yes) >= theta."""
    return Decision(lambda b, theta: int(b[q]["noul"] >= theta) if b[q].get("type") == "noul" else ABSTAIN, theta=0.5)


def reject(q):
    """Chow's reject option: the top option when its probability is at least tau, otherwise abstain."""
    return Decision(lambda b, tau: top(b[q]) if confidence(b[q]) >= tau and top(b[q]) is not None else ABSTAIN, tau=0.0)


def gate(q):
    """An orchestrator's rule: act on its own top option when confident, otherwise hand to the `escalate` worker."""
    return Decision(lambda b, tau: top(b[q]) if confidence(b[q]) >= tau and top(b[q]) is not None else "escalate", tau=0.8)


def vote(q):
    """Majority of the panel's top options; no majority is an abstention."""
    def rule(*bs):
        tops = [top(b[q]) for b in bs if b and top(b[q]) is not None]
        best = max(set(tops), key=tops.count) if tops else None
        return best if best is not None and tops.count(best) * 2 > len(tops) else ABSTAIN
    return Decision(rule)


def pool(q):
    """Average the panel's probability distributions and take the top option."""
    def rule(*bs):
        dists = []
        for b in bs:
            a = b and b[q]
            if a and a.get("type") == "noul":
                dists.append({1: a["noul"], 0: 1 - a["noul"]})
            elif a and "probabilities" in a:
                dists.append({(int(k) if a["type"] == "score" else k): v for k, v in a["probabilities"].items()})
        if not dists:
            return ABSTAIN
        keys = set().union(*dists)
        mean = {k: statistics.fmean(d.get(k, 0.0) for d in dists) for k in keys}
        return max(mean, key=mean.get)
    return Decision(rule)


# ---------------------------------------------------------------------- experiments
def thresholds_and_costs():
    """E1. One unit on Steam: the threshold, and what the costs of errors say it should be."""
    task, q = "steam_recommend", "recommends"
    src = beliefs(task)
    records = src["typesafe"].records()
    grid = [round(0.05 * i, 2) for i in range(1, 20)]
    out = {"providers": {}, "costs": {}}
    for p in PROVIDERS:
        acc = {t: score_decisions(decide_all(Single(src[p], threshold(q).given(theta=t)), records))["accuracy"] for t in grid}
        fit = max(grid, key=lambda t: score_decisions(decide_all(Single(src[p], threshold(q).given(theta=t)), [r for r in records if half(r) == 0]))["accuracy"])
        test = [r for r in records if half(r) == 1]
        out["providers"][p] = {"at_0.5": acc[0.5], "best_theta": max(acc, key=acc.get), "best": max(acc.values()),
                               "fit_theta": fit, "test_at_0.5": score_decisions(decide_all(Single(src[p], threshold(q)), test))["accuracy"],
                               "test_at_fit": score_decisions(decide_all(Single(src[p], threshold(q).given(theta=fit)), test))["accuracy"]}
    # costs: a missed negative review (false "recommends") costs c_fp, a missed positive c_fn.
    for c_fp, c_fn in [(1, 9), (1, 3), (1, 1), (3, 1), (9, 1)]:
        loss = lambda action, label, c_fp=c_fp, c_fn=c_fn: c_fp if (action == 1 and int(label) == 0) else c_fn if (action == 0 and int(label) == 1) else 0
        bayes = c_fp / (c_fp + c_fn)                       # the threshold that minimizes expected cost for a calibrated belief
        row = {}
        for p in PROVIDERS:
            fitted = min(grid, key=lambda t: score_decisions(decide_all(Single(src[p], threshold(q).given(theta=t)), [r for r in records if half(r) == 0]), loss)["risk"])
            test = [r for r in records if half(r) == 1]
            row[p] = {"bayes_theta": bayes, "risk_bayes": score_decisions(decide_all(Single(src[p], threshold(q).given(theta=bayes)), test), loss)["risk"],
                      "fit_theta": fitted, "risk_fit": score_decisions(decide_all(Single(src[p], threshold(q).given(theta=fitted)), test), loss)["risk"]}
        out["costs"][f"{c_fp}:{c_fn}"] = row
    return out


def risk_coverage():
    """E2. The reject option on every eval: selective accuracy as the rule abstains more."""
    out = {}
    for task, q in EVALS.items():
        src = beliefs(task)
        records = src["typesafe"].records()
        out[task] = {}
        for p in PROVIDERS:
            confs = sorted(confidence(src[p](r)["answers"][q]) for r in records if src[p](r))
            curve = []
            for tau in [0.0] + [confs[int(i * (len(confs) - 1) / 40)] for i in range(41)]:   # 41 quantiles of confidence
                s = score_decisions(decide_all(Single(src[p], reject(q).given(tau=tau)), records))
                if s["coverage"] > 0:
                    curve.append((s["coverage"], s["selective_accuracy"]))
            def at(cov):                                   # selective accuracy at the smallest coverage >= cov
                reached = [c for c in curve if c[0] >= cov - 1e-9]
                return min(reached, key=lambda c: c[0])[1] if reached else None
            most = max(c[0] for c in curve)                # below 1 when the provider refuses some records
            levels = [c / 20 for c in range(1, 21) if c / 20 <= most + 1e-9]
            aurc = statistics.fmean(1 - at(c) for c in levels)   # area under the risk-coverage curve, up to `most`
            out[task][p] = {"max_coverage": most, "at_max": at(most), "at_80": at(0.8), "at_50": at(0.5), "aurc": aurc}
    return out


def rule_transfer():
    """E3. Fit tau for a target risk on one provider's beliefs (half A); apply it to every provider (half B)."""
    targets = {"steam_recommend": 0.05, "appstore_stars": 0.40, "appstore_app": 0.20}
    out = {}
    for task, q in EVALS.items():
        src = beliefs(task)
        records = src["typesafe"].records()
        a, b = [r for r in records if half(r) == 0], [r for r in records if half(r) == 1]
        out[task] = {"target_error": targets[task], "fit": {}}
        for p in PROVIDERS:
            feasible = []
            for tau in sorted({round(confidence(src[p](r)["answers"][q]), 4) for r in a if src[p](r)}):
                s = score_decisions(decide_all(Single(src[p], reject(q).given(tau=tau)), a))
                if s["coverage"] > 0 and 1 - s["selective_accuracy"] <= targets[task]:
                    feasible.append((s["coverage"], tau))
            if not feasible:
                out[task]["fit"][p] = None
                continue
            tau = max(feasible)[1]                          # the most coverage that meets the target on half A
            applied = {}
            for other in PROVIDERS:
                s = score_decisions(decide_all(Single(src[other], reject(q).given(tau=tau)), b))
                applied[other] = {"error": None if s["selective_accuracy"] is None else 1 - s["selective_accuracy"], "coverage": s["coverage"]}
            out[task]["fit"][p] = {"tau": tau, "applied": applied}
    return out


def panels():
    """E4. Parallel: the same question to several providers, one decision over all their beliefs."""
    out = {}
    for task, q in EVALS.items():
        src = beliefs(task)
        records = src["typesafe"].records()
        single = {p: decide_all(Single(src[p], reject(q)), records) for p in PROVIDERS}
        best = max(PROVIDERS, key=lambda p: score_decisions(single[p])["accuracy"])
        row = {"best_single": best, "best_single_accuracy": score_decisions(single[best])["accuracy"],
               "typesafe_accuracy": score_decisions(single["typesafe"])["accuracy"]}
        for name, members in [("hosted", HOSTED), ("local", LOCAL), ("all", PROVIDERS)]:
            for how, rule in [("vote", vote(q)), ("pool", pool(q))]:
                result = decide_all(Parallel([src[m] for m in members], rule), records)
                row[f"{name}_{how}"] = {**score_decisions(result), "vs_best": compare(single[best], result)}
        # correlated errors: when two providers are both wrong, how often they give the same wrong answer
        pairs = {}
        for i, x in enumerate(PROVIDERS):
            for y in PROVIDERS[i + 1:]:
                both = [(sx["action"], sy["action"]) for sx, sy in zip(single[x], single[y])
                        if not correct(sx["action"], sx["label"]) and not correct(sy["action"], sy["label"])]
                wrong_x = sum(not correct(s["action"], s["label"]) for s in single[x])
                pairs[f"{x}+{y}"] = {"p_y_wrong_given_x_wrong": len(both) / wrong_x if wrong_x else None,
                                     "same_wrong_answer": statistics.fmean(a == b for a, b in both) if both else None}
        row["errors"] = pairs
        out[task] = row
    return out


def cascades():
    """E5. Orchestrator-worker: a free local unit acts when confident and hands the rest to a hosted worker.
    The control escalates the same number of records chosen at random."""
    out = {}
    for task, q in EVALS.items():
        src = beliefs(task)
        records = src["typesafe"].records()
        out[task] = {}
        for first, worker in [("opendecider", "typesafe"), ("opendecider", "openai"), ("von", "typesafe")]:
            alone = score_decisions(decide_all(Single(src[worker], reject(q)), records))
            local = decide_all(Single(src[first], reject(q)), records)
            hosted = {o["id"]: o for o in decide_all(Single(src[worker], reject(q)), records)}
            rows = []
            for tau in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
                arch = OrchestratorWorker(Single(src[first], gate(q).given(tau=tau)), {"escalate": Single(src[worker], reject(q))})
                result = decide_all(arch, records)
                s = score_decisions(result)
                k = sum(o["routed"] == "escalate" for o in result)
                rng = random.Random(7)
                control = []
                for _ in range(200):                       # escalate k records at random instead of the unsure ones
                    chosen = set(rng.sample([r["id"] for r in records], k))
                    control.append(statistics.fmean(correct((hosted[o["id"]] if o["id"] in chosen else o)["action"], o["label"]) for o in local))
                control.sort()
                rows.append({"tau": tau, "escalated": k / len(records), "accuracy": s["accuracy"], "random_escalation": statistics.fmean(control),
                             "random_95": (control[5], control[194]), "usd_per_1k": s["usd_per_1k"],
                             "vs_worker": compare(list(hosted.values()), result), "vs_first": compare(local, result)})
            out[task][f"{first}->{worker}"] = {"first_alone": score_decisions(local)["accuracy"], "worker_alone": alone["accuracy"],
                                               "worker_usd_per_1k": alone["usd_per_1k"], "sweep": rows}
    return out


if __name__ == "__main__":
    results = {"thresholds_and_costs": thresholds_and_costs(), "risk_coverage": risk_coverage(),
               "rule_transfer": rule_transfer(), "panels": panels(), "cascades": cascades()}
    (OUT / "offline.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(json.dumps(results, indent=1, default=str)[:4000])
