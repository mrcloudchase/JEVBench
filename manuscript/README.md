# Manuscript

**Scope:** the quality of typed decision models' beliefs, compared across models, on data none of them
can have seen in training. (The decision-rule experiments are in the repository's history, at commit
`a38ae5f`, and are not part of this paper.)

**Working title:** *Fresh Beliefs: Typed Decision Models Across Providers on Post-Release Data*

## Outline

| Section | Content | Evidence |
|---|---|---|
| 1 Introduction | typed decision models; why belief quality and calibration matter; why fresh data | — |
| 2 Related work | the 2026 typed-decision-model literature and leaderboards; calibration; contamination and fresh-data evaluation | [`related_work/`](../related_work) |
| 3 Beliefs and the wire format | System One question and answer types; translating other APIs into them | [`docs/engine.md`](../docs/engine.md) |
| 4 Tasks | post-release collection under written reuse grants; labels from the sources themselves (agency designations, authors' categories); masking; data cards; contamination table | [`tasks/`](../tasks) |
| 5 Protocol | models, repeats, metrics, paired comparisons | [`PROTOCOL.md`](../PROTOCOL.md) |
| 6 Results | accuracy, ranking, calibration, consistency, refusals, cost and latency | [`reports/`](../reports) |
| 7 Limitations | sample size; choice questions only so far (no yes/no or score task yet); one collection window; non-deterministic hosted models | — |

## Open before submission

- **The name.** "JevBench" is taken three times, and "Jev" is TypeSafe's product name.
- **More and broader data.** More tasks, more records and more domains, collected under licenses that allow redistribution. Most belief papers stop at accuracy; ours needs enough data for calibration and consistency claims.
- **Consistency tests.** Option order, label renaming and wording perturbations: the audit's least-covered checklist items.
- **References.** Verify every one marked unverified in `related_work/`.
