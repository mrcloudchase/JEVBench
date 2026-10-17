# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions, provider)(state)
```

| File | Job |
|---|---|
| `providers.py` | `Provider`, the generic HTTP client, and one subclass per provider API |
| `data.py` | the questions file, the dataset, and the results file |
| `engine.py` | `Belief`, `run`, and the command line |

| Input | Holds | Read by |
|---|---|---|
| `.env` | which provider and its key | `providers.load_provider` |
| `questions.yaml` | the task: questions in the wire format, keyed by id | `data.load_questions` |
| `dataset.jsonl` | the data: one record per line | `data.load_dataset` |

## Providers

`Provider` owns transport: configuration, the POST, retries on 408, 429, 5xx and 529 with
`Retry-After`, and error messages. A subclass defines only the provider's shapes:

```python
class Provider(ABC):
    url = None                      # class defaults; PROVIDER_URL / PROVIDER_MODEL override
    model = None
    def headers(self) -> dict        # default: Bearer token, JSON
    @abstractmethod
    def payload(self, state, questions) -> dict
    @abstractmethod
    def parse(self, body) -> dict    # -> {"model", "answers", "usage"}, answers in the wire format

@register("typesafe")
class TypeSafe(Provider):
    url = "https://api.typesafe.ai/v1/systemone"
    model = "jev-latest"
    def payload(self, state, questions): return {"model": self.model, "state": state, "questions": questions}
    def parse(self, body): return {"model": body.get("model"), "answers": body["answers"], "usage": body.get("usage", {})}
```

A provider with another API is one subclass. Override `headers`, `payload` and `parse` as needed,
and translate the provider's results into wire-format `answers` in `parse`, so nothing downstream
changes. Select it with `PROVIDER=my_module:MyProvider`, or add `@register("name")`.

## `.env`

```
PROVIDER=typesafe          # a registered name, or "module:Class"
PROVIDER_API_KEY=sk-...
# PROVIDER_URL=...         # optional when the class has a default
# PROVIDER_MODEL=...       # optional when the class has a default
```

Copy `.env.example` to `.env` (git-ignored). Variables already in the environment win.

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
python engine.py examples/questions.yaml examples/tickets.jsonl --out results.jsonl --workers 8
```

Each result line is the record without `state` and `questions`, plus `model`, `answers` and `usage`,
or `error`. Rerunning with the same `--out` skips ids already answered and retries ids that failed.

## Evals

An eval is three steps around the engine: wrangle a source into records, run, score.

| Eval | Records | Question | Result |
|---|---|---|---|
| [`examples/banking77`](examples/banking77) | 419 Banking77 messages | is this a refund request? | accuracy 0.759 at threshold 0.5, 0.833 at 0.7 |

Next: operations on beliefs that turn them into decisions.
