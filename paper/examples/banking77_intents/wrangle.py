"""Banking77 intents -> dataset.jsonl and questions.yaml in the engine's format.

Source: experiments/data/banking.json in this repository: 300 messages sampled (seed 7) from the
3,080-message Banking77 test split (PolyAI, CC BY 4.0), covering 76 of the 77 intents.

    python wrangle.py
"""
import json
from pathlib import Path

source = json.loads((Path(__file__).resolve().parents[3] / "experiments/data/banking.json").read_text(encoding="utf-8"))
names, rows = source["names"], source["rows"]

with open("dataset.jsonl", "w", encoding="utf-8") as out:
    for i, r in enumerate(rows):
        out.write(json.dumps({"id": f"b{i:03d}", "state": r["text"], "label": names[r["label"]]}) + "\n")

lines = ["# One 77-way choice question. Option ids are the Banking77 intent names; descriptions are",
         "# the same names with spaces, the most neutral wording available.",
         "intent:", "  type: choice", "  instructions: What is the customer's intent?", "  criteria:"]
lines += [f"    {n}: {n.replace('_', ' ')}" for n in names]
Path("questions.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(rows)} records, {len(names)} intents")
