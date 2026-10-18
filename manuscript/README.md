# Manuscript

**Working title:** *Beliefs, Values, Actions: Building Decisions on Typed Decision Models*

## Abstract (draft)

Typed decision models answer typed questions about evidence (yes/no, one of several options, or a
level on an ordered scale) with a probability distribution instead of generated text. We argue that
this output is best treated as a *belief*, and that decisions should be made outside the model. A
decision rule, written as a pure expression over beliefs and explicit values such as thresholds and
costs, maps a belief to an action, which can then invoke ordinary function code. This separates what
the model thinks from what the stakeholder wants and makes every decision inspectable. It also lets
values change without calling the model again.

We formalize the *decision unit* (evidence and questions to belief; belief and values to action) and
show that five structures of decision units cover the common decision architectures: single, chained,
parallel, orchestrator-worker and evaluator-optimizer. The structure sets which edges exist; the rules
decide which ones fire.

We evaluate six typed decision models, three hosted and three open, on three tasks built from reviews
written after every model was published. All six return beliefs of the same form. The hosted models
are statistically tied, the open models trail on the task that needs world knowledge, and calibration
does not track accuracy. Re-deciding over the recorded beliefs then shows the following. The choice of
values changes which model is best. Values fitted on one model do not transfer to another. Panels of
providers do not beat the best single provider, because their errors are shared. A confidence-gated
cascade from a free local model matches a hosted model at 17–78% of its cost. Re-asking a model until
it is confident inflates its confidence rather than its accuracy.

## Outline

| Section | Content | Evidence |
|---|---|---|
| 1 Introduction | typed decision models; the belief/decision split; contributions | — |
| 2 Related work | decision theory and the reject option; calibration; cascades and compound AI systems; the 2026 typed-decision-model literature | [`related_work/`](../related_work) |
| 3 The decision unit | evidence, questions, belief; rule, values, action; the wire format | [`docs/engine.md`](../docs/engine.md) |
| 4 Five structures | single, chained, parallel, orchestrator-worker, evaluator-optimizer; structure versus behavior | `src/tdm/decision.py` |
| 5 Setup | six providers; three fresh datasets; contamination control; protocol | [`datasets/`](../datasets), [`experiments/`](../experiments) |
| 6 Beliefs | accuracy, ranking, calibration, cost, latency across providers | [`results/beliefs`](../results/beliefs) |
| 7 Decisions | E1–E7 | [`results/decisions`](../results/decisions) |
| 8 Limitations | 300 records per task; one domain (reviews); single fits without risk control; replay of one recorded run; hosted models not deterministic | — |
| 9 Conclusion | behavior lives in rules; wiring buys cost and coverage, not accuracy | — |

## Before submission

- Rename: "JevBench" is taken by three other projects, and "Jev" is TypeSafe's product name.
- Strengthen the evidence: more records, a second domain, values certified with a risk-control
  method (Learn-then-Test), and repeats in the decision experiments.
- Verify every reference marked unverified in `related_work/`.
