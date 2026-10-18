# Everyone thresholds beliefs; nobody formalizes the rule

Almost every part of the thesis already has precedent. What nobody has published is the combination. Classical decision theory already says that a Bayes-optimal rule depends on the evidence only through the posterior. So "belief, then a rule with explicit values" is textbook (Wald, Berger, Elkan, Chow), and re-tuning those values offline over recorded beliefs follows from the same result. The 2026 typed-decision-model (TDM) literature has moved the same way. About 190 arXiv papers mention Jev or TDMs since the model's 15 September launch, about 85 of them evaluations. Vendor docs, application papers and the newer evaluations all say "the model gives probabilities, your code decides." At least four papers state the belief/rule split outright: Probability Contracts (2609.37470), TypedBench (2610.11392), DICE (2610.14404) and a cs.SE governance paper (2610.10978). JevAgentHarness (2610.21412) derives a cost-based threshold and refits it on shadow logs. At least eight papers replay rules or cascades offline from recorded probabilities. What is still missing is the following. First, a rule as a typed, pure expression with an explicit value table, where abstain is an ordinary action. Second, a taxonomy of how decision units compose, with structure kept apart from behavior: Anthropic's patterns are built from generative calls, and TypeSafe's four patterns are mostly single-call. Third, any evaluation of evaluator-optimizer loops built from TDM calls. Fourth, any TDM leaderboard that scores decisions rather than beliefs. Fifth, any TDM evaluation on naturally occurring text created after the models were released. The paper should therefore claim formalization, unification and two empirical firsts. It should not claim the split itself. As the evaluation is currently specified (accuracy, AUROC, Brier, ECE, repeat agreement, cost, latency), it measures beliefs only. That leaves the paper's central claim untested unless rule-level re-deciding experiments are added. The repo name also needs to change, because three unrelated projects already call themselves "JevBench."

## About 190 papers in five weeks agree that the probability is not the decision

The corpus comes from arXiv API queries run on 18 October 2026. The newest indexed record is dated 15 October, so papers posted on 16-18 October may be missing. Roughly 45 of the evaluation papers below were summarized from abstracts only, so treat their finer numbers as provisional until the full texts have been read.

### Evaluation papers: real speed gains, no accuracy gain from the typed readout

The anchor is the audit by Tang and Zheng (2609.32160, 26 September). It reviewed 28 papers posted 19-24 September. Its main finding: **"the typed readout itself has not shown an independent accuracy advantage over comparable label-probability readouts,"** with Jev's clearest gains in latency and cost. The evidence base is thin, because **21 of 27 model-evaluating papers had no label-probability baseline** and 12 of 27 reported no confidence intervals ([Audit](https://arxiv.org/html/2609.32160)). The audit's 14-item checklist covers baselines, test design, statistics and confidence use. It treats the TDM inside a threshold cascade (items B2 and C3), but **it has no item for the decision rule or values as a separate artifact**. That is a natural extension for this paper to propose. Several matched-readout papers support treating a TDM as one kind of belief source rather than a special mechanism. Visual Jev finds a typed head equal to the LM head (.761 vs .761) ([Audit](https://arxiv.org/html/2609.32160)). LLM-as-Jev (2610.02076) argues that "modern LLMs are inherently effective decision models" when read off the shelf ([arXiv](https://arxiv.org/abs/2610.02076)). Deußer et al. score Qwen3.8-27B through exact next-token option probabilities, and Jev beats it on 27 of 37 datasets ([arXiv](https://arxiv.org/abs/2609.37647)). Together these justify including DeepSeek V4.1 Flash via logprobs as a TDM.

After the audit, the questions shifted from "is Jev accurate?" to "is its probability usable for acting?" The findings sort into five groups.

**Breadth benchmarks.** Results here are mixed. System1-Arena (2610.21244) evaluates 30 models, including the OpenAI Decisions API. It finds the largest System-1 models match fast closed LLMs at a quarter of the latency, but small ones rarely succeed in closed loops ([arXiv](https://arxiv.org/abs/2610.21244)). On MathQA, Jev is 17.7 points below the frontier median ([arXiv](https://arxiv.org/abs/2610.11978)).

**Calibration.** It depends on the model and the workload, and it often points opposite ways. TypedBench calls the hosted model "systematically underconfident" ([arXiv](https://arxiv.org/abs/2610.11392)). JEVal finds decision models "substantially overstating" top-option probability ([arXiv](https://arxiv.org/abs/2610.03935)). One alignment-detection paper reports pooled ECE .047 but a median per-benchmark ECE of .168 ([Audit](https://arxiv.org/html/2609.32160)).

**Coherence and option-set dependence.** Jev's three single-label probabilities sum to 1.14 ([arXiv](https://arxiv.org/abs/2609.33209)). A preregistered IIA test finds that adding one option shifts log-odds by **0.20-0.52 nats RMS, 1.2-3x run-to-run noise** ([arXiv](https://arxiv.org/abs/2610.16655)). In short, a belief is conditional on the option list it was computed over.

**Labels and framing.** **Swapping yes and no flips 50.5 of every 100 Jev answers** ([arXiv](https://arxiv.org/abs/2610.00346)). Labels override definitions, and in open TDMs the cause sits in prompt rendering, not the decision head ([arXiv](https://arxiv.org/abs/2610.02586)). TDMs used as judges are biased in 3-8 of 12 CALM tests, and "good calibration does not protect against bias" ([arXiv](https://arxiv.org/abs/2610.18122)).

**Security and agents.** The results show the limits of confidence-based abstention. One appended opinion flips 12.1% of decisions ([arXiv](https://arxiv.org/abs/2609.31142)). Under an option-channel attack, "a decision an attack has reversed is no less confident than the one it replaced" ([arXiv](https://arxiv.org/abs/2610.12292)). Faster local decisions lower τ-bench success as errors accumulate ([arXiv](https://arxiv.org/abs/2610.03935)), and decision savings in agents are absorbed by extra reasoning and interactions ([arXiv](https://arxiv.org/abs/2610.13092)).

At least six papers include the OpenAI Decisions API (public beta from 6 October), always as one row among many. One of them, Reading Right, Acting Wrong, reports accuracy of 0.706 vs 0.763 for Jev and finds it "acts wrongly in 26% of states with every fact right" ([arXiv](https://arxiv.org/html/2610.18579)). **No paper separates OpenAI Decisions' calibration by question type or compares it with GPT-6 Luna logprobs on matched items.**

### Model and method papers replicate Jev but rarely address decisions

The model papers are open replications. One family is encoders with per-option markers: Von, OpenDecider, Laya and open-jev-deberta. The other is decoders read through option or placeholder logits. Examples are this-that-model-1.0 ([arXiv](https://arxiv.org/abs/2609.23886)), Releasing the Inner Jev ([arXiv](https://arxiv.org/abs/2610.17205)), StartLux-Decision ([arXiv](https://arxiv.org/abs/2610.17309)), Intern-Decision ([arXiv](https://arxiv.org/abs/2610.22131)), SearchJev ([arXiv](https://arxiv.org/abs/2610.05107)) and Verdict ([arXiv](https://arxiv.org/abs/2610.20778)). The usual training story is RLCD and its variants. But SBERT2S1 finds that **after temperature scaling, no objective is clearly better calibrated than cross-entropy** ([arXiv](https://arxiv.org/abs/2610.02486)).

Only one model paper bears directly on the thesis. StartLux reports that "well-calibrated individual predictions need not remain calibrated after downstream selection or routing," and that top-of-32 selection turns 92% individual accuracy into 78%. It concludes that **"calibration and acceptance thresholds must therefore be evaluated on the outputs of the deployed policy"** ([arXiv HTML](https://arxiv.org/html/2610.17309)). This is the strongest empirical warning against treating a calibrated belief as safe to plug into any composed rule, so the paper must address it.

Three of our six TDMs have no paper, only primary cards or repos. Von 1.3 is a 395M ModernBERT with an Option-Marker head, order-invariant since 1.2 ([HF](https://huggingface.co/wfzyx/von)). OpenDecider-nano is a 400M Ettin encoder distilled from Qwen3-235B and DeepSeek V4.1 Flash ([HF](https://huggingface.co/manjunathshiva/opendecider-nano)). open-jev-deberta-v3-large is from kotoba-lang ([GitHub](https://github.com/kotoba-lang/typed-decisions)). Cite these as model cards, not papers.

### Applications always gate on confidence and keep a fallback

Every application paper surveyed keeps a stronger fallback (an LLM or a human) and gates on confidence. None runs a TDM fully autonomously. Examples:

- REFLEX uses π(s) = â if c ≥ τ and the action is executable, otherwise the strong LLM ([arXiv HTML](https://arxiv.org/html/2609.26532)).
- JEV-as-a-Judge accepts confident verdicts with a threshold "frozen in advance" ([arXiv](https://arxiv.org/abs/2609.26550)).
- The crash-narrative paper chains a presence question into a detail question and defines a review budget H(π\*) ([arXiv HTML](https://arxiv.org/html/2609.24052)).
- Jev-LiteMAS is the clearest orchestrator-plus-evaluator composition. Jev picks the next expert or STOP and screens artifacts, and flagged artifacts go to an LLM reviewer and a repair expert in a budgeted loop. **Generative tokens fall 12.7-54.6% with accuracy within 1.34 points** ([arXiv HTML](https://arxiv.org/html/2610.21411)).

Two numbers on this page need caution. For JEV-as-a-Judge, the audit's summary (92.5 vs 93.1 at 57% of the fee) and the paper's abstract (+0.9 points at 41% of the fee) differ, probably across versions. Check before quoting either. A 2,170-project GitHub study finds Choice used in 81.0% of projects and concludes Jev is "a reusable decision component whose functionality varies with the surrounding workflow" ([arXiv](https://arxiv.org/abs/2609.30216)).

Two styles of TDM-driven action appear.

- **Direct dispatch.** A Choice picks a function and other questions fill its arguments. TypeSafe's function-calling cookbook runs `CALLS[command].run()` with call confidence defined as the minimum over arguments, yet **shows no gate before execution** ([TypeSafe](https://docs.typesafe.ai/cookbooks/function_calling.md)). OpenAI's voice guide maps "each Decisions question" to "an action your app runs" ([OpenAI](https://developers.openai.com/api/docs/guides/decisions-voice)).
- **Gating.** The TDM approves or blocks an action someone else proposed. LangChain's `AutoModeMiddleware` blocks risky tool calls before they run ([LangChain](https://www.langchain.com/blog/building-a-harness-with-jev)), and Browserbase's Stagehand falls back to an LLM below 0.7 confidence ([LangChain](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph)).

### Vendor guidance already says "your code decides"

TypeSafe's guidance is explicit:

- "Keep control flow, deterministic rules, and side effects in code" ([TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)).
- "Thresholds scale with risk ... Your code encodes the risk tolerance," set out as act, confirm and escalate bands ([TypeSafe](https://docs.typesafe.ai/confidence.md)).
- The guardrails cookbook comes closest of any source to the decision unit: **"TypeSafe supplies the assessment; your application owns the decision."** It defines named policies ("A policy is just those numbers under a name") and reuses one cached assessment under two policies to produce block versus review ([TypeSafe](https://docs.typesafe.ai/cookbooks/llm_guardrails.md)).

That is offline re-deciding in a cookbook cell. OpenAI's guide says to "choose thresholds based on the cost of false positives and false negatives" and to "send separate requests" for dependent decisions ([OpenAI](https://developers.openai.com/api/docs/guides/decisions)).

Community tools sit one step from a rule layer:

- langgraph-jev: "Jev makes the probabilistic decision; your application code decides what to do with it," with per-question thresholds and a low-confidence policy ([GitHub](https://github.com/iroy2000/langgraph-jev)).
- kotoba-lang keeps `:probabilities` apart from `:admit?` in its wire format ([GitHub](https://github.com/kotoba-lang/typed-decisions)).
- jevlang is a small DSL, `if msg ~ "is urgent" > 0.8:`, with no caching or replay ([PyPI](https://pypi.org/project/jevlang/)).

**No source treats the rule as a versioned, re-runnable artifact over logged beliefs.** LangSmith traces and LangGraph checkpoints keep decisions so a run can resume, which is persistence rather than re-evaluation.

### How close each precedent comes

| Work | Belief/rule separation | Explicit values | Offline re-deciding | Composition |
|---|---|---|---|---|
| Probability Contracts 2609.37470 ([arXiv](https://arxiv.org/html/2609.37470)) | Explicit: "evaluate probability interfaces with their decision rules" | Defer cost; 99-cost grid | Yes, across cost grid | No |
| TypedBench 2610.11392 ([arXiv](https://arxiv.org/html/2610.11392)) | Explicit: argmax vs Bayes policy | Cost matrices (e.g. phishing 20:1) | "Offline via a hybrid threshold sweep" | No |
| JevAgentHarness 2610.21412 ([arXiv](https://arxiv.org/html/2610.21412)) | Implicit; threshold derived from costs | qL − ΔC/V, $1 per solved task | Shadow-mode refit | Agent cascades at 8 decision points |
| Probabilistic Sensing, Deterministic Authority 2610.10978 ([arXiv](https://arxiv.org/html/2610.10978)) | Explicit: score → true/false/unknown → deterministic contract | False-positive ceiling | Bounded verdict flips | No |
| DICE 2610.14404 ([arXiv](https://arxiv.org/html/2610.14404)) | Explicit "protected decision rule" | No | No | Adapter pipeline |
| Risk-budgeted decisions 2610.19811 ([arXiv](https://arxiv.org/html/2610.19811)) | Threshold as decision rule; fallback when deferral unavailable | False-omission risk target; LTT | Fit/calibration/test pools | No |
| Rejection-policy transfer 2610.03387 ([arXiv](https://arxiv.org/html/2610.03387)) | Rejection policy separate | No | "Recomputation without model calls" | No |
| Reading Right, Acting Wrong 2610.18579 ([arXiv](https://arxiv.org/html/2610.18579)) | Facts vs action | No | No | Parallel sub-questions "combined by code" |
| Jev-LiteMAS 2610.21411 ([arXiv](https://arxiv.org/html/2610.21411)) | Decisions vs generation | Cascade cost equations | No | Orchestrator plus evaluator loop |
| TypeSafe guardrails and patterns ([cookbook](https://docs.typesafe.ai/cookbooks/llm_guardrails.md), [patterns](https://docs.typesafe.ai/patterns.md)) | Explicit in prose | Named policies; composite weights | Cached assessment re-decided | Fan-out, gated routing, composite, intent routing |
| Wei Sun 2604.00414 ([arXiv](https://arxiv.org/abs/2604.00414)) | "Separates decision-relevant signals from the policy" | Not stated in abstract | Not stated | Routing, adaptive inference, sequential |

Three other results warn that a better belief does not guarantee a better decision:

- **Using Jev 1.13.0's full probabilities under TypedBench's cost matrices costs 2,300 vs 1,080 for argmax.** A miscalibrated belief makes the Bayes plug-in rule worse ([arXiv](https://arxiv.org/html/2610.11392)).
- A matched random-escalation control does as well as confidence-gated escalation in RAG verification. In the paper's words, "what buys the saving is the escalation share and not the probability" ([arXiv](https://arxiv.org/html/2610.20634)).
- Frozen rejection policies do not transfer across workloads ([arXiv](https://arxiv.org/html/2610.03387)).

The paper should present these as evidence for evaluating the belief and the rule jointly.

## Seven leaderboards score beliefs; none scores decisions or uses post-release text

Seven public TDM evaluations exist. All of them score beliefs: argmax or chance-corrected accuracy, calibration, coherence. Cost and latency appear only as axes or caps, and abstentions count as failures.

| Benchmark | Scale and design | Freshness / contamination | Decision-level scoring | Our six TDMs covered |
|---|---|---|---|---|
| JevBench, Benchmark Heaven ([board](https://benchmarkheaven.com/jev-models), [README](https://github.com/fstandhartinger/jevbench)) | v1.7.46, 1,500 decisions per system (1,200 sealed + 300 public), 183 systems; hand-written English | Fresh sealed draws retired once sent to a provider (A4, A5); "not a contamination proof" | No; abstentions "count as unanswered" | gpt-6-luna, DeepSeek Flash, open-jev-deberta, Jev; Von only historically |
| JevBench, metamorphic coherence, QUB ([report](https://jevbench.github.io/report/JevBench-technical-report.pdf)) | 50 relations, 12,000 tests, 21 open models | Frozen, public, synthetic | `threshold_sweep` tests monotonicity only | "von" (75.9); no closed APIs |
| jevbench.dev ([site](https://jevbench.dev)) | StarCraft II, 4 models | Procedural, no policy | Win rate | Jev |
| Jev Decision Index, HF ([Space](https://huggingface.co/spaces/multimodalart/jev-decision-index)) | Chance-corrected "balanced skill"; coverage figures conflict | Public benchmarks | No | Unverified |
| Artificial Analysis Decision Index ([AA](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index)) | 4 evals, launched 13 Oct 2026 | Mostly adapted public sets | "I don't know" scored as an option; When2Call | GPT-6 Luna (Decisions); ranks not retrievable |
| LocalLLaMA/typed-decisions ([HF](https://huggingface.co/datasets/LocalLLaMA/typed-decisions)) | 1,600 synthetic cases, teacher-mean gold | Public train split | Accuracy only | No |
| Jev-vs-Laya harness ([GitHub](https://github.com/pavanjava/jev_and_laya_benchmarking)) | 400 test cases | Laya fine-tuned on train | "No confidence thresholds, abstention rules, or decision-cost analysis" | No |

Benchmark Heaven's board is the closest analogue to our harness, and the paper should cross-reference its numbers for gpt-6-luna (Composite 62.5, Capability 73.5), DeepSeek V4.1 Flash and open-jev-deberta-v3-large (Capability 35.4). Its contamination practice is careful, but its "fresh" items are newly authored prompts, not naturally occurring text ([board](https://benchmarkheaven.com/jev-models)). **No board reports AUROC or repeat agreement. No third-party board has numbers for OpenDecider nano or Von 1.3.** Our numbers for those two would be the first independent ones. Von's own leaderboard issue shows decision policy contaminating a belief benchmark: a Noul "decision rule" changed to always commit was blamed for its board Intelligence of 0.0 ([Issue #143](https://github.com/fstandhartinger/jevbench/issues/143)). This is a concrete argument for scoring beliefs and rules separately.

**The name collision is real and should be resolved before submission.** Benchmark Heaven's JevBench is by far the most prominent: a Show HN with 154 points, 183 systems, and sibling boards ImageJevBench and AudioJevBench ([HN](https://news.ycombinator.com/item?id=49800574)). Queen's University Belfast owns the GitHub org `JevBench` and the PyPI name `jevbench`, uploaded 1 October ([PyPI](https://pypi.org/pypi/jevbench/json)). A third party holds jevbench.dev. No trademark filing was found, but USPTO, EUIPO and WIPO were not searched directly, so trademark status is unknown rather than confirmed absent. "Jev" is TypeSafe AI's product name ([The New Stack](https://thenewstack.io/typesafe-jev-system-one/)). That makes a Jev-named benchmark read as vendor-centred, which undercuts a cross-provider paper that names no platform. A neutral name fixes this. Candidates such as FreshTDM, TypedBeliefBench or ReviewTDM were suggested, but none was collision-checked.

## Seventy years of decision theory already justify the split

The paper's formal core can be stated almost entirely in classical vocabulary. That makes the contribution easier to defend, but it should then be presented as formalization rather than invention. Berger's terms map directly onto the thesis:

- the state of nature θ is the latent answer to a typed question;
- the observation x is the evidence;
- the posterior π(θ|x) is the belief;
- the decision rule δ is our rule;
- the loss L(θ,a) is our explicit values.

The Bayes rule δ\*(x) = argmin_a Σ_θ L(θ,a)π(θ|x) needs the data only through the belief. So the values can be swapped and the rule re-run without calling the model again. **That is the theorem behind offline re-deciding, and it holds only when beliefs are calibrated** ([Berger 1985](https://doi.org/10.1007/978-1-4757-4286-2); [Wald 1949](https://doi.org/10.1214/aoms/1177730030)). Elkan derives the cost-ratio threshold p\* = (c10 − c00)/(c10 − c00 + c01 − c11). He also explicitly recommends computing decisions from probability estimates rather than retraining, which is the closest classical statement of the belief/rule split ([ML Anthology](https://mlanthology.org/ijcai/2001/elkan2001ijcai-foundations)). Three tools judge a model by the decisions it supports across value settings: ROC convex-hull operating points ([Provost & Fawcett 2001](https://doi.org/10.1023/A:1007601015854)), ROC tutorials ([Fawcett 2006](https://doi.org/10.1016/j.patrec.2005.10.010)), and decision curve analysis with net benefit across threshold probabilities ([Vickers & Elkin 2006](https://doi.org/10.1177/0272989X06295361)). Decision curves are a ready-made figure for re-deciding experiments.

### Abstention has a lineage from Chow to conformal risk control

**Chow's 1970 rule, "reject if max posterior < threshold," is a one-line decision rule over a belief.** Its threshold comes from the reject cost ([Chow 1970](https://doi.org/10.1109/TIT.1970.1054406); [Chow 1957](https://doi.org/10.1109/TEC.1957.5222035)). Selective classification adds the risk-coverage vocabulary ([El-Yaniv & Wiener 2010](https://jmlr.org/papers/v11/el-yaniv10a.html); [Geifman & El-Yaniv 2017](https://arxiv.org/abs/1705.08500)). Learning with rejection learns the reject function jointly with the predictor ([Cortes et al. 2016](https://doi.org/10.1007/978-3-319-46379-7_5)), with plug-in theory in [Herbei & Wegkamp 2006](https://doi.org/10.1002/cjs.5550340410).

Three methods give finite-sample, distribution-free guarantees for choosing a threshold on held-out data. They are risk-controlling prediction sets ([Bates et al. 2021](https://doi.org/10.1145/3478535)), conformal risk control ([Angelopoulos et al. 2022](https://arxiv.org/abs/2208.02814)) and Learn-then-Test ([Angelopoulos et al. 2025](https://doi.org/10.1214/24-AOAS1998)). Learn-then-Test is the closest formal analogue to "re-tune values offline with a guarantee." It is already applied to TDMs: naive threshold selection exceeded the target risk in roughly half of settings, against 7.8% for LTT ([arXiv](https://arxiv.org/html/2610.19811)). The guarantee inherits an exchangeability assumption between recorded and deployment beliefs, and the paper must state it.

Learning to defer differs from the thesis because it learns the deferral function jointly with the model ([Madras et al. 2018](https://arxiv.org/abs/1711.06664); [Mozannar & Sontag 2020](https://arxiv.org/abs/2006.01862)). The complementarity papers argue for optimizing team utility rather than standalone accuracy ([Wilder et al. 2020](https://doi.org/10.24963/ijcai.2020/212); [Bansal et al. 2021](https://doi.org/10.1609/aaai.v35i13.17359); [Steyvers et al. 2022](https://doi.org/10.1073/pnas.2111547119)). Our "defer" edge is the inspectable, rule-level counterpart.

### Proper scores rate beliefs; decision calibration licenses the split

Proper scoring rules reward honest beliefs. Gneiting and Raftery give the definitive characterization ([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437)), with the Brier score ([Brier 1950](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2)), the calibration/refinement decomposition ([DeGroot & Fienberg 1983](https://doi.org/10.2307/2987588)) and the link to elicitation ([Savage 1971](https://doi.org/10.1080/01621459.1971.10482346)). For metrics and recalibration, cite:

- ECE ([Naeini et al. 2015](https://doi.org/10.1609/aaai.v29i1.9602));
- temperature scaling ([Guo et al. 2017](https://arxiv.org/abs/1706.04599));
- isotonic regression ([Zadrozny & Elkan 2002](https://doi.org/10.1145/775047.775151));
- the Platt-vs-isotonic comparison ([Niculescu-Mizil & Caruana 2005](https://doi.org/10.1145/1102351.1102430)).

The single most important theoretical citation is **decision calibration** ([Zhao et al. 2021](https://arxiv.org/abs/2107.05719)). A belief only needs to be calibrated with respect to the class of rules that will consume it. That condition is exactly when the belief/rule split is safe. StartLux's finding that calibration breaks after selection or routing is the empirical counterpart under composition ([arXiv HTML](https://arxiv.org/html/2610.17309)).

The alternative philosophy is predict-then-optimize, or decision-focused learning ([Elmachtoub & Grigas 2022](https://doi.org/10.1287/mnsc.2020.3922); [Donti et al. 2017](https://arxiv.org/abs/1703.04529); [Mandi et al. 2024](https://doi.org/10.1613/jair.1.15320)). It fuses model and values, so the model must be retrained when costs change. The paper should present its decoupling as the deliberate opposite trade-off. It buys cheap value changes and auditability, and it pays when beliefs are miscalibrated, as the TypedBench argmax-vs-Bayes result shows.

### Influence diagrams, DMN and CEL are the engineering ancestors

Influence diagrams already compose chance, decision and value nodes into graphs ([Howard & Matheson 2005](https://doi.org/10.1287/deca.1050.0020); [Shachter 1986](https://doi.org/10.1287/opre.34.6.871); [Pearl 1988](https://doi.org/10.1016/C2009-0-27609-4)). Value of information gives a principled criterion for when to gather more evidence instead of acting ([Howard 1966](https://doi.org/10.1109/TSSC.1966.300074)). The difference: influence-diagram solvers derive optimal policies, whereas our units specify policies as auditable expressions. That is policy evaluation, not policy optimization.

OMG DMN is the closest industrial precedent for "decision logic separate from process and analytics." It has decision requirements graphs, decision tables with hit policies, the side-effect-free FEEL expression language, and formal releases from 1.0 (2015) to 1.6 (September 2026) ([OMG](https://www.omg.org/spec/DMN/)). The intellectual frame is Taylor & Raden's automation of "hidden decisions" ([record](https://finna.fi/Record/3amk.104663)). The deltas to state are these: DMN consumes crisp facts, not probabilistic beliefs; it has no native abstain outcome; and it has no proper-scoring or calibration layer.

CEL is designed for exactly the rule layer. The spec says it "evaluates in linear time, is mutation free, and not Turing-complete" ([cel-spec](https://github.com/google/cel-spec)). Its language definition says it is terminating, gradually typed, and has "no observable side effects" ([langdef](https://github.com/google/cel-spec/blob/master/doc/langdef.md)). It is used at scale in Kubernetes ValidatingAdmissionPolicy ([Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)) and Envoy RBAC ([Envoy](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/rbac_filter)). Its official Python binding was open-sourced in March 2026 ([Google](https://opensource.googleblog.com/2026/03/announcing-cel-expr-python-the-common-expression-language-in-python-now-open-source.html)). Even if the paper names no implementation, citing CEL and FEEL anchors the claim that "pure expression" is a well-defined, decidable class.

### Anthropic's taxonomy has generative nodes and a routing pattern we fold into rules

Anthropic's "Building effective agents" (Schluntz and Zhang; the page shows "Erik S.", 19 December 2024) separates workflows ("predefined code paths") from agents ([Anthropic](https://www.anthropic.com/research/building-effective-agents)). It names an augmented-LLM building block plus five workflows: prompt chaining, **routing**, parallelization (sectioning or voting), orchestrator-workers and evaluator-optimizer. The paper's five structures replace routing with "single." **Say this explicitly.** In our framing a route is a rule whose action selects the next unit, so it lives in behavior, not wiring. Without that sentence, a reviewer will read the list as a misquotation. Two other sources follow similar lines: LangGraph's docs mirror Anthropic's list ([LangChain](https://docs.langchain.com/oss/python/langgraph/workflows-agents)), and OpenAI's guide uses a coarser single/manager/decentralized split ([OpenAI PDF](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)). In every one of these the node is a generative call and the decision sits inside it. The paper's shift is to make the node a belief and the decision an explicit rule.

TypeSafe's own docs push the other way. They explicitly discourage loops: "Avoid agent `while` loops when a software workflow can express the same behavior" ([TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)). That explains why evaluator-optimizer is the least-studied TDM structure.

### Compound systems, cascades and panels set the empirical priors

The compound-AI line treats model calls as program parts:

- the BAIR blog ([Zaharia et al. 2024](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/));
- DSPy ([arXiv](https://arxiv.org/abs/2310.03714));
- LMQL ([arXiv](https://arxiv.org/abs/2212.06094));
- Language Model Cascades, which treats compositions of LM calls as probabilistic programs and is the theory ancestor of "belief as a first-class value" ([arXiv](https://arxiv.org/abs/2207.10342)).

Wei Sun's "Decision-Centric Design for LLM Systems" (2604.00414, April 2026) is **the most direct prior statement of "behavior lives in rules."** It separates "decision-relevant signals from the policy that maps them to actions" so that failures can be attributed to signal estimation, decision policy or execution ([arXiv](https://arxiv.org/abs/2604.00414)). It must be cited and contrasted. Only its abstract was read. The contrast is that its signals are not typed beliefs from a TDM, and it is not organized around composition structures.

Cascade theory agrees that gains depend on how good the deferral score is:

- Confidence deferral "often works remarkably well" except with specialists, noisy labels or shift ([Jitkrittum et al. 2023](https://arxiv.org/abs/2307.02764)).
- Routing and cascading can be unified ([Dekoninck et al. 2024](https://arxiv.org/abs/2410.10347)).
- Bouchard's identity splits the gain of score-based over random escalation into two AUROC terms. **More than two models gave no gain in 118 of 135 comparisons** ([arXiv](https://arxiv.org/abs/2605.06350)).
- UCCI shows that threshold policies on calibrated scores are cost-optimal under stated assumptions ([arXiv](https://arxiv.org/abs/2605.18796)).
- Trust or Escalate gives guaranteed human agreement for cascaded judges ([arXiv](https://arxiv.org/abs/2407.18370)).

The practical lineage includes FrugalGPT ([arXiv](https://arxiv.org/abs/2305.05176)), AutoMix ([arXiv](https://arxiv.org/abs/2310.12963)), RouteLLM ([arXiv](https://arxiv.org/abs/2406.18665)) and a 2026 TMLR survey ([arXiv](https://arxiv.org/abs/2603.04445)).

For parallel panels, PoLL ties its gains to "disjoint model families" ([arXiv](https://arxiv.org/abs/2404.18796)). Errors correlate across 350+ LLMs, with **60% agreement when both models err** on one leaderboard ([Kim et al. 2025](https://arxiv.org/abs/2506.07962)), and mistakes grow more similar with capability ([Goel et al. 2025](https://arxiv.org/abs/2502.04313)). The TDM version: LLM judges repeat Jev's wrong answer in 96% of verdicts on its most confident errors, so a replayed cascade gains at most 1.5 points ([Audit](https://arxiv.org/html/2609.32160)). Voting can even get worse as calls increase ([Chen et al. 2024](https://arxiv.org/abs/2403.02419)).

### Confidence elicitation, option bias and contamination complete the base

The logprob-read DeepSeek baseline sits in a contested literature. Base models are well calibrated on properly formatted multiple-choice and true/false questions ([Kadavath et al. 2022](https://arxiv.org/abs/2207.05221)). RLHF and RLVR degrade token-probability calibration ([Tian et al. 2023](https://arxiv.org/abs/2305.14975); [Leng et al. 2024](https://arxiv.org/abs/2410.09724); [Yaldiz et al. 2026](https://arxiv.org/abs/2601.13284)). Verbalized confidence is overconfident ([Xiong et al. 2024](https://arxiv.org/abs/2306.13063)), or else wins at scale ([Tao et al. 2025](https://arxiv.org/abs/2505.23854)). Verbalized scores take too few distinct values to threshold finely ([Sun et al. 2026](https://arxiv.org/abs/2606.22179)), which is an argument for real-valued beliefs when rules are thresholds. Option-token bias is documented in three papers ([Zhao et al. 2021](https://arxiv.org/abs/2102.09690); [Pezeshkpour & Hruschka 2023](https://arxiv.org/abs/2308.11483); [Zheng et al. 2024](https://arxiv.org/abs/2309.03882)). The encoder TDMs descend from NLI zero-shot classification ([Yin et al. 2019](https://arxiv.org/abs/1909.00161); [Laurer et al. 2023](https://arxiv.org/abs/2312.17543)) and GLiNER/GLiClass ([GLiNER](https://arxiv.org/abs/2311.08526); [GLiClass](https://arxiv.org/abs/2508.07662)). For time-split, contamination-limited design, the precedents are LiveBench ([arXiv](https://arxiv.org/abs/2406.19314)) and LiveCodeBench ([arXiv](https://arxiv.org/abs/2403.07974)). The motivation comes from Sainz et al. ([arXiv](https://arxiv.org/abs/2310.18018)) and the survey by Xu et al. ([arXiv](https://arxiv.org/abs/2406.04244)).

## Four contributions remain open if the paper scopes them precisely

### What is established, partial and open

| Thesis component | Status | Established by | What is left for this paper |
|---|---|---|---|
| TDM maps evidence plus typed question to a distribution | **Established** | Vendor docs ([TypeSafe](https://docs.typesafe.ai/concepts/system-one.md), [OpenAI](https://developers.openai.com/api/docs/guides/decisions)); matched readouts ([Audit](https://arxiv.org/html/2609.32160), [2610.02076](https://arxiv.org/abs/2610.02076)) | Define the belief type precisely, including that it is conditional on the option set ([2610.16655](https://arxiv.org/abs/2610.16655)) |
| Rule over beliefs plus explicit values → action, incl. abstain | **Established in theory; partial in TDM practice** | Wald, Berger, Elkan, Chow; Probability Contracts; TypedBench; JevAgentHarness; 2610.10978; Wei Sun; guardrails cookbook | **Open:** the rule as a typed, pure, versioned expression with a value table, and abstain as an ordinary typed action (no source does this) |
| Actions invoke function code | **Partial** | Function-calling cookbook, OpenAI voice guide, AutoModeMiddleware, REFLEX | Gate before execution (the cookbook shows none); separate the dispatch and gating styles |
| Five structures, structure in wiring and behavior in rules | **Partial** | Anthropic's patterns (generative nodes); TypeSafe's four patterns; scattered TDM examples | **Open:** a taxonomy over decision units, the routing-as-rule argument, and any evaluator-optimizer evaluation over TDMs |
| Offline re-deciding over recorded beliefs | **Established as practice; partial as concept** | Bayes-rule factorization; LTT and conformal risk control; ≥8 TDM replays ([2610.20634](https://arxiv.org/html/2610.20634), [2610.00346](https://arxiv.org/html/2610.00346), [2610.03387](https://arxiv.org/html/2610.03387), [2609.39496](https://arxiv.org/html/2609.39496), [2610.15537](https://arxiv.org/html/2610.15537), [2610.20907](https://arxiv.org/html/2610.20907), [2610.07716](https://arxiv.org/abs/2610.07716), [2609.29769](https://arxiv.org/html/2609.29769)) | **Open:** re-deciding as a named property of the unit; transfer of rules across model versions and providers (the audit lists cross-version stability as unknown) |
| Cross-provider TDM evaluation | **Established** | System1-Arena (30 models), Benchmark Heaven (183 systems), JEVal, TypedBench | Head-to-head across six providers with paired bootstrap deltas, AUROC and repeat agreement |
| Fresh, post-release, natural data | **Open for TDMs** | LiveBench and LiveCodeBench precedent in the LLM world | **First** TDM evaluation on text created after release; first third-party numbers for OpenDecider nano and Von 1.3 |
| Decision-level benchmark scoring | **Open** | No TDM board does it | Risk-coverage, expected cost under stated values, and net benefit, all computed by re-deciding |

The paper should be framed as a **formalization and unification of scattered practice** with two evaluation firsts, not as the discovery that beliefs and decisions should be separated. A defensible contribution statement has four parts. First, a decision-unit abstraction that makes the classical Bayes-rule factorization concrete for typed questions, with values as named, inspectable parameters and abstain as an ordinary action. Second, a five-structure taxonomy adapted from Anthropic, with routing absorbed into rules, which turns "behavior in rules, structure in wiring" into a testable claim: changing a rule's values changes system behavior without rewiring and without new model calls. Third, offline re-deciding as a first-class property, with its validity conditions stated. Fourth, a cross-provider evaluation on data that cannot have been memorized.

The validity conditions need to be explicit, because the TDM literature has already found where they fail:

- **Exactness.** Re-deciding is exact only for deterministic models, and hosted Jev is nondeterministic. Up to 1.33% of decisions change between identical runs ([Audit](https://arxiv.org/html/2609.32160); [2610.00346](https://arxiv.org/html/2610.00346)).
- **Valid scope.** Re-deciding is valid for changes to rules and values, but **not** for changes to the question or option set, because beliefs move when options are added ([2610.16655](https://arxiv.org/abs/2610.16655)) or relabeled ([2610.02586](https://arxiv.org/abs/2610.02586)).
- **Composed rules.** Calibration assumed by a rule can break under composition ([StartLux](https://arxiv.org/html/2610.17309)), so decision calibration ([Zhao et al.](https://arxiv.org/abs/2107.05719)) is the correct sufficient condition.
- **Adversarial inputs.** Abstention on low confidence does not defend against attacks, because flipped decisions stay confident ([2610.12292](https://arxiv.org/abs/2610.12292)).

### The evaluation must test rules, not just beliefs

As specified, the evaluation scores beliefs: accuracy, AUROC, Brier, ECE, repeat agreement, cost and latency. That is a solid cross-provider belief study, but it does not yet test the thesis. Because every belief is recorded, rule-level experiments cost no extra model calls:

- **Sweeps.** Sweep thresholds and cost matrices over the stored beliefs and report risk-coverage curves, expected cost under stated values (TypedBench-style argmax vs Bayes) and decision curves.
- **Certified thresholds.** Fit thresholds with LTT on one split and test on another.
- **Cross-provider rule transfer.** Fit a rule on one TDM's beliefs and apply it to another's. This directly probes the unexamined rule-transfer gap, and the rejection-transfer paper suggests it will fail without recalibration ([2610.03387](https://arxiv.org/html/2610.03387)).
- **Composed structures.** Build the structures from recorded beliefs. Parallel panels across providers can test the correlated-error prediction, and two-stage cascades should include a **matched random-escalation control** ([2610.20634](https://arxiv.org/html/2610.20634); [Bouchard](https://arxiv.org/abs/2605.06350)).
- **Audit hygiene.** Cover the audit's hardest items: DeepSeek logprobs already satisfy B1, and the remaining items are a cheap generative cascade baseline (B2), an option-name swap (T3) and latency with and without caching (C4) ([Audit](https://arxiv.org/html/2609.32160)). If feasible, add a GPT-6 Luna logprob readout. That would give the first matched comparison against the Decisions API.

AUROC deserves emphasis in the paper. No TDM board reports it, and offline deferral gain tracks actor AUROC at ρ=0.87 ([2610.09683](https://arxiv.org/abs/2610.09683)), which ties a belief metric directly to rule value.

Freshness claims need care. The reviews were created 10-17 October 2026, after Jev 1.13.0 (15 September) and the Decisions public beta (6 October; this date comes from secondary coverage, [Unite.AI](https://unite.ai/openai-releases-decisions-api-in-public-beta-powered-by-gpt-6-luna)). That rules out item memorization by construction, provided hosted snapshots are pinned and logged by date. Two caveats remain. Near-duplicate older reviews of the same titles are possible. And the release dates of DeepSeek V4.1 Flash, OpenDecider nano and open-jev-deberta-v3-large were not checked in this sweep.

### Must cite and contrast

| Cite | Why it matters | Contrast to draw |
|---|---|---|
| Tang & Zheng audit 2609.32160 | Field's evidence standard; no typed-readout advantage | Add rule/value reporting items to its checklist |
| Probability Contracts 2609.37470 | Closest explicit "report vs rule" statement | No rule language, no composition, no fresh data |
| TypedBench 2610.11392 | Cost-matrix Bayes vs argmax; offline sweep | Benchmark-level, not a composable unit |
| JevAgentHarness 2610.21412 | Cost-derived threshold refit on shadow logs | Agent-specific; no structure taxonomy |
| Probabilistic Sensing, Deterministic Authority 2610.10978 | Score → admitted value → deterministic contract | No beliefs over typed options or composition |
| Wei Sun 2604.00414 | Signals vs policy as a design principle | Not TDM beliefs; no five structures (abstract only) |
| Jev-LiteMAS 2610.21411 | Orchestrator plus evaluator over TDM | Application; rules not separated as artifacts |
| StartLux 2610.17309 | Calibration breaks after selection or routing | Motivates decision calibration under composition |
| 2610.20634; Bouchard 2605.06350 | Random escalation matches confidence; depth rarely helps | Required controls for cascade claims |
| 2610.16655; 2610.02586; 2610.00346 | Beliefs depend on option set, labels and polarity | Limits on what re-deciding can change |
| Anthropic 2024; Zaharia 2024; Dohan 2022 | Taxonomy and compound-system framing | Generative nodes vs belief nodes; routing as rule |
| Wald/Berger; Elkan; Chow; Zhao 2021; LTT | Formal warrant for split, thresholds, abstain, re-tuning | Our contribution is the operational unit |
| DMN/FEEL; CEL | Engineering precedent for pure decision logic | Crisp facts vs calibrated beliefs; no abstain |
| Elmachtoub & Grigas; Mandi 2024 | Opposing fused philosophy | Decoupling trade-off |
| PoLL; Kim 2025; Goel 2025 | Correlated errors in panels | Cross-provider TDM panels |
| LiveBench; LiveCodeBench; Benchmark Heaven board | Fresh-data precedent and nearest TDM board | Natural post-release text vs authored sealed items |

### References to verify before submission

These details were **not verified** in this sweep and must be checked before citing:

- **Bibliographic details:**
  - publisher and year of the Wald 1950 book and of Savage 1954;
  - Hernández-Orallo, Flach & Ferri 2012 (JMLR volume and pages);
  - the Platt 1999 chapter and Zadrozny & Elkan 2001;
  - Berger page-level definitions;
  - the 1984 Howard & Matheson volume (cite the 2005 reprint).
- **Venues and pages:**
  - Conformal Risk Control (believed to be ICLR 2024);
  - Zhao et al. 2021 (believed to be NeurIPS 2021);
  - pages for Geifman & El-Yaniv (NIPS), Mozannar & Sontag (PMLR) and Guo et al. (PMLR);
  - DSPy (ICLR 2024), FrugalGPT (TMLR), RouteLLM (ICLR 2025) and GLiNER (NAACL 2024);
  - Viola-Jones 2001;
  - Sainz et al.: Findings of EMNLP 2023 vs 2024 (check the ACL Anthology).
- **Dates and authors:** the OpenAI agents-guide date; Anthropic's first author's full name; the original CEL release date.
- **Content claims:**
  - the GPT-4 report's calibration figure;
  - the "Enterprise Decision Management" label for Taylor & Raden;
  - FEEL chapter and conformance clauses;
  - whether Firebase and Cloud IAM use CEL.
- **TDM-specific items:**
  - Wei Sun 2604.00414 and about 45 TDM evaluation papers (abstract-only reads);
  - the JEV-as-a-Judge cost and accuracy figures, which differ between the audit and the abstract;
  - Sun et al. 2609.26758, which has three titles across versions and different headline numbers in different summaries (AUC .815→.581 vs 93.8%→23.2%), so cite a specific version;
  - the kotoba-lang ADR texts (inaccessible);
  - the Vercel SDK method name;
  - the Artificial Analysis and HF Decision Index rankings;
  - the preprints.org 202610.0181 framework (returned 403);
  - Imajev and Verdict model-card claims, plus Plumb-4B and decider-4b (no primary sources);
  - the Show HN date (about 23 September, inferred);
  - trademark status of "Jev" and "JevBench."

## Conclusion

The literature has reached the paper's conclusion from the bottom up. Engineers separate beliefs from rules because hosted TDMs force it, and evaluators keep finding that the rule, not the belief, decides outcomes: thresholds that do not transfer, Bayes plug-ins that lose to argmax, random escalation that matches confidence. What none of them has supplied is the abstraction that makes those findings cumulative. That means a unit whose values are explicit enough to swap, whose rules are pure enough to replay, and whose compositions are named enough to compare across providers. That abstraction is the paper's real opening. It is narrow, because Probability Contracts, TypedBench, JevAgentHarness and Wei Sun each own part of it. It is also real, because none of them unifies it, and none tests it on data the models cannot have seen.

The sharpest risk is internal, not external. A paper arguing that behavior lives in rules, but evaluated only on belief metrics, invites the reply that it has re-benchmarked TDMs. Recorded beliefs make the fix nearly free. If the same six-provider, post-release beliefs are re-decided under many value settings, across providers and through the five structures, the evaluation becomes the first decision-level TDM benchmark. That also turns the open questions above (rule transfer across providers, panel independence, evaluator-optimizer value) into results rather than claims.
