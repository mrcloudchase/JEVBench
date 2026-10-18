# appstore_stars

**Question:** how many stars did the reviewer give? One `score` question with five levels, from "1
star, very dissatisfied" to "5 stars, very satisfied".

**Label:** the reviewer's own star rating, as a level index 0–4.

**Source:** Apple's public customer-review RSS feeds (`itunes.apple.com/us/rss/customerreviews/...
/sortby=mostrecent/json`), US store, reviews posted October 10–17, 2026.

**Sample:** reviews of at least 30 characters from Facebook, Instagram, TikTok, Uber, Spotify, Netflix,
Duolingo, Amazon Shopping, WhatsApp, Gmail, YouTube and Snapchat, 60 per star rating with seed 7.

**State:** `{"app": ..., "title": ..., "review": ...}`. Reviewer names are not kept.

**Known issues:** exact star ratings are noisy. A "3" review often reads like a 2 or a 4, so within-one
accuracy is reported alongside exact accuracy.
