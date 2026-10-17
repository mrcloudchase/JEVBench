# The paper's engine

The primitive: a provider turns state and questions into a belief.

```python
belief = Belief(questions, provider)(state)
```

- `Provider` is any endpoint that speaks the typed-decision wire format, through the official
  `typesafe-sdk`, selected by `base_url`, `api_key` and `model`.
- `Belief` holds questions. Calling it with state makes one provider call and returns the
  provider's answers, untouched, keyed by question id.

## A belief as YAML

```yaml
provider:            # optional: model and base_url; the API key always comes from the environment
  model: jev-latest
questions:           # the wire format's questions, unchanged
  is_urgent:
    type: noul
    instructions: The message conveys urgency or time-sensitivity
state: "..."         # optional: can also be given on the command line
```

## Run TypeSafe's quickstart example

```bash
export TYPESAFE_API_KEY=sk-...
cd paper
python engine.py examples/ticket.yaml                       # state from the file
python engine.py examples/ticket.yaml --state "some text"   # state on the command line
python engine.py examples/ticket.yaml --state-file in.yaml  # state from a YAML or JSON file
```

For the 500-errors ticket in the file: `department` technical, `frustration` about 0.6,
`is_urgent` 0.99. For "could you send me pricing for the enterprise plan": sales, 0.0, 0.08.

Next: operations on beliefs that turn them into decisions.
