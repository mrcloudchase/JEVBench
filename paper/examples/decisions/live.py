"""Decision experiments that need new beliefs: chained and evaluator-optimizer, on TypeSafe and OpenAI.

    python live.py               # runs them; needs ../appstore_*/dataset.jsonl (rebuild with wrangle.py) and the API keys

A chained unit's evidence includes an earlier belief, and an evaluator-optimizer re-asks with the
beliefs so far, so neither can be replayed from the single-unit results. Outcomes, with every belief
they formed, go to outcomes.<experiment>.<provider>.jsonl; responses are cached in cache.<provider>.jsonl.

    python live.py --score       # scores the outcomes; needs only the outcomes and results files
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from data import Cache, load_dataset, load_questions  # noqa: E402
from decide import ABSTAIN, Chained, Decision, EvaluatorOptimizer, Live, confidence, decide_all, top, write_jsonl  # noqa: E402
from engine import load_env  # noqa: E402
from providers import load_provider  # noqa: E402

load_env(HERE.parent.parent / ".env")

AREA = {"area": {"type": "choice", "instructions": "What kind of app is this App Store review about?", "criteria": {
    "social_media": "Social media: feeds, posts, followers, stories, reels, short videos, creators",
    "streaming": "Streaming entertainment: shows, movies, music, podcasts, videos to watch or listen to",
    "communication": "Communication: messaging, chats, calls, email",
    "commerce": "Shopping and services: buying products, orders, deliveries, rides, food",
    "learning": "Learning: lessons, courses, language practice"}}}

FINDINGS = {k: {"type": "noul", "instructions": v} for k, v in {
    "bug": "The reviewer reports a bug, a crash, or something that does not work",
    "praise": "The reviewer praises the app",
    "money": "The reviewer complains about price, ads or subscriptions",
    "request": "The reviewer asks for a feature or a change",
    "recommend": "The reviewer would recommend the app to others"}.items()}

TASKS = {"appstore_app": "app", "appstore_stars": "stars"}


def readings(answer, k=2):
    """A belief as evidence: its k most probable options with their probabilities (none for a refusal)."""
    if "probabilities" not in answer:
        return []
    probs = answer["probabilities"]
    legend = answer.get("legend") or {}
    best = sorted(probs, key=probs.get, reverse=True)[:k]
    return [{"option": legend.get(o, o), "probability": round(probs[o], 2)} for o in best]


def chained(task, q, questions, provider, cache):
    """Ask a coarser question first; its belief becomes part of the evidence for the task's question."""
    if task == "appstore_app":
        first = Live(AREA, provider, cache=cache)
        then_q = {q: {**questions[q], "instructions": questions[q]["instructions"] + " `area` is an earlier reading of what kind of app it is."}}
        then = Live(then_q, provider, cache=cache,
                    evidence=lambda r, formed: {**r["state"], "area": readings(formed[0]["area"], 2)})
    else:
        first = Live(FINDINGS, provider, cache=cache)
        then_q = {q: {**questions[q], "instructions": questions[q]["instructions"] + " `findings` are earlier readings of the review."}}
        then = Live(then_q, provider, cache=cache,
                    evidence=lambda r, formed: {**r["state"], "findings": {FINDINGS[k]["instructions"]: round(a["noul"], 2) for k, a in formed[0].items() if "noul" in a}})
    return Chained([first, then], Decision(lambda b1, b2: top(b2[q]) if top(b2[q]) is not None else ABSTAIN))


def evaluator_optimizer(q, questions, provider, cache, tau=0.7, rounds=3):
    """Re-ask until the top option's probability reaches tau, showing the earlier readings; abstain if it never does."""
    def evidence(record, formed):
        if not formed:
            return record["state"]
        return {**record["state"], "earlier_readings": [readings(a[q]) for a in formed],
                "note": "Earlier readings were unsure between the options in `earlier_readings`. Decide on the strongest evidence in the review."}
    done = Decision(lambda b, tau: confidence(b[q]) >= tau, tau=tau)
    decision = Decision(lambda b, tau: top(b[q]) if confidence(b[q]) >= tau and top(b[q]) is not None else ABSTAIN, tau=tau)
    return EvaluatorOptimizer(Live(questions, provider, evidence=evidence, cache=cache), done, decision, rounds)


if __name__ == "__main__" and "--score" not in sys.argv:
    for name in ("typesafe", "openai"):
        provider = load_provider(name)
        cache = Cache(HERE / f"cache.{name}.jsonl")
        for task, q in TASKS.items():
            records = load_dataset(HERE.parent / task / "dataset.jsonl")
            questions = load_questions(HERE.parent / task / "questions.yaml")
            for experiment, arch in [("chained", chained(task, q, questions, provider, cache)),
                                     ("evaluator_optimizer", evaluator_optimizer(q, questions, provider, cache))]:
                outcomes = decide_all(arch, records)
                write_jsonl(HERE / f"outcomes.{experiment}_{task.split('_')[1]}.{name}.jsonl", outcomes)
                acted = [o for o in outcomes if o["action"] != ABSTAIN]
                print(f"{name} {task} {experiment}: {len(outcomes)} records, {len(acted)} acted, "
                      f"{sum(str(o['action']) == str(o['label']) for o in outcomes)} correct, "
                      f"{sum(o['calls'] for o in outcomes)} calls", flush=True)
    print("LIVE_DONE")


def scores():
    """Chained against the recorded single unit; the loop against its own first round, and against
    re-thresholding that first round to the loop's coverage."""
    from decide import Recorded, Single, compare, score_decisions
    out = {}
    for name in ("typesafe", "openai"):
        for task, q in TASKS.items():
            short = task.split("_")[1]
            single_src = Recorded(HERE.parent / task / f"results.{name}.jsonl")
            single = decide_all(Single(single_src, Decision(lambda b: top(b[q]) if top(b[q]) is not None else ABSTAIN)), single_src.records())
            chain = [json.loads(line) for line in (HERE / f"outcomes.chained_{short}.{name}.jsonl").read_text().splitlines()]
            loop = [json.loads(line) for line in (HERE / f"outcomes.evaluator_optimizer_{short}.{name}.jsonl").read_text().splitlines()]

            def first_round(tau):                          # the same run, deciding on round one only
                return [{**o, "action": (top(o["beliefs"][0][q]) if o["beliefs"][0] and confidence(o["beliefs"][0][q]) >= tau
                                         and top(o["beliefs"][0][q]) is not None else ABSTAIN)} for o in loop]
            loop_s = score_decisions(loop)
            confs = sorted((confidence(o["beliefs"][0][q]) if o["beliefs"][0] else 0.0) for o in loop)
            matched = min(confs, key=lambda t: abs(score_decisions(first_round(t))["coverage"] - loop_s["coverage"]))
            out[f"{name}/{short}"] = {
                "single": score_decisions(single), "chained": score_decisions(chain), "chained_vs_single": compare(single, chain),
                "loop": loop_s, "loop_rounds": sum(o["rounds"] for o in loop) / len(loop),
                "round1_at_tau": score_decisions(first_round(0.7)),
                "round1_matched": {**score_decisions(first_round(matched)), "tau": matched},
                "loop_vs_matched": compare(first_round(matched), loop)}
    return out


if __name__ == "__main__" and "--score" in sys.argv:
    print(json.dumps(scores(), indent=1, default=str))
