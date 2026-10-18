"""National Weather Service alerts from api.weather.gov (the past seven days).

Legal basis: NWS web pages and data "are in the public domain, unless specifically noted otherwise" and
may be used "without charge for any lawful purpose" (https://www.weather.gov/disclaimer); the API is
"intended to be open data, free to use for any purpose" (https://www.weather.gov/documentation/services-web-api).
Conditions: identify NWS material and state it is not subject to copyright; do not imply NWS endorsement;
do not present modified text as official. Shared by the nws_* tasks; pages are cached in tasks/.sources/nws/.
"""

import hashlib
import json
import time
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / ".sources" / "nws"
HEADERS = {"User-Agent": "(tdm-eval research dataset, chase@odovey.com)", "Accept": "application/geo+json"}
NOTICE = "Text from U.S. National Weather Service alerts (api.weather.gov); not subject to copyright. Not an official NWS product."


def alerts(snapshot: str) -> list[dict]:
    """Every first-issuance alert the API holds, fetched once into tasks/.sources/nws/<snapshot>/ and reused after."""
    folder = CACHE / snapshot
    if not folder.exists():
        folder.mkdir(parents=True)
        url, n = "https://api.weather.gov/alerts?status=actual&message_type=alert&limit=500", 0
        while url:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=60) as response:
                page = json.load(response)
            (folder / f"{n:03d}.json").write_text(json.dumps(page))
            url = (page.get("pagination") or {}).get("next") if page.get("features") else None
            n += 1
            time.sleep(1)
    out, seen = [], set()
    for path in sorted(folder.glob("*.json")):
        for feature in json.loads(path.read_text())["features"]:
            a = feature["properties"]
            text = " ".join((a.get("description") or "").split())
            if a["id"] in seen or len(text) < 100:
                continue
            seen.add(a["id"])
            out.append({"id": "nws-" + hashlib.sha1(a["id"].encode()).hexdigest()[:12], "urn": a["id"], "sent": a["sent"],
                        "event": a["event"], "severity": a["severity"], "certainty": a["certainty"], "urgency": a["urgency"],
                        "sender": a.get("senderName"), "description": text,
                        "instruction": " ".join((a.get("instruction") or "").split())})
    return out


def build(here: Path, rows_for, questions_yaml: str, snapshot: str = "2026-10-18") -> list[dict]:
    """Write data.jsonl, manifest.jsonl and questions.yaml for an nws_* task. `rows_for(unique_alerts, rng)`
    returns the records. One record per distinct description: an alert re-issued across zones counts once."""
    import random
    unique = list({a["description"]: a for a in alerts(snapshot)}.values())
    rows = rows_for(unique, random.Random(7))
    random.Random(7).shuffle(rows)
    with open(here / "data.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    with open(here / "manifest.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
    (here / "questions.yaml").write_text(questions_yaml)
    return rows


def record(a: dict, label, text=lambda s: s) -> dict:
    return {"id": a["id"], "state": {"description": text(a["description"]), "instruction": text(a["instruction"])},
            "label": label, "event": a["event"], "sent": a["sent"], "urn": a["urn"]}


def balanced(alerts_: list[dict], key, levels: list, per_level: int, rng) -> dict:
    groups = {level: [a for a in alerts_ if key(a) == level] for level in levels}
    for level, group in groups.items():
        rng.shuffle(group)
        print(f"{level}: {len(group)} available")
    return {level: group[:per_level] for level, group in groups.items()}
