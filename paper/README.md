# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions, provider)(state)
```

| File | Job |
|---|---|
| `providers.py` | `Provider`, the generic HTTP client, and one subclass per provider API |
| `data.py` | the questions file, the dataset, the results file and the response cache |
| `engine.py` | `Belief`, `run`, and the command line that forms beliefs for a dataset |
| `score.py` | the generic scorer: beliefs against labels, one or several providers |
| `local/openjev.py` | serves open-jev-deberta, which ships no server, in the wire format |

| Input | Holds | Read by |
|---|---|---|
| `.env` | which provider and its key | `providers.load_provider` |
| `questions.yaml` | the task: questions in the wire format, keyed by id | `data.load_questions` |
| `dataset.jsonl` | the data: one record per line | `data.load_dataset` |

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
| `openjev` | `OpenJev` | `127.0.0.1:8103/v1/systemone` (`local/openjev.py`) | `open-jev-deberta-v3-large` | local |

`OpenAI` translates both ways: `noul` becomes `predicate`, `criteria` become `choices` and `levels`,
and its list-shaped answers come back as the same answer shapes TypeSafe returns. `DeepSeek` turns a
chat model into a typed decision model: one request per question, each option gets a one-token label,
and the belief is the next-token distribution over those labels (`top_logprobs`, so 20 options at
most). Von and OpenDecider serve the wire format themselves, so their classes only change the URL and
drop the key (`Local`). Every provider's results therefore score with the same code. Another provider is one subclass; select it with
`--provider` or `PROVIDER=my_module:MyProvider`, or add `@register("name")`.

## `.env`

```
PROVIDER=typesafe          # a registered name or "module:Class"; --provider overrides it
PROVIDER_API_KEY=sk-...    # optional when TYPESAFE_API_KEY, OPENAI_API_KEY or DEEPSEEK_API_KEY is set; local servers need none
```

## `questions.yaml` and `dataset.jsonl`

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
cd paper
python engine.py questions.yaml dataset.jsonl --out results.jsonl \
    [--provider openai] [--repeats 3] [--cache cache.jsonl] [--workers 8]
```

Each result line is the record without `state` and `questions`, plus `repeat`, `provider`, `model`,
`answers`, `usage`, `latency_ms` and `cost_usd`, or `error`. Rerunning with the same `--out` skips
answered (id, repeat) pairs and retries failed ones. With `--cache`, a request seen before is answered
from the cache at no cost; each repeat is a distinct request.

## Score

```bash
python score.py results.typesafe.jsonl results.openai.jsonl [--question ID] [--threshold 0.5]
```

The answer type picks the scorer: `noul` (accuracy, precision, recall, F1 at a threshold; AUROC,
Brier and calibration error from the probability), `choice` (accuracy, macro-F1, Brier, calibration
error) and `score` (accuracy, within-one accuracy, mean absolute error, calibration error). Repeats
are averaged with their range, and `agree` is the share of records predicted the same on every
repeat. Cost and latency come from the results. With several files, each is compared with the first
on the same records, with a 95% bootstrap interval.

## Evals

An eval is a folder: a wrangle script, a questions file, a dataset, results per provider and scores.

| Eval | Records | Question | TypeSafe jev-1.13.0 | OpenAI gpt-6-luna |
|---|---|---|---|---|
| [`examples/banking77`](examples/banking77) | 419 | is this a refund request? (noul) | AUROC 0.899; accuracy 0.835 at 0.7 | AUROC 0.861; accuracy 0.790 at 0.7 |
| [`examples/banking77_intents`](examples/banking77_intents) | 300 | which of 77 intents? (choice) | accuracy 0.848 | accuracy 0.853 |

Next: operations on beliefs that turn them into decisions, scored the same way.
