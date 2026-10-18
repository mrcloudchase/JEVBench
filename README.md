# Typed decision model beliefs, across models

An evaluation of typed decision models: models that answer typed questions about evidence (yes/no,
one of several options, or a level on a scale) with a probability distribution instead of text. The
repository measures how good those beliefs are, model against model, on tasks built from text written
after every model was published.

```
build (source → task)  →  run (task × model → beliefs)  →  score (beliefs → metrics)  →  report (metrics → tables)
```

Each stage reads only the previous stage's files. Runs are immutable, and scores and reports are
regenerated from them, so every number traces to a run.

## Layout

```
PROTOCOL.md         what is measured and how, fixed before results
configs/
  models/           one YAML per model: provider, pinned version, repeats, concurrency
  experiments/      one YAML per experiment: tasks × models
tasks/<task>/       card.md, build.py, questions.yaml, manifest.jsonl (committed), data.jsonl (git-ignored text)
runs/<run>/         run.json (task version, model config, models served, commit, times, cost) and beliefs.jsonl
scores/             <experiment>.json, from runs
reports/            <experiment>.md and CSVs, from scores; never edited by hand
src/tdm/            the engine: providers, run, score, report, project layout
servers/            local servers for the open models
docs/               engine reference, TypeSafe API notes
related_work/       literature sweep
manuscript/         the paper's outline
tests/              offline unit and pipeline tests
```

## Use

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env                 # TYPESAFE_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY

make test                            # offline
make score report                    # regenerate scores/ and reports/ from the committed runs: no keys, no calls
make run                             # new runs (local models need servers/README.md)
python -m tdm run fresh-reviews --model openai --task appstore_app
```

Adding a model is one file in `configs/models/` (and a provider class if its API is new; see
`docs/engine.md`). Adding a task is one folder in `tasks/`. Adding an experiment is one file in
`configs/experiments/`.

## Current experiment: `fresh-reviews`

Six models (TypeSafe jev-1.13.0, OpenAI gpt-6-luna, DeepSeek V4.1 Flash read through next-token
probabilities, Von 1.3, OpenDecider nano, open-jev-deberta-v3-large) on three tasks of 300 reviews
each, written October 10–17, 2026. Tables: [`reports/fresh-reviews.md`](reports/fresh-reviews.md).

- **Hosted models:** statistically tied on the yes/no and choice tasks.
- **Open models:** close on sentiment, but 15–26 points behind on the task that needs world knowledge (which app a review is about).
- **Calibration** does not follow accuracy.
- **OpenAI** refuses 18% of star-rating reviews and 6% of app reviews.
