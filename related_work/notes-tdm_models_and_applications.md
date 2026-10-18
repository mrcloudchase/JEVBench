# Typed decision models (TDMs): models, training methods, vendor guidance, and applications/system designs (Sep 15 – Oct 18, 2026)

Scope: papers and official docs that introduce TDMs, training methods, and applications/system designs built on them, with a focus on how each turns TDM outputs into decisions and whether any composes TDM calls into systems. Evaluation, benchmark and audit papers belong to another researcher; I list them only where they bear directly on decision rules or composition.

Source-quality notes for the report writer:
- **TypeSafe docs quotes are verbatim.** I downloaded the raw Markdown from `docs.typesafe.ai/<page>.md` and read it directly.
- **arXiv metadata is reliable.** Titles, authors, dates and abstracts come from the arXiv export API.
- **Some details are paraphrased.** Details from arXiv HTML bodies, GitHub READMEs and HF model cards were extracted by a summarizing fetch tool. Short quoted phrases from those pages are probably exact, but the report should mark them "per paper" rather than presenting them as long verbatim quotes.

---

## Q1. Which model, method and application papers exist, and what does each claim?

### Takeaway
In about five weeks, a dense literature appeared. It has three strands:
- **Open replications of Jev.** These are encoder-based or LLM-readout models: this-that-model-1.0, Releasing the Inner Jev, StartLux-Decision, SBERT2S1, Intern-Decision, Visual Jev, AgentDecision-4B and SearchJev, plus HF-only models (Von, OpenDecider, Laya, open-jev-deberta, Imajev, Verdict).
- **Training methods.** These are RLCD and its variants: RLCD², SLCD, and a leave-one-out fix to RLCD.
- **Application and system papers.** These place a TDM inside agents, multi-agent systems, memory, search agents, judges/cascades, network orchestration and data coding. Almost all of them use the TDM as a confidence-gated "System One" layer that defers to an LLM or a human.

### Cited Findings

**Vendor launch**
- **TypeSafe "Introducing System One Models & Jev"** (Diogo Almeida, byline Sep 15, 2026).
  - Jev is "a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out."
  - Trained with RLCD (Reinforcement Learning for Calibrated Decisions), with the claim "Calibrated: higher confidence means higher accuracy."
  - Price: $0.042 per 1M input tokens; output is free.
  - Positioning: "The surrounding code constrains their freedom, making them easier to compose into reliable systems." — [TypeSafe blog](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- **System One concept page.** It defines the primitives Choice, Score and Noul (Box was later added for images in Jev 1.14). It says "Answers to some question types also include confidence ... so you can decide when to act and when to escalate to a person or a reasoning model." — [docs.typesafe.ai/concepts/system-one](https://docs.typesafe.ai/concepts/system-one.md); Box/Jev 1.14 per [OpenRouter Jev hub](https://openrouter.ai/docs/guides/community/jev)

**Model and training-method papers (arXiv)**
- **2609.23886, "this-that-model-1.0: A typed decision model that decides in 30 ms, for a millionth of a cent"** (Zehua Cheng, Wei Dai, Jiahao Sun; Sep 20, 2026).
  - A 2B model. The answer is "read directly from the hidden state at a designated position and restricted to the option set the caller declared."
  - Framing: "What the program needs back is not prose. It is one of n declared options and a number it can threshold."
  - Results: 30.9 ms; 0.941 score / 0.042 Brier vs Jev's 0.765 / 0.133 on a third party's 68-question cohort; 0.560 on multi-step arithmetic. Weights at HF flock-io. — [arXiv](https://arxiv.org/abs/2609.23886)
- **2610.17205, "Releasing the Inner Jev: A Simple Recipe for Open Decision Models"** (Jonathan Geuter, Andrew Cheng, David Alvarez-Melis; Oct 12, 2026).
  - Zero-shot option-letter logit readout from open instruction-tuned LLMs (Gemma 4 31B/12B, Qwen3.6-27B, Qwen3.5-4B).
  - Fine-tuning: LoRA plus a decision head initialized from a slice of the LM head.
  - New dataset: OpenDecisions (2,352 questions).
  - Results: Gemma 4 31B scores 79.6 zero-shot vs Jev 80.1. After fine-tuning it scores 84.4 on OpenDecisions and 81.5 on JevBench v1.7 (+4.3 / +4.4 over Jev).
  - The abstract says nothing about decision rules or abstention. — [arXiv](https://arxiv.org/abs/2610.17205)
- **2610.17309, "StartLux-Decision: AutoThink Decision Models with Reinforcement Learning for Calibrated Deliberative Decisions"** (Xialie Zhuang, Zunhai Su, Jia Pan, Ngai Wong, Guanhua Chen, Chuan-Wei Kuo; Oct 12, 2026).
  - Models: 0.8B–27B "Instant" models (bidirectional attention in full-attention layers) and 4B/9B/27B "AutoThink" models, which "invoke explicit reasoning for uncertain decisions and answer confident cases directly."
  - RLCD² reward, per paper: r = S(p₁,t) − S(p₀,t) − λ·max(0, |τ| − B).
    - S is a decision-weighted proper score whose weight is a uniform + Beta(8,2) mixture.
    - A frozen reference supplies p₀ and p₁.
    - λ = 10⁻⁴; budget B = 3,072 tokens.
  - Effects: up to +48 pp traces that terminate within the generation limit, and up to −65% reasoning length.
  - New benchmark: DecisionPivot. — [arXiv abs](https://arxiv.org/abs/2610.17309); [arXiv HTML](https://arxiv.org/html/2610.17309)
- **2610.02486, "From Retrieval to Typed Decisions: Calibrated System One Models from Biomedical Sentence Encoders"** (Pritam Deka; Oct 1, 2026).
  - Typed decision models "return probabilities meant to be thresholded."
  - Contributions: SBERT2S1 (bi-encoder, cross-head, and prior-fused residual heads), BIODECIDE, and MEDLINE-S1 (243k decisions).
  - The released RLCD recipe trails cross-entropy by 2.5–3.0 points because "reward normalisation ... inflates the noisy score-function term 3.6-15-fold." An unbiased leave-one-out estimator recovers most of the gap.
  - After temperature scaling, no objective is clearly better calibrated than cross-entropy. — [arXiv](https://arxiv.org/abs/2610.02486)
- **2610.22131, "Intern-Decision: Efficient Multimodal Decision Making with Autoregressive Masked Language Modeling"** (Tong Zhu et al.; Oct 15, 2026).
  - 0.8B/2B/4B multimodal models. One decision placeholder per field in a JSON skeleton, all read in one causal pass.
  - The 4B model scores 90.02% vs Jev v1.13.0 at 88.74%.
  - A "confidence-based handoff study" on 111 JevBench-Hard items raised accuracy from 73.87% to 87.39% by routing 42 items to a larger model. — [arXiv](https://arxiv.org/abs/2610.22131)
- **2609.25845, "Visual Jev: Accurate and Efficient Decisions from Shared Visual Context"** (Guanxu Yu, Yuhang Yao; Sep 22, 2026).
  - Encodes the image once and runs the question suffixes as a batch: 8.9× faster at N = 32 questions.
  - "A matched typed-head control offers no consistent accuracy advantage over the language-model-head readout." — [arXiv](https://arxiv.org/abs/2609.25845)
- **2610.05107, "SearchJev: A Fast and Calibrated System-1 Model for Search Agents"** (Congfeng Cao et al.; Oct 4, 2026).
  - Proposes Soft-Label Learning for Calibrated Decisions (SLCD).
  - "In a dual-system search agent, SearchJev handles short decisions and delegates uncertain judgments to System 2."
  - New benchmark: SearchDecision-Bench. On BrowseComp-Plus: 3.7–4.7× speedup, with accuracy rising from 45% to up to 54%. — [arXiv](https://arxiv.org/abs/2610.05107)
- **2610.21412, "JevAgentHarness: Benchmarking, Deploying and Training Decision Models That Share Control with LLMs"** (Kunlun Zhu, Tao Feng, Xu Han, Heng Wang, Ling Yang, Xiangru Tang, Jiaxuan You, Heng Ji; Oct 15, 2026).
  - Introduces AgentDecisionBench and DecisionGym. Releases AgentDecision-4B: Qwen3-4B LoRA trained on post-mistake agent states with Jev's answers as soft labels, a Brier term, and then GRPO (no measurable gain over SFT, per paper).
  - "without a fitted confidence threshold, delegating tool choices lowered success by 19.0 points." — [arXiv](https://arxiv.org/abs/2610.21412); [HTML](https://arxiv.org/html/2610.21412)

**Application and system papers (arXiv)**
- **2609.26532, "REFLEX with Jev for Efficient Selective Control in LLM Agents"** (Tiantong Wu, Wei Yang Bryan Lim; Sep 22). An agent architecture that uses Jev as a typed decision layer and calls a strong LLM "when confidence is low, or generation is required." Reports 95% success with 72.7% fewer strong-model calls. — [arXiv](https://arxiv.org/abs/2609.26532)
- **2609.23986, "Jev-Mem: System-One-Controlled Agentic Memory for Efficient AI Agents"** (Dongming Jiang, Yi Li, Bingzhe Li; Sep 21).
  - A "System-One control plane" governs memory typing, query routing, retrieval-budget allocation, graph traversal, candidate scoring and adaptive stopping. System Two is used only for complex reasoning and answer synthesis.
  - On LoCoMo: score 0.777 (+11.0%) and 6.6× faster construction. — [arXiv](https://arxiv.org/abs/2609.23986)
- **2610.21411, "Jev-LiteMAS: Separating Decisions from Generation in Multi-Agent Workflows"** (Kaixiang Wang, Zhaijiacheng Zhou, Jiong Lou, Jie Li; Oct 15).
  - Routing and review account for 31.7–43.5% of generative-LLM tokens in the MAS frameworks it profiled.
  - Jev selects experts and screens artifacts; flagged artifacts go to LLM re-review with corrective feedback.
  - Cuts generative tokens by 12.7–54.6% with accuracy within 1.34 pp. — [arXiv](https://arxiv.org/abs/2610.21411)
- **2609.26550, "JEV-as-a-Judge: Accept When Confident, Escalate When Unsure"** (Yubo Li, Yidi Miao, Ramayya Krishnan, Rema Padman; Sep 22).
  - "With a threshold frozen in advance, accepting confident verdicts and escalating the rest is 0.9 points more accurate than GPT-6 on 1,610 held-out pairs at 41% of its fee."
  - Closes "with a simple recipe for validating thresholds locally." — [arXiv](https://arxiv.org/abs/2609.26550)
- **2610.20634, "Jev-as-a-Judge for RAG Claim Verification: Confidence-Gated Cascading Between a Non-Generative Verifier and a Frontier LLM"** (Alden Do Rosario, Kirollos Atef; arXiv lists v1 as Sep 30 despite the 2610 ID).
  - The cascade reaches 74.10 at $2.92 per 1k claims vs 73.83 at $8.93 for the frontier LLM alone.
  - But "a matched random-escalation control ... does as well, so what buys the saving is the escalation share and not the probability that picks what to escalate." — [arXiv](https://arxiv.org/abs/2610.20634)
- **2609.24052, "Calibrated Decisions at Scale: Converting Police Crash Narratives into Probabilistic Crash Variables with a System One Model (Jev)"** (Amir Rafe, Subasish Das; Sep 21).
  - "formulates narrative coding as gated, typed decisions." A screen covered 499,500 narratives and 195,857 were coded with a 27-question schema.
  - Results: F1 0.908 vs human labels; recalibration cuts calibration error by 3.3×.
  - Defines a review budget over flagged records. — [arXiv](https://arxiv.org/abs/2609.24052)
- **2609.22753, "Replacing Large Language Models with Jev Decision Models for Low-Latency Edge Service Orchestration"** (Delong Li, Xu Wang, Haochen Gong, Rui Lang, Guangsheng Yu; Sep 19). Extracts "four to eight bounded intent fields and applies a shared validator, admission policy, and scheduler." Median decision latency drops 22.7–64.5% vs the fastest LLM. — [arXiv](https://arxiv.org/abs/2609.22753)
- **2609.23136, "Intent Interpretation at RIC Timescales: Jev Decision Models versus Large Language Models in 6G Open RAN"** (same group; Sep 19). Jev turns intents into A1 policy fields and meets the 1 s near-real-time budget on 99.8% of calls, vs 17.9% and 0% for two hosted LLMs. — [arXiv](https://arxiv.org/abs/2609.23136)
- **2609.23959, "Open-Jev Judgments on CallScreenBench: Calibrated One-Pass Scam Screening with a Small Language Model"** (Simiao Ren et al.; Sep 21).
  - JevLite: Qwen3-4B LoRA whose temperature-scaled two-label softmax gives P(scam) per caller turn.
  - AUROC .974; decisions come 1.14 turns earlier "under the same hang-up rule." — [arXiv](https://arxiv.org/abs/2609.23959)
- **2609.24395, "JEVQA – Video Quality from Metadata, Bitstream, and Pixel Features with a General-Purpose Decision Model"** (Werner Robitza; Sep 21). Zero-shot video-quality scoring: Pearson 0.737–0.824 vs VMAF. — [arXiv](https://arxiv.org/abs/2609.24395)
- **2609.24965, "Jev for Scientific Decisions: Evaluating Semantic Choices and Their Consequences"** (Boyuan Deng et al.; Sep 21). A harness "that follows its documented guidance and assigns arithmetic to code." Semantic Choices feed deterministic calculations. — [arXiv](https://arxiv.org/abs/2609.24965)
- **2609.30216, "Jev in the Wild: A Data-Driven Analysis of the Jev Model's Functionality, Applications and Ecosystem"** (Guoming Ling, Muen Xue, Zijian Ye; Sep 24).
  - Analyzes 2,170 GitHub projects. Usage shares: Choice 81.0%, Noul 72.2%, Score 45.4%.
  - Routing & Automation holds 41.4% of stars.
  - Conclusion: Jev is "a reusable decision component whose functionality varies with the surrounding workflow." — [arXiv](https://arxiv.org/abs/2609.30216); [HTML](https://arxiv.org/html/2609.30216v1)
- **2610.13092, "When Faster Decisions Do Not Make Better Agents: An Empirical Study of Jev in Agent Workflows"** (Yuchen Ling, Shengcheng Yu, Zhenyu Chen, Chunrong Fang; Oct 9). Covers 4,500 ALFWorld/AndroidWorld executions. "Mean cost per successful outcome increases in one agent even as spending per attempt falls." — [arXiv](https://arxiv.org/abs/2610.13092)

**Adjacent evaluation papers (mainly the other researcher's scope; listed for completeness)**
- 2610.02267 (Jiawei Li, "Fast Models, Slow Evidence"). Its self-audit found in-sample thresholds "(5% target, up to 17% held-out misses)." — [arXiv](https://arxiv.org/abs/2610.02267)
- 2610.03387 (Jiawen Lu, Tongtong Wu; rejection-policy transfer). "Source calibration often fails to preserve the target operating point." — [arXiv](https://arxiv.org/abs/2610.03387)
- 2609.32160 (Lijuan Tang, Yuemeng Zheng; audit of 28 papers). "In practical deployments, confidence is often used to decide when to defer to a stronger model or a human." — [arXiv](https://arxiv.org/abs/2609.32160)
- 2609.26758 (option-name polarity) — [arXiv](https://arxiv.org/abs/2609.26758)
- 2610.18122 (TDMs as judges, bias) — [arXiv](https://arxiv.org/abs/2610.18122)

**Official / vendor TDM APIs and open model cards**
- **OpenAI Decisions API.**
  - Endpoint `POST /v1/decisions`; `gpt-6-luna` is the only model; status "public beta, and we expect to GA in the coming weeks."
  - Question types are named **`predicate`** (probability 0–1), `choice` (choice, probabilities, confidence) and `score` (levels; probability-weighted index plus confidence). OpenAI does **not** use the word "noul."
  - Price: $0.10 per 1M input tokens; no output charges. — [OpenAI docs](https://developers.openai.com/api/docs/guides/decisions)
  - The public-beta date of Oct 6, 2026 (preview at DevDay, reported as Sep 29) comes from secondary coverage. — [Unite.AI](https://unite.ai/openai-releases-decisions-api-in-public-beta-powered-by-gpt-6-luna); [ProPakistani](https://propakistani.pk/2026/10/07/openai-launches-decisions-api-with-up-to-10x-faster-responses/)
- **Von 1.3** (wfzyx; author Victor Hugo Panisa).
  - About 395M parameters: ModernBERT-large plus an Option-Marker head. Order-invariant since 1.2. Trained with listwise softmax-CE + Brier on about 290k items. Apache-2.0. — [HF wfzyx/von](https://huggingface.co/wfzyx/von)
- **OpenDecider-nano** (Manjunath Janardhan).
  - About 400M parameters: Ettin-encoder-400m plus an MLP head. Distilled from Qwen3-235B and DeepSeek V4.1 Flash.
  - typed-decisions accuracy 0.796 vs Laya 0.766 vs Jev 0.754. — [HF](https://huggingface.co/manjunathshiva/opendecider-nano)
- **Laya** (Convai Innovations).
  - ModernBERT-large English, mmBERT-base multilingual, and a typed-decisions checkpoint.
  - Trained with RLCD: "strictly proper scoring rules," Gaussian logit noise, REINFORCE with a group-mean baseline.
  - `laya-serve` exposes a Jev-compatible `/v1/systemone`.
  - The card says "Laya is a fast base to specialise, not a zero-shot decision engine." — [HF convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya)
- **open-jev-deberta-v3-large** (com-kotobalabs) and the **kotoba-lang/typed-decisions** repo.
  - A fine-tuned DeBERTa-v3-large reaches 0.855 accuracy, 42 ms, at $0.26 training cost. ModernBERT and LLaDA-MoE-7B were compared.
  - ADRs exist, including one on `:autonomous` / `:escalate` thresholds (ADR-2609181715), but I could not retrieve their text. — [GitHub kotoba-lang/typed-decisions](https://github.com/kotoba-lang/typed-decisions)
- **StartLux-Decision** (GitHub/HF startlux-models). Code is Apache 2.0; weights are CC BY-NC 4.0. The API is "compatible with System One `/v1/systemone`." — [GitHub](https://github.com/StartLuxLabs/StartLux-Decision)
- **Imajev-4B** (Mohit Garg). A LoRA on Qwen3.5-4B that answers noul/choice/score over text plus up to two images. — [GitHub mohit67890/imajev](https://github.com/mohit67890/imajev); [HF](https://huggingface.co/mohit67890/imajev-4b)
- **Verdict** (drramos/danieltrt).
  - 11.3M trainable parameters: LoRA r = 16, a decision head and three fitted temperatures, on Qwen3.5-0.8B-Base.
  - It says it is not affiliated with TypeSafe. — [HF drramos/verdict](https://huggingface.co/drramos/verdict) (via search snippet only)
- Plumb-4B and decider-4b appear only on JevBench leaderboards and third-party comparison sites. I found no primary model card or paper. — [jev-ai.pro decider comparison](https://jev-ai.pro/compare/jev-vs-decider) (third-party)

### Inferences
- **A shared architecture.** Most open models are either an encoder with per-option marker tokens (Von, OpenDecider, Laya, open-jev-deberta) or a decoder LLM read out through option-letter or placeholder logits (Inner Jev, StartLux, Intern-Decision, Visual Jev, JevLite, AgentDecision-4B, Verdict).
  - Two papers report that a custom typed head adds no accuracy over the LM-head readout: Visual Jev, and the 2609.32160 audit's summary.
- **RLCD is the dominant training framing.** The variants are RLCD² (deliberation reward), SLCD (soft labels) and an LOO-corrected RLCD. However, 2610.02486 finds that cross-entropy plus temperature scaling matches it.
- **Every application paper keeps a separate stronger fallback** (LLM or human) and gates on confidence. None runs a TDM fully autonomously.

### Gaps
- I could not retrieve full bodies for several papers (Jev-Mem, Visual Jev, SearchJev, Intern-Decision, edge orchestration). Their exact decision rules (threshold values) are therefore unverified.
- I found no arXiv paper for JevK5, Plumb or decider-4b, and no Cloudflare "Clef" primary source; Clef is mentioned only on a news aggregator.
- The kotoba-lang ADR texts were not accessible (`gh api` returned nothing), so I cannot quote them.

---

## Q2. How do vendors and papers recommend turning TDM outputs into decisions? Does anyone formalize values/utilities or explicitly separate belief from decision rule?

### Takeaway
The vendor consensus is "the model gives probabilities, your code decides." The guidance has three parts:
- Thresholds that are scaled to the stakes of each action.
- A three-band act / confirm-or-review / escalate scheme.
- Thresholds fitted on your own labeled data.

The clearest explicit belief/decision-rule separations are:
- TypeSafe's LLM-guardrails cookbook: "TypeSafe supplies the assessment; your application owns the decision," with named policies re-applied to one cached assessment.
- langgraph-jev: "Jev makes the probabilistic decision; your application code decides what to do with it."
- The kotoba-lang wire format, which keeps `:probabilities` separate from `:admit?` (threshold plus decision).

Only a few papers formalize costs or utilities:
- JevAgentHarness derives the threshold qL − ΔC/V from call cost and the value of a solved task.
- Jev-LiteMAS gives cascade cost equations.
- The crash-narratives paper defines a review budget H(π\*).
- OpenAI says to choose thresholds "based on the cost of false positives and false negatives."

No source treats the decision rule as a first-class pure expression over beliefs plus a value table. The closest is the guardrails cookbook's named `POLICIES` dict.

### Cited Findings

**TypeSafe, general guidance (verbatim)**
- In "How to build with TypeSafe":
  - The summary box: "Keep control flow, deterministic rules, and side effects in code" and "Use probabilities and confidence to act, ask for review, or escalate."
  - The "Route on uncertainty" step: "Make code take different actions for confident and unconfident answers. Escalate uncertain cases to a person or a more expensive reasoning model. Test thresholds by plotting confidence against accuracy on your data."
  - The example uses `if answer.confidence < 0.8: route_to_human_review(ticket)`. — [docs.typesafe.ai/concepts/how-to-build-with-system-one](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- The page's full triage example builds `spam_risk = 0.45*requests_credentials + 0.30*sender_identity_mismatch + 0.25*unexpected_reward`. It then applies "Escalate uncertain judgments instead of guessing":
  - `spam_is_uncertain = 0.4 < spam_risk < 0.6`, which goes to human review, as does topic confidence < 0.75.
  - `spam_risk >= 0.6` leads to quarantine.
  - Per-branch noul thresholds are 0.7.
  - Priority "high" requires frustration confidence ≥ 0.7 and score ≥ 1.5. — [same page](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- The page also says: "Outputs are sortable and can drive smart `if` statements, thresholds, and comparisons", and "For learned composition, use the probabilities as features in a downstream classical machine-learning model." — [same page](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)

**TypeSafe Confidence page (verbatim)**
- It defines three ranges:
  - "**High confidence:** Act automatically."
  - "**Medium confidence:** Proceed with caution ... ask the user to confirm, flag for review, or gather more information before acting."
  - "**Low confidence:** Do not act. Route to a human, request clarification, or fall back to a different system."
- "Thresholds scale with risk: A confidence threshold is not one number. Different actions within the same system should be gated at different levels depending on the consequences of getting it wrong." Also: "Your code encodes the risk tolerance."
- The example uses a 0.5 floor; `approve_transfer` needs > 0.9.
- Formulas:
  - Choice: confidence = (p_max − 1/n)/(1 − 1/n).
  - Score: 1 − (expected distance from the mode)/MAD_unif, floored at 0.
  - Noul: no confidence is returned. The page suggests |2p − 1|.
  - The page also suggests top probability and the top-to-second ratio as alternatives.
- "Start with conservative thresholds, test with your own data, and adjust as you observe results." — [docs.typesafe.ai/confidence](https://docs.typesafe.ai/confidence.md)

**TypeSafe LLM-guardrails cookbook: the strongest belief vs decision-rule separation (verbatim)**
- "TypeSafe supplies the assessment; your application owns the decision."
- Each Noul is compared against an "action threshold" (which triggers the hazard's configured action) and a lower "review threshold" (which sends it to a human). A severity Score has its own threshold that "can turn a review into a block."
- "A policy is just those numbers under a name, which makes the trade-off something a product picks rather than inherits."
- The policies:
  - `strict`: review 0.35, action 0.70, severity_block 2.0.
  - `permissive`: review 0.35, action 0.85, severity_block 2.0.
- `PRECEDENCE = ["support","block","review","pass"]`.
- Under "The same probabilities, different decisions": "The next cell reuses one cached assessment and changes only the policy. The probabilities do not move; the application decides how much evidence it wants before it acts." Output: strict → block, permissive → review. — [docs.typesafe.ai/cookbooks/llm_guardrails](https://docs.typesafe.ai/cookbooks/llm_guardrails.md)
  - This is effectively offline re-running of a decision rule over recorded beliefs. All cookbook calls are cached in `json_cache.json`.

**Other TypeSafe cookbooks**
- **Self-consistency (nouls).**
  - It maps nouls to no / uncertain / yes with `NOUL_UNCERTAINTY_LOW = 0.30` and `NOUL_UNCERTAINTY_HIGH = 0.70`.
  - "Uncertain cases go to a human. The escalation is application logic over the returned..." and "Set production boundaries from labeled examples and from the cost of incorrect decisions and of review."
  - The covered answers span 0.43–0.53 across 15 runs, crossing 0.5: "probabilities 0.49 and 0.51 cause opposite actions." — [docs.typesafe.ai/cookbooks/consistency_noul_cookbook](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md)
- **Classification using confidence.**
  - Rule: at confidence ≥ 0.9, report the SIC industry group; below that, report its parent division. This is a "back off one level" form of abstention.
  - The confident half is 90% correct; the rest is 40% at group level and 70% at division level.
  - "If a division is too coarse for your application to act on, this branch is where you hand it to a person." — [docs.typesafe.ai/cookbooks/classification_using_confidence](https://docs.typesafe.ai/cookbooks/classification_using_confidence.md)
- **Skill suggestion.** `GATE_THRESHOLD = 0.30` (the mean of three request nouls, "below which nothing is suggested") and `FITS_THRESHOLD = 0.30`. — [docs.typesafe.ai/cookbooks/skill_suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion.md)

**OpenAI Decisions docs**
- "Use it to flag photos for review based on a threshold you choose."
- "Choose thresholds based on the cost of false positives and false negatives."
- Set thresholds from labeled examples, and include a fallback option such as "other" that sends uncovered inputs to a review queue.
- The docs do not define how `confidence` is computed. — [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions)

**Open-model cards**
- **StartLux-Decision.**
  - The README says: "AutoThink models answer in one pass when the top probability reaches a gate, 0.6 by default", while "The AutoThink results use a gate of 0.9." The gate is configurable per request (`gate`, `think_mode` auto/never/always).
  - Moving the 27B gate from 0.9 to 0.6 drops DecisionPivot pair accuracy from 88.1% to 68.4%.
  - Suggests treating `none_probability ≥ 0.2` as "no listed option fits," with `allow_none`. — [GitHub StartLux-Decision](https://github.com/StartLuxLabs/StartLux-Decision)
  - The paper body gives a 0.9 default gate and the fusion p_default = 0.25·p₀ + 0.75·p₁ when max p₀ < 0.9. — [arXiv HTML](https://arxiv.org/html/2610.17309)
  - **The task brief's "gate at 0.6" is the README default; the paper's results use 0.9. They do not conflict once that is noted.**
- **StartLux paper on policy-aware calibration.**
  - "Well-calibrated individual predictions need not remain calibrated after downstream selection or routing."
  - "Calibration and acceptance thresholds must therefore be evaluated on the outputs of the deployed policy."
  - Top-of-32 selection turns 92% individual accuracy into 78%.
  - Policy-aware isotonic maps shrink the gaps from [−11.7, +20.5] to [−2.7, +2.1] pp across 184 settings.
  - The paper "does not establish optimality of the released models' fixed confidence threshold." — [arXiv HTML](https://arxiv.org/html/2610.17309)
- **Von.** A `band` rule maps nouls outside 0.2–0.8; `--noul-decision raw` returns the posterior instead. Users should refit calibration with `von calibrate` on their own labels "before acting on confidence values." — [HF Von](https://huggingface.co/wfzyx/von)
- **Laya.**
  - "Do this on your own data before trusting the probabilities."
  - On non-Latin text, "the model stays confident while being wrong, confidence gating cannot save you."
  - It advises gating on `confidence`, not `action.act_probability`, which "carries no usable signal yet." — [HF Laya](https://huggingface.co/convaiinnovations/laya)
- **OpenDecider.** Its agent examples use a minimum confidence of 0.6 with a fallback to a human agent. — [HF OpenDecider](https://huggingface.co/manjunathshiva/opendecider-nano)
- **kotoba-lang/typed-decisions.**
  - `wire.py` builds a proposal with `:probabilities` separate from `:admit?`, which holds `:threshold` and `:decision :autonomous|:escalate`.
  - Thresholds 0.6 and 0.8 were tried. A 0.8 gate gave 0.92 precision on code holes, with 34% auto-applied.
  - Proposals go to an approval queue rather than executing.
  - SHA-256 memo keys of (state, question, options) avoid re-running identical decisions. — [GitHub](https://github.com/kotoba-lang/typed-decisions)
- **Imajev.** At a 90% threshold it automated 58% of benchmark questions at 97.5% accuracy and sent the rest to a person. This is a developer claim reported via search snippet. — [GitHub imajev](https://github.com/mohit67890/imajev)

**Papers that formalize costs or utilities**
- **JevAgentHarness (2610.21412).**
  - It runs the decision model in shadow mode ("the decision model answers every question silently") on 150 tasks per agent LLM.
  - It estimates qL (LLM accuracy), ΔC (call price) and V (success lost per wrong choice, valued at $1 per solved task). Under calibration, "handing over is worth it exactly when" confidence ≥ qL − ΔC/V.
  - In practice, "the threshold is the lowest confidence above which accepting is worth it, and the confidence need not match its exact chance of being right."
  - Fitted thresholds for Jev+Flash: 1.00 for tools and 0.99 for arguments. A fixed 0.5 threshold "lost 21.5 points."
  - Thresholds "are refitted when the LLM, decision model or task rules change." — [arXiv HTML](https://arxiv.org/html/2610.21412)
  - **This is the most explicit decision-theoretic decision rule over TDM beliefs that I found, and it includes offline refitting over logged beliefs.**
- **REFLEX (2609.26532).**
  - Rule: π(s_t) = â_t if c_t ≥ τ and the action is executable; otherwise L_strong(s_t). τ = 0.5 is the primary setting, swept over {0.5, 0.7, 0.8, 0.9, 0.95}.
  - Metrics: selective risk Risk(τ) = P(invalid | c ≥ τ), Coverage(τ), and AURC.
  - The paper distinguishes "invalid but recoverable" decisions from unsafe or terminal actions, but per extraction it has "no explicit utility function." — [arXiv HTML](https://arxiv.org/html/2609.26532)
- **Jev-LiteMAS (2610.21411).**
  - ρ_esc = π·r + (1 − π)·f; C_cascade = C_J + ρ_esc·C_L. Savings require C_J < (1 − ρ_esc)·C_L.
  - Undetected release: Pr(error, pass) = π(1 − r). — [arXiv HTML](https://arxiv.org/html/2610.21411)
- **Crash narratives (2609.24052).**
  - The per-variable threshold τ is "retuned per variable to maximize weighted F."
  - Review budget: H(π\*) = 1 − max{c(t) : π(t) ≥ π\*}. "a variable no threshold can certify routes every flagged record to review"; tied probability blocks are "accepted or reviewed whole."
  - It warns that choosing and certifying on the same labels "reports the best of many thresholds as though it were the value of one." — [arXiv HTML](https://arxiv.org/html/2609.24052)
- **2610.20634.** Random escalation at the same budget matches confidence-chosen escalation: "what buys the saving is the escalation share and not the probability that picks what to escalate." — [arXiv](https://arxiv.org/abs/2610.20634)
- **2609.26550.** Uses a threshold "frozen in advance" and a "recipe for validating thresholds locally." — [arXiv](https://arxiv.org/abs/2609.26550)

### Inferences
- **Near-universal practice.** Sources almost all keep the TDM output as a belief and put the action choice in caller code. Most present it as engineering advice ("code in control"), not as a formal belief/decision-rule split.
- **Closest prior art to our thesis:**
  - TypeSafe's guardrails cookbook (named policies over a cached assessment).
  - JevAgentHarness (a cost-derived threshold refit offline on shadow logs).
  - kotoba-lang (probabilities kept apart from the admit decision in the wire format).
- **None of them gives a general language or algebra of decision rules over multiple beliefs plus an explicit value table.**
- **Thresholds in examples vary widely** (0.3, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.00). Several papers (2610.21412, 2610.02267, 2610.03387, 2609.24052, StartLux) show that fixed or in-sample thresholds fail out of sample. This supports making values explicit and re-fittable.

### Gaps
- No source defines abstain as a typed action alongside others in a value table. Abstention appears as "route to human," "escalate," "none_probability," "back off a hierarchy level," or a "review" band.
- OpenAI does not document how `confidence` is computed, or any per-action threshold guidance beyond the cost of FP/FN.

---

## Q3. Does anyone compose TDM calls into architectures (cascades, chains, fan-out/panels, hierarchical routing, loops, agents)? Precise summary of TypeSafe's patterns

### Takeaway
Yes. TypeSafe's own docs present composition as the core skill: "Learning to think in terms of discrete, atomic decisions that compose into complex system behavior is a key skill." They give four named patterns (Speculative fan-out, Confidence-gated routing, Composite scoring, Intent routing). Cookbooks add a verifier cascade (SDE cascade), tree search over chained Choices (hierarchical classification), two-stage rank-then-verify (skill suggestion), and LLM-in-the-loop feature discovery (autoresearch).

Research papers add:
- Agent control layers (REFLEX, JevAgentHarness, SearchJev, Jev-Mem).
- Multi-agent orchestrator plus evaluator loops (Jev-LiteMAS).
- Gated chains (crash narratives).
- Judge cascades (JEV-as-a-Judge, the RAG verifier).

TypeSafe explicitly discourages agent `while` loops and sequential chaining in favor of a single parallel fan-out. OpenAI instead says dependent decisions need separate, chained requests.

### Cited Findings

**TypeSafe Patterns index (verbatim)**
- "TypeSafe is designed to sit within a larger system, powering decisions with AI. Learning to think in terms of discrete, atomic decisions that compose into complex system behavior is a key skill."
- The table:
  - Speculative Fan-Out — "Send many questions in a single call, including speculative ones, and let your code decide what's relevant" (Cost, Speed).
  - Confidence-Gated Routing — "Utilize confidence as a second decision axis to build safer systems" (Reliability, Safety).
  - Composite Scoring — "Combine several dimensions of analysis into a single score" (Cost, Reliability, Speed).
  - Intent Routing — "Classify a user's intent and route to the appropriate handler" (Cost, Speed). — [docs.typesafe.ai/patterns](https://docs.typesafe.ai/patterns.md)

**Pattern 1: Speculative fan-out**
- The pattern: "we recommend putting all of the questions your system needs in a single request, and then using code to decide what is relevant after the fact. All questions are evaluated in parallel."
- Example, support triage: one request with five questions (Choice category; Score bug_severity; Noul has_reproducible_steps; Noul refund_requested; Score frustration).
- Code rules:
  - bug_report: `bug_severity.score > 1.5 and bug_repro.noul > 0.6` leads to escalate_to_engineering(high); otherwise backlog.
  - billing: `refund.noul > 0.7` leads to a refund flag.
  - feature_request: log it.
  - Independent of category: `frustration.score > 1.5` flags the ticket for priority.
- "Speculative questions are ignored when irrelevant and save a round trip when they are not."
- Note that there is no confidence gate in this example. — [docs.typesafe.ai/patterns/fan-out](https://docs.typesafe.ai/patterns/fan-out.md)
- The smart-home demo applies the same idea and calls sequential calls "the wrong way": "This approach optimizes for a minimum number of questions, but it ends up being much slower and more expensive than batching all of the questions in to one upfront API call." — [docs.typesafe.ai/demos/smart-home](https://docs.typesafe.ai/demos/smart-home.md)

**Pattern 2: Confidence-gated routing**
- The pattern: "The answer tells you what; confidence tells you whether to act."
- Example, voice banking, with a Choice intent ∈ {check_balance, approve_transfer, other}:
  - confidence < 0.6 → support agent.
  - check_balance at ≥ 0.6 → show the balance.
  - approve_transfer > 0.85 → approve automatically.
  - approve_transfer at 0.6–0.85 → ask the user to confirm.
  - other → support agent.
- "The 0.6 floor catches anything the model is genuinely uncertain about. Above that floor, each action type has its own threshold based on the consequences of acting on a wrong classification." — [docs.typesafe.ai/patterns/confidence-routing](https://docs.typesafe.ai/patterns/confidence-routing.md)

**Pattern 3: Composite scoring**
- The pattern: "break the judgment into independent dimensions, score each one separately, and combine them with weights you control in code."
- Example, resume screening: four five-level Scores (python_depth, team_leadership, system_design, generalist), each normalized as `score/4`.
  - Senior IC = 0.40·py + 0.10·lead + 0.40·arch + 0.10·general.
  - EM = 0.15·py + 0.40·lead + 0.20·arch + 0.25·general.
  - Candidates are ranked per role.
- "it gives you visibility into how exactly the final score is being calculated. If the highest ranking candidates are not matching your expectations, you can adjust the weights."
- The same beliefs are fed into two different value weightings. — [docs.typesafe.ai/patterns/composite-scoring](https://docs.typesafe.ai/patterns/composite-scoring.md)

**Pattern 4: Intent routing**
- The pattern: "TypeSafe can sit in front of all of these as a fast, cheap classifier that determines which handler to invoke."
- Example: a Choice intent ∈ {order_status, product_question, return_exchange, complaint} plus a three-level Score for complexity.
  - intent.confidence < 0.5 → human.
  - order_status → deterministic code.
  - product_question → product-specialist LLM.
  - return_exchange → returns-specialist LLM.
  - complaint → human if `complexity.score > 1 or complexity.confidence < 0.5`; otherwise the complaint-resolution LLM.
- "One intent routes to deterministic code with no LLM involved. Two route to different specialist LLMs ... the expensive resources only get invoked for the requests that actually need them." — [docs.typesafe.ai/patterns/intent-routing](https://docs.typesafe.ai/patterns/intent-routing.md)

**Composition cookbooks**
- **SDE cascade (extract → verify → escalate).**
  - Rung 0 is `gpt-5.4-mini`; rung 1 is `gpt-5.5` (reasoning); the verifier is `jev-1.12`.
  - A per-field battery of Nouls, framed so that `true` = something is wrong, returns P(wrong).
  - Gate: `FIRE_T = 0.7`, "escalate if *any* field flag exceeds" it. "this is a `max`-style gate (escalate if *any* field fires), not a mean, so one confident red flag is enough instead of being averaged into silence."
  - A holistic `__overall__::judge` head is computed but not used by the gate.
  - Sweeping the gate 0→1 over 100 prompts gives a cascade Pareto frontier "up-and-left of every single model."
  - Appendix guidance: "Narrow and grounded", "Bad = TRUE", "Per-field, then aggregate with max", "Independent and cheap", "Separating / calibrated." — [docs.typesafe.ai/cookbooks/sde_cascade](https://docs.typesafe.ai/cookbooks/sde_cascade.md)
- **Hierarchical classification.**
  - Each node is a Choice over its children. Greedy search proceeds root to leaf ("One early mistake cannot be recovered").
  - Beam search keeps K paths, with each path's frontier asked as parallel questions. `path_score = product(edge_probabilities) ** (1 / decisions)`; `separation = top_path_score / second_path_score` (not used for pruning).
  - Datasets: CPC 2026.05, Shopify 2026-02, MeSH 2026, and the CookSafe repo.
  - Beam K = 3 got 4 of 4 leaves right; greedy got 2 of 4. — [docs.typesafe.ai/cookbooks/hierarchical_classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification.md)
- **Skill suggestion (two chained TDM requests per agent turn).**
  - Request 1 ranks all 182 Hermes skills and asks whether any skill is needed, with gate 0.30.
  - Request 2 re-reads the top three in full and "is free to reject all of them," with fits threshold 0.30.
  - The winner is injected as one line in the agent's system prompt.
  - Wrong-skill loads fall from 16.8% to 7.3%; loads when nothing fits fall from 9.8% to 4.0% (488 requests, claude-haiku-4-5). — [docs.typesafe.ai/cookbooks/skill_suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion.md)
- **Autoresearch feature discovery (an evaluator-optimizer-like loop around TDM features).**
  - "An LLM proposes the questions, TypeSafe answers them for every row, and CatBoost trains on the answers. ... CatBoost reports which questions it used and which rows it still gets wrong, the following proposal call reads that report, and the loop runs again."
  - RMSE 1.77 with 38 questions after five rounds, vs 2.15 from asking TypeSafe for the score directly. — [docs.typesafe.ai/cookbooks/autoresearch_feature_discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md)
- **Smart-home demo (TDM + LLM pairing).**
  - "a Noul question identifying if the user request is asking for more than one distinct action. If this is true, the system uses an LLM to split the request into a list of atomic commands. The split requests are then evaluated by TypeSafe individually." This is a TDM → LLM → TDM per sub-request chain.
  - "When TypeSafe determines that the user query is a request for general information or conversation, the system calls an LLM." — [docs.typesafe.ai/demos/smart-home](https://docs.typesafe.ai/demos/smart-home.md)
- **TypeSafe's anti-agent stance.**
  - "System One is TypeSafe's model for building AI-powered software, not agents. It does not generate code or choose its own next action."
  - "Avoid agent `while` loops when a software workflow can express the same behavior."
  - "Questions are evaluated independently and in parallel. One primitive's result does not become hidden context that changes another primitive's result." — [docs.typesafe.ai/concepts/how-to-build-with-system-one](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)

**OpenAI on chaining**
- "For decisions that depend on an earlier answer, send separate requests." The example checks for damage first, then chooses a repair category. — [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions)

**Research architectures**
- **REFLEX.** A per-step selective controller: the TDM decides if c ≥ τ, otherwise the strong LLM does. Roles are separated into control, argument synthesis and generation. On τ²-bench, a cheap Flash self-escalation cascade (B3) was cheaper and numerically more successful (0.917 vs 0.850). — [arXiv HTML](https://arxiv.org/html/2609.26532)
- **Jev-LiteMAS** (orchestrator-worker plus evaluator-optimizer in effect; the paper does not use those terms).
  - Jev chooses the next expert, or STOP, from the legal candidates after each expert finishes. Routing is grounded in prior expert outputs rather than a pre-generated plan; this "prevents up to 18.0 points in accuracy loss."
  - At review points Jev gives d_t ∈ {pass, escalate}. Escalated artifacts go to an LLM reviewer that returns a verdict and feedback; a repair expert revises; the result is re-screened. The loop is bounded by an LLM-call budget B.
  - "Local acceptance and the STOP action remain separate." — [arXiv](https://arxiv.org/abs/2610.21411); [HTML](https://arxiv.org/html/2610.21411)
- **JevAgentHarness.**
  - Eight decision points: tool, arguments, and next action, plus loop-control points (write memory, read memory, reflect, stop, route).
  - Cascade mode: the TDM answers first and is used only above a fitted threshold; below it the LLM decides.
  - The final configuration delegated tool + argument cascades plus a reflection trigger, saving 14.2% cost with Flash and changing no outcome on 500 tasks. — [arXiv HTML](https://arxiv.org/html/2610.21412)
- **Jev-Mem.** A System-One control plane over a multi-relational memory plane and a System-Two reasoning plane. Jev handles typing and relational organization during construction, and "query routing, retrieval-budget allocation, graph traversal, candidate scoring, and adaptive stopping" during retrieval. — [arXiv](https://arxiv.org/abs/2609.23986)
- **SearchJev.** A dual-system search agent covering relevance, evidence sufficiency and search-action decisions. It "delegates uncertain judgments to System 2, which retains planning, query generation, and answer composition." — [arXiv](https://arxiv.org/abs/2610.05107)
- **Crash narratives (a chained/gated structure).** "a detail question is read only when its presence question has fired" (τ_g = 0.5). This is a screen-then-detail chain, with the raw answer kept beside the gated one and a leakage rate λ_v measured. — [arXiv HTML](https://arxiv.org/html/2609.24052)
- **Edge orchestration (2609.22753).** TDM intent fields feed a "shared validator, admission policy, and scheduler." — [arXiv](https://arxiv.org/abs/2609.22753)
- **Judge cascades (2609.26550, 2610.20634).** Accept confident TDM verdicts and escalate the rest to a reasoning or frontier judge. — [2609.26550](https://arxiv.org/abs/2609.26550); [2610.20634](https://arxiv.org/abs/2610.20634)
- **2610.13092 cautions** that agent-level gains do not follow from decision-level savings: "Auxiliary reasoning and additional interactions absorb decision savings, while failed recovery and premature completion limit successful delivery." — [arXiv](https://arxiv.org/abs/2610.13092)

### Inferences
Mapping to our five structures:

| Our structure | Where it appears |
|---|---|
| Single | Confidence-gated routing; intent routing |
| Parallel | Speculative fan-out; composite scoring; parallel questions; beam frontiers |
| Chained | Crash-narrative presence → detail; skill suggestion rank → verify; smart-home split → re-evaluate; OpenAI's dependent requests; hierarchical greedy descent |
| Orchestrator-worker | Intent routing to specialist LLMs/handlers; Jev-LiteMAS expert selection; OpenRouter Jev Router |
| Evaluator-optimizer | Jev-LiteMAS screen → review → repair; SDE cascade (verify → escalate, one-shot not iterative); autoresearch loop (LLM optimizer, TDM as feature extractor) |

- No source names or unifies these as a taxonomy over decision units. TypeSafe's four patterns are mostly single-call parallel structures plus code. They deliberately avoid multi-call loops.
- TypeSafe's "parallel, no hidden context" property means that in its framing, composition always happens in caller code, never inside the model.

### Gaps
- I found no source that composes TDM decision units recursively (a decision unit whose action invokes another decision unit as a formal object) or describes a typed "decision graph" IR.
- I did not read the TypeSafe "Parallel questions," "Simple memory system," "Re-ranking," or "Citation check" cookbooks in detail. They may hold more composition examples.

---

## Q4. Applications where TDM outputs trigger function code or tool calls

### Takeaway
Yes, several:
- TypeSafe's function-calling cookbook turns a sentence into a Python call. A Choice picks the function; Choices and Nouls fill its `Literal`/`bool` arguments.
- OpenAI's Decisions voice guide maps each Choice answer to an app action and uses a `needs_response` question to trigger a Responses-API tool loop.
- LangChain's `AutoModeMiddleware` blocks risky tool calls.
- The REFLEX and JevAgentHarness papers delegate tool and argument choices.
- Browserbase's Stagehand `act()` uses Jev for action selection with a 0.7 fallback.

Notably, the TypeSafe function-calling cookbook computes a call-level confidence but does not show a gate before `.run()`.

### Cited Findings
- **TypeSafe function-calling cookbook.**
  - "a sentence goes in, and out comes a function name and its arguments as evaluated enums, each with a confidence."
  - Ten trading functions. `closed_sets` reads type hints and classifies arguments: `Literal` → choice; `list[Literal]` → set, with one Noul per member; `bool` → flag. A `stated` Noul makes an argument optional: "When the answer is no, the call leaves that argument out and the function's own default applies."
  - 54 questions per command in one request: a `__tool__` Choice plus every function's arguments. The dispatcher "reads only the chosen function's answers," so this is speculative fan-out.
  - Confidence rule: "`confidence` reports the least certain judgement in the call, rather than the product of all of them, since one wrong argument is enough to spoil the result."
  - `CALLS[command].run()` executes the function. I found no confidence threshold before execution in the text. — [docs.typesafe.ai/cookbooks/function_calling](https://docs.typesafe.ai/cookbooks/function_calling.md)
- **TypeSafe "How to build" page, tool-call trace verification.** A broad Noul "Is `trace.tool_calls` correct" is decomposed into nine atomic Nouls (tool relevance, argument–schema conformance, coordinate reuse, date/unit match). — [docs.typesafe.ai/concepts/how-to-build-with-system-one](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- **OpenAI Decisions voice guide.**
  - "Each Decisions question is a choice mapped to an action your app runs" (e.g. `cabin_temperature` ∈ {temperature_up, temperature_down, none}). "An answer of `none` is a no-op for that action."
  - A `needs_response` question decides whether the server calls the Responses API, which uses function tools (`start_navigation`, `find_restaurants`) in a call/output loop.
  - Native delegation lets GPT-Live call Decisions directly.
  - The app should "Wait for confirmation, then send the result to Live." For out-of-order results, "Apply the newest relevant result for each direction."
  - No numeric thresholds are given. — [OpenAI decisions-voice guide](https://developers.openai.com/api/docs/guides/decisions-voice)
- **OpenAI main guide.** It contrasts Decisions with function calling: use function calling "when you need a model to request a tool call with arguments." — [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions)
- **LangChain blog "Building a Harness with Jev"** (Sydney Runkle, Hunter Lovell; Sep 17, 2026).
  - `AutoModeMiddleware(tools=["bash"])` "uses Jev to check tool calls for risky decisions it may take, and block calls before the tool executes."
  - `ModelRouterMiddleware` picks a model per run; its probabilities and confidence stay in agent state. — [LangChain blog](https://www.langchain.com/blog/building-a-harness-with-jev)
- **LangChain blog "Building Production Agents with Jev and LangGraph"** (same authors; Sep 25, 2026).
  - Browserbase's rebuild of Stagehand `act()`: Jev picks the action type and element, and "anything below a 0.7 confidence threshold falls back to an LLM." Median latency went from 1.97 s to 0.46 s.
  - A document-review graph routes each page to set-aside, LLM PII redaction, `attorney_review` (a LangGraph interrupt), or ready.
  - LangSmith traces record "the probabilities behind the decision." Checkpointing means "a failed run resumes with the decisions it already made." — [LangChain blog](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph)
- **Jev in the Wild projects** (per paper):
  - pi-jev (a tool-call risk gate).
  - browser-use Jev Ultrafast, where Jev "selects the action and target but does not generate the text to be entered into a field."
  - jev-router (per-turn model tier).
  - TypeSafe Mario (emulator control).
  - tax-doc-classifier, where "trust and fallback decisions remain in deterministic code." — [arXiv HTML 2609.30216](https://arxiv.org/html/2609.30216v1)
- **REFLEX.** Jev chooses tools and actions from typed sets. Arguments are either deterministic functions of the state or filled by a cheap generative executor. — [arXiv HTML](https://arxiv.org/html/2609.26532)
- **JevAgentHarness.** Tool and argument cascades with fitted thresholds. — [arXiv HTML](https://arxiv.org/html/2610.21412)
- **kotoba-lang.** "Code decisions are emitted as wire-reference proposals with a pointer to the function referenced"; `jev_holes.py` asks one Choice per code hole, verifies with tests, and backtracks through the model's ranking. — [GitHub](https://github.com/kotoba-lang/typed-decisions)
- **Network orchestration papers.** Typed fields become A1 policies and admission/scheduling actions. — [2609.23136](https://arxiv.org/abs/2609.23136); [2609.22753](https://arxiv.org/abs/2609.22753)

### Inferences
- **Two styles of TDM-driven action exist:**
  1. Direct dispatch: a Choice picks a handler or function, and Choices/Nouls fill its arguments (TypeSafe function calling, OpenAI voice actions, intent routing).
  2. Gating: a TDM approves or blocks an action that someone else proposed (AutoModeMiddleware, pi-jev, guardrails, the SDE verifier).
- The function-calling cookbook's "min over arguments" call confidence is a concrete belief aggregation for a composite action. Yet the cookbook leaves the act/abstain rule unstated, which leaves room for an explicit decision rule.

### Gaps
- I could not confirm whether the TypeSafe `Dispatcher` (dispatch.py) applies any internal confidence gate before `.run()`. The source file was not inspected.

---

## Q5. Decision engines, decision graphs, orchestration frameworks and integrations built on TDMs

### Takeaway
There is no official "decision graph" or "decision engine" framework. The ecosystem consists of:
- Integrations: LangChain's `langchain-typesafe` (TypeSafeClassifier plus experimental middleware), community LangGraph nodes and routers, OpenRouter's Decisions endpoint plus a Jev Router plugin, and Vercel AI Gateway.
- Small DSLs: jevlang.
- MCP and agent tools from open-model vendors.

langgraph-jev has the clearest framework-level belief/decision split (per-question thresholds plus a low-confidence policy). I found no Promptfoo provider.

### Cited Findings
- **langchain-typesafe** (official LangChain integration). `TypeSafeClassifier` runnable; experimental `ModelRouterMiddleware`, `ModelChoice` and `AutoModeMiddleware`. — [LangChain blog](https://www.langchain.com/blog/building-a-harness-with-jev)
- **langgraph-jev** (iroy2000, community).
  - `JevNode` is a LangGraph node, "not an LLM and not an LLM wrapper."
  - `route_by_decision(decision, field="work_type", routes={...}, fallback="human_review")`.
  - Per-question `thresholds={"work_type": 0.85, "priority": 0.90}` with `low_confidence="allow"|"human_review"|"error"`.
  - "Jev makes the probabilistic decision; your application code decides what to do with it. Routing stays deterministic."
  - "Low-confidence decisions are never silently discarded."
  - Example graph: understand → Jev → ticket → routed workers (coding, support, docs). — [GitHub iroy2000/langgraph-jev](https://github.com/iroy2000/langgraph-jev)
- **langgraph-jev-router** (JTankariya; PyPI). A "native LangGraph conditional edge" for routing between specialized agents, with helpers for conditional edges, command nodes and prebuilt supervisors. It states it is not affiliated with TypeSafe. I saw it only via search snippet. — [GitHub](https://github.com/JTankariya/langgraph-jev-router); [PyPI](https://pypi.org/project/langgraph-jev-router/)
- **OpenRouter.**
  - Serves `typesafe/jev-1.14` and `~typesafe/jev-latest` (1.13 is still available) via `POST /api/alpha/decisions`. Primitives are Choice, Noul, Score and Box; output tokens are free. — [OpenRouter Jev hub](https://openrouter.ai/docs/guides/community/jev)
  - **Jev Router plugin** (`"id": "jev-router"`): "Jev evaluates the conversation to identify what the task needs," then picks a model and reasoning effort under `cost_tier` low/medium/high ("a routing preference, not a fixed model ..."). `models`/`allowed_models` are soft preferences with fallback; `excluded_models` is a hard limit ("Exclusions are never ignored"). The `X-OpenRouter-Metadata` header exposes the reason for each choice. — [OpenRouter Jev Router](https://openrouter.ai/docs/guides/routing/routers/jev-router.md)
- **Vercel AI Gateway.**
  - A Vercel changelog entry says OpenAI's Decisions API is available through an OpenAI-compatible `/v1/decisions`. — [Vercel changelog](https://vercel.com/changelog/openai-decisions-api-now-available-on-ai-gateway)
  - A third-party summary says Jev was added to AI Gateway via an AI SDK experimental API. — [createwith.com](https://createwith.com/tool/vercel/updates/vercel-adds-jev-from-typesafe-ai-to-ai-gateway)
  - Sources disagree on the SDK method name (`experimental_evaluate` vs `experimental_decide`). I could not extract the Vercel page body to verify.
- **jevlang** (Suman Michael; PyPI 0.1.0, Sep 20, 2026; MIT; alpha).
  - The `~` operator asks a TDM question (string → probability; list → scale; dict → label), e.g. `if msg ~ "is urgent" > 0.8:`.
  - A `jev` block feeds if/elif/else with `case` guards such as `if confidence > 0.8`. It recommends that consequential branches carry a guard plus an `else`, in the spirit of "act, confirm, or hand to a human."
  - `ask_all` batches questions. Workflows are plain functions with "no graph, runner, or shared state object."
  - It has no caching or replay. — [PyPI jevlang](https://pypi.org/project/jevlang/)
- **jev-router (prismhq).** A LiteLLM-based router in which a Jev decision picks the serving model. Seen via search snippet only. — [search result listing](https://openrouter.ai/docs/guides/community/jev) (not independently verified)
- **Open-model serving and agent tooling:**
  - StartLux `startlux-decide serve` (vLLM-fronted, `/v1/decisions` and `/v1/systemone`-compatible). — [GitHub](https://github.com/StartLuxLabs/StartLux-Decision)
  - Laya `laya-serve` (Jev-compatible `/v1/systemone`), an MCP server (`laya[mcp]`), and LangChain/LangGraph mentions. — [HF Laya](https://huggingface.co/convaiinnovations/laya)
  - OpenDecider exposes `decide`, `choose`, `yes_no` and `score` as MCP and agent-framework tools, plus a `Guard` class. — [HF OpenDecider](https://huggingface.co/manjunathshiva/opendecider-nano)
- **TypeSafe agent skill and coding-agent guidance** exist (`/agent-skill`, `/introduction/coding-agents`), but I did not analyze them in detail. — [docs.typesafe.ai/llms.txt](https://docs.typesafe.ai/llms.txt)
- **Jev in the Wild** reports no data on LangChain/LangGraph, gateways, OpenRouter or Promptfoo. — [arXiv HTML](https://arxiv.org/html/2609.30216v1)
- **Promptfoo.** I found no Promptfoo provider for TDMs in searches.

### Inferences
- **Framework-level support is thin.** It amounts to conditional-edge routing with per-question thresholds and fallbacks (langgraph-jev) or middleware (LangChain).
- **No framework treats the decision rule as a separate, versioned, re-runnable artifact over logged beliefs.** LangSmith traces log probabilities, and LangGraph checkpointing preserves decisions for resume. That is persistence, not offline rule re-evaluation.
- **Our five-structure decision-unit framing would be novel relative to all observed frameworks.**

### Gaps
- No primary Vercel AI SDK documentation was retrieved, so the method name for Jev or Decisions is unverified.
- I found no Promptfoo provider and no "decision graph" or "decision engine" project. The MCP-market "TypeSafe Jev Decision Engine" skill listing was not inspected.
