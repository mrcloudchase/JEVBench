# The paper's engine

Two files. `engine.py` is the whole engine (about 100 lines); `architectures.py` builds eight
decision architectures from it and runs them live.

    evidence + questions  ->  belief      Believe(questions, evidence, *inputs, **values)
    beliefs  + values     ->  decision    Decide(rule, *beliefs, **values)
    decision              ->  evidence    a node's value is an input to any later node

Positional arguments are nodes whose values the function receives. Keyword arguments are the
author's values: thresholds, labels, framings. The argument list is the wiring. An `Architecture`
is everything reachable from its output node; it infers execution levels, runs independent beliefs
concurrently, and is callable, so it can be the function of a node in another architecture.

A `Provider` is any endpoint that speaks the typed-decision wire format, reached through the official
SDK and selected by `base_url`, `api_key` and `model`.

## Run

```bash
export TYPESAFE_API_KEY=sk-...
cd paper && python architectures.py
```

```
single      levels=2 max_calls=1  ->  complaint
gated       levels=2 max_calls=1  ->  complaint
routed      levels=2 max_calls=1  ->  human
panel       levels=3 max_calls=3  ->  complaint
escalation  levels=4 max_calls=2  ->  return_exchange
chain       levels=3 max_calls=2  ->  agent
vetoed      levels=2 max_calls=1  ->  complaint
nested      levels=2 max_calls=3  ->  complaint
```

| Architecture | What it shows |
|---|---|
| single | one belief, one rule |
| gated | a threshold value and an abstain label |
| routed | TypeSafe's own routing example as one belief with two questions |
| panel | three framed beliefs, one aggregate rule |
| escalation | a second belief formed only when a decision says the first was unsure |
| chain | a belief as evidence for the next belief |
| vetoed | a value that overrides any belief |
| nested | an architecture as a node of another |
