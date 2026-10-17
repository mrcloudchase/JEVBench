"""The canonical architectures. Questions are in the model API's own format; beliefs are its answers.
Decide(rule, *beliefs, **values): the rule receives beliefs positionally and the author's values by name."""

from engine import INPUT, Architecture, Believe, Decide, majority

INTENT = {"intent": {"type": "choice", "instructions": "The primary intent of this customer message", "criteria": {
    "order_status": "Asking about an existing order", "product_question": "Asking about a product before buying",
    "return_exchange": "Wants to return or exchange something", "complaint": "Unhappy with experience, wants resolution"}}}
COMPLEXITY = {"complexity": {"type": "score", "instructions": "How complex is this request to resolve", "criteria": [
    "Simple lookup or standard procedure", "Requires some judgment or multi-step process", "Unusual situation, edge case, or escalation needed"]}}
THREAT = {"threat": {"type": "noul", "instructions": "Does the message contain a threat of violence?"}}
HANDLE = {"handle": {"type": "choice", "instructions": "Given `triage`, who should handle `message`?", "criteria": {
    "bot": "An automated reply is enough", "agent": "A human agent is needed", "manager": "Needs a manager"}}}


def single():
    return Architecture(Decide(lambda b: b["intent"]["choice"], Believe(INTENT)))


def gated():
    return Architecture(Decide(lambda b, floor, abstain: b["intent"]["choice"] if b["intent"]["confidence"] >= floor else abstain,
                               Believe(INTENT), floor=0.6, abstain="abstain"))


def routed():                                    # TypeSafe's routing code; one call, two questions
    def rule(b, floor, complex_above):
        intent, complexity = b["intent"], b["complexity"]
        if intent["confidence"] < floor:
            return "human"
        if intent["choice"] == "complaint":
            return "human" if complexity["score"] > complex_above or complexity["confidence"] < floor else "complaint_llm"
        return intent["choice"]
    return Architecture(Decide(rule, Believe(INTENT | COMPLEXITY), floor=0.5, complex_above=1))


def panel():
    frame = lambda m, note: {"message": m, "note": note}
    a = Believe(INTENT, frame, note="Read the message strictly and literally.")
    b = Believe(INTENT, frame, note="Read the message charitably.")
    c = Believe(INTENT, provider="jev-preview")
    vote = Decide(lambda a, b, c: majority(a["intent"]["choice"], b["intent"]["choice"], c["intent"]["choice"]), a, b, c)
    return Architecture(Decide(lambda v, fallback: v or fallback, vote, fallback="human"))


def escalation():
    first = Believe(INTENT)
    unsure = Decide(lambda f, floor: f["intent"]["confidence"] < floor, first, floor=0.8)
    second = Believe(INTENT, lambda m, hint: {"message": m, "hint": hint}, INPUT, provider="jev-preview", when=unsure,
                     hint="A first reading was unsure; weigh the customer's main goal.")
    return Architecture(Decide(lambda f, s: (s or f)["intent"]["choice"], first, second))


def chain():                                     # a belief becomes evidence
    triage = Believe(INTENT | COMPLEXITY)
    chair = Believe(HANDLE, lambda m, t: {"message": m, "triage": t}, INPUT, triage)
    return Architecture(Decide(lambda c: c["handle"]["choice"], chair))


def vetoed():                                    # a gate: a value that overrides any belief
    return Architecture(Decide(lambda b, floor, to: to if b["threat"]["noul"] >= floor else b["intent"]["choice"],
                               Believe(INTENT | THREAT), floor=0.5, to="security_team"))


def nested():                                    # an architecture is callable, so it is a node's function
    council = Decide(panel())
    return Architecture(Decide(lambda c: c, council))


MESSAGE = ("I ordered the blue jacket three weeks ago, it arrived in the wrong size, and when I called nobody "
           "could tell me how to swap it. This is the second order you've messed up and I want it sorted today.")

if __name__ == "__main__":
    for name, build in [("single", single), ("gated", gated), ("routed", routed), ("panel", panel),
                        ("escalation", escalation), ("chain", chain), ("vetoed", vetoed), ("nested", nested)]:
        arch = build()
        print(f"{name:11s} levels={len(arch.levels)} max_calls={arch.calls}  ->  {arch(MESSAGE)}")
