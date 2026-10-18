# Experiments

Three scripts produce every result in the paper. Run them from the repository root after
`pip install -e .` and with keys in `.env` (see `.env.example`).

| Script | What it does | Calls | Writes |
|---|---|---|---|
| `beliefs.py` | every provider on every dataset: 3 repeats for hosted models, 1 for local ones; then scores | 8,100 hosted, 2,700 local | `results/beliefs/` |
| `decisions_offline.py` | E1–E5: thresholds and costs, reject option, value transfer, panels, cascades, over the recorded beliefs | none | `results/decisions/offline.json` |
| `decisions_live.py` | E6–E7: chained and evaluator-optimizer on TypeSafe and OpenAI | 4,361 | `results/decisions/outcomes/`, `live.json` |

```bash
python experiments/beliefs.py                  # needs datasets/*/dataset.jsonl and the local servers for von, opendecider, openjev
python experiments/beliefs.py --score          # re-scores the committed results, no calls
python experiments/decisions_offline.py
python experiments/decisions_live.py           # then: --score
```

Runs resume and cache responses, so rerunning finishes immediately and costs nothing. The paper's run
(October 17–18, 2026) cost $0.34 in API calls: $0.22 for beliefs and $0.12 for the live decisions.

**Protocol:** 300 records per dataset. Decision experiments use each provider's first repeat. Values
are fitted on a fixed half of the records (split by id hash) and tested on the other half. Intervals
are 95% paired bootstraps (2,000 resamples). Confidence is the top option's probability for every
provider, `max(p, 1 − p)` for yes/no. A refusal is an abstention, and an abstention counts as wrong for
accuracy.
