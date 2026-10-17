"""The primitive: a provider turns state and questions into a belief.

    belief = Belief(questions, provider)(state)

A Provider is any endpoint that speaks the typed-decision wire format, reached through the official
typesafe-sdk and selected by base_url, api_key and model (defaults: TYPESAFE_BASE_URL, TYPESAFE_API_KEY,
TYPESAFE_DEFAULT_MODEL). A Belief holds a set of questions; calling it with state makes one provider
call and returns the provider's answers, untouched, keyed by question id.

A belief can be written as YAML:

    provider:            # optional; model and base_url. The API key always comes from the environment.
      model: jev-latest
    questions:           # the wire format's questions, unchanged
      is_urgent: {type: noul, instructions: "The message conveys urgency"}
    state: "..."         # optional; can also be given on the command line

    python engine.py belief.yaml [--state TEXT | --state-file FILE]
"""

from __future__ import annotations

from pathlib import Path

import yaml


class Provider:
    """state + questions -> answers, through any endpoint that speaks the wire format."""

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None, **options):
        from typesafe_sdk import TypeSafeClient
        self.client = TypeSafeClient(api_key=api_key, base_url=base_url, model=model, **options)

    def __call__(self, state, questions: dict) -> dict:
        return self.client.system_one(state, questions).model_dump(mode="json")["answers"]


class Belief:
    """A set of questions. Calling it with state returns the provider's answers to them."""

    def __init__(self, questions: dict, provider: Provider | None = None, state=None):
        self.questions, self.provider, self.state = questions, provider or Provider(), state

    def __call__(self, state=None) -> dict:
        state = self.state if state is None else state
        if state is None:
            raise ValueError("no state: put `state:` in the YAML or pass it in")
        return self.provider(state, self.questions)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Belief":
        spec = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        provider = spec.get("provider") or {}
        if "api_key" in provider:
            raise ValueError("keep api_key out of YAML; set TYPESAFE_API_KEY in the environment")
        return cls(spec["questions"], Provider(**provider), spec.get("state"))


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Form a belief from a YAML file of questions and state.")
    parser.add_argument("belief", help="YAML file with `questions`, optional `provider` and `state`")
    parser.add_argument("--state", help="state as text, overriding the file's `state`")
    parser.add_argument("--state-file", help="state from a YAML or JSON file, overriding the file's `state`")
    args = parser.parse_args()

    state = args.state
    if args.state_file:
        state = yaml.safe_load(Path(args.state_file).read_text(encoding="utf-8"))
    print(json.dumps(Belief.from_yaml(args.belief)(state), indent=2))
