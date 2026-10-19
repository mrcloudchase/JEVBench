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
  experiments/      one YAML per experiment: tasks × models, optionally pinned to task versions
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
make score report EXP=public-fresh-v1   # regenerate scores/ and reports/ from the committed runs: no keys, no calls
make run                             # new runs (local models need servers/README.md)
python -m tdm run public-fresh --model openai --task arxiv_category
```

Adding a model is one file in `configs/models/` (and a provider class if its API is new; see
`docs/engine.md`). Adding a task is one folder in `tasks/`. Adding an experiment is one file in
`configs/experiments/`.

## Current experiment: `public-fresh`

Six models on seven tasks covering every text question type, built from text written after every model
was published, from sources whose reuse is granted in writing:

| Task | Type | Question | Records |
|---|---|---|---|
| `nws_warning` | yes/no | is this weather alert a warning? | 1,000 |
| `arxiv_crosslist` | yes/no | is this paper also listed in cs.LG? | 973 |
| `nws_severity` | score (4) | how severe is the threat the alert describes? | 916 |
| `nws_certainty` | score (3) | how certain is the hazard? | 897 |
| `fedreg_type` | choice (3) | is a Federal Register document a rule, a proposed rule or a notice? | 559 |
| `fedreg_agency` | choice (10) | which agency issued it? (agency names masked) | 600 |
| `arxiv_category` | choice (12) | which arXiv category is a new paper's primary one? | 1,109 |

The six models:
- TypeSafe jev-1.13.0
- OpenAI gpt-6-luna
- DeepSeek V4.1 Flash, read through next-token probabilities
- Von 1.3
- OpenDecider nano
- open-jev-deberta-v3-large

The task text is committed: Federal Register and National Weather Service text is public domain, and arXiv metadata is CC0;
see [`tasks/README.md`](tasks/README.md).

The tasks were enlarged on October 19, 2026, from 2,382 records to 6,054, and the earlier samples are
contained in the new ones. The 42 runs of October 18–19 are on the earlier task versions. They stay in
`runs/` as experiment `public-fresh-v1`, which pins those versions, and
[`reports/public-fresh-v1.md`](reports/public-fresh-v1.md) has their results
(`make score report EXP=public-fresh-v1`). `public-fresh` itself is on the enlarged tasks and has no runs
yet. Local-model latencies in that report are not comparable: Von ran alone, slowed
by a server backlog, after its timeout was raised from 120s to 600s (commit `42894db`), which changes no
belief.

The first experiment, on Steam and App Store reviews, was removed because those reviews carry no reuse
grant. Its code and results are in the repository's history (commit `6385d80`).

## License

The code and documentation are under the [MIT License](LICENSE). The task text in `tasks/*/data.jsonl`
is not ours to license: Federal Register and National Weather Service text is public domain, and arXiv
metadata is CC0, so its reuse terms are the sources' own (see [`tasks/README.md`](tasks/README.md)). Text
from NWS alerts is not subject to copyright and is not an official NWS product; the NWS asks that it be
identified as such and that no endorsement be implied.
