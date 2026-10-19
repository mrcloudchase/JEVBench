"""Build nws_severity: how severe a threat does this weather alert describe? (score, 4 levels)

The label is the alert's CAP severity as issued by the National Weather Service: Minor < Moderate <
Severe < Extreme. The evidence is the alert's description and instructions; the event name and headline
are left out. Alerts issued October 11-18, 2026; up to 300 per level with seed 7 (Extreme had only 16).

    python -m tdm build nws_severity
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nws import balanced, build, record  # noqa: E402

LEVELS = ["Minor", "Moderate", "Severe", "Extreme"]
rows = build(HERE, lambda alerts, rng: [record(a, i) for i, level in enumerate(LEVELS)
                                        for a in balanced(alerts, lambda a: a["severity"], LEVELS, 300, rng)[level]], """\
# One four-level score question. The label is the alert's CAP severity as issued by the National Weather Service.
severity:
  type: score
  instructions: How severe a threat to life or property does this weather alert describe?
  criteria:
    - "Minor: minimal to no known threat to life or property"
    - "Moderate: possible threat to life or property"
    - "Severe: significant threat to life or property"
    - "Extreme: extraordinary threat to life or property"
""")
print(f"{len(rows)} records")
