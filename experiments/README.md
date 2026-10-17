# Experiment: decision architectures from two primitives

Every architecture here is a JEVBench framework built from the same two primitives, decisions and
expressions, run by the same engine over the same items. The frameworks are task-agnostic: the task
supplies the question, the alternatives and the framing text as input.

## Setup

| Task | Source | Items | Alternatives |
|---|---|---|---|
| offensive | TweetEval `offensive`, test split, first 300 | 300 (204 not offensive, 96 offensive) | 2, nominal |
| claims | Climate-FEVER evidence pairs, 100 per label | 300 | 3, nominal (supports, refutes, not enough info) |
| banking | Banking77, 300 sampled from the 3,080-item test split | 300 across 76 intents | 77, nominal |

| Architecture | File | Calls per item | What it adds |
|---|---|---|---|
| single | `architectures/single.yaml` | 1 | one decision, argmax |
| gated | `architectures/gated.yaml` | 1 | abstain when confidence < 0.5 |
| panel / panel_pool | `architectures/panel.yaml` | 3 | three framings (one on jev-1.14), majority vote; and a pool that averages the probability vectors |
| escalation | `architectures/escalation.yaml` | 1 to 2 | second decision on jev-1.14 with a hint, only when the first is below 0.5 |
| chain | `architectures/chain.yaml` | 2 | three auxiliary yes/no decisions become evidence for the main decision |
| contrastive | `architectures/contrastive.yaml` | 2 to 3 | two opposed framings; an arbiter on jev-1.14 only when they disagree |
| iterative | `architectures/iterative.yaml` | 1 to 3 | re-ask with the previous belief until confidence ≥ 0.5 |

Primary model jev-1.13.0; secondary jev-1.14.0. Six concurrent workers. The full run was 9,713
calls, 7.2 M input tokens, USD 0.30, about three minutes of wall time, zero failed items. Two
replicate runs of the single decision per task measure run-to-run noise.

Reproduce: `python experiments/run.py <task>` then `python experiments/analyze.py <task>`.
Raw per-item results are in `results/<task>/<architecture>.jsonl`; tables in `results/<task>.md`.

## Findings

Full tables with bootstrap intervals and paired deltas are in `results/offensive.md`,
`results/claims.md` and `results/banking.md`. Headline numbers:

| Task | single | best full-coverage | best selective (coverage) | noise across 3 runs of single |
|---|---|---|---|---|
| offensive | 0.793 | panel 0.813 (+0.020, CI 0.000 to 0.040) | gated 0.834 (82%); single at τ=0.9: 0.919 (54%) | accuracy range 0.010, 97.7% items agree |
| claims | 0.603 | chain 0.637 (+0.033, CI 0.007 to 0.060) | gated 0.679 (74%); single at τ=0.9: 0.781 (38%) | range 0.004, 97.7% agree |
| banking | 0.847 | panel 0.860 (+0.013, CI −0.003 to 0.033) | gated 0.872 (96%); single at τ=0.9: 0.964 (75%) | range 0.007, 97.3% agree |

1. **Calibrated abstention is the dominant lever, and it is free.** Raising the confidence floor on
   the single decision moves selective accuracy monotonically on all three tasks, from 79% to 94%
   (offensive), 60% to 80% (claims) and 85% to 98% (banking) at the strictest floor, with no extra
   calls. Every architecture that abstains lands close to this curve.
2. **A second look recovers coverage but does not beat the curve.** Escalation and iteration raise
   coverage over gating (offensive: 87% and 89% versus 82%) at nearly the same selective accuracy,
   for 0.17 to 0.42 extra calls per item. At equal coverage they match the single decision with a
   lower floor. A second opinion from a sibling model is close to re-thresholding the first.
3. **Decomposition helps when the question has structure, and only then.** Feeding three auxiliary
   beliefs to the main decision is the only architecture with a significant full-coverage gain, on
   claim verification (+3.3 points). On offensive language it changes the most items (46) and is
   slightly worse. On intents it is neutral.
4. **Panels of one model family are not independent.** The three framed judges were unanimous on 80
   to 95% of items. Gains are 1 to 2 points at three times the cost, and pooling probabilities is
   indistinguishable from voting. Contrastive framing contested only 4 to 12% of items.
5. **Architecture moves cost, coverage and calibration far more than accuracy.** Across the
   architectures, calls per item range 1.0 to 3.0, cost per thousand decisions USD 0.016 to 0.21,
   p50 latency 95 to 226 ms, coverage 74% to 100%, and expected calibration error 0.04 to 0.20,
   while full-coverage accuracy moves by at most 3 points.

## Caveats

One run per architecture and 300 items per task: the 95% intervals on accuracy are about ±4.5
points, so only the paired deltas whose interval excludes zero should be read as effects. The model
is not deterministic; replicate runs disagree on 2 to 3% of items. All judges share one model
family, so independence was constructed by framing and version only. Thresholds (0.5) were fixed
in advance, not tuned. The tasks are short-text classification; longer evidence and ordinal
questions are untested here.
