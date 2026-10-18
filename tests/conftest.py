import json
from pathlib import Path

import pytest

from tdm.providers import Provider

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class Fake(Provider):
    """A provider that answers from a function of the state, counting its calls. No network."""

    name, url, model, required = "fake", "http://fake.invalid/v1/systemone", "fake-1", ("url", "model")

    def __init__(self, answer=None, fail_on=(), **kw):
        super().__init__(**kw)
        self.answer = answer or (lambda state: {"refund": {"type": "noul", "noul": 0.9 if "refund" in str(state) else 0.1}})
        self.fail_on, self.calls = set(fail_on), 0

    def payload(self, state, questions):
        return {"model": self.model, "state": state, "questions": questions}

    def parse(self, body, questions):
        return body

    def __call__(self, state, questions):
        self.calls += 1
        if isinstance(state, str) and state in self.fail_on:
            raise RuntimeError("HTTP 500 from fake")
        return {"provider": self.name, "model": self.model, "answers": self.answer(state),
                "usage": {"input_tokens": 10}, "latency_ms": 1.0, "cost_usd": 1e-6}


@pytest.fixture
def fake():
    return Fake()


@pytest.fixture
def records():
    return [{"id": "a", "state": "I want a refund", "label": 1, "source": "x"},
            {"id": "b", "state": "Where is my order?", "label": 0, "source": "y"},
            {"id": "c", "state": "refund please", "label": 1}]


@pytest.fixture
def questions():
    return {"refund": {"type": "noul", "instructions": "The customer asks for a refund"}}
