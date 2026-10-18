# TDM benchmarks, leaderboards and public evaluation harnesses (state as of 2026-10-18)

Scope: every public benchmark, leaderboard or harness for typed decision models (TDMs: models that return distributions over typed Noul / Choice / Score questions), what each measures, how it controls contamination, current rankings, how each differs from our harness, and the "JevBench" name collision.

Our harness, for comparison: 6 TDMs (TypeSafe jev-1.13.0, OpenAI Decisions gpt-6-luna, DeepSeek V4.1 Flash via next-token logprobs, Von 1.3, OpenDecider nano, open-jev-deberta-v3-large). Fresh real-world data (Steam and App Store reviews created Oct 10-17, 2026). Metrics: accuracy, AUROC, Brier, ECE, repeat agreement, cost, latency, paired bootstrap deltas.

## Q1. Benchmark by benchmark: owner, launch, tasks, item counts, metrics, sealed design, contamination policy, top systems

### Takeaway
Seven public TDM evaluations exist. The dominant one is Benchmark Heaven's JevBench (fstandhartinger/jevbench, benchmarkheaven.com/jev-models). It is now board v1.7.46, with 1,500 decisions per system (1,200 sealed + 300 public), 183 systems and about 40 API rows, and it scores accuracy, calibration, cost and latency. The others are narrower: a label-free metamorphic coherence benchmark that is also called JevBench (Queen's University Belfast, 21 models), a StarCraft II game leaderboard at jevbench.dev (4 models), the community "Jev Decision Index" on Hugging Face (multimodalart), the Artificial Analysis Decision Index (launched Oct 13, 2026), the LocalLLaMA/typed-decisions dataset with its HF leaderboard, and the pavanjava Jev-vs-Laya harness. "jabr v2" is only a self-reported suite in model cards.

### Cited Findings

**A. JevBench by Benchmark Heaven (fstandhartinger/jevbench; benchmarkheaven.com/jev-models)**
- Owner: "Maintained by Benchmark Heaven, independently of TypeSafe AI". It is a one-person hobby project, and donations go to productivity-boost.com Betriebs UG (haftungsbeschränkt) & Co. KG. The harness and the 72 original public decisions are MIT-licensed. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- History: the earliest dated release is v1.1 (19 Sep 2026). v1.0 had 242 decisions (72 public, 24 held-out private, 146 imported). v1.1 had 314. v1.2 onward had 534 per system, with a hard tier of 220 items (111 public, 109 held out). v1.6.1 was "initially published 2026-10-06", with addenda a6-a12 on Oct 7-8. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- v1.4.2.2 (published Sep 27, 2026 per the jevmodel.org FAQ) used 842 decisions per system: 534 public (easy 72 / standard 96 / judge 146 / hard 220) and 308 sealed. Sealed chance level was 29.3%. 95 systems were listed and 91 ranked. — [jevmodel.org/jevbench](https://jevmodel.org/jevbench); counts confirmed by the [README](https://github.com/fstandhartinger/jevbench). jevmodel.org gives conflicting dates for the page itself ("updated September 28" in the header, "September 24" in the footer).
- Task families: request routing, answer-adequacy judging, policy yes/no checks, intent classification, ordinal severity scoring, enum extraction. All are English and short, and the README calls the cases hand-written. Each item declares its label set. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- Metrics: Intelligence is chance-corrected accuracy with a majority-class floor. The README also reports Calibration, schema validity, Brier, ECE, ordinal MAE, paraphrase consistency, p50/p95 latency and cost per 1,000 decisions. Capability Score (v1.6.1+) is the mean of Intelligence and Calibration, with caps of USD 0.0646 per 1k decisions and 1.23 s adjusted median latency. Composite Score is a weighted harmonic mean of Intelligence, Calibration, Speed and Cost (25% each, Intelligence floor 50). The v1.2 score used a geometric mean of the four axes, with Speed and Cost log-scaled. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- Current live board: "JevBench · board v1.7.46 · updated 2026-10-17". It lists "182 ranked open-weights systems · Jev 1.13.0 shown as reference · 1,500 decisions each" and "Show all 183 systems", including 131 Jev-class systems and about 40 API rows. "Jev-class" means at most 2× the cost and the median latency of Jev (v1.5 reference). Open-weights rows run on hardware Benchmark Heaven rents. Self-hosted latency is estimated as 2× measured on-GPU p50 + 150 ms. — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models) (page text retrieved 2026-10-18)
- Sealed/open design and equating. "Every draw shares the same 300 public items (P)". Each new draw is equated to the v1.6.1 reference scale (draw v1.6.0) with fixed anchor systems measured on both draws: offset = median over anchors of (metric on reference S∪P) − (metric on new draw S∪P), with a bootstrap 95% interval. — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Contamination controls for API models. Most API offerings were measured on 6 Oct 2026 on "a fresh sealed API set A4 (300 never-used sealed items) plus the same 300 public items" (offsets +2.57 Intelligence, +3.35 Calibration). "A4 is now retired for everyone." OpenAI Decisions (gpt-6-luna) then ran on a further fresh set A5 "since A4 had already been sent to OpenAI" (offsets +5.78 / +6.15). In other words, a sealed set counts as exposed once it has been sent to a provider. — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Stated contamination policy: "Training on the public split must be disclosed". The public half "can be trained on or selected against". A v1.2.15 exact normalized-text audit of a 79,116-row public training projection found no JevBench items. The README warns: "Not public is not the same as not seen, and this is not a contamination proof." — [GitHub README](https://github.com/fstandhartinger/jevbench)
- Exposure note: language supplement L3 items "were reviewed by an OpenAI model, so cells based on L3 carry that exposure; headline scores do not use L3." — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Current open-weights Capability top 5 (v1.7.46): 1 basal-omni-1.0-ultra (Remek Kinas, Gemma-4-31B-it + LoRA) at 82.5 (Intelligence 74.1, Calibration 91.0, $0.045/1k); 2 Quyet-1.0-Large at 81.7 (73.4 / 90.0); 3 Jeff-1.0-Large; 4 metask-jev-rain-31B-trained service v3; 5 decisio v0.8.0 on gemma-4-31B-it. The Jev 1.13.0 reference (unranked) scores Capability 77.1 (Intelligence 63.6, Calibration 90.6, $0.032/1k, 0.24 s). — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Earlier rankings, which the README says should not be compared across method versions. v1.4.2.2 Composite: Imajev-4B 67.37, Plumb-4B 65.84, decider-4b v2 64.13, Jev 1.13.0 63.29, JevK5 v0.2.0 62.04. v1.2: Jev 1.13.0 74.4, SemIf 73.1, djev 73.0, Winnow-12B Q8 71.2, reflex 4B 70.3. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- API board rows for our systems:
  - OpenAI Decisions (gpt-6-luna), v1.7.10 (2026-10-06): Composite 62.5 (95% interval 51.6–64.6), Capability 73.5, 598 of 600 answered, list price USD 0.10 per 1M input tokens.
  - Highest raw Capability, all outside the Jev-class caps: "GPT-6 Luna, Qwen3.8 27B, GPT-6 Luna low, DeepSeek Flash and GPT-5.6 Luna" at 98.4, 98.2, 97.8, 97.4 and 94.5. DeepSeek V4.1 Flash is listed as "API · A4+P+L1+L2+L3".
  - Liquid AI d1 (v1.7.8): Composite 73.0, Capability 74.4.

  — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Rows for our other systems:
  - open-jev-deberta-v3-large: Capability 35.4, Intelligence 2.8, Calibration 68.0, $0.0056/1k, measured p50 1.689 s on local CPU. It is outside Jev-class at 5.7× Jev latency and ranked #150 / #169 depending on view.
  - Von (wfzyx, Option-Marker 395M): only a historical v1.5.0 row (2026-09-28) with a score of 41.7 / 0.0 ("was #110 on v1.5.7"), $0.0038 estimate, 0.92 s. Language cells were re-measured with the original pinned setup in v1.7.37 (2026-10-10).
  - "OpenDecider" and "Von 1.3" do not appear anywhere in the board text.

  — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Von's "v1.5.1 live board, sealed + open halves" citation comes from issue #143. It reports Intelligence 0.0 on the board, which the author attributes to a Noul decision rule. Open / sealed results: Noul CC −78.6 / −98.0, Choice 34.4 / 17.9, Score 38.5 / 30.5. The author's own figures: public hard 0.378→0.441 (n=111, p=0.065) and "jabr v2 out-of-sample (n=869) 0.713". The author discloses that the chain library was tuned on the public hard items. The maintainer said claims would come only from Benchmark Heaven's own runs, and redirected submissions to benchmarkheaven.com/submit. The issue was opened Sep 28 and closed Oct 8, 2026. — [Issue #143](https://github.com/fstandhartinger/jevbench/issues/143)
- Show HN, "JevBench, a reproducible benchmark for typed decision models", by florianstandhar: 154 points, 39 comments. At posting it had 534 decisions and v1.3 scoring, led by Jev 74.4, SemIf 73.1 and djev 73.0. Critiques raised in the thread:
  - narrow text tasks (vessenes)
  - tuning to the 534 public questions (adityamishra241)
  - the maintainer conceding that "sending our private held-out set of tasks to an external API produces some headaches", so the set must be rotated
  - TypeSafe being "openly against public benchmarks" (tomrod, arbot360)
  - mismatches with another leaderboard (sean_pedersen)

  — [HN 49800574](https://news.ycombinator.com/item?id=49800574); a Spanish aggregator headlines it "JevBench v1.3.0: Jev 1.13.0 lidera entre 52 modelos" — [zeli.app](https://zeli.app/es/story/49800574)
- Benchmark Heaven also runs sibling boards "ImageJevBench v0.3.0" and "AudioJevBench". — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Mirrors and aggregators of Benchmark Heaven's JevBench: jevmodel.org, which is independent and "not affiliated with ... TypeSafe AI" — [jevmodel.org/jevbench](https://jevmodel.org/jevbench). Also [llmreference.com/benchmark/jevbench](https://www.llmreference.com/benchmark/jevbench) and [benchlm.ai/benchmarks/jevbench](https://benchlm.ai/benchmarks/jevbench), both surfaced in search but not fetched.

**B. JevBench, metamorphic coherence (jevbench.github.io; GitHub org JevBench; PyPI `jevbench`)**
- Owner: Chen Feng, ML Lab, Queen's University Belfast (c.feng@qub.ac.uk). Apache-2.0. Technical report "v0.1 · October 2026", titled "JevBench: Metamorphic Coherence Testing for Typed Probabilistic Decision Models". — [jevbench.github.io](https://jevbench.github.io); [technical report PDF](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- PyPI package `jevbench` 0.1.0, first uploaded 2026-10-01T21:36, author Chen Feng. — [PyPI JSON](https://pypi.org/pypi/jevbench/json)
- Design: 50 metamorphic relations, each a single law of probability or choice theory, grouped into 5 dimensions: representation, batch independence, probability measure, logical order, choice-set conditioning. Only the question is transformed, never the input. Tests are frozen in advance. There are 240 synthetic cases in 12 domains, giving 12,000 tests (JevBench-240). The reported subset is JevBench-mini (1,200 tests), which matches the full ranking at Spearman 0.983. A test passes within a tolerance of 0.05 probability units. No gold labels are needed for coherence. Accuracy is reported alongside, using rule-based gold annotations from "fact-first" generated cases. — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- Results: 21 openly released models with coherence from 56.5 to 83.9. A uniform input-ignoring reference model scores 89.4, which is above every tested model, at chance accuracy. Decoder accuracy varies little (82.4–89.2%) while coherence varies widely (64.2–83.9). Additivity, especially the complement law, "fails broadly". — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- Leaderboard (jevbench-mini, version 0.1.0, coherence % with 95% CI, then accuracy %):
  - open-jev-9b: 83.9 [82.5, 85.2], accuracy 88.4
  - jevany-gemma-4b: 81.2, 87.6
  - jevany-qwen-4b: 79.4, 88.8
  - decider-4b: 78.4, 88.6
  - jevany-qwen-4b-direct: 77.8
  - tinyjev-4b: 77.3
  - jebadiah-9b: 76.9, 89.1
  - von: 75.9, 72.2
  - jevk5-4b: 72.8
  - onejev-4b: 72.5, 89.2
  - laya-typed: 63.9
  - laya: 56.5 (last)

  Closed APIs (Jev, gpt-6-luna) are not listed. — [leaderboard.json](https://jevbench.github.io/data/leaderboard.json)
- The report says it is "not affiliated with any provider of the interface; 'Jev' only names it" (POST /v1/systemone). It defines Noul, Choice and Score. Neither its abstract nor its related-work section mentions Benchmark Heaven's JevBench. — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- Benchmark Heaven's README disambiguates: the metamorphic coherence benchmark at jevbench.github.io is "a separate project; its consistency scores measure a different property." — [GitHub README](https://github.com/fstandhartinger/jevbench)
- Held-out or contamination policy: the site doesn't mention one. The tests are frozen and public. — [jevbench.github.io](https://jevbench.github.io)

**C. jevbench.dev (game-based leaderboard)**
- Runs StarCraft II arenas, with "Liberation Day" live and two arenas in total. Game state is turned into a list of legal moves, the model picks one, and runs are verified against the game objective, with "no self-reported scores". Totals: 24 verified wins across 105 published runs and 12,901 scored decisions. TypeSafe Jev 1.13 is #1 with an 84% win rate. 4 models are ranked. The page was updated 25 Sep 2026. It links rapidstartup/jev-plays-starcraft-2 and X @lifeonautosite, and names no team. The footer reads "© 2026 JevBench · jevbench.dev". There is no contamination policy. — [jevbench.dev](https://jevbench.dev)

**D. Jev Decision Index (community, Hugging Face Space multimodalart/jev-decision-index)**
- Run by Apolinário (multimodalart) on HF. The Space has 712 likes, but its content did not render when fetched. — [HF Space](https://huggingface.co/spaces/multimodalart/jev-decision-index)
- Headline metric is "balanced skill", which "chance-corrects each benchmark so random guessing is 0 and perfect is 100". The areas are Knowledge, Language, Retrieval, Tools and Arts. The live Space edition is 0.3.2 as of 2026-10-15, and the page edition is 0.2.1. Vendor-reported scores: SubQ Snap 61.7 (not on the Space board file), Surogate Rune 26B-A4B 57.4, pplx-decider-v1-27b 56.4, d1-3B 48.6, d1-omni-600M 15.9. — [llmreference.com Decision Index](https://www.llmreference.com/benchmark/decision-index)
- A Korean write-up reports Decision Index 0.2.1 scores of Jev 57.91, Surogate Rune 26B-A4B v3 57.44 and Decider chat 57.33. Vendor-reported Fastino GLiDE is 64.81 but is not on the board. — [discuss.pytorch.kr](https://discuss.pytorch.kr/t/jev-decision-index-jevbench/12095.md) (search snippet only)
- Coverage figures conflict across secondary sources: "132,422 requests across 37 benchmarks", "70 models on 38 benchmarks" and "ranks 30+ open-weight decision models". House rules reportedly ban prompt tuning, truncation and option filtering (search snippets only, unverified). — [aiweekly.co](https://aiweekly.co/alerts/jev-decision-index-ranks-30-open-weight-decision-models)
- Benchmark Heaven imported the top 20 of this index into its own sealed pool (v1.7.11, 2026-10-07). — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)

**E. Artificial Analysis Decision Index (artificialanalysis.ai), a distinct project**
- v1.0 launched October 13, 2026, as an equal-weighted composite of 4 evaluations at 25% each:
  - AA-Omniscience-Decision: 500 private questions with 5 options, including "I don't know". Its 25% is split into accuracy 12.5% and non-hallucination rate 12.5%.
  - HLE-MultiChoice: 513 text-only questions.
  - When2Call (NVIDIA): answer directly, call a tool, ask, or decline.
  - WildGuardTest (Ai2), scored by average F1.

  Calibration compares the probability of the chosen answer with accuracy in bins of 0.1 with at least 20 answers per bin. Cost per million tasks and median time per task are also reported. — [AA evaluations page](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index); [AA launch article](https://artificialanalysis.ai/articles/artificial-analysis-decision-index)
- The calibration chart names Celeris-1 Decision, Clef, Clef-OmniG, GLiDE, Mercury Decided, 1d1-ultra, GPT-6 Luna (Decisions), Microsoft-Decision-1, Decider v1.1 27B and Jev 1.14. Numeric ranks were not retrievable, and DeepSeek V4.1 Flash and Von are not on the page. — [AA evaluations page](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index)
- A secondary news item headlines "Decision Index shows Jev beats Claude Haiku 5.5 at 11x speed" (not fetched). — [hermes-ai.net](https://hermes-ai.net/news/artificial-analysis-decision-index-shows-jev-beats-claude-haiku-5-5-at-11x-speed/)

**F. LocalLLaMA/typed-decisions (HF dataset + "Official Benchmark" leaderboard)**
- Apache-2.0, tagged synthetic, English. Four workflows of 400 rows each: agent_trace_observability, customer_service, invoice_processing, security_incidents. Train/test is 300/100 per subset, which gives 1,600 cases (1,200 train, 400 test). The leaderboard metric is accuracy. Top entries: FINAL-Bench/Darwin-27B-ZTC-v5 0.81, Darwin-27B-ZTC 0.74, empiriolabsai/aplomb-1 0.74, openjev/openjev 0.73, ProKope-421M-8K 0.72. — [HF dataset](https://huggingface.co/datasets/LocalLLaMA/typed-decisions)
- Gold labels are "the mean of three teacher-model samples". Each case has 5 typed questions, for 8,000 decisions per model. — [pavanjava harness](https://github.com/pavanjava/jev_and_laya_benchmarking)
- Vendor blog: on "TypeSafe's typed-decisions benchmark", zero-shot Laya scores 0.362 against Jev 0.727, a majority baseline of 0.461 and random 0.318. On Banking77, Laya scores 0.425 against Jev 0.870. — [orcarouter.ai](https://www.orcarouter.ai/blog/jev-vs-laya). The blog calls it "TypeSafe's" benchmark while HF hosts it under the LocalLLaMA org, so its provenance is unclear.

**G. Jev-vs-Laya harness (github.com/pavanjava/jev_and_laya_benchmarking)**
- Compares Jev (TypeSafe API) with Laya (convaiinnovations/laya, typed-decisions weights, run on M1 Pro CPU) on the typed-decisions test split (400 cases). Accuracy: Laya 0.766 vs Jev 0.734, a +3.2 point gap with a 95% bootstrap CI of +1.1 to +5.5. p50 latency: Laya 484 ms vs Jev 756 ms. Calibration (Brier, ECE, KL) and cost are not computed. Laya was fine-tuned on the train split, scoring 0.854 on train vs 0.766 on test. — [GitHub](https://github.com/pavanjava/jev_and_laya_benchmarking)
- Commentary: Wavect reports Laya ECE 0.213 vs Jev 0.144, and calls its piece "a review of public sources, not a benchmark we ran." — [wavect.io](https://wavect.io/blog/laya-vs-jev-benchmark-ai-startup-moat/). OrcaRouter is a vendor blog that reports Laya at 32.8 ms p50 on a T4 against Jev's hosted 236–276 ms. — [orcarouter.ai](https://www.orcarouter.ai/blog/jev-vs-laya)

**H. "jabr v2" (self-reported only)**
- Described on a model card as a suite of "49 diverse classification, policy routing, Boolean verification (noul), and ordinal rubric scoring (score) tasks". The card's jabr v1 result is 79.75%. — [HF MiniCPM5-2B-Jev](https://huggingface.co/ytbai/MiniCPM5-2B-Jev)
- Von's author cites "jabr v2 out-of-sample (n=869) 0.713". — [Issue #143](https://github.com/fstandhartinger/jevbench/issues/143)

### Inferences
- Benchmark Heaven's JevBench is the closest analogue to our harness. Both are multi-system, measure accuracy, calibration, cost and latency, and include gpt-6-luna, DeepSeek V4.1 Flash, open-jev-deberta-v3-large and (historically) Von. Our paper should cross-reference its numbers for the overlapping systems.
- Benchmark Heaven ranks by composite or capped scores over synthetic hand-written items. We instead report per-metric results (AUROC, Brier, ECE, repeat agreement) with paired bootstrap deltas on real user-generated text. Benchmark Heaven does not report AUROC or repeat agreement. The closest it has are "paraphrase consistency" and its note that some engines' "answers to the same public items differ between machines for about 10% of items".
- OpenDecider nano and Von 1.3 have no third-party measurement on any board found. Our numbers for them would be the first independent ones.

### Gaps
- No ranked numeric scores for the AA Decision Index could be retrieved. The page is JS-rendered and shows only a calibration chart list.
- The HF Jev Decision Index Space did not render. Its scores come only from secondary aggregators, which disagree on version (0.2.1 vs 0.3.2) and coverage (37 vs 38 benchmarks, 30+ vs 70 models).
- The preprint at preprints.org/manuscript/202610.0181, which describes "an open evaluation framework... across 12 slices", returned 403. Its authors and contents are unverified.
- Arize's "Decision model benchmark: Jev, Kev, Liquid d1, and more" ([arize.com](https://arize.com/?p=32807)) and benchlm.ai/decision-models surfaced in search but were not fetched.
- No besthub.dev Laya-vs-Jev post was found by search.
- Who maintains jabr v2 is not known.
- The Show HN absolute date was not shown. The page said "25 days" before capture, which implies roughly Sep 23, 2026 (unconfirmed).

## Q2. Does any benchmark evaluate decisions (thresholds, abstention, costs, coverage, selective accuracy) or architectures (cascades, ensembles), rather than only beliefs/answers?

### Takeaway
No. None of the benchmarks found evaluates decision policies, meaning thresholding, abstention against a cost, risk-coverage or selective accuracy, and none evaluates cascades or ensembles as systems. All of them score beliefs: argmax accuracy, chance-corrected accuracy, calibration and coherence. They treat cost and latency only as per-model axes or caps, and they count abstentions as failures.

### Cited Findings
- Benchmark Heaven counts abstentions as unanswered: for one engine, "The engine abstains on about 30 % of items and returns invalid UTF-8 on about 7 %... both count as unanswered." — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Benchmark Heaven's nearest cost-aware feature is a Pareto frontier of Capability vs cost per 1,000 decisions and vs median latency (v1.7.43, 2026-10-10, display only). There is also a GPU-cost "What-If" calculator that "never changes a score or rank". — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Benchmark Heaven lists wrappers but doesn't rank them. "classifier.dev (fast tier) is listed as a wrapper, not ranked" because its fast tier "is Jev". It is the only system-architecture-like entry, and it is excluded rather than evaluated. — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models); [README](https://github.com/fstandhartinger/jevbench)
- Von's author changed a Noul "decision rule" so that every answer commits instead of abstaining. This raised Noul accuracy on jabr, and the author expected worse calibration. Benchmark Heaven's Intelligence of 0.0 for Von was attributed to that rule. This is an example of decision policy confounding a belief benchmark. — [Issue #143](https://github.com/fstandhartinger/jevbench/issues/143)
- AA Decision Index has an abstention-like component. AA-Omniscience-Decision includes an "I don't know" option and scores a non-hallucination rate at 12.5% weight. When2Call scores the choice between answering, calling a tool, asking or declining. Both treat abstaining as one more option to classify, not as a threshold policy scored against costs. — [AA evaluations page](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index)
- The coherence benchmark includes a `threshold_sweep` relation. It tests monotonicity of probabilities across thresholds, which is a coherence law, not decision utility. Its motivation section notes that "a moderation pipeline thresholds the probability of a violation". — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf); [leaderboard.json](https://jevbench.github.io/data/leaderboard.json)
- The Jev-vs-Laya harness uses only the top answer, "with no confidence thresholds, abstention rules, or decision-cost analysis." — [GitHub](https://github.com/pavanjava/jev_and_laya_benchmarking)
- An HN commenter (pushpendraw) raised the decision-relevant point that "confident and wrong is worse than an LLM that just hedges", but the benchmark does not operationalise it. — [HN 49800574](https://news.ycombinator.com/item?id=49800574)

### Inferences
- If our paper adds decision-level evaluation (thresholds, abstention and cost-coverage curves, selective accuracy, or cascade/ensemble policies built from the six TDMs' beliefs), that would be a clear gap no existing TDM benchmark fills. As specified, our metric list (accuracy, AUROC, Brier, ECE) is still belief-level. AUROC is threshold-free, and it is the one metric we have that no TDM board reports.

### Gaps
- I could not verify whether the AA Decision Index, Arize's write-up or the HF Decision Index report selective accuracy or coverage curves, since their pages were not fully retrievable.

## Q3. Does any benchmark use fresh, post-release data to rule out training contamination?

### Takeaway
Not in the sense we mean. Benchmark Heaven uses fresh sealed draws: never-used items that it retires once sent to a provider, such as A4 and A5, drawn and reviewed on 6 Oct 2026. Those items are authored or synthetic decision prompts, though, not naturally occurring data created after the models were released. The coherence benchmark and typed-decisions are frozen synthetic sets. No benchmark found uses timestamped real-world text created after the models' release, as our Oct 10-17, 2026 Steam and App Store reviews are.

### Cited Findings
- Benchmark Heaven: "a fresh sealed API set A4 (300 never-used sealed items)". "A4 is now retired for everyone". gpt-6-luna used A5 "since A4 had already been sent to OpenAI". The language and use-case supplements (354 + 33 items) were "drawn and reviewed on 6 Oct 2026". — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models)
- Benchmark Heaven's own limits: "Not public is not the same as not seen, and this is not a contamination proof". The private part "will need to evolve as the field changes". The held-out split is sent to the evaluated services. Items are "short hand-written cases", in English only. — [GitHub README](https://github.com/fstandhartinger/jevbench)
- Coherence JevBench uses 240 synthetic cases "generated fact-first" and frozen in advance. Its tests are public. — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- typed-decisions is tagged synthetic, with gold labels taken from a teacher-model mean, and has a public train split that Laya was fine-tuned on. — [HF dataset](https://huggingface.co/datasets/LocalLLaMA/typed-decisions); [pavanjava harness](https://github.com/pavanjava/jev_and_laya_benchmarking)
- AA-Omniscience-Decision is a private set adapted from AA-Omniscience. HLE-MultiChoice, When2Call and WildGuardTest are adaptations of pre-existing public benchmarks. — [AA evaluations page](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index)
- jevbench.dev's StarCraft II arena generates states live per run. That gives procedural freshness, but the page states no contamination policy. — [jevbench.dev](https://jevbench.dev)

### Inferences
- Our use of reviews created Oct 10-17, 2026, after the Jev 1.13.0, gpt-6-luna (Decisions API opened 6 Oct 2026) and Von 1.3 releases, is a distinctive contribution. It rules out item-level memorisation by construction. Benchmark Heaven's rotation only rules out exposure to its own earlier draws.
- This needs one caveat. Fresh text does not rule out a model having seen near-duplicate reviews of the same apps or games, and gpt-6-luna's release came only days before our data window. We should state per-model release dates against the data creation dates.

### Gaps
- Exact release dates for DeepSeek V4.1 Flash, OpenDecider nano and open-jev-deberta-v3-large were not checked in this sweep.

## Q4. Which "JevBench" is most prominent, is the name trademarked or claimed, and what alternatives avoid collision?

### Takeaway
At least three unrelated projects use "JevBench". Benchmark Heaven's is by far the most prominent: a Show HN with 154 points, cited in model cards such as Von's, mirrored by jevmodel.org, llmreference and benchlm, and covering 183 systems with sibling boards ImageJevBench and AudioJevBench. Queen's University Belfast's coherence JevBench owns the GitHub org `JevBench` and the PyPI name `jevbench`. A third party holds jevbench.dev. I found no trademark registration for "JevBench" or "Jev". "Jev" is TypeSafe AI's product name, so any Jev-derived name implies a vendor association. We should rename to a vendor-neutral name.

### Cited Findings
- Benchmark Heaven: Show HN with 154 points and 39 comments — [HN 49800574](https://news.ycombinator.com/item?id=49800574). 183 systems on board v1.7.46, plus sibling boards ImageJevBench v0.3.0 and AudioJevBench — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models). Model authors file bench requests against it — [Issue #143](https://github.com/fstandhartinger/jevbench/issues/143). Mirrored by an independent guide site — [jevmodel.org/jevbench](https://jevmodel.org/jevbench).
- Coherence JevBench: GitHub org JevBench (github.com/JevBench/jevbench), the jevbench.github.io site, PyPI `jevbench` 0.1.0 (uploaded 2026-10-01), technical report v0.1, and 21 models. — [jevbench.github.io](https://jevbench.github.io); [PyPI](https://pypi.org/pypi/jevbench/json)
- jevbench.dev: "© 2026 JevBench · jevbench.dev", with 4 ranked models. — [jevbench.dev](https://jevbench.dev)
- Benchmark Heaven explicitly disambiguates itself from the coherence project. It calls itself "independent of TypeSafe AI" and says "Jev is TypeSafe AI's decision model; JevBench also evaluates Jev-compatible systems." — [GitHub README](https://github.com/fstandhartinger/jevbench)
- The coherence report uses "Jev" as the name of the wire interface (POST /v1/systemone) and disclaims affiliation with any provider. — [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)
- Jev is TypeSafe AI's first "System One" model, released Sep 15, 2026 in early access. TypeSafe has $40M in funding. — [The New Stack](https://thenewstack.io/typesafe-jev-system-one/)
- No trademark filing or registration for "JevBench" or "Jev" was found in web results. A search of USPTO, EUIPO and WIPO databases directly would be needed to confirm. — [web search, no results]; see [The New Stack](https://thenewstack.io/typesafe-jev-system-one/) and [llmreference Jev](https://www.llmreference.com/model/jev/typesafe-ai) for product-only coverage
- Benchmark Heaven calls the systems it ranks "Jev-class" and "Jev-compatible", and the coherence report calls the interface "Jev". The ecosystem therefore treats "Jev" as both a vendor product and a de facto interface name. — [benchmarkheaven.com/jev-models](https://benchmarkheaven.com/jev-models); [technical report](https://jevbench.github.io/report/JevBench-technical-report.pdf)

### Inferences
- Our repo name "JEVBench" differs only in case from three existing projects. A reader or reviewer citing "JevBench" will default to Benchmark Heaven's. The PyPI name `jevbench` and the GitHub org `JevBench` are already taken, so publishing a package or org under that name is blocked anyway.
- Even without a registered trademark, putting "Jev" (a funded company's product name) in a benchmark name suggests the benchmark is centred on or endorsed by TypeSafe AI. This is a problem for a paper that compares six vendors' TDMs.
- Vendor-neutral alternatives that signal what makes our work different (fresh post-release data and typed beliefs). None of these was collision-checked, so check GitHub, PyPI, HF and domains before adopting one:
  - "FreshTDM" or "TDM-Fresh"
  - "PostCutoff-TDM"
  - "TypedBeliefs" or "TypedBeliefBench"
  - "ReviewTDM" (Steam and App Store sources)
  - "BeliefCheck-TDM"
  - "DecisionDrift"

  "TDMBench" is generic and may collide with "TDM" (text and data mining) usage.

### Gaps
- I did not check USPTO, EUIPO or WIPO directly. Trademark status is unknown, not confirmed absent.
- jevbench.com and jevbench.org ownership was not determined. A HEAD request to jevbench.org failed (proxy 502), and the jevbench.com result was ambiguous.
- GitHub star counts and creation dates for the three repos could not be retrieved, because the GitHub API was not enabled for this session's repo scope. The prominence comparison therefore rests on HN points, system counts and citations, not stars.
