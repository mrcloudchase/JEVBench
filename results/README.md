# Results

Everything the paper reports, committed so every number reproduces without calling a model.

| Folder | What it holds | Made by |
|---|---|---|
| [`beliefs/<dataset>/`](beliefs) | one results file per provider (`<provider>.jsonl`), `scores.json`, and a README with the tables | `experiments/beliefs.py` |
| [`decisions/`](decisions) | `offline.json` (E1–E5), `live.json` (E6–E7), `outcomes/` with every live belief, and a README with the tables | `experiments/decisions_offline.py`, `experiments/decisions_live.py` |

No file here contains review text: results keep each record's id and label, the answers, usage,
latency and cost. Response caches (`cache.*.jsonl`) are git-ignored.

## Beliefs (October 17, 2026)

| Provider | Steam: accuracy, AUROC | Stars: accuracy, within one | App: accuracy | $ per 1k records |
|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.864, 0.945 | 0.468, 0.802 | 0.596 | 0.015–0.022 |
| OpenAI gpt-6-luna | **0.893**, 0.938 | 0.373*, 0.741 | **0.603*** | 0.019–0.025 |
| DeepSeek V4.1 Flash | 0.890, **0.965** | **0.470**, 0.780 | 0.598 | 0.034–0.048 |
| Von 1.3 | 0.827, 0.888 | 0.300, 0.737 | 0.373 | local |
| OpenDecider nano | 0.840, 0.946 | 0.450, 0.807 | 0.450 | local |
| open-jev-deberta-v3-large | 0.867, 0.947 | 0.410, **0.837** | 0.343 | local |

\* OpenAI refused 18% of star reviews and 6% of app reviews; refusals count as wrong. On what it
answered: 0.453 and 0.644.

The three hosted models are statistically tied on Steam and on the app question; on stars, OpenAI
trails only because of its refusals. The local models stay close on sentiment, where AUROC is
0.89–0.95, and fall 15–26 points behind on the app question, which needs world knowledge. Calibration
does not follow accuracy: OpenDecider nano is the best calibrated model on the app question, and Von
on stars.

Per-dataset tables: [`steam_recommend`](beliefs/steam_recommend), [`appstore_stars`](beliefs/appstore_stars),
[`appstore_app`](beliefs/appstore_app).

## Decisions

| Experiment | Structure | Finding |
|---|---|---|
| E1 threshold and costs | single | The best threshold differs by provider (0.05 to 0.45), and the best provider changes with the cost of errors: DeepSeek is best at equal costs and worst when a miss costs nine times more |
| E2 reject option | single | Abstaining on half the records raises TypeSafe from 0.600 to 0.861 on the app question at no cost |
| E3 value transfer | single | A threshold fitted on one provider misses its target on others, and misses on held-out data 9 times out of 17 on its own |
| E4 panels | parallel | No panel of providers beats the best single one; when one hosted model is wrong, another is wrong 55–92% of the time |
| E5 cascades | orchestrator-worker | A free local model escalating only when unsure matches the hosted model at 17–78% of its cost; confidence beats random escalation in every row |
| E6 decomposition | chained | Helps only when the subquestions add information (stars +2.7 points on TypeSafe, nearly significant) |
| E7 re-asking | evaluator-optimizer | Re-asking with earlier readings inflates confidence: for TypeSafe the loop equals lowering the threshold, at 1.5× the calls |

Tables, intervals and method: [`decisions/README.md`](decisions/README.md).
