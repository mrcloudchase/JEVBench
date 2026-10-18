"""Fresh eval: which app is an App Store review about? Reviews posted 2026-10-10..2026-10-17, after every
evaluated model was trained.

label = the app the review was posted to, one of twelve. App names (and their obvious variants) are masked
as "[app]" in the title and text, so the model must infer the app from what the reviewer describes.
Reviews of at least 30 characters, balanced 25 per app with seed 7. Reviewer names are not kept.

    python -m tdm build appstore_app   # fetches Apple's public review feeds; the result depends on the day it is run
"""
import json, random, re, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

START, END = "2026-10-10", "2026-10-18"
APPS = {284882215: ("facebook", ["facebook", "fb", "meta"]), 389801252: ("instagram", ["instagram", "insta", "ig"]),
        835599320: ("tiktok", ["tiktok", "tik tok"]), 368677368: ("uber", ["uber"]), 324684580: ("spotify", ["spotify"]),
        363590051: ("netflix", ["netflix"]), 570060128: ("duolingo", ["duolingo", "duo", "duolingo's"]),
        297606951: ("amazon_shopping", ["amazon"]), 310633997: ("whatsapp", ["whatsapp", "whats app"]),
        422689480: ("gmail", ["gmail", "google mail"]), 544007664: ("youtube", ["youtube", "yt", "you tube"]),
        447188370: ("snapchat", ["snapchat", "snap chat", "snap"])}

def mask(text, names):
    for n in sorted(names, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(n)}\b", "[app]", text, flags=re.I)
    return text

pool = []
for appid, (app, names) in APPS.items():
    for page in range(1, 11):
        url = f"https://itunes.apple.com/us/rss/customerreviews/page={page}/id={appid}/sortby=mostrecent/json"
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                entries = json.load(r)["feed"].get("entry", [])
        except Exception:
            break
        entries = [entries] if isinstance(entries, dict) else entries
        for e in entries:
            content = " ".join(e["content"]["label"].split())
            if START <= e["updated"]["label"][:10] < END and len(content) >= 30:
                pool.append({"id": f"appstore-{e['id']['label']}",
                             "state": {"title": mask(e["title"]["label"], names), "review": mask(content, names)[:1500]},
                             "label": app, "created": e["updated"]["label"]})
        if not entries or min(e["updated"]["label"][:10] for e in entries) < START:
            break
        time.sleep(0.3)

rng, rows = random.Random(7), []
for appid, (app, _) in APPS.items():
    group = [p for p in pool if p["label"] == app]
    rng.shuffle(group)
    rows += group[:25]
    print(app, len(group))
rng.shuffle(rows)
with open(HERE / "data.jsonl", "w", encoding="utf-8") as f:              # the text: git-ignored
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
with open(HERE / "manifest.jsonl", "w", encoding="utf-8") as f:             # the sample without the text: committed
    f.writelines(json.dumps({k: v for k, v in r.items() if k != "state"}) + "\n" for r in rows)
labels = {"facebook": "Facebook", "instagram": "Instagram", "tiktok": "TikTok", "uber": "Uber rides and Uber Eats",
          "spotify": "Spotify music and podcasts", "netflix": "Netflix streaming", "duolingo": "Duolingo language learning",
          "amazon_shopping": "Amazon Shopping", "whatsapp": "WhatsApp messaging", "gmail": "Gmail email",
          "youtube": "YouTube video", "snapchat": "Snapchat"}
lines = ["# One 12-way choice question. The answer is the app the review was posted to; app names are masked in the text.",
         "app:", "  type: choice", "  instructions: Which app is this App Store review about?", "  criteria:"]
lines += [f"    {k}: {v}" for k, v in labels.items()]
open(HERE / "questions.yaml", "w").write("\n".join(lines) + "\n")
print(f"{len(rows)} records")
