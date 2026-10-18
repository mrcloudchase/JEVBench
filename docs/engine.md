# The engine: `tdm`

Two primitives. A provider turns evidence and questions into a belief; a decision rule turns beliefs
and values into an action.

```python
belief = Belief(questions, provider)(state)
action = Decision(rule, **values)(belief)
```

| Module | Job |
|---|---|
| `tdm.providers` | `Provider`, the generic HTTP client, and one subclass per provider API |
| `tdm.data` | the questions file, the dataset, the results file and the response cache |
| `tdm.belief` | `Belief`, `run`, `evaluate`, and the command line that forms beliefs for a dataset |
| `tdm.score` | the generic scorer: beliefs against labels, one or several providers |
| `tdm.decision` | `Decision`, live and recorded belief sources, the five structures, and decision scoring |

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
| `openjev` | `OpenJev` | `127.0.0.1:8103/v1/systemone` (`servers/openjev.py`) | `open-jev-deberta-v3-large` | local |

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
python -m tdm.belief datasets/steam_recommend/questions.yaml datasets/steam_recommend/dataset.jsonl --out results.jsonl \
    [--provider openai] [--repeats 3] [--cache cache.jsonl] [--workers 8]
```

Each result line is the record without `state` and `questions`, plus `repeat`, `provider`, `model`,
`answers`, `usage`, `latency_ms` and `cost_usd`, or `error`. Rerunning with the same `--out` skips
answered (id, repeat) pairs and retries failed ones. With `--cache`, a request seen before is answered
from the cache at no cost; each repeat is a distinct request.

## Score

```bash
python -m tdm.score results/beliefs/steam_recommend/typesafe.jsonl results/beliefs/steam_recommend/openai.jsonl [--question ID] [--threshold 0.5]
```

The answer type picks the scorer: `noul` (accuracy, precision, recall, F1 at a threshold; AUROC,
Brier and calibration error from the probability), `choice` (accuracy, macro-F1, Brier, calibration
error) and `score` (accuracy, within-one accuracy, mean absolute error, calibration error). Repeats
are averaged with their range, and `agree` is the share of records predicted the same on every
repeat. Cost and latency come from the results. With several files, each is compared with the first
on the same records, with a 95% bootstrap interval.

## Local servers

Von, OpenDecider and open-jev run on this machine; see [`servers/README.md`](../servers/README.md).

## Decisions

A rule is a pure expression over beliefs and named values that returns an action or `ABSTAIN`;
acting on the action is ordinary code. A unit is a belief and a decision, and an architecture wires
units one of five ways. The architecture sets which edges exist; the rules decide which ones fire.

```python
gate = Decision(lambda b, tau: top(b["app"]) if confidence(b["app"]) >= tau else "escalate", tau=0.8)

Single(belief, decision)                           # one unit
Chained([b1, b2], decision)                        # b1's belief is evidence for b2
Parallel([b1, b2, b3], decision)                   # one decision over independent beliefs
OrchestratorWorker(Single(local, gate), {"escalate": Single(hosted, decision)})
EvaluatorOptimizer(belief, done, decision, rounds=3)
```

A belief comes from `Live(questions, provider, evidence)` or from `Recorded("results/beliefs/<dataset>/<provider>.jsonl")`, a
results file read back by record id. The same architecture therefore runs live or over recorded
beliefs, and re-deciding with new values (`decision.given(tau=0.6)`) costs no model calls.
`score_decisions` reports accuracy (an abstention counts as wrong), coverage, selective accuracy,
calls, cost and, given a loss, the expected loss per decision. `compare` gives paired intervals.

The decision experiments and their results are in [`results/decisions`](../results/decisions).
