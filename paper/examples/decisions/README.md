# Decision experiments

The fresh evals scored beliefs. These experiments score **decisions**: a rule applied to beliefs,
with explicit values, wired into the five structures. Everything uses `../../decide.py`.

```python
action = Decision(rule, **values)(*beliefs)

threshold = Decision(lambda b, theta: int(b["recommends"]["noul"] >= theta), theta=0.5)
reject    = Decision(lambda b, tau: top(b[q]) if confidence(b[q]) >= tau else ABSTAIN, tau=0.7)
```

`top` is the answer's most probable option and `confidence` its probability, `max(p, 1 − p)` for a
yes/no answer. That is the same statistic for every provider, so values mean the same thing everywhere.
A refusal is an abstention. Accuracy counts an abstention as wrong; selective accuracy is accuracy on
the records the rule acted on, and coverage is their share.

| File | What it is |
|---|---|
| `offline.py` → `offline.json` | E1–E5: single, parallel and orchestrator-worker, re-decided over the recorded beliefs (first repeat). No model is called. |
| `live.py` → `outcomes.*.jsonl`, `live.json` | E6–E7: chained and evaluator-optimizer, which need new beliefs, on TypeSafe and OpenAI. Each outcome keeps every belief it formed. |

```bash
python offline.py              # about 40 seconds, no API calls
python live.py                 # needs ../appstore_*/dataset.jsonl and the API keys; responses cached in cache.*.jsonl
python live.py --score         # scores the outcomes from the committed files alone
```

300 records per eval. Intervals are 95% paired bootstraps. Values fitted on data are fitted on one
fixed half of the records (by id hash) and tested on the other.

## E1. One unit, one threshold (Steam, yes/no)

The belief is fixed; only the threshold θ changes.

| Provider | Accuracy at θ = 0.5 | Best θ | Accuracy at best θ | θ fitted on half A | Half B at 0.5 → at fitted θ |
|---|---|---|---|---|---|
| TypeSafe | 0.867 | 0.25 | 0.883 | 0.45 | 0.846 → 0.846 |
| OpenAI | 0.893 | 0.10 | 0.907 | 0.10 | 0.885 → 0.897 |
| DeepSeek | 0.890 | 0.05 | 0.900 | 0.05 | 0.897 → 0.904 |
| Von | 0.827 | 0.45 | 0.840 | 0.40 | 0.833 → 0.814 |
| OpenDecider | 0.840 | 0.20 | 0.873 | 0.20 | 0.853 → 0.885 |
| open-jev | 0.867 | 0.40 | 0.887 | 0.40 | 0.878 → 0.885 |

The right threshold is a property of the provider: 0.05 for DeepSeek, 0.45 for Von. Fitting it
gains up to 3.2 points on held-out records (OpenDecider), and costs Von 1.9.

**When errors have different costs.** A false "recommends" costs c_FP and a missed one c_FN. For a
calibrated belief the Bayes threshold is θ = c_FP / (c_FP + c_FN). Expected cost per decision on half B,
with θ fitted on half A (lower is better; best in bold):

| c_FP : c_FN | TypeSafe | OpenAI | DeepSeek | Von | OpenDecider | open-jev |
|---|---|---|---|---|---|---|
| 1 : 9 | **0.282** | 0.513 | 0.712 | 0.532 | 0.391 | 0.340 |
| 1 : 3 | 0.218 | 0.205 | 0.250 | 0.365 | **0.179** | 0.186 |
| 1 : 1 | 0.154 | 0.103 | **0.096** | 0.186 | 0.115 | 0.115 |
| 3 : 1 | 0.256 | 0.154 | **0.135** | 0.199 | 0.160 | 0.179 |
| 9 : 1 | 0.487 | 0.346 | 0.212 | **0.192** | 0.218 | 0.327 |

**Which provider is best depends on the values.**
- At equal costs DeepSeek is best; when a missed positive costs nine times more it is the worst, at 2.5 times TypeSafe's cost. Its beliefs are near 0 or 1, so no threshold can trade one error for the other.
- TypeSafe goes from best (1:9) to worst (9:1).
- With 150 records to fit on, the Bayes threshold is sometimes the better choice. At 9:1, TypeSafe's Bayes threshold costs 0.269 against 0.487 when fitted; `offline.json` has both for every cell.

## E2. The reject option (all evals)

Selective accuracy as the rule abstains more, and the area under the risk-coverage curve (AURC, lower
is better). OpenAI's maximum coverage is below 100% because it refuses (82% on stars, 94% on app).

| Provider | Steam: at max, at 50%, AURC | Stars: at max, at 50%, AURC | App: at max, at 50%, AURC |
|---|---|---|---|
| TypeSafe | 0.867, 0.968, 0.049 | 0.467, 0.660, 0.374 | 0.600, 0.861, 0.166 |
| OpenAI | 0.893, 0.925, 0.079 | 0.453, 0.552, 0.421 | 0.641, 0.863, **0.129** |
| DeepSeek | 0.890, **0.987**, **0.039** | 0.470, 0.636, **0.332** | 0.600, **0.887**, 0.157 |
| Von | 0.827, 0.921, 0.081 | 0.300, 0.338, 0.623 | 0.373, 0.477, 0.459 |
| OpenDecider | 0.840, 0.954, 0.050 | 0.450, 0.629, 0.372 | 0.450, 0.722, 0.291 |
| open-jev | 0.867, 0.960, 0.047 | 0.410, 0.523, 0.404 | 0.343, 0.603, 0.363 |

Abstaining on half the records raises TypeSafe from 0.600 to 0.861 on the app question, with no
extra calls. The ranking by AURC differs from the ranking by accuracy. OpenAI is the most accurate on
Steam but ranks its own errors worst among the hosted models (AURC 0.079).

## E3. Do values transfer?

Fit τ on one provider's half A to reach a target error, then apply that τ to every provider's half B.

| Eval (target error) | Fitted τ met the target on its own provider's half B | Error when another provider's τ is applied |
|---|---|---|
| Steam (5%) | 3 of 5; OpenAI cannot reach 5% at any τ | 0.0–10.0% |
| Stars (40%) | 0 of 6 (realized 45–65%) | 14–55% |
| App (20%) | 5 of 6 (OpenDecider 25%) | 0–64% |

Values do not transfer across providers. On the app question, TypeSafe's τ = 0.61 gives TypeSafe
19.3% error and DeepSeek 36.3%. Even on the same provider, a naively fitted τ misses the target on
held-out data 9 times out of 17 (the stars fits miss by 5 to 25 points). A rule's values must be
fitted per provider, and a guarantee needs a risk-control procedure, not a single fit.

## E4. Parallel: panels across providers

The same question to several providers. *Vote* takes the majority of top options and abstains without
a majority; *pool* averages the probability distributions. Each is compared with the best single
provider on that eval.

| Panel | Steam | Stars | App |
|---|---|---|---|
| Best single | OpenAI 0.893 | DeepSeek 0.470 | TypeSafe 0.600 |
| Hosted vote (3) | 0.897 (+0.003) | 0.447 (−0.023) | 0.593 (−0.007) |
| Hosted pool (3) | 0.887 (−0.007) | 0.477 (+0.007) | 0.617 (+0.017) |
| Local pool (3) | 0.873 (−0.020) | 0.457 (−0.013) | 0.440 (**−0.160**) |
| All six, pool | 0.887 (−0.007) | 0.467 (−0.003) | 0.610 (+0.010) |
| All six, vote | 0.870 (−0.023) | 0.390 (**−0.080**) | 0.483 (**−0.117**) |

No panel beats the best single provider; every interval includes zero or is negative (bold).
Panels cost three to six calls. The reason is that errors are shared:

| Hosted pair | P(one wrong given the other wrong): Steam, Stars, App | Same wrong answer: Stars, App |
|---|---|---|
| TypeSafe + OpenAI | 0.55, 0.92, 0.87 | 63%, 51% |
| TypeSafe + DeepSeek | 0.68, 0.88, 0.88 | 81%, 67% |
| OpenAI + DeepSeek | 0.69, 0.78, 0.86 | 61%, 52% |

The local models make more varied mistakes (OpenDecider and open-jev give the same wrong app 15% of
the time) but are too weak for their disagreement to help.

## E5. Orchestrator-worker: a free local model first

The orchestrator's rule acts on its own answer when confident and otherwise names the worker:
`top(b) if confidence(b) >= tau else "escalate"`. The control escalates the same number of records
chosen at random (200 draws; 95% range shown).

| Eval | Cascade (τ) | Escalated | Accuracy | Worker alone | Random escalation | Cost vs worker alone |
|---|---|---|---|---|---|---|
| Steam | OpenDecider → OpenAI (0.8) | 16% | **0.903** | 0.893 (+0.010, −0.017 to +0.037) | 0.848 (0.837–0.863) | 18% |
| Steam | OpenDecider → TypeSafe (0.8) | 16% | 0.873 | 0.867 (+0.007) | 0.844 (0.830–0.857) | 17% |
| Stars | OpenDecider → TypeSafe (0.8) | 52% | 0.480 | 0.467 (+0.013) | 0.461 (0.440–0.487) | 52% |
| Stars | OpenDecider → OpenAI (0.7) | 37% | 0.453 | 0.373 (**+0.080**, +0.033 to +0.123) | 0.423 (0.390–0.450) | 35% |
| App | OpenDecider → TypeSafe (0.8) | 78% | 0.593 | 0.600 (−0.007) | 0.569 (0.550–0.590) | 78% |
| App | Von → TypeSafe (0.8) | 53% | 0.520 | 0.600 (**−0.080**) | 0.493 (0.463–0.520) | 54% |

- With a well-calibrated first stage (OpenDecider), the cascade matches the hosted worker at 17–78% of its cost.
- Escalating by confidence beats escalating at random in every row, outside the random 95% range in four of the six rows.
- The cascade beats OpenAI on stars because the local model answers some reviews that OpenAI refuses.
- Von's confidence separates its errors poorly, so a Von-first cascade loses 8 points on the app question. The first stage's calibration decides whether a cascade works.

## E6. Chained: a belief becomes evidence

Step one asks a coarser question:
- **App:** "what kind of app", over five areas.
- **Stars:** five yes/no findings: bug, praise, money complaint, feature request, would recommend.

Its belief is added to the evidence for step two, the eval's own question.

| Provider / eval | Single | Chained | Chained − single | Coverage single → chained | Cost |
|---|---|---|---|---|---|
| TypeSafe / app | 0.600 | 0.607 | +0.007 (−0.023 to +0.037) | 100% → 100% | 2.0× |
| TypeSafe / stars | 0.467 | 0.493 | +0.027 (−0.003 to +0.057) | 100% → 100% | 2.3× |
| OpenAI / app | 0.600 | 0.607 | +0.007 (−0.030 to +0.040) | 94% → 99% | 2.3× |
| OpenAI / stars | 0.373 | 0.463 | **+0.090** (+0.043 to +0.137) | 82% → 96% | 6.1× |

Decomposition helps where the subquestions carry information the final question lacks: the
findings for star ratings (+2.7 on TypeSafe, nearly significant). It does nothing for the app question. OpenAI's
significant gain is mostly from refusing less once the review comes with findings (82% → 96%
coverage); its selective accuracy rises from 0.453 to 0.484.

## E7. Evaluator-optimizer: re-ask until confident

Ask; if the top probability is below τ = 0.7, ask again. The evidence now includes the earlier
readings' top two options, plus "decide on the strongest evidence". At most three rounds; abstain
if τ is never reached. Two comparisons from the same run:
- **Round one at τ:** the single unit with the same rule.
- **Matched re-threshold:** round one with τ lowered until it acts on as many records as the loop.

| Provider / eval | Round one at τ = 0.7: coverage, selective | Loop: coverage, selective, rounds | Round one re-thresholded to the loop's coverage | Loop − matched |
|---|---|---|---|---|
| TypeSafe / app | 55%, 0.836 | 99.7%, 0.592, 1.50 | τ = 0.20: 0.595 | −0.003 (−0.010 to 0.000) |
| TypeSafe / stars | 67%, 0.552 | 93%, 0.493, 1.44 | τ = 0.49: 0.491 | +0.003 (−0.017 to +0.027) |
| OpenAI / app | 55%, 0.849 | 92%, 0.667, 1.61 | τ = 0.24: 0.643 | +0.020 (−0.003 to +0.043) |
| OpenAI / stars | 26%, 0.628 | 92%, 0.457, 1.99 | max coverage 82%: 0.453 | **+0.047** (+0.013 to +0.083) |

**The loop manufactures confidence.** On TypeSafe's app question, round one reaches τ = 0.7 on 55%
of records. After re-asking with the earlier readings, 99.7% reach it, and the loop's decisions are
exactly as accurate as round one with the bar lowered to 0.20. The second reading narrows to the two
options it was shown and becomes confident without becoming right, so τ no longer means what it
meant. For TypeSafe the loop equals re-thresholding at 1.4–1.5× the calls.

For OpenAI the loop helps by recovering refusals (stars: +4.7 points over the best re-threshold)
rather than by sharpening beliefs.

## What the experiments show

1. **Behavior is in the rule.** The same beliefs give different actions and costs under different values. The best provider changes with the cost of errors (E1), and abstaining is the largest free lever (E2).
2. **Values are per provider.** A threshold fitted on one provider's beliefs misses its target on another's (E3). Even within a provider, one fit is not a guarantee.
3. **Wiring mostly buys cost or coverage, not accuracy.**
   - Panels: no gain, because errors are shared (E4).
   - Cascades: same accuracy for less, if the first stage is calibrated (E5).
   - Chains: help only when the subquestions add information (E6).
   - Loops: re-asking is re-thresholding, and it inflates confidence (E7).
4. **Recorded beliefs make decisions cheap to study.** E1–E5 re-decide 18 results files with no model calls. Re-deciding is exact here because each result is replayed as recorded. Live hosted Jev is not deterministic (its repeats agree on 94–99.7% of records), so a re-decided outcome describes the recorded beliefs, not a new run.
