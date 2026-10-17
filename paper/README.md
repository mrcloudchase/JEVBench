# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions, provider)(state)
```

- `Provider` is any endpoint that speaks the typed-decision wire format, through the official
  `typesafe-sdk`, selected by `base_url`, `api_key` and `model`.
- `Belief` holds questions. Calling it with state makes one provider call and returns the
  provider's answers, untouched, keyed by question id.

## Run TypeSafe's quickstart example

```bash
export TYPESAFE_API_KEY=sk-...
cd paper && python engine.py
```

Returns, for the 500-errors ticket: `department` technical (confidence 1.0), `frustration` score
about 0.6 on the three-level rubric, `is_urgent` 0.99. Values vary slightly between runs.

Next: operations on beliefs that turn them into decisions.
