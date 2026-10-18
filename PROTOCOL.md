# Protocol

Fixed before results are read. A change here is a dated amendment, never an edit.

*Written October 18, 2026, after the `fresh-reviews` runs. It records the method those runs used, and it
binds every task and run made after that date.*

## Question

How good are typed decision models' beliefs, compared across models, on evidence none of them can
have seen in training?

## Tasks

Built by `tasks/<task>/build.py` and frozen by `manifest.jsonl`.
- **Labels** come from the source itself: an agency's designation, or the authors' own choice. They are never an annotator's or a model's judgment.
- **Dates:** all text is dated after the release of every evaluated model, by filing date where a source has one.
- **Inclusion:** a source is used only if a primary source grants reuse of its text in writing, and we have read that grant.
- **Masking:** where the evidence would state the label outright (an agency's name, a document's type), those words are masked identically in every record.
- **Versioning:** a task's version is a hash of its questions and manifest, and results are always reported with the version.

*Amended October 18, 2026: the review tasks were replaced by Federal Register and arXiv tasks under the
inclusion rule; no runs of the new tasks existed when this was written.*

## Models

One config per model in `configs/models/`, with the model pinned (`jev-1.13.0`, not `jev-latest`).
Every run records the model versions the API actually served. Hosted models are asked 3 times per
record, because they need not be deterministic; local models once.

## What is measured

| Question type | Prediction | Metrics |
|---|---|---|
| noul | yes when P(yes) ≥ 0.5 | accuracy, precision, recall, F1; AUROC, Brier score, ECE (10 equal-width bins) from the probability |
| choice | the most probable option | accuracy, macro-F1, Brier score over all options, ECE of the top probability |
| score | the most probable level | accuracy, within-one accuracy, mean absolute error of the expected score, ECE of the top probability |

These are reported for every model:
- repeat agreement: the share of records with the same prediction on every repeat
- refusals
- errors
- cost per 1,000 records at list price
- input tokens
- p50 and p95 latency

A refusal counts as wrong; a refusal or an error is never dropped from the denominator.

## Comparisons

Each model is compared with the experiment's first model on the same records, using the first
repeat: the difference in accuracy, with a 95% paired bootstrap interval (2,000 resamples, seed 1). A
difference is reported as significant only when its interval excludes zero. No other test is run and
no metric is chosen after the fact.

## Not done

- No model is tuned or prompted per task beyond the questions in `questions.yaml`, which are identical for every model.
- No records are excluded after a run.
- Latency is measured from one machine and is comparable only within a run batch. Local models ran on 4 CPUs.
