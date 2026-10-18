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
tasks/<task>/       card.md, build.py, questions.yaml, manifest.jsonl, data.jsonl (all committed)
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
python -m tdm run public-fresh --model openai --task arxiv_category
```

Adding a model is one file in `configs/models/` (and a provider class if its API is new; see
`docs/engine.md`). Adding a task is one folder in `tasks/`. Adding an experiment is one file in
`configs/experiments/`.

## Current experiment: `public-fresh`

Six models on three tasks built from text written after every model was published, from sources whose
reuse is granted in writing:

| Task | Question | Records |
|---|---|---|
| `fedreg_type` | is a Federal Register document a rule, a proposed rule or a notice? | 270 |
| `fedreg_agency` | which of ten agencies issued it? (agency names masked) | 296 |
| `arxiv_category` | which of twelve arXiv categories is a new paper's primary one? | 600 |

The six models:
- TypeSafe jev-1.13.0
- OpenAI gpt-6-luna
- DeepSeek V4.1 Flash, read through next-token probabilities
- Von 1.3
- OpenDecider nano
- open-jev-deberta-v3-large

The task text is committed, because the Federal Register is public domain and arXiv metadata is CC0;
see [`tasks/README.md`](tasks/README.md). No runs have been made yet: `make run` produces them, then
`make score report` writes [`reports/public-fresh.md`](reports/).

The first experiment, on Steam and App Store reviews, was removed because those reviews carry no reuse
grant. Its code and results are in the repository's history (commit `6385d80`).
