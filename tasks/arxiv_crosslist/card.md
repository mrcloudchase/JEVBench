# arxiv_crosslist

**Question:** did the authors also list this paper in Machine Learning (cs.LG)? One `noul` question.

**Label:** 1 when cs.LG is among the paper's arXiv categories (a cross-list the authors chose), else 0.

**Source, legal basis and window:** as for [`arxiv_category`](../arxiv_category/card.md): arXiv API, titles and
abstracts under CC0, first versions dated September 28 – October 15, 2026.

**Sample:** primary categories cs.CL, cs.CV, cs.RO and cs.CR. In the window, 780 of 5,723 such papers were
cross-listed to cs.LG. 150 cross-listed and 150 not with seed 7, split 38, 38, 37 and 37 across the four
primary categories, so the primary category carries no clue. Each record's full category list is in the manifest.

**State:** `{"title": ..., "abstract": ...}`.

**Known issues:** cross-listing is a choice, not a fact about the paper: two similar papers can differ. This task
measures how well a model predicts that choice, so calibration matters more than accuracy here.
