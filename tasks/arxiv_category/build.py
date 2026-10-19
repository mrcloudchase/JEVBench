"""Build arxiv_category: which arXiv category is this paper's primary one?

The label is the primary category the authors chose at submission. The evidence is the title and
abstract. New submissions (first version) dated September 28 - October 15, 2026; up to 100 per category
with seed 7 (all of econ.GN and q-bio.NC, which have fewer). Cross-listed categories are kept in the manifest.

Legal basis and fetching: see ../arxiv.py (CC0 descriptive metadata; one request every 3 seconds).

    python -m tdm build arxiv_category
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from arxiv import primaries, write  # noqa: E402

FIRST, LAST = "2026-09-28", "2026-10-15"
PER_CATEGORY = 100
CATEGORIES = {
    "cs.CL": "Computation and Language: natural language processing, speech, language models",
    "cs.CV": "Computer Vision and Pattern Recognition: images, video, visual recognition",
    "cs.CR": "Cryptography and Security: security, privacy, attacks and defenses, cryptography",
    "cs.RO": "Robotics: robot control, manipulation, navigation, planning",
    "math.NT": "Number Theory: primes, modular forms, Diophantine equations, arithmetic geometry",
    "math.PR": "Probability: stochastic processes, random structures, limit theorems",
    "stat.ME": "Statistics Methodology: statistical methods, inference, design, causal inference",
    "quant-ph": "Quantum Physics: quantum information, quantum computing, quantum optics, foundations",
    "astro-ph.GA": "Astrophysics of Galaxies: galaxies, the interstellar medium, star formation, galactic structure",
    "cond-mat.mtrl-sci": "Materials Science: properties, synthesis and computation of materials",
    "q-bio.NC": "Neurons and Cognition: neuroscience, neural coding, cognition, brain imaging",
    "econ.GN": "General Economics: economic analysis, policy, labor, development, markets",
}
pool = {category: primaries(category, FIRST, LAST) for category in CATEGORIES}
for category, entries in pool.items():
    print(f"{category}: {len(entries)} new primary submissions")

rng = random.Random(7)
rows = []
for category, entries in pool.items():
    rng.shuffle(entries)
    rows += [{"id": e["id"], "state": {"title": e["title"], "abstract": e["abstract"]}, "label": category,
              "cross_lists": [c for c in e["categories"] if c != category], "published": e["published"]} for e in entries[:PER_CATEGORY]]
rng.shuffle(rows)
lines = ["# One 12-way choice question. The label is the primary category the authors chose.",
         "category:", "  type: choice", "  instructions: Which arXiv category is this paper's primary category?", "  criteria:"]
lines += [f"    {k}: {json.dumps(v)}" for k, v in CATEGORIES.items()]   # quoted: descriptions contain colons
write(HERE, rows, "\n".join(lines) + "\n")
print(f"{len(rows)} records")
