"""The canonical architectures. Questions are in the model API's own format; beliefs are its answers."""

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
    b = Believe(INTENT)
    return Architecture(Decide(lambda b: b["intent"]["choice"], b))


def gated(floor=0.6):
    b = Believe(INTENT)
    return Architecture(Decide(lambda b: b["intent"]["choice"] if b["intent"]["confidence"] >= floor else "abstain", b))


def routed():                                    # TypeSafe's routing code; one call, two questions
    b = Believe(INTENT | COMPLEXITY)
    def rule(b):
        intent, complexity = b["intent"], b["complexity"]
        if intent["confidence"] < 0.5:
            return "human"
        if intent["choice"] == "complaint":
            return "human" if complexity["score"] > 1 or complexity["confidence"] < 0.5 else "complaint_llm"
        return intent["choice"]
    return Architecture(Decide(rule, b))


def panel():
    a = Believe(INTENT, lambda m: {"message": m, "note": "Read the message strictly and literally."})
    b = Believe(INTENT, lambda m: {"message": m, "note": "Read the message charitably."})
    c = Believe(INTENT, provider="jev-preview")
    vote = Decide(lambda a, b, c: majority(a["intent"]["choice"], b["intent"]["choice"], c["intent"]["choice"]), a, b, c)
    return Architecture(Decide(lambda v: v or "human", vote))


def escalation(floor=0.8):
    first = Believe(INTENT)
    unsure = Decide(lambda f: f["intent"]["confidence"] < floor, first)
    second = Believe(INTENT, lambda m: {"message": m, "hint": "A first reading was unsure; weigh the customer's main goal."},
                     INPUT, provider="jev-preview", when=unsure)
    return Architecture(Decide(lambda f, s: (s or f)["intent"]["choice"], first, second))


def chain():                                     # a belief becomes evidence
    triage = Believe(INTENT | COMPLEXITY)
    chair = Believe(HANDLE, lambda m, t: {"message": m, "triage": t}, INPUT, triage)
    return Architecture(Decide(lambda c: c["handle"]["choice"], chair))


def vetoed():                                    # a gate: stakes as a constant that overrides any belief
    b = Believe(INTENT | THREAT)
    return Architecture(Decide(lambda b: "security_team" if b["threat"]["noul"] >= 0.5 else b["intent"]["choice"], b))


def nested():                                    # an architecture is callable, so it is a node's function
    council = Decide(panel())
    return Architecture(Decide(lambda c: "human" if c == "human" else c, council))


MESSAGE = ("I ordered the blue jacket three weeks ago, it arrived in the wrong size, and when I called nobody "
           "could tell me how to swap it. This is the second order you've messed up and I want it sorted today.")

if __name__ == "__main__":
    for name, build in [("single", single), ("gated", gated), ("routed", routed), ("panel", panel),
                        ("escalation", escalation), ("chain", chain), ("vetoed", vetoed), ("nested", nested)]:
        arch = build()
        print(f"{name:11s} levels={len(arch.levels)} max_calls={arch.calls}  ->  {arch(MESSAGE)}")
