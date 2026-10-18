# The paper's engine

Two primitives. A provider turns evidence and questions into a belief; a decision rule turns beliefs
and values into an action.

```python
belief = Belief(questions, provider)(state)
action = Decision(rule, **values)(belief)
```

| File | Job |
|---|---|
| `providers.py` | `Provider`, the generic HTTP client, and one subclass per provider API |
| `data.py` | the questions file, the dataset, the results file and the response cache |
| `engine.py` | `Belief`, `run`, and the command line that forms beliefs for a dataset |
| `score.py` | the generic scorer: beliefs against labels, one or several providers |
| `decide.py` | `Decision`, live and recorded belief sources, the five structures, and decision scoring |
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

## Local servers

```bash
pip install von-sdk 'opendecider[serve]' torch transformers huggingface_hub
von serve --port 8101 --device cpu --noul-decision raw   # raw: the posterior, not Von's abstention band
opendecider serve --port 8102 --device cpu
python local/openjev.py --port 8103
```

## Evals

An eval is a folder: a wrangle script, a questions file, a dataset, results per provider and scores.

| Eval | Records | Question | Data |
|---|---|---|---|
| [`examples/banking77`](examples/banking77) | 419 | is this a refund request? (noul) | Banking77, public since 2020 |
| [`examples/banking77_intents`](examples/banking77_intents) | 300 | which of 77 intents? (choice) | Banking77 |
| [`examples/steam_recommend`](examples/steam_recommend) | 300 | does the reviewer recommend the game? (noul) | Steam reviews, October 10–17, 2026 |
| [`examples/appstore_stars`](examples/appstore_stars) | 300 | how many stars? (score, five levels) | App Store reviews, October 10–17, 2026 |
| [`examples/appstore_app`](examples/appstore_app) | 300 | which of 12 apps, names masked? (choice) | App Store reviews, October 10–17, 2026 |

### Contamination

Banking77 is in Von's and open-jev's training data, and probably in others', so it measures
TypeSafe against OpenAI only. The three fresh evals use reviews written after every model was
published, so the open models cannot have trained on them, and the hosted ones almost certainly did not:

| Provider | Model | Published | Training data | Fresh data unseen? |
|---|---|---|---|---|
| TypeSafe | jev-1.13.0 | not stated; superseded by jev-1.14.0 on October 14, 2026 | not published | almost certainly: data within the window would have to reach a release that was already serving |
| OpenAI | gpt-6-luna | public beta October 6, 2026 | not published | yes |
| DeepSeek | V4.1-Flash-1017 (`deepseek-chat`) | October 17, 2026 | not published | very likely, not provable: released during the data window |
| Von | 1.3 | weights September 24, 2026 | includes Banking77 | yes |
| OpenDecider | nano | weights September 27, 2026 | eleven named datasets, among them CLINC150 and a typed-decisions set | yes |
| open-jev | deberta-v3-large | weights September 18, 2026 | Banking77, SST-5, BoolQ | yes |

The review text is git-ignored: it belongs to the reviewers and the repository is public. The results
files keep each record's id and label, so every score reproduces from the repository. `wrangle.py`
builds a new sample from the live source.

### Results on fresh data (October 17, 2026)

| Provider | Steam: accuracy, AUROC | Stars: accuracy, within one | App: accuracy | $ per 1k records |
|---|---|---|---|---|
| TypeSafe jev-1.13.0 | 0.864, 0.945 | 0.468, 0.802 | 0.596 | 0.015–0.022 |
| OpenAI gpt-6-luna | **0.893**, 0.938 | 0.373*, 0.741 | **0.603*** | 0.019–0.025 |
| DeepSeek V4.1 Flash | 0.890, **0.965** | **0.470**, 0.780 | 0.598 | 0.034–0.048 |
| Von 1.3 | 0.827, 0.888 | 0.300, 0.737 | 0.373 | local |
| OpenDecider nano | 0.840, 0.946 | 0.450, 0.807 | 0.450 | local |
| open-jev-deberta-v3-large | 0.867, 0.947 | 0.410, **0.837** | 0.343 | local |

\* OpenAI refused 18% of star reviews and 6% of app reviews; refusals count as wrong. On what it
answered: 0.453 and 0.644.

The three hosted models are statistically tied on Steam and on the app question; on stars, OpenAI
trails only because of its refusals. The local models stay close on sentiment, where AUROC is
0.89–0.95, and fall 15–26 points behind on the app question, which needs world knowledge. Calibration
does not follow accuracy: OpenDecider nano is the best calibrated model on the app question, and Von
on stars.

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

A belief comes from `Live(questions, provider, evidence)` or from `Recorded("results.x.jsonl")`, a
results file read back by record id. The same architecture therefore runs live or over recorded
beliefs, and re-deciding with new values (`decision.given(tau=0.6)`) costs no model calls.
`score_decisions` reports accuracy (an abstention counts as wrong), coverage, selective accuracy,
calls, cost and, given a loss, the expected loss per decision. `compare` gives paired intervals.

The decision experiments are in [`examples/decisions`](examples/decisions):

| Experiment | Structure | Finding |
|---|---|---|
| E1 threshold and costs | single | The best threshold differs by provider (0.05 to 0.45), and the best provider changes with the cost of errors: DeepSeek is best at equal costs and worst when a miss costs nine times more |
| E2 reject option | single | Abstaining on half the records raises TypeSafe from 0.600 to 0.861 on the app question at no cost |
| E3 value transfer | single | A threshold fitted on one provider misses its target on others, and misses on held-out data 9 times out of 17 on its own |
| E4 panels | parallel | No panel of providers beats the best single one; when one hosted model is wrong, another is wrong 55–92% of the time |
| E5 cascades | orchestrator-worker | A free local model escalating only when unsure matches the hosted model at 17–78% of its cost; confidence beats random escalation in every row |
| E6 decomposition | chained | Helps only when the subquestions add information (stars +2.7 points on TypeSafe, nearly significant) |
| E7 re-asking | evaluator-optimizer | Re-asking with earlier readings inflates confidence: for TypeSafe the loop equals lowering the threshold, at 1.5× the calls |
