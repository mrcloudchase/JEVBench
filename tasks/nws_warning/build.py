"""Build nws_warning: is this weather alert a warning? (noul)

The label is 1 when the National Weather Service issued the alert as a Warning (its event name ends in
"Warning"), and 0 for advisories, watches and statements. The evidence is the description and
instructions, with the words warning, watch, advisory and statement masked as [alert], so the product
type must be inferred from the hazard described. Alerts issued October 11-18, 2026; 500 of each with seed 7.

    python -m tdm build nws_warning
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nws import balanced, build, record  # noqa: E402

MASK = re.compile(r"\b(warnings?|watch(es)?|advisor(y|ies)|statements?)\b", re.I)
hide = lambda s: MASK.sub("[alert]", s)
rows = build(HERE, lambda alerts, rng: [record(a, label, hide) for label, group in
                                        balanced(alerts, lambda a: int(a["event"].endswith("Warning")), [1, 0], 500, rng).items() for a in group], """\
# One yes/no question. The label is whether the National Weather Service issued the alert as a Warning.
warning:
  type: noul
  instructions: This weather alert is a warning, meaning a hazard is occurring or imminent and calls for protective action now
  criteria:
    "true": A warning, issued when a hazardous weather event is occurring, imminent or highly likely
    "false": An advisory, watch or statement, issued for less serious conditions or for hazards that are possible but not yet imminent
""")
print(f"{len(rows)} records")
