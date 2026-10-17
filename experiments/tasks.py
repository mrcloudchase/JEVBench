"""The three exemplar decisions. Each task supplies the question, the alternatives and the framing text
that the task-agnostic architectures consume. Items carry the ground-truth label."""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def _load(name: str):
    return json.loads((DATA / name).read_text())


def offensive() -> dict:
    rows = _load("offensive.json")
    labels = {0: "not_offensive", 1: "offensive"}
    return {
        "name": "offensive",
        "description": "Offensive language detection (TweetEval offensive, test split, first 300).",
        "items": [{"text": r["text"], "label": labels[r["label"]]} for r in rows],
        "instructions": "Is `text` offensive?",
        "criteria": {"offensive": "Contains insults, slurs, threats or targeted harassment",
                     "not_offensive": "No offensive content, even if blunt or critical"},
        "frames": ["Read the text strictly and literally.",
                   "Read the text charitably, allowing for humour, slang and context.",
                   "Judge as a content moderator applying community standards."],
        "aux": ["Does the text contain an insult or a slur?",
                "Does the text direct hostility at a person or a group?",
                "Does the text contain a threat or incitement?"],
        "stance_for": "Look for every reason the text is harmless.",
        "stance_against": "Look for every reason the text is offensive.",
    }


def claims() -> dict:
    pairs = _load("claims.json")
    labels = {0: "supports", 1: "refutes", 2: "not_enough_info"}
    random.seed(11)
    by_label = {k: [p for p in pairs if p["label"] == k] for k in labels}
    items = []
    for k, group in by_label.items():
        random.shuffle(group)
        items += [{"text": {"claim": p["claim"], "evidence": p["evidence"]}, "label": labels[k]} for p in group[:100]]
    random.shuffle(items)
    return {
        "name": "claims",
        "description": "Claim verification (Climate-FEVER claim/evidence pairs, 100 per label).",
        "items": items,
        "instructions": "Does `evidence` support or refute `claim`?",
        "criteria": {"supports": "The evidence supports the claim",
                     "refutes": "The evidence contradicts the claim",
                     "not_enough_info": "The evidence neither supports nor refutes the claim"},
        "frames": ["Read literally: the evidence must state the claim's content directly.",
                   "Allow reasonable inference from the evidence to the claim.",
                   "Judge as a professional fact-checker."],
        "aux": ["Does the evidence discuss the same subject as the claim?",
                "Does the evidence state a fact that bears on whether the claim is true?",
                "Does the evidence contradict any part of the claim?"],
        "stance_for": "Look for every reason the evidence supports the claim.",
        "stance_against": "Look for every reason the evidence refutes the claim or is unrelated to it.",
    }


def banking() -> dict:
    data = _load("banking.json")
    names = data["names"]
    return {
        "name": "banking",
        "description": "Customer intent routing (Banking77, 77 intents, 300 sampled test items).",
        "items": [{"text": r["text"], "label": names[r["label"]]} for r in data["rows"]],
        "instructions": "What is the customer's intent?",
        "criteria": {n: n.replace("_", " ") for n in names},
        "frames": ["Read the message literally.",
                   "Infer the customer's underlying goal.",
                   "Judge as an experienced bank support agent."],
        "aux": ["Is the customer asking about a card?",
                "Is the customer asking about a payment, transfer or top-up?",
                "Is the customer reporting something that went wrong?"],
        "stance_for": None,
        "stance_against": None,
    }


TASKS = {"offensive": offensive, "claims": claims, "banking": banking}
