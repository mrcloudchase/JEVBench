# Eval: refund requests in Banking77

The first eval run through the engine. One yes/no question over 419 customer messages, scored
against labels.

| File | What it is |
|---|---|
| `wrangle.py` | downloads the source at a pinned commit and writes `dataset.jsonl` |
| `dataset.jsonl` | 419 records: `id`, `state` (the message), `label` (1 = refund request), `intent` |
| `questions.yaml` | one `noul` question: "The customer is asking for a refund" |
| `results.jsonl` | the recorded run: one line per record with the provider's answer |
| `score.py` | accuracy, precision and recall at chosen thresholds |

**Source.** `cookbooks/question_tuning/banking77_refunds.json` from
[typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples)
(MIT), at commit `25e9d37`, test split only. The underlying data is
[Banking77](https://huggingface.co/datasets/PolyAI/banking77) (PolyAI, CC BY 4.0). `label` is 1
exactly when the intent is `request_refund`: 109 of 419 test records. The question wording is ours;
TypeSafe's repo publishes the dataset but not the question they used.

## Reproduce

```bash
cd paper/examples/banking77
python wrangle.py                                                    # -> dataset.jsonl
python ../../engine.py questions.yaml dataset.jsonl --out results.jsonl --workers 8
python score.py results.jsonl 0.3 0.5 0.7
```

Delete `results.jsonl` first to rerun from scratch; otherwise answered ids are skipped.

## Recorded run

jev-1.13.0, 419 records, 0 errors, 121,371 input tokens, about 10 seconds with 8 workers.
The rule is: predict refund when `refund.noul >= threshold`.

| Threshold | Accuracy | Precision | Recall |
|---|---|---|---|
| 0.3 | 0.673 | 0.440 | 0.945 |
| 0.5 | 0.759 | 0.523 | 0.844 |
| 0.7 | 0.833 | 0.651 | 0.771 |

Most errors are false positives on refund-adjacent intents, where the customer wants money back
without asking for a refund: `transaction_charged_twice` (19), `direct_debit_payment_not_recognised`
(17), `Refund_not_showing_up` (16). Seventeen true refund requests are missed. One run only; earlier
replicates varied by about one point between runs.

The threshold is the first decision rule: a belief plus a value gives an action.
