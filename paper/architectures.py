"""The canonical architectures, assembled from Believe and Decide nodes and operations.
Questions are in the model API's own format; beliefs are its answers."""

from engine import Aggregate, Architecture, Believe, Decide, Evidence, Input, Select, Use, majority

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
    return Architecture(Decide(b.intent.choice))


def gated(floor=0.6):
    b = Believe(INTENT)
    return Architecture(Decide(Select((b.intent.confidence >= floor, b.intent.choice), default="abstain")))


def routed():                                    # TypeSafe's routing code, as objects; one call, two questions
    b = Believe(INTENT | COMPLEXITY)
    return Architecture(Decide(Select(
        (b.intent.confidence < 0.5, "human"),
        (b.intent.choice == "complaint", Select(((b.complexity.score > 1) | (b.complexity.confidence < 0.5), "human"), default="complaint_llm")),
        default=b.intent.choice)))


def panel():
    a = Believe(INTENT, Evidence(message=Input(), note="Read the message strictly and literally."))
    b = Believe(INTENT, Evidence(message=Input(), note="Read the message charitably."))
    c = Believe(INTENT, provider="jev-preview")
    vote = Aggregate(majority, a.intent.choice, b.intent.choice, c.intent.choice)
    return Architecture(Decide(Select((vote.is_none(), "human"), default=vote)))


def escalation(floor=0.8):
    first = Believe(INTENT)
    second = Believe(INTENT, Evidence(message=Input(), hint="A first reading was unsure; weigh the customer's main goal."),
                     provider="jev-preview", when=first.intent.confidence < floor)
    return Architecture(Decide(Select((second.is_none(), first.intent.choice), default=second.intent.choice)))


def chain():                                     # a belief becomes evidence
    triage = Believe(INTENT | COMPLEXITY)
    chair = Believe(HANDLE, Evidence(message=Input(), triage=triage))
    return Architecture(Decide(chair.handle.choice))


def vetoed():                                    # a gate: stakes as a constant that overrides any belief
    b = Believe(INTENT | THREAT)
    return Architecture(Decide(Select((b.threat.noul >= 0.5, "security_team"), default=b.intent.choice)))


def nested():                                    # an architecture as a node
    council = Use(panel())
    return Architecture(Decide(Select((council == "human", "human"), default=council)))


MESSAGE = ("I ordered the blue jacket three weeks ago, it arrived in the wrong size, and when I called nobody "
           "could tell me how to swap it. This is the second order you've messed up and I want it sorted today.")

if __name__ == "__main__":
    for name, build in [("single", single), ("gated", gated), ("routed", routed), ("panel", panel),
                        ("escalation", escalation), ("chain", chain), ("vetoed", vetoed), ("nested", nested)]:
        arch = build()
        print(f"{name:11s} levels={len(arch.levels)} max_calls={arch.calls}  ->  {arch(MESSAGE)}")
