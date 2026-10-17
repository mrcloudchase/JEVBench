"""The canonical architectures, assembled from Believe and Decide nodes and expression objects."""

from engine import Aggregate, Architecture, Believe, Decide, Evidence, Input, Nominal, Ordinal, Select, Use, majority

INTENT = Nominal("The primary intent of this customer message", {
    "order_status": "Asking about an existing order", "product_question": "Asking about a product before buying",
    "return_exchange": "Wants to return or exchange something", "complaint": "Unhappy with experience, wants resolution"})
COMPLEXITY = Ordinal("How complex is this request to resolve",
                     ["Simple lookup or standard procedure", "Requires some judgment or multi-step process", "Unusual situation, edge case, or escalation needed"])


def single():
    intent = Believe(INTENT)
    return Architecture(Decide(intent.top))


def gated(floor=0.6):
    intent = Believe(INTENT)
    return Architecture(Decide(Select((intent.confidence >= floor, intent.top), default="abstain")))


def routed():                                   # TypeSafe's routing code, as objects
    intent = Believe(INTENT)
    complexity = Believe(COMPLEXITY)
    return Architecture(Decide(Select(
        (intent.confidence < 0.5, "human"),
        (intent.top == "complaint", Select(((complexity.expected > 1) | (complexity.confidence < 0.5), "human"), default="complaint_llm")),
        default=intent.top)))


def panel():
    a = Believe(INTENT, Evidence(message=Input(), note="Read the message strictly and literally."))
    b = Believe(INTENT, Evidence(message=Input(), note="Read the message charitably."))
    c = Believe(INTENT, model="jev-preview")
    vote = Aggregate(majority, a.top, b.top, c.top)
    return Architecture(Decide(Select((vote.is_none(), "human"), default=vote)))


def escalation(floor=0.8):
    first = Believe(INTENT)
    second = Believe(INTENT, Evidence(message=Input(), hint="A first reading was unsure; weigh the customer's main goal."),
                     model="jev-preview", when=first.confidence < floor)
    return Architecture(Decide(Select((second.is_none(), first.top), default=second.top)))


def chain():                                     # beliefs become evidence
    triage = Believe(INTENT)
    complexity = Believe(COMPLEXITY)
    handle = Nominal("Given `triage` and `complexity`, who should handle `message`?",
                     {"bot": "An automated reply is enough", "agent": "A human agent is needed", "manager": "Needs a manager"})
    chair = Believe(handle, Evidence(message=Input(), triage=triage.probabilities, complexity=complexity.probabilities))
    return Architecture(Decide(chair.top))


def vetoed():                                    # a gate: stakes as a constant that overrides any belief
    intent = Believe(INTENT)
    threat = Believe(Nominal("Does the message contain a threat of violence?", {"yes": None, "no": None}))
    return Architecture(Decide(Select((threat.p("yes") >= 0.5, "security_team"), default=intent.top)))


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
