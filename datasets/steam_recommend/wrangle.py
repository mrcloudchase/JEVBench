"""Fresh eval: Steam reviews created 2026-10-10..2026-10-17, after every evaluated model was trained.

label = 1 when the reviewer marked the game "Recommended" (their own verdict), else 0. English reviews of
50-1500 characters from ten popular games, balanced 150/150 with seed 7. Reviewer identities are not kept.

    python datasets/steam_recommend/wrangle.py   # fetches live from store.steampowered.com; the result depends on the day it is run
"""
import json, random, time, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent

START, END = datetime(2026, 10, 10, tzinfo=timezone.utc).timestamp(), datetime(2026, 10, 18, tzinfo=timezone.utc).timestamp()
GAMES = {730: "Counter-Strike 2", 570: "Dota 2", 1086940: "Baldur's Gate 3", 1091500: "Cyberpunk 2077", 578080: "PUBG",
         1172470: "Apex Legends", 1245620: "Elden Ring", 553850: "Helldivers 2", 252490: "Rust", 271590: "Grand Theft Auto V"}

def fetch(appid):
    cursor, out = "*", []
    for _ in range(30):
        q = urllib.parse.urlencode({"json": 1, "filter": "recent", "language": "english", "num_per_page": 100,
                                    "purchase_type": "all", "cursor": cursor})
        with urllib.request.urlopen(f"https://store.steampowered.com/appreviews/{appid}?{q}", timeout=60) as r:
            page = json.load(r)
        reviews = page.get("reviews", [])
        out += [x for x in reviews if START <= x["timestamp_created"] < END]
        if not reviews or reviews[-1]["timestamp_created"] < START or page.get("cursor") in (None, cursor):
            return out
        cursor = page["cursor"]
        time.sleep(0.5)
    return out

pool = []
for appid, game in GAMES.items():
    for x in fetch(appid):
        text = " ".join(x["review"].split())
        if 50 <= len(text) <= 1500:
            pool.append({"id": f"steam-{x['recommendationid']}", "state": {"game": game, "review": text},
                         "label": int(x["voted_up"]), "game": game,
                         "created": datetime.fromtimestamp(x["timestamp_created"], timezone.utc).isoformat()})
    print(game, sum(p["game"] == game for p in pool))

rng = random.Random(7)
up, down = [p for p in pool if p["label"] == 1], [p for p in pool if p["label"] == 0]
rng.shuffle(up); rng.shuffle(down)
rows = up[:150] + down[:150]
rng.shuffle(rows)
with open(HERE / "dataset.jsonl", "w", encoding="utf-8") as f:              # the text: git-ignored
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:             # the sample without the text: committed
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
print(f"{len(rows)} records ({len(up)} recommended and {len(down)} not in the pool)")
