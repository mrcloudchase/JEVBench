# Eval: does the Steam reviewer recommend the game? (fresh data)

One yes/no question over 300 Steam reviews posted October 10–17, 2026, after every evaluated model
was published. The label is the reviewer's own verdict: they press "Recommended" or "Not Recommended"
when they write the review.

| File | What it is |
|---|---|
| `wrangle.py` | fetches recent English reviews for ten games from Steam's public review API, writes `dataset.jsonl` |
| `dataset.jsonl` | git-ignored (the text is the reviewers'): `id`, `state` (`game`, `review`), `label` (1 = recommended), `game`, `created` |
| `questions.yaml` | one `noul` question: "The reviewer recommends the game" |
| `results.<provider>.jsonl` | the recorded runs for six providers |
| `scores.json` | the scorer's summaries |

**Sample.** English reviews of 50–1,500 characters from Counter-Strike 2, Dota 2, Baldur's Gate 3,
Cyberpunk 2077, Apex Legends, Elden Ring, Helldivers 2, Rust and Grand Theft Auto V (PUBG had none in
the window), balanced to 150 recommended and 150 not with seed 7.

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

Threshold 0.5. 0 errors and 0 refusals for every provider.

| Provider | Accuracy | Precision | Recall | AUROC | Brier | ECE | $ per 1k | p50 ms |
|---|---|---|---|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.864 | 0.894 | **0.827** | 0.945 | 0.098 | **0.063** | **0.0149** | **184** |
| OpenAI gpt-6-luna | **0.893** | **0.968** | 0.813 | 0.938 | **0.097** | 0.111 | 0.0230 | 226 |
| DeepSeek V4.1 Flash | 0.890 | 0.947 | **0.827** | **0.965** | **0.097** | 0.098 | 0.0338 | 913 |
| Von 1.3 (local) | 0.827 | 0.938 | 0.700 | 0.888 | 0.160 | 0.179 | 0 | 1022 |
| OpenDecider nano (local) | 0.840 | 0.932 | 0.733 | 0.946 | 0.111 | 0.099 | 0 | 512 |
| open-jev-deberta-v3-large (local) | 0.867 | 0.937 | 0.787 | 0.947 | 0.100 | 0.082 | 0 | 1040 |

Hosted providers ran 3 repeats with 8 concurrent calls; local models ran once (they are deterministic) on
this container's 4 CPUs with 2 concurrent calls, so their latency is not comparable to hosted GPUs.
open-jev reports no token usage. Bold marks the best value in a column.

**Reading.** Sentiment is the easy case, and every model separates the classes well (AUROC 0.89–0.97).
No accuracy difference from TypeSafe is significant: every 95% interval includes zero, Von's only just
(−0.040, −0.083 to +0.003). The local models lose most of their accuracy on recall at 0.5: their
probabilities rank well (OpenDecider and open-jev match TypeSafe's AUROC) but sit low, so a lower
threshold would recover it. That is a decision-rule question, not a belief question. DeepSeek, a
chat model read through its next-token probabilities, ranks best but costs about twice as much as
TypeSafe and is five times slower.
