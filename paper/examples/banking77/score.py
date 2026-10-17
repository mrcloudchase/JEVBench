"""Score results.jsonl against each record's label with the rule: refund if refund.noul >= threshold.

    python score.py results.jsonl [threshold ...]      # default thresholds: 0.3 0.5 0.7
"""
import json
import sys

path, thresholds = sys.argv[1], [float(t) for t in sys.argv[2:]] or [0.3, 0.5, 0.7]
rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
answered = [r for r in rows if "answers" in r]
gold = [r["label"] for r in answered]

print(f"{len(answered)} answered of {len(rows)}")
print("threshold  accuracy  precision  recall")
for t in thresholds:
    pred = [int(r["answers"]["refund"]["noul"] >= t) for r in answered]
    tp = sum(p and g for p, g in zip(pred, gold))
    fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum(g and not p for p, g in zip(pred, gold))
    accuracy = sum(p == g for p, g in zip(pred, gold)) / len(answered)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    print(f"{t:9.2f}  {accuracy:8.3f}  {precision:9.3f}  {recall:6.3f}")
