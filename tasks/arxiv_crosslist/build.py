"""Build arxiv_crosslist: is this paper also listed in Machine Learning (cs.LG)? (noul)

The label is 1 when the authors cross-listed the paper to cs.LG, from its arXiv categories. Papers have
primary category cs.CL, cs.CV, cs.RO or cs.CR, first version dated September 28 - October 15, 2026; 150
cross-listed and 150 not, with seed 7, drawn evenly across the four primary categories. The evidence is
the title and abstract. Legal basis and fetching: see ../arxiv.py.

    python -m tdm build arxiv_crosslist
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from arxiv import primaries, write  # noqa: E402

PRIMARY = {"cs.CL": 38, "cs.CV": 38, "cs.RO": 37, "cs.CR": 37}     # per label: 150 cross-listed and 150 not
rng = random.Random(7)
rows = []
for category, n in PRIMARY.items():
    entries = primaries(category, "2026-09-28", "2026-10-15")
    for label in (1, 0):
        group = [e for e in entries if ("cs.LG" in e["categories"]) == bool(label)]
        rng.shuffle(group)
        print(f"{category} {'cross-listed' if label else 'not cross-listed'}: {len(group)} available")
        rows += [{"id": e["id"], "state": {"title": e["title"], "abstract": e["abstract"]}, "label": label, "primary": category,
                  "categories": e["categories"], "published": e["published"]} for e in group[:n]]
rng.shuffle(rows)
write(HERE, rows, """\
# One yes/no question. The label is whether the authors cross-listed the paper to Machine Learning (cs.LG).
crosslisted_lg:
  type: noul
  instructions: The authors also listed this paper in arXiv's Machine Learning category (cs.LG)
  criteria:
    "true": The paper is cross-listed to cs.LG, Machine Learning
    "false": The paper is not listed in cs.LG
""")
print(f"{len(rows)} records")
