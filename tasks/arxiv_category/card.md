# arxiv_category

**Question:** which arXiv category is this paper's primary category? One `choice` question over twelve
categories from eight archives, with each category's official name and scope as its description.

**Label:** the primary category the authors chose at submission.

**Source:** the arXiv API (`export.arxiv.org/api/query`), newest submissions per category.

**Legal basis:** arXiv's API terms: "You are free to use descriptive metadata about arXiv e-prints under the
terms of the Creative Commons Universal (CC0 1.0)". Only titles and abstracts are used, never full
text. The build makes one request at a time, 3 seconds apart, as the terms ask. The text is committed.

**Window:** first versions submitted September 28 – October 15, 2026. The API had indexed submissions
through October 15 when the task was built.

**Sample:** up to 100 per category with seed 7 (all 59 of q-bio.NC and all 50 of econ.GN), 1,109 papers,
drawn from the new primary submissions in the window:

| Category | Primary submissions in the window |
|---|---|
| cs.CV | 2,306 |
| quant-ph | 1,432 |
| cs.RO | 1,394 |
| cs.CL | 1,393 |
| cs.CR | 630 |
| math.NT | 427 |
| cond-mat.mtrl-sci | 399 |
| math.PR | 375 |
| astro-ph.GA | 320 |
| stat.ME | 299 |
| q-bio.NC | 59 |
| econ.GN | 50 |

463 of the 1,109 papers are cross-listed elsewhere. Their other categories are in `cross_lists` in the manifest.

**State:** `{"title": ..., "abstract": ...}`.

**Known issues:** categories overlap, for example cs.CL and cs.CV for multimodal work, so the top-1 label is
sometimes debatable. Probability-based metrics (Brier score, calibration) and the cross-lists help here.
The pool is large enough for a much bigger task if balance across categories is relaxed.
