# Eval: refund requests in Banking77, TypeSafe versus OpenAI

One yes/no question over 419 customer messages, asked of two providers three times each, scored
against labels with the generic scorer.

| File | What it is |
|---|---|
| `wrangle.py` | downloads the source at a pinned commit and writes `dataset.jsonl` |
| `dataset.jsonl` | 419 records: `id`, `state` (the message), `label` (1 = refund request), `intent` |
| `questions.yaml` | one `noul` question: "The customer is asking for a refund" |
| `results.typesafe.jsonl`, `results.openai.jsonl` | the recorded runs: one line per record and repeat |
| `scores.t0.3.json`, `scores.t0.5.json`, `scores.t0.7.json` | the scorer's summaries at each threshold |

**Source.** `cookbooks/question_tuning/banking77_refunds.json` from
[typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples)
(MIT), at commit `25e9d37`, test split only. The underlying data is
[Banking77](https://huggingface.co/datasets/PolyAI/banking77) (PolyAI, CC BY 4.0). `label` is 1
exactly when the intent is `request_refund`: 109 of 419 records. The question wording is ours;
TypeSafe's repo publishes the dataset but not the question they used.

## Reproduce

```bash
cd paper/examples/banking77
python wrangle.py
python ../../engine.py questions.yaml dataset.jsonl --provider typesafe --repeats 3 --cache cache.typesafe.jsonl --out results.typesafe.jsonl
python ../../engine.py questions.yaml dataset.jsonl --provider openai   --repeats 3 --cache cache.openai.jsonl   --out results.openai.jsonl
python ../../score.py results.typesafe.jsonl results.openai.jsonl --threshold 0.5
```

## Recorded run (October 17, 2026)

TypeSafe `jev-1.13.0` and OpenAI `gpt-6-luna`, 3 repeats, 1,257 calls each, 0 errors, 0 refusals.
Values are means over repeats; ranges are omitted where every repeat agreed.

Threshold-free, comparing the probabilities themselves:

| Provider | AUROC | Brier | ECE | Same answer on all 3 repeats |
|---|---|---|---|---|
| TypeSafe jev-1.13.0 | **0.899** | **0.162** | 0.194 | 98.3% of records |
| OpenAI gpt-6-luna | 0.861 | 0.192 | **0.188** | 100% |

At a threshold (predict refund when the probability is at least the threshold):

| Threshold | TypeSafe accuracy | OpenAI accuracy | OpenAI minus TypeSafe, same records | 95% interval |
|---|---|---|---|---|
| 0.3 | 0.680 | 0.704 | +0.021 | −0.017 to +0.060 |
| 0.5 | 0.757 | 0.749 | −0.005 | −0.041 to +0.033 |
| 0.7 | **0.835** | 0.790 | **−0.045** | −0.074 to −0.017 |

Cost and speed, measured from this container with 8 concurrent calls per provider:

| Provider | Input tokens per record | $ per 1,000 records | p50 latency | p95 latency |
|---|---|---|---|---|
| TypeSafe | 290 | 0.0122 | 170 ms | 242 ms |
| OpenAI | 172 | 0.0172 | 219 ms | 272 ms |

**Reading.** TypeSafe's probabilities rank refund requests better (AUROC 0.899 against 0.861), so
it improves faster as the threshold rises, and at 0.7 it is ahead by 4.5 points with an interval
that excludes zero. At 0.3 and 0.5 the two are indistinguishable. OpenAI is deterministic: every
repeat returned identical probabilities. TypeSafe varies slightly between runs, changing the
prediction on 1.7% of records at 0.5. OpenAI's tokenizer counts about 40% fewer tokens, but its
price per token is 2.4 times higher, so it costs about 40% more per record. Both providers' main
error is the same: refund-adjacent intents such as `transaction_charged_twice`, where the customer
wants money back without asking for a refund.

The threshold is the first decision rule: a belief plus a value gives an action. Which provider is
better depends on that rule, which is the case for scoring decisions, not only beliefs.
