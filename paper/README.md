# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions, provider)(state)
```

Three inputs, three places:

| File | Holds | Written by |
|---|---|---|
| `.env` | which provider: URL, key, model, handler | you, once per provider |
| `questions.yaml` | the task: questions in the wire format, keyed by id | hand |
| `dataset.jsonl` | the data: one record per line | a wrangling script |

## `.env`

Copy `.env.example` to `.env` (git-ignored). Variables already in the environment win.

```
PROVIDER_URL=https://api.typesafe.ai/v1/systemone
PROVIDER_API_KEY=sk-...
PROVIDER_MODEL=jev-latest
PROVIDER_HANDLER=typesafe          # optional
```

## Providers and handlers

The engine speaks raw HTTP and depends only on PyYAML. A `Handler` is the only code that knows a
provider's payloads:

```python
class Handler:
    def headers(self, api_key) -> dict                          # default: Bearer token, JSON
    def request(self, state, questions, model) -> dict          # default: TypeSafe wire format
    def response(self, body) -> dict                            # must return {model, answers, usage}
```

The default handler speaks the TypeSafe wire format, so any provider that accepts it needs only a
different `PROVIDER_URL`. For a provider with different payloads, subclass `Handler`, override what
differs, and set `PROVIDER_HANDLER=my_module:MyHandler`. `answers` must keep the wire format's answer
shapes so everything downstream works unchanged.

## `questions.yaml`

```yaml
department:
  type: choice
  instructions: Which team should handle this
  criteria: {billing: Payment or subscription issues, technical: Bugs or integration problems, sales: Pricing or account questions}
is_urgent:
  type: noul
  instructions: The message conveys urgency or time-sensitivity
```

## `dataset.jsonl`

```jsonl
{"id": "t1", "label": "technical", "state": "Our API started returning 500 errors 20 minutes ago..."}
{"id": "t3", "label": "sales", "state": {"subject": "Enterprise pricing", "body": "Could you send me pricing?"}}
{"id": "t6", "state": "Do you still have the blue jacket in medium?", "questions": {"stock_question": {"type": "noul", "instructions": "Is the customer asking whether an item is in stock?"}}}
```

`id` and `state` are required. Only `state` and the questions are sent to the provider. `label` and
any other fields are copied to the result. A record's own `questions` replace the shared file's
for that record. A YAML list of the same records also works.

## Run

```bash
cd paper
python engine.py examples/questions.yaml examples/tickets.jsonl --out results.jsonl --workers 8
```

Each result line is the record without `state` and `questions`, plus `model`, `answers` and `usage`,
or `error` if that record failed. Rerunning with the same `--out` skips ids already there.

On the example dataset, all five labelled tickets match and `t6` answers its own question:

| id | label | department | frustration | is_urgent |
|---|---|---|---|---|
| t1 | technical | technical | 0.67 | 0.99 |
| t2 | billing | billing | 0.08 | 0.31 |
| t3 | sales | sales | 0.00 | 0.08 |
| t4 | billing | billing | 1.89 | 0.99 |
| t5 | technical | technical | 0.35 | 0.63 |
| t6 | | stock_question 0.97 | | |

Next: operations on beliefs that turn them into decisions.
