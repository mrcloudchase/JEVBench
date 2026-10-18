# The engine: `tdm`

A provider turns evidence and questions into a belief:

```python
belief = Belief(questions, provider)(state)
```

| Module | Job |
|---|---|
| `tdm.providers` | `Provider`, the generic HTTP client, and one subclass per provider API |
| `tdm.data` | the questions file, the dataset, the results file and the response cache |
| `tdm.project` | the layout on disk: configs, tasks (with versions), run folders |
| `tdm.run` | `Belief`, `run`, and `execute`, which makes a run folder for a task and a model |
| `tdm.score` | the generic scorer: beliefs against labels, per question type, compared across models |
| `tdm.report` | tables from scores |
| `python -m tdm` | `build`, `run`, `score`, `report` |

| Input | Holds | Read by |
|---|---|---|
| `.env` | provider keys | `run.load_env` |
| `configs/models/<model>.yaml` | provider, pinned model, repeats, workers, optional `url` | `Project.model`, `Project.provider` |
| `configs/experiments/<experiment>.yaml` | `tasks` and `models`; the first model is the comparison base | `Project.experiment` |
| `tasks/<task>/questions.yaml` | the task: questions in the wire format, keyed by id | `Task.questions` |
| `tasks/<task>/data.jsonl` | the data: one record per line, checked against `manifest.jsonl` | `Task.records` |

## Providers

`Provider` owns transport: configuration, the POST, retries on 408, 429, 5xx and 529 with
`Retry-After`, timing and cost. A subclass defines only the provider's shapes:

```python
class Provider(ABC):
    url = None                       # class defaults; PROVIDER_URL / PROVIDER_MODEL override
    model = None
    key_env = None                   # the vendor's key variable, used when PROVIDER_API_KEY is unset
    usd_per_mtok_input = 0.0         # list price, for cost reporting
    def headers(self) -> dict         # default: Bearer token, JSON
    @abstractmethod
    def payload(self, state, questions) -> dict
    @abstractmethod
    def parse(self, body, questions) -> dict   # -> {"model", "answers", "usage"}, answers in the wire format's shapes
```

| Name | Class | Endpoint | Default model | Price per 1M input tokens |
|---|---|---|---|---|
| `typesafe` | `TypeSafe` | `api.typesafe.ai/v1/systemone` | `jev-latest` | $0.042 |
| `openai` | `OpenAI` | `api.openai.com/v1/decisions` | `gpt-6-luna` | $0.10 |
| `deepseek` | `DeepSeek` | `api.deepseek.com/chat/completions` | `deepseek-chat` | $0.30 |
| `von` | `Von` | `127.0.0.1:8101/v1/systemone` (`von serve`) | `von-1.3` | local |
| `opendecider` | `OpenDecider` | `127.0.0.1:8102/v1/systemone` (`opendecider serve`) | `opendecider-nano` | local |
| `openjev` | `OpenJev` | `127.0.0.1:8103/v1/systemone` (`servers/openjev.py`) | `open-jev-deberta-v3-large` | local |

`OpenAI` translates both ways: `noul` becomes `predicate`, `criteria` become `choices` and `levels`,
and its list-shaped answers come back as the same answer shapes TypeSafe returns. `DeepSeek` turns a
chat model into a typed decision model: one request per question, each option gets a one-token label,
and the belief is the next-token distribution over those labels (`top_logprobs`, so 20 options at
most). Von and OpenDecider serve the wire format themselves, so their classes only change the URL and
drop the key (`Local`). Every provider's results therefore score with the same code. Another provider is one subclass; select it with
`@register("name")` and a model config that names it.

## `.env`

```
TYPESAFE_API_KEY=...
OPENAI_API_KEY=...
DEEPSEEK_API_KEY=...       # local servers need no key
```

## `questions.yaml` and `data.jsonl`

```yaml
department:
  type: choice
  instructions: Which team should handle this
  criteria: {billing: Payment or subscription issues, technical: Bugs or integration problems, sales: Pricing or account questions}
```

```jsonl
{"id": "t1", "label": "technical", "state": "Our API started returning 500 errors 20 minutes ago..."}
{"id": "t6", "state": "Do you still have the blue jacket in medium?", "questions": {"stock_question": {"type": "noul", "instructions": "Is the customer asking whether an item is in stock?"}}}
```

`id` and `state` are required. Only `state` and the questions are sent to the provider; `label` and
other fields are copied to the result. A record's own `questions` replace the shared ones.

## Run

```bash
python -m tdm run fresh-reviews [--model openai] [--task appstore_app] [--date 2026-10-17]
```

Each (task, model) pair becomes `runs/<date>_<model>_<task>_<version>/`:

- `run.json`: the task version, the model config, the model versions the API served, the git commit, times, row counts, cost and status.
- `beliefs.jsonl`: one line per record and repeat. Each line is the record without `state` and `questions`, plus `repeat`, `provider`, `model`, `answers`, `usage`, `latency_ms` and `cost_usd`, or `error`.

An incomplete run resumes: answered (id, repeat) pairs are skipped and failed ones are retried. A
complete run is never touched again. A run on another day is a new folder.

## Score and report

```bash
python -m tdm score fresh-reviews       # -> scores/fresh-reviews.json
python -m tdm report fresh-reviews      # -> reports/fresh-reviews.md and reports/fresh-reviews.<task>.csv
```

Scoring takes the latest complete run of each model on each task's current version. The answer type
picks the scorer:
- `noul`: accuracy, precision, recall and F1 at a threshold; AUROC, Brier score and calibration error from the probability.
- `choice`: accuracy, macro-F1, Brier score and calibration error.
- `score`: accuracy, within-one accuracy, mean absolute error and calibration error.

Repeats are averaged with their range, and `agree` is the share of records predicted the same on
every repeat. Cost and latency come from the run. Each model is compared with the experiment's first
model on the same records, with a 95% paired bootstrap interval. See `PROTOCOL.md`.

## Local servers

Von, OpenDecider and open-jev run on this machine; see [`servers/README.md`](../servers/README.md).
