# Beliefs, Values, Actions

Code, data and results for a paper on typed decision models: models that answer typed questions about
evidence with a probability distribution instead of generated text.

**The idea.** A typed decision model produces a *belief*. A *decision rule*, a pure expression over
beliefs and explicit values, turns that belief into an action. Decision systems are decision units
wired one of five ways, and their behavior lives in the rules, not in the wiring.

```python
from tdm import Belief, Decision, load_provider, top, confidence, ABSTAIN

belief = Belief(questions, load_provider("typesafe"))(state)                       # evidence + questions -> belief
route = Decision(lambda b, tau: top(b["app"]) if confidence(b["app"]) >= tau else ABSTAIN, tau=0.7)
action = route(belief)                                                             # belief + values -> action
```

## Repository

```
src/tdm/          the engine: providers, belief runs, scoring, decisions          docs/engine.md
datasets/         three fresh datasets, one per question type, with data cards    datasets/README.md
experiments/      the three scripts that produce every result                     experiments/README.md
results/          committed results: beliefs per provider, decision experiments   results/README.md
servers/          local servers for the three open models                         servers/README.md
related_work/     literature sweep and notes                                      related_work/README.md
manuscript/       abstract and outline                                            manuscript/README.md
docs/             engine reference, TypeSafe API notes
tests/            unit tests, offline
```

## Models and data

| Provider | Model | Kind | How it is reached |
|---|---|---|---|
| `typesafe` | jev-1.13.0 | hosted | System One API, native |
| `openai` | gpt-6-luna | hosted | Decisions API, translated to System One |
| `deepseek` | V4.1 Flash | hosted chat model | one request per question, belief from next-token probabilities |
| `von` | Von 1.3 | open, local | `von serve`, native |
| `opendecider` | OpenDecider nano | open, local | `opendecider serve`, native |
| `openjev` | open-jev-deberta-v3-large | open, local | `servers/openjev.py` |

| Dataset | Question | Label |
|---|---|---|
| `steam_recommend` | does the reviewer recommend the game? (yes/no) | the reviewer's Recommended button |
| `appstore_stars` | how many stars? (five levels) | the reviewer's star rating |
| `appstore_app` | which of 12 apps? (choice, names masked) | the app reviewed |

All 900 records were written October 10–17, 2026, after every model was published.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env                  # TYPESAFE_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY
make test                             # offline unit tests
make scores decisions-offline         # every committed number, from committed results, no API calls
make data beliefs decisions-live      # the full run: new data, new calls (servers/README.md for local models)
```

## Headline results

- **Beliefs:**
  - The three hosted models are statistically tied on yes/no and choice.
  - The open models trail by 15–26 points where world knowledge matters.
  - Calibration does not track accuracy.
- **Decisions:**
  - The best model depends on what errors cost.
  - Abstaining is the largest free lever: 0.600 → 0.861 on the app question.
  - Values do not transfer between models.
  - Panels of providers do not beat the best single one.
  - A confidence-gated cascade from a free local model matches a hosted model at 17–78% of its cost.
  - Re-asking until confident inflates confidence, not accuracy.

Details: [`results/README.md`](results/README.md).
