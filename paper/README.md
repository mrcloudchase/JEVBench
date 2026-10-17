# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions)(state)
```

## Configuration: `.env`

The official `typesafe-sdk` reads these. Copy `.env.example` to `.env` (git-ignored) in `paper/`
or the working directory; variables already in the environment win.

```
TYPESAFE_API_KEY=sk-...
TYPESAFE_BASE_URL=https://api.typesafe.ai      # any endpoint that speaks the wire format
TYPESAFE_DEFAULT_MODEL=jev-latest
```

## Data: YAML of states and questions

One case:

```yaml
questions:
  is_urgent: {type: noul, instructions: The message conveys urgency or time-sensitivity}
state: Our API has returned 500 errors for 20 minutes.
```

A dataset: shared questions, many states. Any other keys (`id`, `label`, ...) pass through to the
output, so ground truth travels with each result. A case may bring its own `questions`.

```yaml
questions: {...}
cases:
  - {id: t1, label: technical, state: "..."}
  - {id: t2, label: billing,   state: "..."}
```

## Run

```bash
cd paper
python engine.py examples/ticket.yaml                                    # TypeSafe's quickstart example
python engine.py examples/tickets.yaml --workers 8 --out results.jsonl   # a dataset
```

Output is one JSON record per case: the case's own fields plus the provider's `model`, `answers`
and `usage`. A failed case is recorded with an `error` instead of stopping the run.

On `examples/tickets.yaml` all five department labels match:

| id | label | department | frustration | is_urgent |
|---|---|---|---|---|
| t1 | technical | technical | 0.64 | 0.99 |
| t2 | billing | billing | 0.03 | 0.30 |
| t3 | sales | sales | 0.00 | 0.07 |
| t4 | billing | billing | 1.68 | 0.99 |
| t5 | technical | technical | 0.29 | 0.50 |

Next: operations on beliefs that turn them into decisions.
