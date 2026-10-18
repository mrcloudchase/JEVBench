# steam_recommend

**Question:** does the reviewer recommend the game? One `noul` question: "The reviewer recommends the game".

**Label:** 1 when the reviewer pressed "Recommended", 0 for "Not Recommended". It is their own verdict,
given with the review.

**Source:** Steam's public review endpoint (`store.steampowered.com/appreviews/<appid>`), most recent
English reviews, keeping reviews created October 10–17, 2026 (UTC).

**Sample:** reviews of 50–1,500 characters from Counter-Strike 2, Dota 2, Baldur's Gate 3, Cyberpunk
2077, Apex Legends, Elden Ring, Helldivers 2, Rust and Grand Theft Auto V. PUBG was queried but had no
reviews in the window. The pool held 1,786 recommended and 619 not recommended reviews; 150 of each were
drawn with seed 7.

**State:** `{"game": ..., "review": ...}`. Reviewer identities are not kept.

**Known issues:** Steam masks profanity with "♥" characters. Some reviews are sarcastic, a known hard case
for sentiment.
