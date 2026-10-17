# Eval: 77-way intent classification in Banking77, TypeSafe versus OpenAI

One choice question with 77 options over 300 customer messages, asked of two providers three times
each, scored against labels with the generic scorer.

| File | What it is |
|---|---|
| `wrangle.py` | writes `dataset.jsonl` and `questions.yaml` from the sample in `experiments/data/banking.json` |
| `dataset.jsonl` | 300 records: `id`, `state` (the message), `label` (the intent name) |
| `questions.yaml` | one `choice` question over all 77 intents; descriptions are the names with spaces |
| `results.typesafe.jsonl`, `results.openai.jsonl` | the recorded runs: one line per record and repeat |
| `scores.json` | the scorer's summaries |

**Source.** [Banking77](https://huggingface.co/datasets/PolyAI/banking77) (PolyAI, CC BY 4.0), test
split, 300 messages sampled with seed 7, covering 76 of the 77 intents. The sample is committed at
`experiments/data/banking.json`, so `wrangle.py` needs no network.

## Reproduce

```bash
cd paper/examples/banking77_intents
python wrangle.py
python ../../engine.py questions.yaml dataset.jsonl --provider typesafe --repeats 3 --cache cache.typesafe.jsonl --out results.typesafe.jsonl
python ../../engine.py questions.yaml dataset.jsonl --provider openai   --repeats 3 --cache cache.openai.jsonl   --out results.openai.jsonl
python ../../score.py results.typesafe.jsonl results.openai.jsonl
```

## Recorded run (October 17, 2026)

TypeSafe `jev-1.13.0` and OpenAI `gpt-6-luna`, 3 repeats, 900 calls each, 0 errors, 0 refusals.

| Provider | Accuracy | Macro-F1 | Brier | ECE | Same answer on all 3 repeats | Tokens per record | $ per 1,000 | p50 latency |
|---|---|---|---|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.848 (0.840–0.853) | 0.804 | 0.226 | 0.071 | 97.3% | 1,686 | 0.0708 | 193 ms |
| OpenAI gpt-6-luna | 0.853 | 0.807 | 0.228 | 0.063 | 100% | 984 | 0.0984 | 232 ms |

On the same records the accuracy difference is 0.000 (95% interval −0.030 to +0.030); each provider
gets 10 records right that the other gets wrong. **The two are indistinguishable on this task.**
TypeSafe is cheaper and faster per record; OpenAI is deterministic and slightly better calibrated.
