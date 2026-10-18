# Beliefs: appstore_stars

How many stars did the reviewer give? (five-level score). Dataset and data card: [`datasets/appstore_stars`](../../../datasets/appstore_stars). Each `<provider>.jsonl` holds one
line per record and repeat: the record's id and label, the provider's answers, usage, latency and cost.
`scores.json` is the scorer's summary. Reproduce with `python experiments/beliefs.py --dataset appstore_stars`.

## Recorded run (October 17, 2026)

Accuracy is an exact star match; within one allows one star off; MAE is the mean absolute error of
the expected score, in stars. 0 errors for every provider.

| Provider | Accuracy | Within one | MAE | ECE | Refusals | $ per 1k | p50 ms |
|---|---|---|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.468 | 0.802 | **0.785** | 0.321 | 0 | **0.0172** | **185** |
| OpenAI gpt-6-luna | 0.373 | 0.741 | 0.807 | 0.172 | 159 of 900 | 0.0189 | 221 |
| DeepSeek V4.1 Flash | **0.470** | 0.780 | 0.818 | 0.466 | 0 | 0.0432 | 888 |
| Von 1.3 (local) | 0.300 | 0.737 | 0.907 | **0.135** | 0 | 0 | 753 |
| OpenDecider nano (local) | 0.450 | 0.807 | 0.786 | 0.289 | 0 | 0 | 668 |
| open-jev-deberta-v3-large (local) | 0.410 | **0.837** | 0.801 | 0.190 | 0 | 0 | 1117 |

Hosted providers ran 3 repeats with 8 concurrent calls; local models ran once (they are deterministic) on
this container's 4 CPUs with 2 concurrent calls, so their latency is not comparable to hosted GPUs.
open-jev reports no token usage. Bold marks the best value in a column.

**Reading.** Exact stars are hard, because the middle ratings are noisy: a "3" review often reads like
a 2 or a 4. Nobody gets far above 47%, while 74–84% are within one star. TypeSafe, DeepSeek and
OpenDecider are tied on exact accuracy. OpenAI is 9.3 points behind TypeSafe (interval −14.0 to −4.7)
because it refused 18% of the reviews, ordinary reviews among them, with no reason given. Refusals
count as wrong; on the reviews it did answer, its accuracy is 0.453. A refusal is a built-in abstention,
which a decision rule could route to a person, so whether it is a cost depends on the rule. Calibration
splits the field: the probabilities from DeepSeek (ECE 0.47) and TypeSafe (0.32) are overconfident
here, and Von's are the best calibrated while being the least accurate.
