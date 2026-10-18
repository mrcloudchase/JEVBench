# appstore_app

**Question:** which app is this App Store review about? One `choice` question over twelve apps, each
with a short description ("Uber rides and Uber Eats"). `wrangle.py` writes `questions.yaml` too.

**Label:** the app the review was posted to.

**Source:** the same feeds as `appstore_stars`, reviews posted October 10–17, 2026.

**Sample:** reviews of at least 30 characters, 25 per app with seed 7.

**State:** `{"title": ..., "review": ...}`, with app names and their obvious variants replaced by `[app]`
(124 of 300 reviews contained one).

**Known issues:** masking uses a word list, so misspellings get through. One review spells Spotify
"Spodify". Product clues ("Reels", "streak", "Google") are kept on purpose: inferring the app from
what the reviewer describes is the task.
