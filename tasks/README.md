# Tasks

Seven tasks, covering every text question type, built from text written after every evaluated model was
published, from sources whose reuse is granted in writing by a primary source. Each label is the source's
own designation (the agency's document type, the issuing agency, the authors' arXiv categories, the
Weather Service's alert classification), never a judgment by an annotator or a model.

| Task | Type | Records | Label | Source | Legal basis |
|---|---|---|---|---|---|
| [`nws_warning`](nws_warning/card.md) | noul | 1,000 (500/500) | is the alert a Warning | NWS alerts API | NWS: public domain, open data |
| [`arxiv_crosslist`](arxiv_crosslist/card.md) | noul | 973 (473/500) | did the authors cross-list to cs.LG | arXiv API | CC0 1.0 |
| [`nws_severity`](nws_severity/card.md) | score (4) | 916 | CAP severity: Minor to Extreme | NWS alerts API | NWS: public domain, open data |
| [`nws_certainty`](nws_certainty/card.md) | score (3) | 897 | CAP certainty: Possible to Observed | NWS alerts API | NWS: public domain, open data |
| [`fedreg_type`](fedreg_type/card.md) | choice (3) | 559 | rule, proposed rule or notice | Federal Register (GovInfo) | 1 CFR 2.6; 17 U.S.C. 105 |
| [`fedreg_agency`](fedreg_agency/card.md) | choice (10) | 600 | issuing agency; names masked | Federal Register (GovInfo) | 1 CFR 2.6; 17 U.S.C. 105 |
| [`arxiv_category`](arxiv_category/card.md) | choice (12) | 1,109 | the authors' primary category | arXiv API | CC0 1.0 |

6,054 records in all. Each task takes up to a fixed number of records per class, and every record of a
class with fewer, so `fedreg_type`, `fedreg_agency`, `arxiv_category` and `nws_severity` are unbalanced.
The caps were raised on October 19, 2026 from the first experiment's sample (2,382 records) with the same
windows and seeds, so each task's sample contains its earlier one. The windows cannot grow backward, since
they start after the last model's release; the remaining limits are the small classes (16 Extreme alerts,
98 proposed rules, 26 Defense documents, 50 econ.GN papers), which only later collection can enlarge.

**Box questions** (locating a region in an image) are not covered. Only TypeSafe jev-1.14 answers them, so
they cannot be compared across models, and no source found so far pairs post-release images with true
regions under a written reuse grant. Images we generate ourselves would satisfy the legal rule.

Each folder holds:

| File | What it is |
|---|---|
| `card.md` | the data card: source, legal basis, window, label, sample, masking, known issues |
| `build.py` | fetches the source and writes the files below (`python -m tdm build <task>`) |
| `questions.yaml` | the task, in the System One wire format |
| `manifest.jsonl` | the sample: every record's `id`, `label` and dates, without the text |
| `data.jsonl` | the records with their text (`state`). Committed: every source permits redistribution. |

`federal_register.py`, `arxiv.py` and `nws.py` are the shared readers for each source, with the legal basis and fetching rules in their headers. Raw downloads
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
| Wikipedia | allowed (CC BY-SA 4.0), but its labels are editor-made and changing, and share-alike would bind the dataset's license; not needed while natural labels cover every type |

## Contamination

| Model | Published | Unseen? |
|---|---|---|
| TypeSafe jev-1.13.0 | release date not stated; superseded October 14, 2026 | almost certainly |
| OpenAI gpt-6-luna | Decisions API public beta, October 6, 2026 | almost certainly |
| DeepSeek V4.1-Flash-1017 | October 17, 2026 | very likely, not provable: released at the end of the window |
| Von 1.3 | weights September 24, 2026 | yes |
| OpenDecider nano | weights September 27, 2026 | yes |
| open-jev-deberta-v3-large | weights September 18, 2026 | yes |
