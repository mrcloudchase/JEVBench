"""Build arxiv_category: which arXiv category is this paper's primary one?

The label is the primary category the authors chose at submission. The evidence is the title and
abstract. New submissions (first version) dated September 28 - October 17, 2026; 50 per category with
seed 7. Cross-listed categories are kept in the manifest for analysis.

Legal basis: arXiv's API terms, "You are free to use descriptive metadata about arXiv e-prints under the
terms of the Creative Commons Universal (CC0 1.0)" (https://info.arxiv.org/help/api/tou.html). Only
descriptive metadata is used, never full text, and requests are made one at a time, 3 seconds apart.

    python -m tdm build arxiv_category
"""
import json
import random
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIRST, LAST = "2026-09-28", "2026-10-17"
PER_CATEGORY = 50
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
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def page(category: str, start: int) -> list[dict]:
    query = urllib.parse.urlencode({"search_query": f"cat:{category}", "sortBy": "submittedDate", "sortOrder": "descending",
                                    "start": start, "max_results": 200})
    with urllib.request.urlopen(f"https://export.arxiv.org/api/query?{query}", timeout=60) as response:
        root = ET.fromstring(response.read())
    time.sleep(3)                                         # arXiv: one request every three seconds
    out = []
    for e in root.findall("a:entry", NS):
        clean = lambda tag: " ".join((e.find(tag, NS).text or "").split())
        out.append({"id": "arxiv-" + clean("a:id").rsplit("/", 1)[-1].split("v")[0], "published": clean("a:published")[:10],
                    "primary": e.find("arxiv:primary_category", NS).get("term"),
                    "categories": [c.get("term") for c in e.findall("a:category", NS)],
                    "title": clean("a:title"), "abstract": clean("a:summary")})
    return out


pool = {}
for category in CATEGORIES:
    start, found = 0, []
    while True:
        entries = page(category, start)
        found += [e for e in entries if e["primary"] == category and FIRST <= e["published"] <= LAST]
        if not entries or entries[-1]["published"] < FIRST:
            break
        start += len(entries)
    pool[category] = list({e["id"]: e for e in found}.values())
    print(f"{category}: {len(pool[category])} new primary submissions")

rng = random.Random(7)
rows = []
for category, entries in pool.items():
    rng.shuffle(entries)
    rows += [{"id": e["id"], "state": {"title": e["title"], "abstract": e["abstract"]}, "label": category,
              "cross_lists": [c for c in e["categories"] if c != category], "published": e["published"]} for e in entries[:PER_CATEGORY]]
rng.shuffle(rows)
with open(HERE / "data.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
lines = ["# One 12-way choice question. The label is the primary category the authors chose.",
         "category:", "  type: choice", "  instructions: Which arXiv category is this paper's primary category?", "  criteria:"]
lines += [f"    {k}: {json.dumps(v)}" for k, v in CATEGORIES.items()]   # quoted: descriptions contain colons
(HERE / "questions.yaml").write_text("\n".join(lines) + "\n")
print(f"{len(rows)} records")
