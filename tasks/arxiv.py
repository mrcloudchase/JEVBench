"""New arXiv submissions per category from the arXiv API: titles, abstracts and categories only.

Legal basis: arXiv's API terms, "You are free to use descriptive metadata about arXiv e-prints under the
terms of the Creative Commons Universal (CC0 1.0)" (https://info.arxiv.org/help/api/tou.html). Only
descriptive metadata is used, never full text; requests go one at a time, 3 seconds apart, as the terms
ask. Shared by the arxiv_* tasks; each category's listing is cached in tasks/.sources/arxiv/.
"""

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CACHE = Path(__file__).resolve().parent / ".sources" / "arxiv"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def _page(category: str, start: int) -> list[dict]:
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


def primaries(category: str, first: str, last: str) -> list[dict]:
    """Papers whose primary category is `category`, first version dated first..last (inclusive)."""
    path = CACHE / f"{category}_{first}_{last}.json"
    if not path.exists():
        start, found = 0, []
        while True:
            entries = _page(category, start)
            found += [e for e in entries if e["primary"] == category and first <= e["published"] <= last]
            if not entries or entries[-1]["published"] < first:
                break
            start += len(entries)
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(list({e["id"]: e for e in found}.values())))
    return json.loads(path.read_text())


def write(here: Path, rows: list[dict], questions_yaml: str) -> None:
    with open(here / "data.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    with open(here / "manifest.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
    (here / "questions.yaml").write_text(questions_yaml)
