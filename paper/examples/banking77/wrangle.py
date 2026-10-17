"""TypeSafe's banking77_refunds.json -> dataset.jsonl in the engine's record format.

Source: typesafe-ai/typesafe-public-examples (MIT), pinned to one commit so the dataset is reproducible.
The underlying data is Banking77 (PolyAI, CC BY 4.0). label is 1 when the intent is request_refund.

    python wrangle.py [source.json]      # default: download the pinned file
"""
import json
import sys
import urllib.request

SOURCE = ("https://raw.githubusercontent.com/typesafe-ai/typesafe-public-examples/"
          "25e9d373f4853b3e7e300e55a194f50e54838f68/cookbooks/question_tuning/banking77_refunds.json")

if len(sys.argv) > 1:
    records = json.load(open(sys.argv[1], encoding="utf-8"))
else:
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        records = json.load(response)

with open("dataset.jsonl", "w", encoding="utf-8") as out:
    n = 0
    for i, r in enumerate(records):
        if r["split"] == "test":
            out.write(json.dumps({"id": f"test-{i}", "state": r["text"], "label": r["label"], "intent": r["intent"]}) + "\n")
            n += 1
print(f"{n} test records -> dataset.jsonl")
