<p align="center">
  <a href="assets/judgejev-owl.svg"><img src="assets/judgejev-owl.svg" alt="JudgeJEV owl mascot" width="220"></a>
</p>

# JEVBench

A CLI-first, API-first, file-driven workbench for composing, executing and experimenting with
judging frameworks on [Jev](https://docs.typesafe.ai) and other JEV-wire-compatible decision models.

```
jevbench run framework.yaml --input data.json
```

One execution engine, one YAML/JSON schema. The graph in the file *is* the architecture:
a single judge, a parallel council, a hierarchical review, an adversarial trial, a confidence
cascade, a bounded refinement loop, or any combination of those, with no mode switch.

## Concepts

| Term | Meaning |
|---|---|
| **JudgeJEV** | A `judge` node. One node, one Issue, one API call, one Ruling. |
| **Issue** | Shared `state` plus one or more typed questions (`noul`, `choice`, `score`, `box`). |
| **Ruling** | The provider's answers to every question in the Issue, plus model and usage. |
| **Judging Policy** | A non-judge node that interprets or combines rulings: `threshold`, `vote`, `aggregate`, `consensus`, `constraint`, `decide`, `expr`. |
| **Judging Framework** | The whole graph. `subgraph` reuses another framework; `loop` bounds iteration. |
| **JEVdiciary** | Any composition of judges and policies. It produces the final **Judgment** (`output`). |

## Install

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
export TYPESAFE_API_KEY=sk-...          # the built-in provider reads this
jevbench providers                      # confirm the key is picked up
jevbench run examples/single_judge.yaml -i examples/inputs/ticket.json
```

Everything except the provider call works offline: `--mock` answers judges synthetically,
and tests with `mock:` sections never touch the network.

## A framework file

```yaml
jevbench: 1                      # schema version
name: escalation_cascade
version: 1.0.0
inputs:
  message: {required: true}
  confidence_floor: {default: 0.6}

nodes:
  first_pass:                    # JudgeJEV: one API call
    type: judge
    model: jev-latest
    state: ${input.message}
    questions:
      intent:
        type: choice
        instructions: Primary intent of the message
        criteria: {order_status: Asking about an order, complaint: Unhappy, other: null}

  confident:                     # policy
    type: threshold
    value: nodes.first_pass.answers.intent.confidence
    min: ${input.confidence_floor}

  escalated:                     # conditional: only runs when needed
    type: judge
    when: not nodes.confident
    model: jev-preview
    state: {message: "${input.message}", hint: "first pass was unsure"}
    questions: {intent: {type: choice, instructions: Primary intent, criteria: {order_status: null, complaint: null, other: null}}}

  route:
    type: decide
    cases:
      - {when: nodes.confident, then: "${nodes.first_pass.answers.intent.choice}"}
      - {when: nodes.escalated.answers.intent.confidence >= 0.5, then: "${nodes.escalated.answers.intent.choice}"}
    default: human

output: {route: "${nodes.route}", escalated: "${nodes.escalated is not None}"}

tests:
  - name: unsure first pass escalates
    input: {message: "it arrived broken"}
    mock:
      first_pass: {intent: {complaint: 0.45, other: 0.4, order_status: 0.15}}
      escalated: {intent: complaint}
    expect: ["judgment.route == 'complaint'", "judgment.escalated"]
```

Dependencies are inferred from the expressions (`nodes.<id>` references), so nodes that don't
depend on each other run in parallel. Cycles are rejected; feedback goes through a `loop` node.

### Expressions and templates

* **Bare expressions** (`when`, `value`, `cases[].when`, `values`, `inputs`, `output` strings):
  a safe subset of Python expression syntax over `input`, `nodes` and `loop`.
  Attribute access reads mapping keys, so `nodes.triage.answers.dept.choice` works on the raw
  wire response. Comparisons, arithmetic, `and/or/not`, `in`, `is None`, ternaries,
  list/dict literals, comprehensions and these functions: `min max sum len abs round any all
  sorted mean median argmax argmin clamp str int float bool list dict`.
* **Templates** (`state`, question content, `then`, `default`, `output` objects): `${expr}`
  inside any string. A string that is exactly one `${...}` keeps the value's type.
* A skipped node (its `when` was false) is `None` downstream.

### Node types

| Type | Purpose | Key fields | Output |
|---|---|---|---|
| `judge` | One provider call | `state`, `questions`, `provider`, `model`, `headers`, `assets` | `{provider, model, answers, usage, latency_ms}` |
| `expr` | Arbitrary computation | `value` | the value |
| `threshold` | Range check | `value`, `min`, `max`, `exclusive` | bool |
| `decide` | First matching case (branching, escalation, abstention) | `cases[{when, then}]`, `default` | `then` value |
| `vote` | Weighted label voting | `values`/`from`, `weights`, `method` (plurality/majority/unanimous), `min_share`, `tie` | `{winner, tally, share, total, unanimous, tied}` |
| `aggregate` | Combine numbers | `values`/`from`, `weights`, `method` (mean/sum/min/max/median/count/any/all/spread/product) | number or bool |
| `consensus` | Agreement check | `values`/`from`, `tolerance` | `{agreed, value, spread}` |
| `constraint` | Hard rules | `rules[{name, require}]` | `{satisfied, violations}` |
| `subgraph` | Reuse a framework | `framework` (path or `name@version`) or inline `body`, `inputs` | nested judgment |
| `loop` | Bounded iteration | `max_iterations`, `until`, `body`/`framework`, `inputs` | `{value, iterations, converged, history}` |

Every node also accepts `description`, `when` and `depends_on`. `jevbench schema nodes` prints
the full field schema of every registered type; adding a node type is one class registered
with `@registry.register`.

### Questions (JEV wire format, one-to-one)

```yaml
noul:   {type: noul,   instructions: "Is the customer asking for a refund?", criteria: {true: ..., false: ...}}  # criteria optional
choice: {type: choice, instructions: "...", criteria: {billing: "Charges and refunds", other: null}}            # ≤ 255 options
score:  {type: score,  instructions: "...", criteria: [Calm, Frustrated, Furious]}                                # 2–10 ordered levels
box:    {type: box,    instructions: "the red rectangle in `photo`"}                                               # needs images + jev-1.14
```

Answers come back exactly as the API returns them: `noul` (0–1), `choice` + `probabilities` +
`confidence`, `score` + `legend` + `probabilities` + `confidence`, `box` + `confidence`.
Score maps are keyed by string level (`"0"`, `"1"`, ...) regardless of client.

## Providers

Credentials never live in framework files. The built-in `typesafe` provider reads
`TYPESAFE_API_KEY` (and optionally `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`). Additional
providers go in `jevbench.providers.yaml` (cwd), `~/.config/jevbench/providers.yaml`,
`$JEVBENCH_PROVIDERS`, or `--providers path`:

```yaml
default: typesafe
providers:
  typesafe_114: {api_key: "${env:TYPESAFE_API_KEY}", default_model: jev-1.14.0}
  gateway:      {base_url: https://gateway.example.com, path: /v1/evaluate, client: http,
                 api_key: "${env:GATEWAY_KEY}", default_model: typesafe-ai/jev, capabilities: []}
  mock:         {client: mock, mock_answers: {department: billing}}
```

Each provider has a base URL, key, default model, optional headers and capabilities.
`client: sdk` uses the official `typesafe-sdk`; `client: http` is a raw-wire adapter for
gateways that mount the same body elsewhere; `client: mock` is deterministic and offline.
Each `judge` picks its own `provider` and `model` (falling back to the framework `defaults`).
The images header is added automatically when a judge sends assets or box questions.

## CLI

| Command | What it does |
|---|---|
| `jevbench validate fw.yaml` | Schema + semantic checks (types, expressions, references, cycles, nested frameworks). |
| `jevbench inspect fw.yaml` | Nodes, dependencies, execution levels, worst-case API call count. `-f json` for machines. |
| `jevbench run fw.yaml -i in.json [-s k=v] [--mock] [--mocks pins.json] [--trace out.json] [-v/-vv] [-f json\|yaml\|trace]` | Execute with runtime input. |
| `jevbench test fw.yaml [--cases file] [--live] [--mock]` | Run the declarative test cases. Offline by default. |
| `jevbench save fw.yaml` / `jevbench list` | Version frameworks in the store (`~/.jevbench/frameworks/<name>/<version>.yaml`). Reference them as `name@version`. |
| `jevbench providers` | Show configured providers with keys redacted. |
| `jevbench schema [framework\|nodes]` | JSON schema of the file format, or the node-type catalogue. |

Traces record every node: status, timing, resolved Issue, provider, model, token usage, output,
nested children for subgraphs and loops (with iteration numbers).

## Testing frameworks

A `tests:` section (or a separate cases file) lists cases with `input`, optional `mock` rulings
keyed by node path (`council.judge_a`; a list is consumed one entry per loop iteration) and
`expect` expressions over `input`, `nodes` and `judgment`. Cases without mocks are skipped
unless `--live`.

## Python API

```python
from jevbench import load_framework, run_framework, validate_framework, run_tests

framework, base_dir = load_framework("examples/parallel_council.yaml")
assert validate_framework(framework, base_dir) == []
result = run_framework(framework, {"message": "..."}, base_dir=base_dir)
result.judgment          # the final Judgment
result.trace.to_dict()   # full execution history
```

The CLI is a thin layer over `jevbench.api`; a web canvas would use the same functions,
`framework_schema()` and `node_types()`.

## Examples

| File | Pattern |
|---|---|
| `examples/single_judge.yaml` | Smallest framework |
| `examples/parallel_council.yaml` | Parallel judges, weighted vote, aggregation, hard constraints, abstention |
| `examples/hierarchical_council.yaml` | Specialists feed a chair judge; veto constraints |
| `examples/adversarial.yaml` | Prosecutor vs. defender with an arbiter |
| `examples/escalation_cascade.yaml` | Conditional routing to a second judge |
| `examples/iterative_review.yaml` | Bounded loop until confident |
| `examples/composed.yaml` + `policies/majority_vote.yaml` | Reusable policy subgraph |
| `examples/image_box.yaml` | Image assets and the `box` primitive |

## Layout

```
src/jevbench/
  schema/      models.py (versioned schema)  validator.py (semantic analysis)
  providers/   config.py (registry)  clients.py (sdk / http / mock)  wire.py (Issue, Ruling)
  engine/      expressions.py  graph.py  context.py  executor.py  trace.py
  engine/nodes/  base.py (registry)  judge.py  policy.py  composite.py
  store.py  testing.py  api.py  cli.py
```

## Design rules

* One `judge` node → one Issue → one API call → one Ruling.
* No hard-coded frameworks and no mode field; the graph decides.
* Loops are always bounded (`max_iterations`), cycles elsewhere are errors.
* Policies are pure functions of data; judges are the only side effects.
* Everything is addressable by expression, so new policies rarely need new node types.
