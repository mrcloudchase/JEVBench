"""Fresh eval: App Store reviews posted 2026-10-10..2026-10-17, after every evaluated model was trained.

label = the reviewer's own star rating, as a level index 0-4 (one to five stars). Reviews of at least 30
characters from twelve popular apps, balanced up to 60 per star with seed 7. Reviewer names are not kept.

    python datasets/appstore_stars/wrangle.py   # fetches Apple's public review feeds; the result depends on the day it is run
"""
import json, random, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

START, END = "2026-10-10", "2026-10-18"
APPS = {284882215: "Facebook", 389801252: "Instagram", 835599320: "TikTok", 368677368: "Uber", 324684580: "Spotify",
        363590051: "Netflix", 570060128: "Duolingo", 297606951: "Amazon Shopping", 310633997: "WhatsApp",
        422689480: "Gmail", 544007664: "YouTube", 447188370: "Snapchat"}

pool = []
for appid, app in APPS.items():
    for page in range(1, 11):
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={appid}/sortby=mostrecent/json"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                entries = json.load(r)["feed"].get("entry", [])
        except Exception:
            break
        if isinstance(entries, dict):
            entries = [entries]
        for e in entries:
            day = e["updated"]["label"][:10]
            content = " ".join(e["content"]["label"].split())
            if START <= day < END and len(content) >= 30:
                pool.append({"id": f"appstore-{e['id']['label']}", "state": {"app": app, "title": e["title"]["label"], "review": content[:1500]},
                             "label": int(e["im:rating"]["label"]) - 1, "app": app, "created": e["updated"]["label"]})
        if not entries or min(e["updated"]["label"][:10] for e in entries) < START:
            break
        time.sleep(0.3)
    print(app, sum(p["app"] == app for p in pool))

rng, rows = random.Random(7), []
for level in range(5):
    group = [p for p in pool if p["label"] == level]
    rng.shuffle(group)
    rows += group[:60]
    print(f"{level + 1} stars: {len(group)} available")
rng.shuffle(rows)
with open(HERE / "dataset.jsonl", "w", encoding="utf-8") as f:              # the text: git-ignored
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:             # the sample without the text: committed
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
print(f"{len(rows)} records")
