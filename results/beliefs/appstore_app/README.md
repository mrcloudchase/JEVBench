# Beliefs: appstore_app

Which app is the review about? (12-way choice). Dataset and data card: [`datasets/appstore_app`](../../../datasets/appstore_app). Each `<provider>.jsonl` holds one
line per record and repeat: the record's id and label, the provider's answers, usage, latency and cost.
`scores.json` is the scorer's summary. Reproduce with `python experiments/beliefs.py --dataset appstore_app`.

## Recorded run (October 17, 2026)

Chance is 1 in 12 (0.083). 0 errors for every provider.

| Provider | Accuracy | Macro-F1 | Brier | ECE | Refusals | $ per 1k | p50 ms |
|---|---|---|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.596 | 0.595 | 0.523 | 0.115 | 0 | **0.0223** | **200** |
| OpenAI gpt-6-luna | **0.603** | **0.622** | **0.480** | 0.104 | 57 of 900 | 0.0246 | 229 |
| DeepSeek V4.1 Flash | 0.598 | 0.608 | 0.675 | 0.313 | 0 | 0.0476 | 873 |
| Von 1.3 (local) | 0.373 | 0.366 | 0.964 | 0.341 | 0 | 0 | 789 |
| OpenDecider nano (local) | 0.450 | 0.467 | 0.642 | **0.042** | 0 | 0 | 840 |
| open-jev-deberta-v3-large (local) | 0.343 | 0.333 | 0.761 | 0.140 | 0 | 0 | 1128 |

Hosted providers ran 3 repeats with 8 concurrent calls; local models ran once (they are deterministic) on
this container's 4 CPUs with 2 concurrent calls, so their latency is not comparable to hosted GPUs.
open-jev reports no token usage. Bold marks the best value in a column.

**Reading.** This eval separates hosted from local models. The three hosted models are tied around
60% (every interval against TypeSafe straddles zero), even though OpenAI counts 6% refusals as wrong
(0.644 on what it answered). The local models are 15–26 points behind, and every gap is significant.
Telling apps apart from a description needs world knowledge (what Duolingo's owl is, what Uber Eats
sells), which a 0.4B encoder doesn't have. OpenDecider nano is the best calibrated model on this
eval, which makes it usable behind a confidence threshold even at 45% accuracy.
