# Eval: how many stars did the App Store reviewer give? (fresh data)

One five-level score question over 300 App Store reviews posted October 10–17, 2026, after every
evaluated model was published. The label is the reviewer's own star rating.

| File | What it is |
|---|---|
| `wrangle.py` | fetches the most recent reviews for twelve apps from Apple's public review feeds, writes `dataset.jsonl` |
| `dataset.jsonl` | git-ignored (the text is the reviewers'): `id`, `state` (`app`, `title`, `review`), `label` (0–4 = one to five stars), `app`, `created` |
| `questions.yaml` | one `score` question with five levels, "1 star, very dissatisfied" to "5 stars, very satisfied" |
| `results.<provider>.jsonl` | the recorded runs for six providers |
| `scores.json` | the scorer's summaries |

**Sample.** Reviews of at least 30 characters from Facebook, Instagram, TikTok, Uber, Spotify, Netflix,
Duolingo, Amazon Shopping, WhatsApp, Gmail, YouTube and Snapchat, 60 per star rating with seed 7.

## Reproduce

```bash
python wrangle.py          # rebuilds dataset.jsonl from the live source; a later day gives a different sample
for p in typesafe openai deepseek; do python ../../engine.py questions.yaml dataset.jsonl --provider $p --repeats 3 --cache cache.$p.jsonl --out results.$p.jsonl; done
for p in von opendecider openjev; do python ../../engine.py questions.yaml dataset.jsonl --provider $p --workers 2 --out results.$p.jsonl; done
python ../../score.py results.typesafe.jsonl results.openai.jsonl results.deepseek.jsonl results.von.jsonl results.opendecider.jsonl results.openjev.jsonl --json scores.json
```

The local providers need their servers running first (see the paper README). Scoring needs only the
committed results files: they keep each record's `id` and `label`, not its text.

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
