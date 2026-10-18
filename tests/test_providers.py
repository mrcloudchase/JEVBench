import json
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conftest import fixture
from tdm.providers import PROVIDERS, DeepSeek, OpenAI, TypeSafe, Von, load_provider

QUESTIONS = {
    "urgent": {"type": "noul", "instructions": "Is it urgent?", "criteria": {"true": "needs action today"}},
    "team": {"type": "choice", "instructions": "Which team?", "criteria": {"billing": "Payments", "other": None}},
    "anger": {"type": "score", "instructions": "How angry?", "criteria": ["Calm", "Annoyed", "Furious"]},
}


def test_registered_providers():
    assert {"typesafe", "openai", "deepseek", "von", "opendecider", "openjev"} <= set(PROVIDERS)


def test_key_comes_from_vendor_variable_and_local_needs_none():
    assert load_provider("typesafe", {"TYPESAFE_API_KEY": "k"}).api_key == "k"
    assert load_provider("von", {}).url.endswith(":8101/v1/systemone")
    with pytest.raises(RuntimeError, match="PROVIDER_API_KEY"):
        load_provider("openai", {})


def test_typesafe_is_the_wire_format_unchanged():
    request, response = fixture("example_request_text.json"), fixture("example_response_text_jev-1.13.0.json")
    p = TypeSafe(api_key="k")
    assert p.payload(request["state"], request["questions"])["questions"] == request["questions"]
    assert p.parse(response, request["questions"])["answers"] == response["answers"]


def test_openai_translates_questions_both_ways():
    p = OpenAI(api_key="k")
    body = p.payload({"msg": "hi"}, QUESTIONS)
    assert body["input"] == '{"msg": "hi"}'
    noul, choice, score = body["questions"]
    assert noul["type"] == "predicate" and "True means: needs action today." in noul["instructions"]
    assert choice["choices"] == [{"value": "billing", "description": "Payments"}, {"value": "other"}]
    assert score["levels"] == [{"label": "Calm"}, {"label": "Annoyed"}, {"label": "Furious"}]
    answers = p.parse({"model": "gpt-6-luna", "answers": [
        {"type": "predicate", "name": "urgent", "probability": 0.8},
        {"type": "choice", "name": "team", "choice": "billing", "confidence": 0.9,
         "probabilities": [{"value": "billing", "probability": 0.95}, {"value": "other", "probability": 0.05}]},
        {"type": "refusal", "name": "anger"}]}, QUESTIONS)["answers"]
    assert answers["urgent"] == {"type": "noul", "noul": 0.8}
    assert answers["team"]["probabilities"] == {"billing": 0.95, "other": 0.05}
    assert answers["anger"] == {"type": "refusal"}


def test_deepseek_reads_a_belief_from_next_token_probabilities():
    p = DeepSeek(api_key="k")
    q = {"team": QUESTIONS["team"]}
    assert "A: Payments\nB: other" in p.payload("hi", q)["messages"][1]["content"]
    top = [{"token": " A", "logprob": math.log(0.6)}, {"token": "B", "logprob": math.log(0.2)}, {"token": "The", "logprob": math.log(0.2)}]
    body = {"model": "deepseek-flash", "usage": {"prompt_tokens": 50, "completion_tokens": 1},
            "choices": [{"logprobs": {"content": [{"top_logprobs": top}]}}]}
    answer = p.parse(body, q)["answers"]["team"]
    assert answer["choice"] == "billing" and answer["probabilities"]["billing"] == pytest.approx(0.75)
    body["choices"][0]["logprobs"]["content"][0]["top_logprobs"] = [{"token": "The", "logprob": 0.0}]
    assert p.parse(body, q)["answers"]["team"] == {"type": "refusal"}
    assert len(p.key("hi", QUESTIONS).split("+")) == 3            # one request per question


def test_http_client_retries_then_answers():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            status, body = (503, b"{}") if len(seen) == 1 else (200, json.dumps(
                {"model": "von-1.3.0", "answers": {"urgent": {"type": "noul", "noul": 0.7}}, "usage": {"input_tokens": 1000}}).encode())
            self.send_response(status)
            self.send_header("Retry-After", "0")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        p = Von(url=f"http://127.0.0.1:{server.server_port}/v1/systemone")
        result = p("ticket", {"urgent": QUESTIONS["urgent"]})
    finally:
        server.shutdown()
    assert len(seen) == 2 and seen[1]["state"] == "ticket"
    assert result["answers"]["urgent"]["noul"] == 0.7 and result["cost_usd"] == 0.0 and result["provider"] == "von"
