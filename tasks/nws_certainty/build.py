"""Build nws_certainty: how certain is the hazard this weather alert describes? (score, 3 levels)

The label is the alert's CAP certainty as issued by the National Weather Service: Possible < Likely <
Observed. The evidence is the alert's description and instructions; the event name and headline are
left out. Alerts issued October 11-18, 2026; 100 per level with seed 7.

    python -m tdm build nws_certainty
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nws import balanced, build, record  # noqa: E402

LEVELS = ["Possible", "Likely", "Observed"]
rows = build(HERE, lambda alerts, rng: [record(a, i) for i, level in enumerate(LEVELS)
                                        for a in balanced(alerts, lambda a: a["certainty"], LEVELS, 100, rng)[level]], """\
# One three-level score question. The label is the alert's CAP certainty as issued by the National Weather Service.
certainty:
  type: score
  instructions: How certain is it that the hazard described in this weather alert occurs?
  criteria:
    - "Possible: it may occur, but is not likely (probability about 50% or less)"
    - "Likely: it is likely to occur (probability above about 50%)"
    - "Observed: it is occurring or has occurred"
""")
print(f"{len(rows)} records")
