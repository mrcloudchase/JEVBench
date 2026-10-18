# Tasks

Three tasks, built from text written after every evaluated model was published, from sources whose reuse
is granted in writing by a primary source. Each label is the source's own designation (the agency's
document type, the issuing agency, the authors' arXiv category), not a judgment by an annotator or a model.

| Task | Question type | Records | Label | Source | Legal basis |
|---|---|---|---|---|---|
| [`fedreg_type`](fedreg_type/card.md) | choice (3) | 270, 90 per type | rule, proposed rule or notice | Federal Register (GovInfo bulk XML) | 1 CFR 2.6; 17 U.S.C. 105 |
| [`fedreg_agency`](fedreg_agency/card.md) | choice (10) | 296, 30 per agency (Defense 26) | issuing department or agency; names masked | Federal Register (GovInfo bulk XML) | 1 CFR 2.6; 17 U.S.C. 105 |
| [`arxiv_category`](arxiv_category/card.md) | choice (12) | 600, 50 per category | the authors' primary category | arXiv API, titles and abstracts | CC0 1.0 (arXiv API terms) |

Each folder holds:

| File | What it is |
|---|---|
| `card.md` | the data card: source, legal basis, window, label, sample, masking, known issues |
| `build.py` | fetches the source and writes the files below (`python -m tdm build <task>`) |
| `questions.yaml` | the task, in the System One wire format |
| `manifest.jsonl` | the sample: every record's `id`, `label` and dates, without the text |
| `data.jsonl` | the records with their text (`state`). Committed: every source permits redistribution. |

`federal_register.py` is the Federal Register reader shared by the two `fedreg_*` tasks. Raw downloads
are cached in `tasks/.sources/`, which is git-ignored.

A task's version is a hash of `questions.yaml` and `manifest.jsonl`, and every run records the version it
saw. Rebuilding refetches the source; the window and seeds are fixed in `build.py`, so a rebuild draws the
same sample unless the source itself changed.

## Inclusion rule

A source is used only if a primary source grants reuse of the text in writing and we have read that
grant. On October 18, 2026 this excluded the following:

| Source | Why it was excluded |
|---|---|
| NHTSA vehicle complaints and FDA MAUDE device reports | the narratives are written by members of the public and by manufacturers, not by the government |
| Stack Exchange | its API terms were not reviewed |
| CFPB complaints | narratives are no longer published |
| Steam and App Store reviews | no reuse grant (the first experiment used them; they are in the repository's history) |

## Contamination

| Model | Published | Unseen? |
|---|---|---|
| TypeSafe jev-1.13.0 | release date not stated; superseded October 14, 2026 | almost certainly |
| OpenAI gpt-6-luna | Decisions API public beta, October 6, 2026 | almost certainly |
| DeepSeek V4.1-Flash-1017 | October 17, 2026 | very likely, not provable: released at the end of the window |
| Von 1.3 | weights September 24, 2026 | yes |
| OpenDecider nano | weights September 27, 2026 | yes |
| open-jev-deberta-v3-large | weights September 18, 2026 | yes |
