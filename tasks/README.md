# Tasks

Three tasks, one per question type. All were built from reviews written October 10–17, 2026, after
every evaluated model was published, so none can be in a model's training data. Each label is the
reviewer's own action (a button, a star rating, the app they reviewed), not an annotator's judgment.

| Task | Question type | Records | Label | Source |
|---|---|---|---|---|
| [`steam_recommend`](steam_recommend/card.md) | noul (yes/no) | 300, balanced 150/150 | the reviewer pressed "Recommended" | Steam public review API, 9 games |
| [`appstore_stars`](appstore_stars/card.md) | score (5 levels) | 300, 60 per star | the reviewer's star rating | Apple's public App Store review feeds, 12 apps |
| [`appstore_app`](appstore_app/card.md) | choice (12 options) | 300, 25 per app | the app the review was posted to; names masked | the same feeds |

Each folder holds:

| File | Committed | What it is |
|---|---|---|
| `card.md` | yes | the data card: source, window, label, sample, known issues |
| `build.py` | yes | fetches the source and writes the two files below (`python -m tdm build <task>`) |
| `questions.yaml` | yes | the task, in the System One wire format |
| `manifest.jsonl` | yes | the sample: every record's `id`, `label` and timestamp, without the text |
| `data.jsonl` | no | the records with their text (`state`); the text belongs to the reviewers and is not redistributed |

A task's version is a hash of `questions.yaml` and `manifest.jsonl`, and every run records the version it
saw. Rebuilding fetches the latest reviews, so it draws a new sample and therefore a new version; runs of
the old version stay valid and keep their numbers. A new draw is itself a fresh, uncontaminated replication.

## Contamination

| Model | Published | Training data | This data unseen? |
|---|---|---|---|
| TypeSafe jev-1.13.0 | release date not stated; superseded by jev-1.14.0 on October 14, 2026 | not published | almost certainly |
| OpenAI gpt-6-luna | Decisions API public beta, October 6, 2026 | not published | almost certainly |
| DeepSeek V4.1-Flash-1017 | October 17, 2026 | not published | very likely, not provable: released during the data window |
| Von 1.3 | weights September 24, 2026 | includes Banking77 | yes |
| OpenDecider nano | weights September 27, 2026 | eleven named datasets | yes |
| open-jev-deberta-v3-large | weights September 18, 2026 | Banking77, SST-5, BoolQ | yes |

## Not used

Banking77 (TypeSafe's refund example and the 77-intent task) was the first eval. It is in Von's and
open-jev's training data, and only two providers were run on it, so it cannot support cross-provider
claims. It remains in the repository's history.
