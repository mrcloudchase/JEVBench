# TDM Evaluation Literature on arXiv, 15 Sep - 18 Oct 2026 (evaluation, benchmarking, audit, robustness and bias papers)

Method note (for the report writer): the corpus was built with arXiv API queries run on 18 Oct 2026 (`all:jev`, abstract searches for "typed decision", "typed decisions", "System One", "System-1"+decision, TypeSafe, "Decisions API", noul, Laya, StartLux, OpenDecider, Von, `ti:"decision model"`). An arXiv web search sorted by announcement date was used as a cross-check. The searches returned about 190 papers dated after 15 Sep that mention Jev or TDMs. About 85 of them are evaluation, benchmark, audit, robustness or bias papers, and those are catalogued below. Papers that introduce models or training methods, and pure application papers, are out of scope (another researcher covers them). They appear only by name in Gaps. Full HTML texts were downloaded and searched for 41 papers: the audit, the six named starting points, and the papers most relevant to decision rules and composition. The rest are summarized from their arXiv abstracts. Dates are v1 submission dates from the arXiv API. The newest record any query returned is dated 15 Oct 2026, so papers from 16-18 Oct may not be indexed yet.

## Q1. Which evaluation papers exist, and what does each claim (title, authors, arXiv id, date, key numbers)?

### Takeaway
The literature is large and fast-moving. The audit (2609.32160) reviewed 28 papers from 19-24 Sep, and I found about 55 more evaluation papers from 25 Sep to 15 Oct. The consensus finding: TDMs win clearly on latency and cost. They show no accuracy advantage that can be attributed to the typed readout itself. They trail frontier LLMs on harder, multi-step, numeric and long-horizon tasks. Their reliability problems are well documented: label and definition effects, option-set dependence, order bias, yes/no swaps, incoherence, and context and injection attacks.

### Cited Findings

**A. The audit and its 28-paper corpus (19-24 Sep 2026).** The full list was identified from the audit's Appendix A, Table 7.
- Audit: "Typed Decision Models: An Early Evidence Audit and Evaluation Checklist", Lijuan Tang and Yuemeng Zheng (Northeastern), 2609.32160, 26 Sep 2026. It reviews 28 papers posted 19-24 Sep. Its main finding: "the typed readout itself has not shown an independent accuracy advantage over comparable label-probability readouts. Jev's clearest gains are in latency and cost, while accuracy gaps remain on harder tasks." It derives a 14-item checklist. Corpus search: the arXiv API query `all:jev` plus abstract searches for "typed decision model", "decision model", "System One model" and "TypeSafe", run 24-25 Sep. 29 hits; one excluded. 22 papers evaluate hosted Jev, five build open or alternative TDMs, and one analyzes GitHub projects — [Audit](https://arxiv.org/abs/2609.32160); [HTML](https://arxiv.org/html/2609.32160)
- The audit's six findings: (1) no independent typed-readout accuracy advantage: 21 of 27 model-evaluating papers include no label-probability baseline. (2) Reported parity often comes from saturated tests (100/100 on 20 scientific choices; 63/63 contract checks; 212-216/216 intents). (3) Latency and cost gains are substantial but depend on context; caching cut one paper's latency advantage to under 1 ms. (4) Calibration must be evaluated per model and per workload. (5) Confidence-based escalation is a recurring deployment pattern. (6) Reporting practices vary: 12 of 27 report no CIs or significance tests, and at least 7 made choices after seeing results — [Audit](https://arxiv.org/html/2609.32160)
- The 28 corpus papers (arXiv id, first author, short title, audit headline):
  - 2609.22753, Li et al., Replacing LLMs with Jev for low-latency edge service orchestration: 212-214 vs 215-216 of 216 vs DeepSeek V4.1 Flash; 16-27% lower median latency, under 1 ms gap once cached; 69-73% lower cost.
  - 2609.23136, Li et al., Fast intent-driven orchestration for 6G (v2 retitled "Intent Interpretation at RIC Timescales: Jev Decision Models versus LLMs in 6G Open RAN"): 63/63 at ceiling; most of the completion gain comes from caching and a numerical scheduler (Jev rises from 43% to 96%).
  - 2609.23886, Cheng et al., this-that-model-1.0 (an open 1.88B TDM; a model paper, but in the corpus).
  - 2609.23959, Ren et al., Open-Jev on CallScreenBench: typed AUROC .974 vs .950 for a same-backbone label-token readout (n.s.).
  - 2609.23986, Jiang et al., Jev-Mem (memory controller).
  - 2609.24052, Rafe and Das, crash narratives with Jev: F1 .908 vs .967 for Claude Fable 5.1; calibration slope 1.63; recalibration cuts error 3.3x.
  - 2609.24395, Robitza, JEVQA video quality: PLCC .797 after input redesigns vs .96 for a trained model.
  - 2609.24574, Ibrahim and Zaki, decision models for computational social science annotation: Jev trails the per-task best of 19 LLMs by a median 11.6 macro-F1 and is behind on 14 of 15 tasks.
  - 2609.24965, Deng et al., Jev for scientific decisions: 100/100 on 20 items.
  - 2609.25498, Dağlı et al., Universal Fractal decision map (self-reported).
  - 2609.25845, Yu and Yao, Visual Jev: a typed head equals the LM head (.761 vs .761).
  - 2609.26532, Wu and Lim, REFLEX selective control: the TDM cascade is not more accurate than a cheap generative cascade on the external benchmark.
  - 2609.26550, Li et al., JEV-as-a-Judge (accept when confident, escalate when unsure): a frozen cascade scores 92.5 vs 93.1 for GPT-6 at 57% of the fee.
  - 2609.26758, Sun et al., "Type-Safe Is Not Error-Free" (v3 title: "Typed Decision Models Follow the Option Name, Not the Definition Bound to It"): a no/yes polarity swap moves Jev AUC from .815 to .581.
  - 2609.27331, Ma et al., JEV-Star (StarCraft II).
  - 2609.27535, Li, KITE population experiments.
  - 2609.27607, Huang et al., Jev judging radiology reports.
  - 2609.27678, Zhang et al., "Same Scores, Different Decisions" (legal): 77.4% vs 83.2% for Gemini 3.1 Pro.
  - 2609.28587, Ye et al., NumericJev: threshold probabilities are non-monotone in 25 of 48 query groups.
  - 2609.28613, Wu and Lim, Decision Hijacking (prompt injection): attack success rises from 1.8% to 3.5% under adaptive attack.
  - 2609.28919, Abbasi et al., routing coding agents (v2 retitled "Harness Tokenomics").
  - 2609.28940, dos Santos Barbosa, JEV and Laya for pentest harnesses.
  - 2609.29283, Zhou et al., PixelJev.
  - 2609.29429, Guo et al., "Just Ask Jev" (alignment-failure detection): pooled ECE .047 but median per-benchmark ECE .168.
  - 2609.29769, Rao and Callison-Burch, rubric judges.
  - 2609.30186, Zhang, Jev-Mobile.
  - 2609.30216, Ling et al., Jev in the Wild (ecosystem study).
  - 2609.30243, Xu, JevOut: optimized answer-preserving context flips 61.4% of correct decisions.
  - Source for all of the above: [Audit Tables 4, 5 and 7](https://arxiv.org/html/2609.32160)
- The audit also cites two concurrent GitHub-only working drafts: Luo, "Jev and Typed Decision Models: An Empirical Survey of Calibration, Selective Control, and Open Implementations" (github.com/Eurekaleo/awesome-jev-survey, v0.2.0, data cutoff 24 Sep), and Anonymous, "Decisions, Not Tokens: A Survey of ... Decision Models from Classical Classifiers to Jev" (github.com/youzizzz1028/Awesome-Jev, 21 Sep) — [Audit](https://arxiv.org/html/2609.32160)

**B. The six named starting points (verified).**
- 2609.29769, Delip Rao and Chris Callison-Burch, 24 Sep. v1 title: "JEV vs. LLMs as Rubric Judges: Cheaper, Faster, and Wrong in the Same Places"; v3 title: "Decision Models vs. LLMs as Rubric Judges: Cheaper, Faster, and Wrong in the Same Places". Later versions add Perplexity's Decider (v1.1, released 5 Oct, an open-weight fine-tune of Qwen3.8-27B served through Perplexity's Decisions API at $0.02/M input tokens). Per the audit: Jev differs from three flash-tier LLM judges in 8 of 27 comparisons (4 ahead, 4 behind, up to 16.4 points behind on graded criteria); it is 30-220x faster and 29-325x cheaper; confidence ranks errors only weakly (AUROC 0.57-0.70); LLM judges repeat Jev's wrong answer in 96% of verdicts on its most confident errors; a replayed cross-fitted cascade gains at most 1.5 points (2.0 with oracle thresholds); asking through Score instead of Choice moves graded accuracy by up to 10.5 points — [arXiv](https://arxiv.org/abs/2609.29769); [Audit](https://arxiv.org/html/2609.32160)
- 2610.00346, Amir Rafe and Subasish Das, 29 Sep, "Benchmarking System One decision models against trained classifiers and language models for automated decision gates". Eight decision-model checkpoints from six families, including Jev, plus four open generative models. A fine-tuned DeBERTa-v3-large is most accurate on every labeled benchmark but one. Without labels, no decision model is significantly better than Jev. A guaranteed 5% risk leaves Jev 0.528 coverage on intents, and an in-scope threshold still accepts 0.310 of out-of-scope requests. Swapping yes and no flips 50.5 of every 100 Jev answers, at least 16.8 for every generative model, and at most 6.5 for four fine-tuned decision checkpoints. Training-data exposure explains the largest open-checkpoint lead. An intent-trained first stage escalating to Gemma-4-31B reaches Gemma's accuracy at roughly Jev's price — [arXiv](https://arxiv.org/abs/2610.00346)
- 2610.18122, Fabian Lukassen, Christoph Weisser and Alexander Silbersdorff, 13 Oct, "Cheap, Consistent, Calibrated, but Biased? Typed Decision Models as Judges". They run CALM's 12 bias tests on 8 TDMs and 7 LLM judges. Every TDM is biased in 3-8 of 12 tests. Emotional-tone rewriting drops a typical TDM from 99% to 42%. All eight TDMs show position bias, which the 2026 LLM judges hardly do. Bias mostly flips verdicts the TDM was unsure of, and "good calibration does not protect against bias". TDMs are 37x cheaper — [arXiv](https://arxiv.org/abs/2610.18122)
- 2610.02586, Seyedarmin Azizi, Erfan Baghaei Potraghloo and Massoud Pedram, 1 Oct, "Labels Override Definitions in Jev-Style Typed Decision Models". Deleting every definition leaves laya-td accuracy unchanged (0.8559 vs 0.8487), and renaming options to A/B raises accuracy by +0.1511. Von is unaffected. The cause is located in prompt rendering ("{label}: {definition}" vs definition only), not in the decision head. Flipping that one expression makes the laya checkpoints exactly invariant and creates the effect in Von (0.8511 to 0.2281 when a label contradicts its definition). The paper introduces PolicyBench and a two-call diagnostic test — [arXiv](https://arxiv.org/abs/2610.02586)
- 2610.19536, Baowen Zhang, Hangting Ye and Hongyuan Zha, 14 Oct, "Typed Decision Models on Tabular Data". It compares four decision models (Jev, Clef, Kev-27B, GPT-6 Luna Decisions) with three LLMs, using 21 content-preserving rewrites. Decision models match the LLMs at lower cost, and three are far more robust to question wording. No model is robust to table organization. For every model, at least a third of row decisions change under some rewrite. Low-probability decisions are the ones most likely to change — [arXiv](https://arxiv.org/abs/2610.19536)
- 2610.18610, Kawai Chung et al., 13 Oct, "Jev-ToM: Evaluating Theory of Mind in Typed Decision Models". Five TDMs and seven generative baselines on 11,117 questions from 9 ToM benchmarks. Jev reaches 73.2% source-balanced accuracy and ranks 1st or 2nd in all six capabilities. Confidence-based selection is benchmark-dependent — [arXiv](https://arxiv.org/abs/2610.18610)

**C. Post-audit evaluation papers (25 Sep - 15 Oct), grouped by theme.**

*Broad benchmarks*
- 2609.37647, Deußer, Sparrenberg and Sifa, 29 Sep, "Evaluating and Benchmarking the System One Model Jev". jev-1.13.0, zero-shot, 37 datasets, 346,009 requests for under $10. Jev reaches 95-99% on IMDB, SST-2, HellaSwag and ARC, and 86.7% on Belebele. It beats Qwen3.8-27B (exact next-token option probabilities) on 27 of 37 datasets and Gemma-4-E4B on all 37. Choice probabilities are well calibrated, but binary probabilities are "poorly placed relative to a fixed 0.5 threshold"; tuned thresholds raise UNFAIR-ToS micro-F1 from 0.50 to 0.75. Rotating options leaves accuracy unchanged, and withholding the question drops it to near chance — [arXiv](https://arxiv.org/abs/2609.37647)
- 2610.03935, Duan et al., 2 Oct, "General Decision Models: Benchmarking and Insights Beyond Jev" (JEVal benchmark). Bilingual, 11,257 instances from 36 datasets, 25 configurations. Decision models "often identify the most likely outcome while substantially overstating its probability". On τ-bench, faster local decisions lower task success as errors accumulate. The paper also proposes SII-Decision models — [arXiv](https://arxiv.org/abs/2610.03935)
- 2610.11978, Xing Li et al., 8 Oct, "Specialized Decision Models vs. General-Purpose LLMs". 13 MCQ benchmarks against 19 LLMs. Jev is best on MMLU-Redux and ARC-Challenge, but on MathQA it is 17.7 points below the frontier median and below all 19 LLMs — [arXiv](https://arxiv.org/abs/2610.11978)
- 2610.21244, Tianyu Chen et al., 15 Oct, "System1-Arena: Which Decisions Can Be Left to System 1?". 92k questions, 105 tasks from 268 public sources, and 138 closed-loop environments, including a real-time mode. 30 models: 7 closed LLMs, 13 open LLMs read at the answer token, and 10 System-1 models including Jev and the OpenAI Decisions API. The largest System-1 models match or exceed fast closed LLMs at a quarter of the latency, with better calibration. In closed loops, small System-1 models rarely succeed; large open LLMs reach up to 32.9% — [arXiv](https://arxiv.org/abs/2610.21244)
- 2610.11392, Rahul Sharma, Andrew B. Duncan, Gaétan Marceau Caron and Sebastian J. Vollmer, 8 Oct, "TypedBench: A Benchmark for Calibration, Framing Sensitivity, and Cost in System One Decision Models". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.11392)
- 2610.17016, Dai, Tang, Futami and Ishida, 12 Oct, "ProbabilityBench". Simulated domains with exact ground-truth probabilities; 16 models. Most models on the cost-quality Pareto frontier are decision models, including Jev and Perplexity Decider — [arXiv](https://arxiv.org/abs/2610.17016)
- 2609.35342, Porcedda, 28 Sep, "Jev thinks 'I don't know', but doesn't say it: Sys1Cal-v1". True/False items with known P(A), asked through Noul, Choice and Score. Choice answers behave as if a suppressed third value U ("I don't know") exists. Recovering P(U) lifts median soft accuracy from 0.771 to 0.978 — [arXiv](https://arxiv.org/abs/2609.35342)
- 2610.02293, Teke, 1 Oct, "HakemBench" (Turkish). 2,346 items and 4,275 choice/yes-no/score questions. The composite combines macro-F1, normalized Brier and normalized risk-coverage AUC. The author's own model ranks 7th of 16 and is flagged as contaminated — [arXiv](https://arxiv.org/abs/2610.02293)
- 2610.06354, Yang, Zhang and Zhao, 5 Oct, "GraphDecisionBench". 14 model-interface configurations. Accurate adjacency recognition does not guarantee structural correctness — [arXiv](https://arxiv.org/abs/2610.06354)
- 2610.16191, Lai et al., 12 Oct, "Choice2Seq". Jev selects correctly 97.1% (arithmetic) and 99.5% (lexical retrieval) of the time but keeps only 33.0% and 2.1% of those correct choices when building the answer through serial local decisions — [arXiv](https://arxiv.org/abs/2610.16191)

*Calibration, coherence and self-knowledge*
- 2609.33209, Keyi Li, Yihao He and Quanyi Li, 27 Sep, "Beyond Calibration: Do a Typed-Decision Model's Probabilities Obey the Probability Axioms?". On 480 negation pairs, Jev misses summing to one by 0.064, against 0.293 for Qwen3.8-27B first-token probabilities and 0.122 for its verbalized probabilities. Jev's three single-label probabilities sum to 1.14, and its violations are about 5x its repeat noise — [arXiv](https://arxiv.org/abs/2609.33209)
- 2609.33971, Joy, 27 Sep, "Do System One Decisions Add Up? A Study of Probabilistic Coherence". Jev and Laya; 72,000 questions on TREC, CLINC150 and MASSIVE. Reconstructing fine labels through broad categories cuts Jev's CLINC150 accuracy by 22.9 points and raises Laya's by 21.3 — [arXiv](https://arxiv.org/abs/2609.33971)
- 2609.33843, Nandakishore, 27 Sep, Laya reproduction plus a preregistered calibration and escalation study. Laya is uniformly under-confident (gap −0.214). Temperature T=0.469 cuts held-out ECE from 0.204 to 0.037. The frozen gate misses its 10% accepted-set error target — [arXiv](https://arxiv.org/abs/2609.33843)
- 2610.01006, Shankaranarayana, Runje and Jannink, 1 Oct, "Beyond Answer Confidence: A Controlled Audit of Self-Knowledge in a Black-Box Decision Model". With no answer-relevant information, Jev still assigns up to 0.80 to a salient option. On news past its knowledge boundary, confidence exceeds accuracy by 0.21-0.33. Targeted yes/no questions are sharper: "is the evidence sufficient?" reaches AUROC 0.95 against 0.85 for confidence — [arXiv](https://arxiv.org/abs/2610.01006)
- 2610.18488, Xiaoyu Li and Chiwun Yang, 13 Oct, theory paper: minimax rates for recalibrating many developer-written yes/no questions with few labels each (pooled isotonic regression plus a per-question correction) — [arXiv](https://arxiv.org/abs/2610.18488)
- 2610.06625, Denney and DiGiuseppe, 5 Oct, seven political-science replications. Jev matches or comes close to GPT-6 Luna and Qwen3.8-27B. It has no cost advantage over GPT-6 Luna batch pricing. It is better calibrated than Luna's token probabilities but not consistently better than Qwen's — [arXiv](https://arxiv.org/abs/2610.06625)

*Option, label and format sensitivity*
- 2609.38827, Tianxiang Gao et al., 30 Sep, "More Choices, Fewer Decisions: Ordinal-Scale Bias". 40 datasets, nine models from the JEV, KEV and StartLux Decision families. Decisions concentrate on fewer labels than the gold distribution, and finer scales make it worse — [arXiv](https://arxiv.org/abs/2609.38827)
- 2610.16655, Rajput, Chauhan and Kosaraju, 12 Oct, a preregistered IIA test of jev-1.13.0 (299,463 calls). Adding an option shifts gold-vs-rival log-odds by an RMS of 0.20-0.52 nats, 1.2-3x run-to-run noise, rising to about 1 nat at 255 options. Questions packed into one call do not interact (bias <0.001). Per-option yes/no scoring removes the dependence but is 8.7 points less accurate — [arXiv](https://arxiv.org/abs/2610.16655)
- 2610.14631, Chen, 10 Oct, "The Company a Question Keeps: Auditing Open Jev-Style Models for Retrieval". Seven open checkpoints. Adding requested questions flips 9.1%/8.0% of Nimble's binary judgments and changes 21.4%/18.9% of selection-or-abstention actions at a fixed 0.5 threshold. All 70 flips are traced to schema serialization — [arXiv](https://arxiv.org/abs/2610.14631)
- 2610.19856, Xie et al., 14 Oct, "Lost in the Fallback". The Paired Fallback Robustness test: correct recognition does not reliably carry over to choosing the fallback option, and logically equivalent fallback rules disagree — [arXiv](https://arxiv.org/abs/2610.19856)
- 2609.39496, Zhong, Li and Lai, 30 Sep, "Arithmetic-Dependent Rejection Bottleneck". With the answer present Jev is 99% correct; with it absent, correct rejection is 7% despite a "none" option. Boolean verification is 99% accurate. A threshold chosen on development data raises rejection to 79% while keeping 97% answer-present accuracy — [arXiv](https://arxiv.org/abs/2609.39496)
- 2610.03387, Lu and Wu, 2 Oct, "Benchmarking candidate coverage and rejection policy transfer". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.03387)
- 2610.19619, Imperatrice et al., 14 Oct, "Are AI Decision Models Biased? A Case Study of Jev". 41,500 responses. Jev mostly avoids classic human bias patterns in its chosen answers, but it is sensitive to irrelevant numbers and option order, and cognitive-bias manipulations move its probabilities. It violates the conjunction rule in 54% of 15,000 responses across 30 tasks — [arXiv](https://arxiv.org/abs/2610.19619)
- 2609.36399, Asseri and Asseri, 28 Sep, "Calibrated to Whom?". Values Survey Module, 288,000 answers, ICC 0.997. With no persona Jev answers like its American personas. Saudi personas reproduce 87% of the human Saudi-US gap in English and 62% in Arabic — [arXiv](https://arxiv.org/abs/2609.36399)
- 2610.14912, Lukauskas and Šarkauskaitė, 10 Oct, "Probable but Not Valid". 14 decision models from 11 providers and 47 LLMs as survey respondents. 13 of 14 decision models score below gpt-5.4-mini on PSS. Averaged probability vectors come much closer to the human item marginals than rounded answers do — [arXiv](https://arxiv.org/abs/2610.14912)

*Judges*
- 2609.34862, Zhiqiang Wang et al., 28 Sep. Jev as an agent-trace security judge: benchmark-averaged F1 77.8 vs 74.1 for GLM-5.2 across 5,219 trajectories — [arXiv](https://arxiv.org/abs/2609.34862)
- 2610.20634, Do Rosario and Atef, 30 Sep, RAG claim verification. Details under Q3 — [arXiv](https://arxiv.org/abs/2610.20634)
- 2610.07177, Nandakishore, 5 Oct, "CLM-as-a-Judge". The open CLM-v0.1-8B is near chance on hard judge benchmarks. Order-flip rate is 0.0002. A gate at the preregistered 0.97 retention bar escalates 0.923-1.000 of items — [arXiv](https://arxiv.org/abs/2610.07177)
- 2610.11436, Hongliang Liu, 8 Oct, "Adversarial Cues ... Request Presentation". Adding one colon to a candidate raises Jev's false acceptance from 1.0% to 26.0% under one request presentation; logically equivalent presentations differ sharply — [arXiv](https://arxiv.org/abs/2610.11436)
- 2610.08675, Chuhong Xu et al., 6 Oct, "Same-Number Citation Swaps" (Jev as a financial evidence judge). A signed-number-at-pointer baseline explains most of the recovery — [arXiv](https://arxiv.org/abs/2610.08675)
- 2610.18497, Linhai Ma et al., 13 Oct, "Judges Follow the Reference". A derivation gap appears in all seven judges, including the System One models CLM and Jev — [arXiv](https://arxiv.org/abs/2610.18497)
- 2610.18389, Yamamoto and Kuroki, 13 Oct, PRISM: counterfactual-probe calibration of black-box judges, including Jev — [arXiv](https://arxiv.org/abs/2610.18389)

*Security, robustness and adversarial work*
- 2609.31142, Hu et al., 25 Sep, "JevAdvBench". 812 questions, 66 scenarios, 9,744 single-edit variants. Rewording stays within 1.2 points of re-run noise. One appended unverified opinion flips 12.1% of decisions and pushes 38% of confident answers below the 0.8 human-review threshold — [arXiv](https://arxiv.org/abs/2609.31142)
- 2610.04985, Shang Wang et al., 4 Oct, "Hidden Risks of Jev". Prompt injection, adversarial suffixes, backdoors (NanoJev), membership and attribute inference, and dual use — [arXiv](https://arxiv.org/abs/2610.04985)
- 2610.12292, Azizi, Baghaei Potraghloo and Pedram, 8 Oct, "One Word Opens the Gate". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.12292)
- 2610.14404, Dong et al., 9 Oct, "DICE: Tilting the Odds through Interface Attacks". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.14404)
- 2610.15537, Wu, Chang and Yan, 11 Oct, "Poisoned into Action: Context Attacks on Typed Decision Workflows". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.15537)
- 2610.17820, Xiang Li et al., 13 Oct, "Same Attack, Different Judge". Jev is most robust on input moderation: a "why might someone ask" sentence bypasses 9% of its blocks vs 56% for GPT-6 Astra. On phishing, forgeries bypass 19-29% of the emails it flags, and with no attack it detects only 62% of phishing. It flags the most benign requests (27%) — [arXiv](https://arxiv.org/abs/2610.17820)
- 2610.18612, Luo et al., 13 Oct, "Nudge the Judge". JevProbe across 228 real-world Jev applications and 2,273 test cases: 81.5% show decision flips, and 98.6% of those have potential downstream security impact — [arXiv](https://arxiv.org/abs/2610.18612)
- 2610.19118, Lan et al., 13 Oct, "DecisionRobust". Text and vision robustness benchmark; 30 text and 17 vision configurations. Label-consistency checks substantially reduce measured attack success — [arXiv](https://arxiv.org/abs/2610.19118)
- 2610.20907, Lan, Kaul, Pandurangan and Sanyal, 14 Oct, "From Detection to Decision". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.20907)
- 2609.33401, Yixuan Liu, 27 Sep, "Evaluating System One Models for Agent Security Decisions". Details under Q3 — [arXiv](https://arxiv.org/abs/2609.33401)

*Agents, controllers and systems*
- 2610.18579, Yubo Li, Ramayya Krishnan and Rema Padman, 13 Oct, "Reading Right, Acting Wrong". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.18579)
- 2610.13092, Ling et al., 9 Oct, "When Faster Decisions Do Not Make Better Agents". Five agents, 4,500 executions on ALFWorld and AndroidWorld. Decision cost and latency fall, but task success drops on mobile, and cost per success rises in one agent — [arXiv](https://arxiv.org/abs/2610.13092)
- 2610.02267, Jiawei Li, 1 Oct, "Fast Models, Slow Evidence". Laya vs Jev at 11 agent decision points (7,283 base cases and 6,640 variants). Jev is significantly better on 9 of 11. Neither beats chance on zero-shot model routing. Laya changes 30% of answers when option order is reversed. A self-audit found three analysis errors (see Q3) — [arXiv](https://arxiv.org/abs/2610.02267)
- 2610.21412, Zhu et al., 15 Oct, "JevAgentHarness" (AgentDecisionBench). The model most accurate on isolated questions solved only 69.5% of agent tasks. Without a fitted threshold, delegating tool choices cut success by 19.0 points. (Also trains AgentDecision-4B; partly a model paper.) — [arXiv](https://arxiv.org/abs/2610.21412)
- 2610.09683, Bailo, 7 Oct, "System Switch: When Should a Fast Decision Model Stop and Think?". Doom. Deferring the least confident 30% gains over random deferral in proportion to the actor's AUROC (ρ=0.87). In closed loop, no variant reaches the exit — [arXiv](https://arxiv.org/abs/2610.09683)
- 2610.06425, Delong Li et al., 5 Oct, "SoK: Semantic Decision Engines in Network Control Loops". Of 139 paper families, 50 claim control-loop or time-budget fit, but only 4 support the claim with matched measurement. "A decision that meets a 10 s budget for every isolated request meets it for none once decisions queue" — [arXiv](https://arxiv.org/abs/2610.06425)
- 2610.07716, Ran Li and Lei Chen, 6 Oct, "JevCascade". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.07716)
- 2609.34227, Sharma and Lall, 28 Sep, preregistered agent-memory study. Jev-selected raw turns are non-inferior to LLM extraction (bound −3.0 against a −5 margin) at 3,061x lower write cost. Reranking lowers correct abstention — [arXiv](https://arxiv.org/abs/2609.34227)
- 2610.15710, Xupeng Chen and Chenqian Le, 11 Oct, "Suggested Is Not Superseded". Details under Q3 — [arXiv](https://arxiv.org/abs/2610.15710)
- 2609.33689, Kourtis and Xilouris, 27 Sep, 5G control. Details under Q3 — [arXiv](https://arxiv.org/abs/2609.33689)
- 2609.37832, Rajput, Chauhan and Kosaraju, 29 Sep, "Can a Cacheable Decision Model Follow Rules?". Converting Certo to cacheable scoring drops recall@1 from 1.00 to 0.24 — [arXiv](https://arxiv.org/abs/2609.37832)

*Domain evaluations (evaluation-style, single domain)*
- 2609.34024, Madrid-García and Merino-Barbancho, 27 Sep, Jev in Medicine. Similar to GPT-6 Sol on PubMedQA (78.4% vs 78.2%) but 59.8% vs 82.4% on DiagnosisArena. Answers at p≥0.9 are 93.4% accurate. Jev picks "I don't know" for 10.5% of the questions where that is correct — [arXiv](https://arxiv.org/abs/2609.34024)
- 2610.18529, Du et al., 13 Oct, medical reliability: 15 datasets, 8,742 instances. Jev has the lowest decision-reversal rate under format changes. Most models fail at abstention awareness. "Normalizing option-wise binary scores yields higher retained accuracy than choice scoring" — [arXiv](https://arxiv.org/abs/2610.18529)
- 2610.03324, Paschalides, Pallis and Dikaiakos, 2 Oct, HATEDECIDE. Supplying definitions changes up to 28% of predictions without consistent gains. Decomposition helps in only 20% of comparisons — [arXiv](https://arxiv.org/abs/2610.03324)
- 2610.07953, Mazzoni and Failla, 6 Oct, "Benchmarking System One Models in Online Moderation". Five benchmarks. Retrieved precedents help Jev. Confidence supports selective review but is not consistently calibrated — [arXiv](https://arxiv.org/abs/2610.07953)
- 2610.14112, Fadli et al., 9 Oct, Indonesian regional languages, preregistered. Supplying the Indonesian translation adds up to 37.2 points. ECE does not grow, but error ranking degrades. A cascade to IndoBERT or an LLM matches the LLM at 24-77% lower cost — [arXiv](https://arxiv.org/abs/2610.14112)
- 2610.11901, Xing Li et al., 8 Oct, stance (VAST, ZS-CSD) — [arXiv](https://arxiv.org/abs/2610.11901)
- 2610.00376, Xu and Mei, 30 Sep, network traffic: 28.42% with 40 examples, against 69.95% for Random Forest — [arXiv](https://arxiv.org/abs/2610.00376)
- 2609.36154, Konak, 28 Sep, human activity recognition: macro-F1 0.038-0.118 vs 0.686-0.907 for supervised models — [arXiv](https://arxiv.org/abs/2609.36154)
- 2610.09937, Jung, 7 Oct, HVAC fault diagnosis under shift — [arXiv](https://arxiv.org/abs/2610.09937)
- 2609.34180, Qin et al., 28 Sep, video anomaly decision readouts (exploratory) — [arXiv](https://arxiv.org/abs/2609.34180)
- 2610.04345, Rahimi et al., 3 Oct, wireless decision-making — [arXiv](https://arxiv.org/abs/2610.04345)
- 2610.13675, Minh, Tran and Tan, 9 Oct, CLEF and CLEF-Flash on breast ultrasound; all configurations fall below the majority class on BUS-BRA — [arXiv](https://arxiv.org/abs/2610.13675)
- 2609.40241, Lyu and Xia, 30 Sep, recommendation reranking with Jev and OpenAI Decisions — [arXiv](https://arxiv.org/abs/2609.40241)
- 2609.33538, Cinà, 27 Sep, speech-neuroprosthesis rescoring: 7.5% WER vs 7.8% for 7B LMs — [arXiv](https://arxiv.org/abs/2609.33538)
- 2610.11135, Lee and Park, 8 Oct, knowledge tracing: mean AUC .706 zero-data — [arXiv](https://arxiv.org/abs/2610.11135)
- 2610.10321, Rafe and Das, 7 Oct, Kumo Tabular plus Jev with human recalibration for crash factors — [arXiv](https://arxiv.org/abs/2610.10321)
- Essay: 2610.01231, Richard Hill, 1 Oct, "Judgement in the Age of Jev". A conceptual "conditional Jevons hypothesis". It notes that evaluations "change practical decision rights through thresholds and exception routing" — [arXiv](https://arxiv.org/abs/2610.01231)

### Inferences
- The post-audit wave moves from "is Jev accurate?" to "is the probability usable for acting?": coherence (2609.33209, 2609.33971), IIA (2610.16655), cost-sensitive decision value (2610.11392), risk budgets (2610.19811), rejection-policy transfer (2610.03387). This is directly adjacent to our thesis.
- Several groups have written more than one paper: Rafe and Das (3 or more); Azizi et al. (2); Rajput et al. (2); Nandakishore (2); Yubo Li et al. (2: 2609.26550 and 2610.18579); Delong Li et al. (3). Cite them as clusters, not as independent replications.

### Gaps
- Papers posted 16-18 Oct 2026 are not in the arXiv API results; the newest record is from 15 Oct.
- The audit's supplementary_corpus.csv was not retrieved. The 28-paper list above is reconstructed from its Appendix Table 7.
- About 45 of the papers above were summarized from abstracts only.
- Semantic Scholar, alphaxiv and Hacker News were not consulted; arXiv was the only source used.

## Q2. Which models and datasets are evaluated? Do any papers evaluate OpenAI's Decisions API or chat-LLM logprob readouts as TDMs?

### Takeaway
Hosted Jev 1.13 (jev-1.13.0, snapshot 20260917) appears in almost every paper. Open TDMs include Laya, Von, Kev, Clef/Clef-Flash, Perplexity Decider, StartLux, CLM, Certo and others. At least six papers evaluate the OpenAI Decisions API. Several compare against answer-token or first-token logprob readouts of open LLMs, and one argues that LLMs already are Jev-style decision models.

### Cited Findings
- Every hosted-Jev paper in the audit corpus that names a version uses 1.13 (jev-1.13.0). Jev's probabilities lie on a two-decimal grid; it caps options at 255; it is not deterministic (4 of 510 labels changed on an identical repeat). Only 5 of 26 papers include a label-logprob baseline (checklist item B1) — [Audit](https://arxiv.org/html/2609.32160)
- **OpenAI Decisions API, evaluated.**
  - 2610.18579 includes "OpenAI Decisions (OpenAI, 2026a) | hosted (public beta) | native distribution (two decimals)". Accuracy 0.706 vs 0.763 for JEV. It "acts wrongly in 26% of states with every fact right". Cost $0.29 vs $0.13 per 1,000 decision states for JEV — [2610.18579](https://arxiv.org/html/2610.18579)
  - 2610.21244: "The OpenAI Decisions API ... provides the same decision interface through GPT-6 Luna"; it "is faster and better calibrated than GPT-6 Luna, but achieves a lower success rate on long-horizon tasks" — [2610.21244](https://arxiv.org/html/2610.21244)
  - 2610.19536 evaluates "GPT-6 Luna Decisions"; served through the Decisions API, "the same model costs 3.4 times less on row classification and 1.8 times less on anomaly detection" — [2610.19536](https://arxiv.org/html/2610.19536)
  - 2610.21412 includes OpenAI Decisions as a baseline: 79.2% isolated accuracy, ECE 0.027, and "10 refusals count as wrong" — [2610.21412](https://arxiv.org/html/2610.21412)
  - 2609.40241 evaluates "OpenAI Decisions using GPT-6-Luna" for reranking — [2609.40241](https://arxiv.org/html/2609.40241)
  - 2610.14404 describes the API ("evaluates text and images and returns typed answers for classification, routing, and prioritization") but attacks a Jev pipeline — [2610.14404](https://arxiv.org/html/2610.14404)
- Other hosted decision APIs: Perplexity Decisions API / Decider 27B v1.1 (2609.29769; 2610.18122). OpenRouter's Decisions API exposes Jev 1.13, Kev 4B, Tev1 4B, Solar Decide, Liquid D1, Perplexity Decider and Clef/Clef Flash (2610.18122). Microsoft-Decision-1, post-trained Qwen3.5-9B (2610.21244) — [2610.18122](https://arxiv.org/html/2610.18122); [2610.21244](https://arxiv.org/html/2610.21244)
- **Chat-LLM logprob readouts as TDMs.**
  - 2609.37647 scores Qwen3.8-27B and Gemma-4-E4B "via their exact next-token probabilities over the options" — [2609.37647](https://arxiv.org/abs/2609.37647)
  - System1-Arena includes "13 open LLMs read at the answer token" — [2610.21244](https://arxiv.org/abs/2610.21244)
  - 2609.33209 compares Qwen3.8-27B first-token vs verbalized probabilities — [2609.33209](https://arxiv.org/abs/2609.33209)
  - 2610.00346 compares "stated probabilities" (which become unreadable when a reply misses the key format) with "key likelihoods" (which avoid this but can saturate) — [2610.00346](https://arxiv.org/abs/2610.00346)
  - 2610.02076 (LLM-as-Jev, Yinheng Li and Justin Wagle, 1 Oct): "modern LLMs are inherently effective decision models: off the shelf, frozen models match or exceed existing training-free readouts on the same 4B backbone", and a "Thinking Jev" variant uses budgeted reasoning. This is partly a method paper — [2610.02076](https://arxiv.org/abs/2610.02076)
  - Earlier evidence from the audit: Ren et al. (label-token AUROC .950 vs typed .972/.974, n.s.); Yu and Yao (typed head = LM head, .761); Zhou et al. ("restricted option-logit readout matches greedy generation exactly whenever the generated answer is valid") — [Audit](https://arxiv.org/html/2609.32160)
- Datasets recur across papers. Intent and topic: CLINC150, BANKING77, MASSIVE, TREC, AG News. Judges: RewardBench, JudgeBench, RM-Bench, HelpSteer2, HealthBench, LLM-AggreFact, CALM bias tests. Medical: MetaMedQA, PubMedQA, DiagnosisArena, NEJM. Agents: ALFWorld, AndroidWorld, τ-bench, BFCL, When2Call, Mind2Web. Security: WAInjectBench, R-Judge, AgentHarm. Social science: Ziems et al. — [2610.16655](https://arxiv.org/abs/2610.16655); [2609.33401](https://arxiv.org/html/2609.33401); [2610.18579](https://arxiv.org/html/2610.18579); [Audit](https://arxiv.org/html/2609.32160)

### Inferences
- The OpenAI Decisions API (public beta from 6 Oct) appears in at least six papers within about 10 days, but only as one row among many. No paper is devoted to it.
- Matched logprob baselines remain the evidence that the "typed readout" is not itself the source of accuracy gains. This supports treating a TDM as one kind of belief source among others (including chat-LLM logprobs) rather than a privileged mechanism.

### Gaps
- None of the papers found separates OpenAI Decisions' calibration by primitive (noul, choice, score), and none tests it against GPT-6 Luna logprobs on matched items.

## Q3. Does any paper separate beliefs from decision rules and values, evaluate thresholds, abstention, selective prediction or cost-sensitive decisions, or compose TDM calls into architectures? Relevant passages.

### Takeaway
No paper states our full thesis: beliefs, a separate pure decision rule over beliefs plus explicit values, five composition structures, and offline re-running of rules. But many pieces exist separately. Probability Contracts and DICE explicitly separate "reported quantity" from "decision rule". TypedBench compares an argmax policy with a Bayes cost-matrix policy. Several papers evaluate allow/block/defer thresholds, risk-controlled thresholds and rejection-policy transfer. At least eight papers replay decision rules or cascades offline over recorded probabilities. Composition appears mostly as two-stage cascades. Chains and code-composed sub-questions also appear: hierarchical two-stage questions, Reading Right/Acting Wrong, and Jev-LiteMAS.

### Cited Findings

**Explicit separation of belief or report from decision rule**
- Probability Contracts (2609.37470, Han Chen and Yingrui Li, 27 Sep): "Readout and belief–choice sensitivity motivate distinguishing the reported quantity from the rule used to act on it." Also: "The controller minimizes expected cost under the report." And: "The practical implication is to evaluate probability interfaces with their decision rules." Key results: Jev's Event and Choice interfaces change the binary action on 32.8% of valid pairs at defer cost 0.10. The loss contrast between policies "takes both signs on a 99-cost grid". Disagreement certifies only 11-52% of mean binary pair error — [2609.37470](https://arxiv.org/html/2609.37470)
- DICE (2610.14404) models the pipeline as source → policy → state/question adapters → Jev response → interpretation adapter → "protected decision rule". "Each attack condition compromises one LLM adapter; Jev and the final decision rule remain protected." Its finding: each adapter can change the final decision even while Jev's authentic responses stay untouched — [2610.14404](https://arxiv.org/html/2610.14404)
- Probabilistic Sensing, Deterministic Authority (2610.10978, Gaston Besanson, Universidad Torcuato Di Tella, 7 Oct, cs.SE). It does not mention Jev in the abstract but is the closest conceptual match. "We admit the model's output only as an observation record with a score. An admission policy, with thresholds fitted on a held-out split at a declared false-positive ceiling, maps each score to true, false or unknown. Unknown denies. A deterministic, sufficiency-checked contract decides." The probability that sensing flips a verdict is bounded by the sum of admitted-wrong and unknown rates; 13 of 21,000 verdicts flipped, all under the bound; 36,000 model calls — [2610.10978](https://arxiv.org/html/2610.10978)
- One Word Opens the Gate (2610.12292): "Parsing each policy field into a typed value does eliminate one attack, but it also makes the model unnecessary: a deterministic rule over those values reaches 100% accuracy on all six policies." It also reports: "Escalating the least confident decisions does not help either: a decision an attack has reversed is no less confident than the one it replaced." It reports fail-open and fail-closed errors separately, with gate accuracy of 36-72% against a 50% chance level — [2610.12292](https://arxiv.org/abs/2610.12292)
- 2610.00346: "Selective prediction and escalation supply the decision rule that acts on a probability." It derives "condition-dependent design rules for automated decision gates, each tied to a measured quantity" — [2610.00346](https://arxiv.org/html/2610.00346)
- 2610.20907 (prompt-injection deferral): "probability calibration alone does not determine a useful decision policy". "The primary security–deferral curves use the real frozen reviewer decision rule." At a 1% FNR target, all gate-reviewer systems need more than 91.8% escalation. AUROC: LLM judge 0.897, Jev 0.871, Prompt Guard 2 86M 0.757 — [2610.20907](https://arxiv.org/html/2610.20907)

**Cost-sensitive decisions (explicit values)**
- TypedBench (2610.11392): "Software can act on these probabilities through thresholds, cost-weighted choices, and escalation rules." "A model's output can be used through its top answer (argmax) or through its full probability vector (Bayes), which picks the answer with the lowest expected cost"; "the value of calibration is cost(argmax) − cost(Bayes)". Explicit cost matrices: phishing (missed attack 20, false alarm 1); priority (2 per level under-prioritized, 1 per level over); anger (3 vs 0.5); queue (3 vs 1). Headline: the hosted model "is wording-sensitive and systematically underconfident; under asymmetric costs, using its probabilities can be worse than taking its top answer". For Jev 1.13.0, argmax costs 1,080 vs 2,300 under the Bayes policy; on phishing, Bayes flags 498 of 500 emails. For Laya-english, argmax 12,740 vs Bayes 11,840. Calibration error is reported relative to the finite-sample noise floor of a perfectly calibrated predictor. The paper also notes it "evaluates this same cost-saving trade-off offline via a hybrid threshold sweep" — [2610.11392](https://arxiv.org/html/2610.11392)
- 2609.33689 (5G control): "an optimal act/escalate/abstain gate, an escalation-feasibility floor ... per-type conformal risk control." In a trace-driven replay, the authors "replaced the heuristic rule 'escalate if System-2's p99 fits' with the rule of Theorem 1 ... pricing a miss like an error". SLA violations fell from 0.068 to 0.044. The fine-tuned Laya "returned its training answer for 98-99.5% of changed questions, and its calibrated gate then acted wrongly on up to 80% of them" — [2609.33689](https://arxiv.org/html/2609.33689)
- 2610.21412 states a cost-constrained objective (minimize expected cost per episode subject to non-inferior task success, margin 3 points) and fits a per-choice threshold on the agent's own trajectories — [2610.21412](https://arxiv.org/html/2610.21412)

**Thresholds, risk control, abstention and rejection**
- 2610.19811 (Messoudi and Mansar, "Calibration and Risk-Budgeted Decisions with System One Models", 14 Oct): "When human deferral is unavailable, uncertain cases must still receive an action." The paper defaults to a conservative fallback and controls false-omission risk. "We use threshold to define the binary decision rule" over disjoint Fit, Calibration and Test pools. Naive threshold selection exceeds the target risk "in roughly half of settings ... compared with 7.8% for Learn Then Test (LTT)". Conclusion: "relying on a probability-like interface is insufficient for deployment decisions" — [2610.19811](https://arxiv.org/abs/2610.19811); [HTML](https://arxiv.org/html/2610.19811)
- 2609.33401 (agent security): "The policy compares unsafe probability with an allow threshold and a block threshold"; inputs at a threshold escalate. Example rule: "Allow below 10.5% Block above 89.5% Otherwise escalate". "Choosing allow and block thresholds separately increases automation mainly through additional blocks." The paper recommends reporting the allowed and blocked fractions separately — [2609.33401](https://arxiv.org/html/2609.33401)
- 2610.03387 (rejection-policy transfer): "A Jev policy calibrated on DBpedia rejects 69.3% of covered Emotion test inputs, while an Emotion policy loses detection entirely." With ten intent candidates, Laya detects 99.0% of out-of-scope queries but rejects 48.8% of covered ones. "Recorded predictions support offline recomputation without model calls." "The released package recomputes probability and discrete scores from recorded predictions without new model calls" — [2610.03387](https://arxiv.org/html/2610.03387)
- 2609.39496: "All calibration is performed offline on saved scores, and each selected threshold is applied unchanged to its evaluation set, requiring neither retraining nor additional inference." Arithmetic rejection rises from 7% to 79% — [2609.39496](https://arxiv.org/html/2609.39496)
- 2610.15710 (memory-retirement gate): "a binary score should not be wired to delete: route suggested changes to pending evidence". A three-way decision (SUPERSEDED / NEEDS-CONFIRMATION / COMPATIBLE) cuts premature retirement from 39.2% to 15.5%, but it "lands on the binary gate's own threshold frontier". A cascade selected on development data was indistinguishable from raising the threshold — [2610.15710](https://arxiv.org/abs/2610.15710)
- 2610.00346: under a guaranteed 5% risk, Jev keeps 0.528 of intent decisions; saturated likelihoods (Gemma-4-31B) "receive none ... because no threshold separates decisions whose top probabilities all lie near one" — [2610.00346](https://arxiv.org/html/2610.00346)
- 2609.37647: Jev's binary probabilities are "poorly placed relative to a fixed 0.5 threshold"; thresholds tuned on training data raise UNFAIR-ToS micro-F1 from 0.50 to 0.75 — [2609.37647](https://arxiv.org/abs/2609.37647)
- 2609.31142: an appended opinion "pushes 38% of confident answers below the 0.8 confidence threshold that routes them to human review" — [2609.31142](https://arxiv.org/abs/2609.31142)
- 2610.02267's self-audit found that in-sample thresholds with a 5% target produced up to 17% held-out misses, and that "gate accuracy reported as end-to-end quality" (58% vs 98%) had distorted the headline claims — [2610.02267](https://arxiv.org/abs/2610.02267)
- Audit checklist C3 requires thresholds fitted on separate data or fixed before evaluation, and tested for transfer across workloads or fallback models. 7 of 7 applicable papers complied; 3 were unclear — [Audit](https://arxiv.org/html/2609.32160)

**Offline re-running of rules over recorded outputs**
- 2610.20634: "The cascade is simulated offline from the locked prediction files, with no additional inference: a claim is accepted from the decision model when its probability is confident either way and otherwise takes the frontier model's stored verdict." "Table 13 re-scores the identical predictions at other constants." The key negative result: "a matched random-escalation control ... does as well, so what buys the saving is the escalation share and not the probability that picks what to escalate." Jev ties Astra on the headline metric (−0.56 points) at a 187-fold cost difference, but admits 23.2% of claims annotators marked unsupported, against 14.1% for Astra — [2610.20634](https://arxiv.org/html/2610.20634)
- 2609.29769: "We replay cascades with each decision model first" — [2609.29769](https://arxiv.org/html/2609.29769)
- 2610.15537: "Correcting the gate's empty-scope behavior restores twelve of the clean decisions without additional model calls"; "The scope replay adds local state records and no model calls" — [2610.15537](https://arxiv.org/html/2610.15537)
- 2610.20907: "Full security–deferral curves are regenerated offline from the bundled prediction artifacts" — [2610.20907](https://arxiv.org/html/2610.20907)
- 2610.00346 includes "three propositions that make temperature recovery, hierarchical accuracy and cascade accuracy computable from the recorded answers". The offline estimate is "exact for a model that returns the same distribution for the same request" and only an estimate for the nondeterministic hosted model — [2610.00346](https://arxiv.org/html/2610.00346)
- 2610.07716 (JevCascade): "the cascade threshold is a quantile of the confidence distribution and needs no labels". A restriction predictor computes post-menu-change accuracy from cached first-pass probabilities, landing within 4.2 points. "At matched cost a confidence cascade beats every scheme that re-asks the same model." A curated 5-candidate menu with a 0.8B model reaches 95.4% on CLINC150, against 80.0% for a 4B model on the full 150-label menu — [2610.07716](https://arxiv.org/abs/2610.07716)

**Composition into architectures**
- *Cascades / evaluator-gate (most common).* 2609.26550: a frozen cascade scores 92.5 vs 93.1 at 57% of the fee. 2610.14112: deferring the least confident 10-30% to IndoBERT matches the better system. 2610.00346: intent-trained first stage plus Gemma-4-31B. 2610.09683: offline deferral gain tracks actor AUROC (ρ=0.87). 2610.07177: the gate escalates 92-100% at a 0.97 retention bar. 2609.29769: LLM judges share Jev's errors, so the cascade gains at most 1.5 points — [2609.26550](https://arxiv.org/abs/2609.26550); [2610.14112](https://arxiv.org/abs/2610.14112); [2610.09683](https://arxiv.org/abs/2610.09683); [2610.07177](https://arxiv.org/abs/2610.07177); [Audit](https://arxiv.org/html/2609.32160)
- *Chained / hierarchical.* 2610.00346: "A two-stage condition asks the domain and then the intent within the gold domain, and Proposition 2 turns the two answers into the accuracy of the hierarchical policy." 2609.33971: reconstructing labels through categories costs Jev 22.9 points on CLINC150. 2610.16191: serial construction keeps only 2.1-33% of correct choices — [2610.00346](https://arxiv.org/html/2610.00346); [2609.33971](https://arxiv.org/abs/2609.33971); [2610.16191](https://arxiv.org/abs/2610.16191)
- *Parallel questions combined by code.* 2610.18579: "This is the usage pattern that System One models are designed for: many narrow questions in parallel, combined by code." "The sub-questions go to the same choice-only model and the composition is done by the calling program." "Where the probed facts provably determine the action, models that read every fact still fail to combine them, and their own answers, composed by code, repair the failure." On real states, models' own answers repair 25-34% of facts-right/action-wrong states (Qwen3.8-27B, JEV, Gemma, Clef) but break 2-4% of correct states, which is about five times as many states. OpenAI Decisions repairs 33% and breaks 6.8%. JEV makes 73% of its errors after reading correctly. "The interesting design space is therefore not System One versus reasoning models, but which states a fast model can be trusted on, which need a composed decision, and which need deliberation" — [2610.18579](https://arxiv.org/html/2610.18579)
- 2610.16655: questions packed into one call do not interact (bias <0.001), while option-set changes do — [2610.16655](https://arxiv.org/abs/2610.16655). 2610.14631 finds the opposite for some open checkpoints: request expansion flips 8-9% of judgments through schema serialization — [2610.14631](https://arxiv.org/abs/2610.14631)
- 2610.03324: decomposing hate-speech definitions into multiple questions "significantly improves performance in only 20% of the comparisons" — [2610.03324](https://arxiv.org/abs/2610.03324)
- *Orchestrator-worker / multi-agent.* Jev-LiteMAS (2610.21411, 15 Oct): routing and review account for 31.7-43.5% of generative-LLM tokens in three MAS frameworks. Jev selects experts and screens artifacts: "passing artifacts proceed directly, whereas flagged ones undergo LLM re-review". Tokens fall 12.7-54.6% with accuracy within 1.34 points. It is an application/framework paper, but it is the clearest orchestrator plus evaluator-gate composition — [2610.21411](https://arxiv.org/abs/2610.21411)
- *Loops / long-horizon (mostly negative).* 2610.03935: on τ-bench, "faster local decisions reduce median episode time but lower task success as decision errors accumulate". 2610.13092: auxiliary reasoning and extra interactions absorb the decision savings. 2610.21412: delegating tool choices without a fitted threshold costs 19.0 points. 2610.06425: per-request latency budgets fail once decisions queue — [2610.03935](https://arxiv.org/abs/2610.03935); [2610.13092](https://arxiv.org/abs/2610.13092); [2610.21412](https://arxiv.org/abs/2610.21412); [2610.06425](https://arxiv.org/abs/2610.06425)
- *Workflows to execution.* 2610.15537 traces "poisoned evidence through retrieval, model choice, automated action, and persisted state". 2610.18612 traces Jev judgments through "application logic [that] maps diverse Jev judgments to observable decisions" — [2610.15537](https://arxiv.org/abs/2610.15537); [2610.18612](https://arxiv.org/abs/2610.18612)
- The audit's open problem: "When does a TDM cascade beat a generative cascade?" Escalation benefit "depends on how complementary the errors of the two stages are" — [Audit](https://arxiv.org/html/2609.32160)

### Inferences
- The closest existing statements of the "belief vs decision rule" thesis are in Probability Contracts (2609.37470), TypedBench (2610.11392), DICE (2610.14404), and the cs.SE governance paper 2610.10978. None of them proposes a general rule language, a typology of composition structures, or a pure-expression rule that can be re-run offline. Our contribution should be framed as unifying and formalizing these scattered practices.
- Offline replay over recorded probabilities is already common methodology (cascade replays, threshold re-fitting, scope repair "without additional model calls"). This strongly supports our "rules can be re-run offline" claim. Two caveats come from the papers themselves: replays are exact only for deterministic models (2610.00346), and hosted Jev is nondeterministic.
- Several results warn that a better probability does not guarantee a better decision: Bayes with Jev's probabilities can do worse than argmax (2610.11392); random escalation matches confidence-gated escalation (2610.20634); attacked decisions stay confident (2610.12292); per-question thresholds do not transfer (2610.03387). Our paper should treat these as evidence for evaluating the belief and the rule jointly.
- Among the five structures: single and evaluator-gate cascades are heavily studied; chained/hierarchical and parallel-with-code-composition have some evidence; orchestrator-worker has only application-style evidence; evaluator-optimizer loops have essentially no TDM-specific evaluation.

### Gaps
- I found no paper that evaluates evaluator-optimizer loops built from TDM calls.
- I found no paper that evaluates whether decision rules generalize across model versions using recorded beliefs (the audit notes cross-version stability is unknown).
- The full texts of 2610.21411, 2610.12292 and 2610.19811 were only partly read (abstract and keyword matches).

## Q4. What do the papers say about calibration, label/definition effects, option-order bias, yes/no swap sensitivity and contamination?

### Takeaway
Calibration is model- and workload-specific, and recalibration is usually needed. Jev is reported overconfident in some settings and underconfident in others. Labels often override definitions, a cause one paper locates in prompt rendering. Yes/no swaps flip roughly half of Jev's answers on some tasks. Option order affects Jev less than open models but still matters in judging and bias tasks. Contamination is flagged but rarely tested.

### Cited Findings
- **Calibration**
  - Crash coding: slope 1.63; prevalence overstated (4.8% vs 2.7%); held-out recalibration cuts error 3.3x; the 0.01 output grid limits rare-label resolution — [Audit](https://arxiv.org/html/2609.32160)
  - TypedBench: hosted model "systematically underconfident" — [2610.11392](https://arxiv.org/abs/2610.11392)
  - JEVal: models "substantially overstating" the probability of the most likely outcome — [2610.03935](https://arxiv.org/abs/2610.03935)
  - Laya: uniformly under-confident; one temperature fixes it — [2609.33843](https://arxiv.org/abs/2609.33843)
  - Medicine: ECE 0.063 vs 0.146 for GPT-6 Sol on MetaMedQA, but AUROC 0.645 on DiagnosisArena — [2609.34024](https://arxiv.org/abs/2609.34024)
  - Political science: better than GPT-6 Luna token probabilities, not consistently better than Qwen3.8-27B — [2610.06625](https://arxiv.org/abs/2610.06625)
  - Prompt injection: Jev's native probabilities "do not consistently outperform post-hoc calibrated classifier scores" — [2610.20907](https://arxiv.org/abs/2610.20907)
  - Self-knowledge: calibrated on familiar tasks; fails beyond the knowledge boundary — [2610.01006](https://arxiv.org/abs/2610.01006)
  - Judges: "good calibration does not protect against bias" — [2610.18122](https://arxiv.org/abs/2610.18122)
- **Labels vs definitions**
  - Swapping no/yes names across rubrics moved Jev AUC from .815 to .581 with zero type errors (Sun et al.); asking through Score instead of Choice moved accuracy by up to 10.5 points — [Audit](https://arxiv.org/html/2609.32160)
  - In open TDMs the effect comes from prompt rendering, not the decision head — [2610.02586](https://arxiv.org/abs/2610.02586)
  - A misleading permissive-option name raises guardrail fail-open to 93-100% — [2610.12292](https://arxiv.org/abs/2610.12292)
  - Hate-speech definitions change up to 28% of predictions without consistent gains — [2610.03324](https://arxiv.org/abs/2610.03324)
- **Option order and option-set effects**
  - Rotating options leaves Jev's accuracy unchanged — [2609.37647](https://arxiv.org/abs/2609.37647)
  - Laya changes 30% of answers under order reversal — [2610.02267](https://arxiv.org/abs/2610.02267)
  - All 8 TDMs show position bias as pairwise judges — [2610.18122](https://arxiv.org/abs/2610.18122)
  - Jev is order-sensitive on cognitive-bias tasks — [2610.19619](https://arxiv.org/abs/2610.19619)
  - IIA violations of 0.20-0.52 nats — [2610.16655](https://arxiv.org/abs/2610.16655)
  - Ordinal compression worsens on finer scales and is reduced, not eliminated, by randomizing order — [2609.38827](https://arxiv.org/abs/2609.38827)
  - Order-invariance model papers exist (2610.18233 "Consider, Then Choose"; 2610.22066 Prism-1; 2610.06744), but they are model papers and out of scope — [arXiv listing](https://arxiv.org/abs/2610.18233)
- **Yes/no swap**
  - Swapping yes and no flips 50.5 of every 100 Jev answers, at least 16.8 for every generative model, and at most 6.5 for four fine-tuned checkpoints — [2610.00346](https://arxiv.org/abs/2610.00346)
  - In Sun et al., DeBERTa Open-Jev flips 19.5% vs 76.9% for ModernBERT Laya — [Audit](https://arxiv.org/html/2609.32160)
  - Negation-pair incoherence: Jev misses summing to one by 0.064 — [2609.33209](https://arxiv.org/abs/2609.33209)
- **Contamination**
  - Contamination concerns are unresolved in Ibrahim and Zaki and Zhang et al. (audit checklist T4) — [Audit](https://arxiv.org/html/2609.32160)
  - Rotation and question-withholding rule out shallow memorization "but not memorized question-answer pairs" — [2609.37647](https://arxiv.org/abs/2609.37647)
  - Exposure to training data explains the largest open-checkpoint lead — [2610.00346](https://arxiv.org/abs/2610.00346)
  - HakemBench flags its own model's tracks as contaminated — [2610.02293](https://arxiv.org/abs/2610.02293)
  - Knowledge-tracing contamination checks found no evidence — [2610.11135](https://arxiv.org/abs/2610.11135)
- **Nondeterminism**
  - Up to 1.33% of decisions change between identical runs; 4 of 510 labels changed on repeat — [Audit](https://arxiv.org/html/2609.32160)

### Inferences
- These sensitivities are belief-quality problems: wording, labels, option sets and order. They argue for keeping rules separate from beliefs and for re-validating thresholds whenever question framing changes, since the probability depends on the option list it was computed over (2610.16655).

### Gaps
- No systematic contamination study of hosted Jev was found.

## Q5. What is the audit's 14-item evaluation checklist?

### Takeaway
The checklist has 14 items in four groups: Baselines B1-B3, Test design T1-T4, Reproducibility and statistics R1-R3, and Confidence and deployment C1-C4. Nine items are scored. Compliance is lowest for option-name invariance (T3, 1/27), cascade baselines (B2, 1/5), latency with and without caching (C4, 3/20), and label-logprob baselines (B1, 5/26).

### Cited Findings
Source for every item below: [Audit Table 6 and Appendix B](https://arxiv.org/html/2609.32160). Counts are compliant papers over applicable papers.
- **B1.** "A baseline that reads label log-probabilities from an ordinary or same-backbone LM." 5/26; 1 unclear.
- **B2.** "Where a confidence threshold passes decisions to another model: a cheap generative cascade as a baseline." 1/5.
- **B3.** "Where labeled data suffice to train one: a task-specific model (encoder, classical classifier, reward model or probe) as a baseline." 7/13; 3 unclear.
- **T1.** "Spread between models on the test; avoid parity claims on saturated tests." Unscored.
- **T2.** "Correctness or agreement of individual decisions across repeated, reordered or reworded requests, not only aggregate accuracy." 17/26; 1 unclear.
- **T3.** "Option-name invariance test: swap names across rubrics or compare neutral with semantic names." 1/27 (only Sun et al.).
- **T4.** "Data provenance: synthetic or real, gold-label source, and whether a public benchmark predates the model." Unscored.
- **R1.** "Exact model version and run date." Unscored.
- **R2.** "Confidence intervals or significance tests on headline results." 15/27.
- **R3.** "Disclose prompts, recipes, baselines, or thresholds chosen after seeing test data." Unscored.
- **C1.** Where TDM probabilities are used or described as calibrated, measure calibration (ECE, Brier, reliability), preferably on held-out data, with a metric suited to prevalence, before and after recalibration. 13/17; 1 unclear.
- **C2.** "Accuracy among the highest-confidence examples, by task." Unscored.
- **C3.** "Where confidence thresholds gate acceptance or escalation: thresholds fitted on data separate from the evaluation set, or fixed before evaluation and not tuned on it." The audit adds that frozen thresholds should be tested for transfer across workloads or fallback models. 7/7; 3 unclear.
- **C4.** "Where TDM latency is reported or a latency advantage is claimed: latency both with and without caching." Also state serving location, concurrency and cost per correct outcome. 3/20; 1 unclear.
- Minimal reporting card implied by the checklist: "exact model version and run date; test difficulty or model spread; one ordinary-LM readout baseline; one cheap generative baseline; intervals from repeated runs; held-out calibration; and, when a cascade is used, a frozen threshold evaluated on a new workload or fallback model."
- The audit's open problems: attributing Jev's gains; decisions that need computation; faithfulness to option semantics; calibration under deployment shift; when a TDM cascade beats a generative cascade.

### Inferences
- The checklist evaluates the TDM, and the TDM inside a threshold cascade (B2, C3), but it has no item for the decision rule or values as a separate artifact: cost matrices, abstention policy, or offline re-scoring of rules. Our thesis could propose extensions such as "report the decision rule and values separately", "report decision value under the stated costs", and "release recorded beliefs so rules can be re-run". TypedBench (2610.11392) and Probability Contracts (2609.37470) are the precedents for those extensions.

### Gaps
- Per-item compliance for papers after 25 Sep has not been coded by anyone, as far as I found.
