"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions, provider)(state)

A Provider is any endpoint that speaks the typed-decision wire format, reached through the official
typesafe-sdk and selected by base_url, api_key and model (defaults: TYPESAFE_BASE_URL, TYPESAFE_API_KEY,
TYPESAFE_DEFAULT_MODEL). A Belief holds a set of questions; calling it with state makes one provider
call and returns the provider's answers, untouched, keyed by question id.
"""

from __future__ import annotations


class Provider:
    """state + questions -> answers, through any endpoint that speaks the wire format."""

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None, **options):
        from typesafe_sdk import TypeSafeClient
        self.client = TypeSafeClient(api_key=api_key, base_url=base_url, model=model, **options)

    def __call__(self, state, questions: dict) -> dict:
        return self.client.system_one(state, questions).model_dump(mode="json")["answers"]


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider | None = None):
        self.questions, self.provider = questions, provider or Provider()

    def __call__(self, state) -> dict:
        return self.provider(state, self.questions)


if __name__ == "__main__":
    # TypeSafe's quickstart example, verbatim: https://docs.typesafe.ai/introduction/quickstart
    import json

    ticket = Belief({
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this",
            "criteria": {
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "sales": "Pricing or account questions",
            },
        },
        "frustration": {
            "type": "score",
            "instructions": "How frustrated the customer appears",
            "criteria": ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"],
        },
        "is_urgent": {
            "type": "noul",
            "instructions": "The message conveys urgency or time-sensitivity",
        },
    })

    state = ("Our API integration started returning 500 errors on every request about 20 minutes ago, "
             "and we can't process any customer orders until this is fixed.")

    print(json.dumps(ticket(state), indent=2))
