# Classical Foundations for "Decision Rules over Model Beliefs"

Verification legend used throughout:
- **[V-Crossref]** DOI resolved this session on api.crossref.org and the authors, title, venue, volume, issue, pages and year matched.
- **[V-arXiv]** arXiv ID resolved this session on export.arxiv.org and the title and authors matched.
- **[V-web]** confirmed this session on a primary web page (publisher, standards body or official docs).
- **[UNVERIFIED]** from prior knowledge only. Not confirmed this session, so check before citing.

Where the notes give terminology or formulas from standard textbooks (for example Berger's notation), they come from domain knowledge of the cited work, not from a page-level quote retrieved this session. They are marked as such.

---

## Q1. Statistical decision theory (Wald, Savage, Berger; Bayes rule, risk, Bayes risk, terminology)

### Takeaway
Our "decision rule over beliefs" is the classical Wald/Berger decision rule δ applied to a posterior. Under expected loss, the Bayes-optimal rule depends on the data only through the posterior (the "belief"). This is the formal justification for splitting a *model* (evidence → belief) from a *rule* (belief + values → action), and for re-tuning the values offline. Use Berger's vocabulary throughout: state of nature θ, observation x, action a ∈ A, loss L(θ,a), decision rule δ: X → A, frequentist risk R(θ,δ), Bayes risk r(π,δ).

### Cited Findings
- **Wald, A. (1949).** "Statistical Decision Functions." *The Annals of Mathematical Statistics* 20(2):165–205. DOI: 10.1214/aoms/1177730030. [V-Crossref] This journal article gave the first general formulation of statistical inference as a game against nature with loss and risk functions. — [Crossref/DOI](https://doi.org/10.1214/aoms/1177730030)
- **Wald, A. (1950).** *Statistical Decision Functions.* New York: John Wiley & Sons. This book-length treatment is the canonical citation for "statistical decision theory." No DOI; publisher and city are [UNVERIFIED] this session but are standard. Cite the 1949 article above for a DOI-bearing reference. — [Crossref record of the 1949 article](https://doi.org/10.1214/aoms/1177730030)
- **Savage, L. J. (1954).** *The Foundations of Statistics.* New York: Wiley. Second revised edition: Dover, 1972. [UNVERIFIED this session: publisher and year are standard bibliographic facts.] It provides the axiomatic subjective expected-utility foundation: preferences over acts imply a personal probability and a utility, and rational choice maximizes expected utility. This is the normative basis for treating a model output as a *belief* that is separate from *values*.
- **Savage, L. J. (1971).** "Elicitation of Personal Probabilities and Expectations." *JASA* 66(336):783–801. DOI: 10.1080/01621459.1971.10482346. [V-Crossref] It links proper scoring rules to honest probability elicitation, which bridges Q1 and Q4. — [DOI](https://doi.org/10.1080/01621459.1971.10482346)
- **Berger, J. O. (1985).** *Statistical Decision Theory and Bayesian Analysis*, 2nd ed. Springer Series in Statistics. New York: Springer. DOI: 10.1007/978-1-4757-4286-2. [V-Crossref] It is the standard textbook reference for the vocabulary we need (from domain knowledge of the textbook):
  - θ ∈ Θ is the "state of nature."
  - a ∈ A is an "action."
  - L(θ,a) is the loss.
  - δ(x) is a (nonrandomized) "decision rule."
  - R(θ,δ) = E_θ[L(θ,δ(X))] is the risk.
  - The Bayes risk is r(π,δ) = E_π[R(θ,δ)].
  - The Bayes rule minimizes posterior expected loss for each x.

  It also covers randomized rules, admissibility and minimax. — [Springer/DOI](https://doi.org/10.1007/978-1-4757-4286-2)
- **Howard, R. A. (1966).** "Information Value Theory." *IEEE Trans. Systems Science and Cybernetics* 2(1):22–26. DOI: 10.1109/TSSC.1966.300074. [V-Crossref] It defines the expected value of (perfect or imperfect) information within a decision problem. This applies directly to "should this decision unit gather more evidence, or abstain/defer?" — [DOI](https://doi.org/10.1109/TSSC.1966.300074)

### Inferences
- **Terminology mapping for the paper:**
  - Berger's *state of nature* θ corresponds to the latent answer to our typed question.
  - The *observation* x corresponds to evidence.
  - The posterior π(θ|x) corresponds to the *belief*.
  - δ corresponds to our *decision rule*.
  - The loss matrix, thresholds and costs correspond to our *explicit values*.

  "Policy" is the RL/control synonym. We recommend "decision rule" to stay aligned with Wald and Berger.
- **The theoretical warrant for "pure expression over beliefs":** the Bayes rule factors as δ*(x) = argmin_a Σ_θ L(θ,a) π(θ|x). So once a belief is recorded, the loss (values) can be swapped and the rule re-evaluated without re-running the model. That is exactly our offline re-tuning over recorded beliefs (from Berger, domain knowledge). This holds only if the belief is calibrated (see Q4). Otherwise the plug-in rule is not Bayes-optimal.
- **Abstention in Wald's framework:** treat "abstain/defer" as just another action in A with its own loss. Chow's reject rule (Q3) is the special case for classification.

### Gaps
- I did not retrieve the 1950 Wiley book's front matter or Savage 1954's publisher page this session. Treat publisher and year as standard but unverified.
- I did not verify page-level quotes for Berger's definitions. Cite chapter 1 or 4 generically, or check page numbers in the 2nd edition.
- Optional classics not checked: von Neumann & Morgenstern (1944) *Theory of Games and Economic Behavior*; Raiffa & Schlaifer (1961) *Applied Statistical Decision Theory*; DeGroot (1970) *Optimal Statistical Decisions*.

---

## Q2. Cost-sensitive classification, threshold selection, decision curves, ROC operating points

### Takeaway
The cost ratio fixes the optimal threshold on a calibrated probability: p* = (c10 − c00)/(c10 − c00 + c01 − c11) (Elkan 2001). Elkan explicitly recommends computing decisions *from probability estimates* rather than retraining. That is the same separation of belief from decision rule that our paper formalizes. Decision curve analysis (net benefit vs. threshold) and ROC iso-cost lines are the evaluation-side counterparts for choosing and justifying a threshold value.

### Cited Findings
- **Elkan, C. (2001).** "The Foundations of Cost-Sensitive Learning." *Proceedings of the 17th International Joint Conference on Artificial Intelligence (IJCAI-01)*, Seattle, pp. 973–978. [V-web: venue and pages confirmed via ML Anthology and multiple reference lists. No DOI.]
  - **Core principle:** predict the class with minimum expected cost, Σ_j P(j|x) C(i,j). For two classes this reduces to a threshold p* on P(y=1|x) determined by the cost matrix (formula from domain knowledge of the paper).
  - **Theorem on rebalancing:** changing the proportion of negative training examples makes a cost-insensitive learner cost-sensitive.
  - **Recommendation:** since rebalancing has little effect on Bayesian and decision-tree learners, compute decisions from probability estimates instead.
  - **Coherence:** the paper also discusses when a cost matrix is "reasonable" or economically coherent.

  — [ML Anthology](https://mlanthology.org/ijcai/2001/elkan2001ijcai-foundations)
- **Vickers, A. J. & Elkin, E. B. (2006).** "Decision Curve Analysis: A Novel Method for Evaluating Prediction Models." *Medical Decision Making* 26(6):565–574. DOI: 10.1177/0272989X06295361. [V-Crossref] It introduces net benefit as a function of threshold probability p_t: NB = TP/n − (FP/n)·p_t/(1−p_t). The threshold probability encodes the harm-to-benefit ratio, so a model is judged by the *decisions* it supports across a range of value settings (formula from domain knowledge). — [DOI](https://doi.org/10.1177/0272989X06295361)
- **Vickers, A. J., van Calster, B. & Steyerberg, E. W. (2019).** "A simple, step-by-step guide to interpreting decision curve analysis." *Diagnostic and Prognostic Research* 3:18. DOI: 10.1186/s41512-019-0064-7. [V-Crossref; article number 18 is UNVERIFIED] It is a tutorial reference for net benefit and treat-all/treat-none baselines. — [DOI](https://doi.org/10.1186/s41512-019-0064-7)
- **Provost, F. & Fawcett, T. (2001).** "Robust Classification for Imprecise Environments." *Machine Learning* 42(3):203–231. DOI: 10.1023/A:1007601015854. [V-Crossref] It introduces the ROC convex hull method. The optimal operating point for given class priors and costs is where an iso-performance line of slope (c(FP)·P(neg))/(c(FN)·P(pos)) touches the hull. This is the formal basis for "pick the operating point from values, after training" (slope formula from domain knowledge). — [DOI](https://doi.org/10.1023/A:1007601015854)
- **Fawcett, T. (2006).** "An introduction to ROC analysis." *Pattern Recognition Letters* 27(8):861–874. DOI: 10.1016/j.patrec.2005.10.010. [V-Crossref] It is the standard tutorial on ROC space, thresholds as operating points, and iso-performance lines. — [DOI](https://doi.org/10.1016/j.patrec.2005.10.010)
- **Hernández-Orallo, J., Flach, P. & Ferri, C. (2012).** "A Unified View of Performance Metrics: Translating Threshold Choice into Expected Classification Loss." *JMLR* 13:2813–2869. [UNVERIFIED this session: the Crossref query did not return it, and volume and pages are from memory.] It shows that many metrics (AUC, Brier score, etc.) equal expected loss under different threshold-choice methods and cost distributions. It is useful for arguing that scoring rules and decision metrics are linked through the threshold-selection procedure.

### Inferences
- **Positioning:** Elkan, Provost & Fawcett, and Vickers each treat the threshold as a post hoc, value-dependent choice over a probability output. Our contribution is to make the threshold a *typed, named, versioned value* in a pure rule expression, rather than an implicit hyperparameter or a line in an analysis script. The rule should also be composable across units and re-tunable over logged beliefs.
- **Decision curves as a metric:** a decision curve (net benefit across p_t) is a ready-made way to report "expected cost across value settings." It is a natural evaluation figure for re-tuning experiments.

### Gaps
- I did not verify the Hernández-Orallo, Flach & Ferri (2012) bibliographic details.
- No DOI exists for IJCAI 2001 papers. Cite by proceedings and page range.

---

## Q3. Reject option, selective prediction, conformal risk control, learning to defer, human-AI complementarity

### Takeaway
Abstention has a 70-year lineage. Chow (1957, 1970) derived the Bayes-optimal reject rule: reject when max_k P(k|x) < 1 − t for a reject cost t, which gives an error–reject trade-off curve. El-Yaniv & Wiener (2010) formalized selective classification and the risk–coverage trade-off. Geifman & El-Yaniv (2017) brought it to deep nets with a guaranteed-risk threshold. Conformal risk control and Learn-then-Test give distribution-free, finite-sample guarantees for choosing a threshold value on held-out data, which is a principled version of our offline re-tuning. Learning-to-defer and complementarity work extends "abstain" to "route to a human or another decision unit," which matches our decision graphs.

### Cited Findings
- **Chow, C. K. (1957).** "An optimum character recognition system using decision functions." *IRE Transactions on Electronic Computers* EC-6(4):247–254. DOI: 10.1109/TEC.1957.5222035. [V-Crossref] It is the original statistical-decision-theoretic treatment of recognition with a reject option. — [DOI](https://doi.org/10.1109/TEC.1957.5222035)
- **Chow, C. K. (1970).** "On optimum recognition error and reject tradeoff." *IEEE Transactions on Information Theory* 16(1):41–46. DOI: 10.1109/TIT.1970.1054406. [V-Crossref] It derives the optimal rule, "reject if max posterior < threshold," and characterizes the error–reject trade-off curve. It is the classical ancestor of risk–coverage curves (content from domain knowledge). — [DOI](https://doi.org/10.1109/TIT.1970.1054406)
- **Herbei, R. & Wegkamp, M. H. (2006).** "Classification with reject option." *Canadian Journal of Statistics* 34(4):709–721. DOI: 10.1002/cjs.5550340410. [V-Crossref] It covers statistical learning theory (plug-in rules, rates) for the reject option under a cost d for rejecting. — [DOI](https://doi.org/10.1002/cjs.5550340410)
- **El-Yaniv, R. & Wiener, Y. (2010).** "On the Foundations of Noise-free Selective Classification." *JMLR* 11(53):1605–1641. [V-web] It formalizes selective classification, in which a classifier gives up coverage to gain accuracy (the "risk-coverage (RC) trade-off"). It characterizes RC trade-offs and shows that in the noise-free realizable setting a "perfect" selective classifier exists. — [JMLR](https://jmlr.org/papers/v11/el-yaniv10a.html)
- **Geifman, Y. & El-Yaniv, R. (2017).** "Selective Classification for Deep Neural Networks." *Advances in Neural Information Processing Systems 30 (NIPS 2017)*. arXiv:1705.08500. [V-arXiv for title and authors. NIPS 2017 venue and pages 4878–4887 are UNVERIFIED this session.] Given a desired risk level, it chooses a confidence threshold (softmax response or MC-dropout) with a high-probability guarantee on selective risk. It popularized risk–coverage curves and AURC-style evaluation for deep models. — [arXiv](https://arxiv.org/abs/1705.08500)
- **Cortes, C., DeSalvo, G. & Mohri, M. (2016).** "Learning with Rejection." In *Algorithmic Learning Theory (ALT 2016)*, LNCS, pp. 67–82. DOI: 10.1007/978-3-319-46379-7_5. [V-Crossref] It learns a rejection function jointly with the predictor (rather than thresholding confidence) under a fixed rejection cost. — [DOI](https://doi.org/10.1007/978-3-319-46379-7_5)
- **Bates, S., Angelopoulos, A. N., Lei, L., Malik, J. & Jordan, M. I. (2021).** "Distribution-free, Risk-controlling Prediction Sets." *Journal of the ACM* 68(6):1–34. DOI: 10.1145/3478535. [V-Crossref] It calibrates a threshold on held-out data so that a user-chosen risk is controlled with high probability, without distributional assumptions. — [DOI](https://doi.org/10.1145/3478535)
- **Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L. & Schuster, T. (2022).** "Conformal Risk Control." arXiv:2208.02814. [V-arXiv. Publication at ICLR 2024 is UNVERIFIED this session.] It extends split conformal prediction to control the *expected value* of any monotone loss: E[L] ≤ α, with a finite-sample guarantee via a simple threshold choice on calibration data. — [arXiv](https://arxiv.org/abs/2208.02814)
- **Angelopoulos, A. N., Bates, S., Candès, E. J., Jordan, M. I. & Lei, L. (2025).** "Learn then Test: Calibrating predictive algorithms to achieve risk control." *The Annals of Applied Statistics* 19(2):1641–1662. DOI: 10.1214/24-AOAS1998. arXiv:2110.01052 (2021). [V-Crossref, V-arXiv] It frames choosing hyperparameters or thresholds as multiple hypothesis testing. It controls risk for non-monotone losses and multiple simultaneous risks, including selective-classification thresholds. It is the closest formal analogue to "re-tune values offline over recorded beliefs with a guarantee." — [DOI](https://doi.org/10.1214/24-AOAS1998), [arXiv](https://arxiv.org/abs/2110.01052)
- **Madras, D., Pitassi, T. & Zemel, R. (2018).** "Predict Responsibly: Improving Fairness and Accuracy by Learning to Defer." *NeurIPS 2018*. arXiv:1711.06664. [V-arXiv: the comment confirms "Accepted as a conference paper at Neural Information Processing Systems 2018".] It distinguishes *rejecting* (a fixed cost) from *deferring* to a specific downstream decision-maker whose accuracy and bias matter. The model is trained to account for that downstream expert. — [arXiv](https://arxiv.org/abs/1711.06664)
- **Mozannar, H. & Sontag, D. (2020).** "Consistent Estimators for Learning to Defer to an Expert." *ICML 2020*, PMLR 119. arXiv:2006.01862. [V-arXiv; ICML 2020 is confirmed by the arXiv comment. Pages 7076–7087 are UNVERIFIED.] It gives a consistent surrogate loss for jointly learning a classifier and a deferral rule (a reduction to cost-sensitive learning with an added "defer" class). — [arXiv](https://arxiv.org/abs/2006.01862)
- **Wilder, B., Horvitz, E. & Kamar, E. (2020).** "Learning to Complement Humans." *Proceedings of IJCAI-20*, pp. 1526–1533. DOI: 10.24963/ijcai.2020/212. [V-Crossref] It optimizes a model for joint human–AI team performance under a deferral cost, rather than for standalone accuracy. — [DOI](https://doi.org/10.24963/ijcai.2020/212)
- **Bansal, G., Nushi, B., Kamar, E., Horvitz, E. & Weld, D. S. (2021).** "Is the Most Accurate AI the Best Teammate? Optimizing AI for Teamwork." *Proceedings of AAAI* 35(13):11405–11414. DOI: 10.1609/aaai.v35i13.17359. [V-Crossref] It shows that the most accurate model is not necessarily optimal when a human decides whether to accept its recommendation, and argues for optimizing expected team utility. — [DOI](https://doi.org/10.1609/aaai.v35i13.17359)
- **Steyvers, M., Tejeda, H., Kerrigan, G. & Smyth, P. (2022).** "Bayesian modeling of human–AI complementarity." *PNAS* 119(11): e2111547119. DOI: 10.1073/pnas.2111547119. [V-Crossref] It is a Bayesian framework for combining human and model probabilistic judgments and shows when hybrid teams outperform either alone. — [DOI](https://doi.org/10.1073/pnas.2111547119)

### Inferences
- **Chow's rule in our framing:** Chow's rule is exactly a one-line decision rule over a belief ("abstain if max(p) < τ"), with τ derived from the reject cost. Our framing generalizes it to typed beliefs, arbitrary pure expressions and composed units.
- **Two kinds of evaluation:** El-Yaniv & Wiener and Geifman & El-Yaniv provide the risk/coverage *evaluation* vocabulary. Bates et al., Conformal Risk Control and Learn-then-Test provide the *guaranteed re-tuning* methodology. Re-tuning values offline over recorded beliefs can inherit these finite-sample guarantees when the recorded calibration set is exchangeable with deployment data. That assumption should be stated explicitly in the paper.
- **Defer vs. abstain:** learning-to-defer differs from our framing because it *learns* the deferral function jointly with the model. Ours keeps the rule an explicit, inspectable expression with tunable values. Our "defer" edge in a decision graph is the system-level analogue: the downstream unit can be a human or another model.

### Gaps
- I did not verify the final venue of Conformal Risk Control (believed to be ICLR 2024).
- I did not verify NeurIPS and PMLR page ranges for Geifman & El-Yaniv and for Mozannar & Sontag.
- I did not check other "selective conformal" papers, such as Jin & Candès, "Selection by Prediction with Conformal p-values" (JMLR 2023), or selective conformal risk control variants. Verify before citing.
- I did not check the newer deferral surveys (e.g., Mozannar et al. 2023 "Who should predict?"; Verma & Nalisnick 2022 on calibrated L2D).

---

## Q4. Proper scoring rules, calibration, recalibration methods, decision calibration, predict-then-optimize

### Takeaway
Proper scoring rules (Brier 1950; Gneiting & Raftery 2007) are the right objective for scoring *beliefs*, because they reward honest probabilities. Calibration (DeGroot & Fienberg 1983; ECE per Naeini et al. 2015; Guo et al. 2017) is what makes threshold rules derived from costs correct when applied to model outputs. Decision calibration (Zhao et al. 2021) is the most directly relevant modern notion: a belief need only be calibrated with respect to the decision rules that will consume it. Predict-then-optimize / decision-focused learning (Elmachtoub & Grigas 2022; Donti et al. 2017; Mandi et al. 2024) is the main *alternative* philosophy: it trains models end-to-end for the downstream decision, which couples model and values. Our framing deliberately decouples them.

### Cited Findings
- **Brier, G. W. (1950).** "Verification of Forecasts Expressed in Terms of Probability." *Monthly Weather Review* 78(1):1–3. DOI: 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2. [V-Crossref] It introduces the quadratic (Brier) score for probabilistic forecasts. — [DOI](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2)
- **DeGroot, M. H. & Fienberg, S. E. (1983).** "The Comparison and Evaluation of Forecasters." *Journal of the Royal Statistical Society, Series D (The Statistician)* 32(1/2):12–22. DOI: 10.2307/2987588. [V-Crossref; the end page 22 is from memory, since Crossref lists the first page only.] It formalizes calibration ("well-calibrated") and refinement, and shows that proper scores decompose into calibration and refinement. — [DOI](https://doi.org/10.2307/2987588)
- **Gneiting, T. & Raftery, A. E. (2007).** "Strictly Proper Scoring Rules, Prediction, and Estimation." *JASA* 102(477):359–378. DOI: 10.1198/016214506000001437. [V-Crossref] It is the definitive review and characterization of (strictly) proper scoring rules: log, Brier, spherical, CRPS, and the Savage/Schervish representations. It establishes that expected score is optimized by reporting one's true belief. This is the theoretical justification for scoring the belief layer separately from the decision layer. — [DOI](https://doi.org/10.1198/016214506000001437)
- **Naeini, M. P., Cooper, G. F. & Hauskrecht, M. (2015).** "Obtaining Well Calibrated Probabilities Using Bayesian Binning." *Proceedings of AAAI* 29(1). DOI: 10.1609/aaai.v29i1.9602. [V-Crossref] It introduces BBQ recalibration and is the usual citation for the binned Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) metrics (the ECE/MCE attribution is from domain knowledge). — [DOI](https://doi.org/10.1609/aaai.v29i1.9602)
- **Guo, C., Pleiss, G., Sun, Y. & Weinberger, K. Q. (2017).** "On Calibration of Modern Neural Networks." *ICML 2017*, PMLR 70:1321–1330. arXiv:1706.04599. [V-arXiv; ICML 2017 is confirmed by the arXiv comment. PMLR pages are UNVERIFIED.] It shows that modern deep nets are miscalibrated (overconfident) and that single-parameter **temperature scaling** is a simple, effective post hoc fix. It popularized ECE and reliability diagrams in ML. — [arXiv](https://arxiv.org/abs/1706.04599)
- **Platt, J. C. (1999).** "Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods." In A. Smola, P. Bartlett, B. Schölkopf & D. Schuurmans (eds.), *Advances in Large Margin Classifiers*, MIT Press (2000), pp. 61–74. [UNVERIFIED this session: the Crossref search returned only Platt's SMO paper and Lin, Lin & Weng (2007).] It introduced **Platt scaling**, which fits a sigmoid to classifier scores. The related note Lin, H.-T., Lin, C.-J. & Weng, R. C. (2007), *Machine Learning* 68:267–276, DOI 10.1007/s10994-007-5018-6, is [V-Crossref]. — [Lin et al. DOI](https://doi.org/10.1007/s10994-007-5018-6)
- **Zadrozny, B. & Elkan, C. (2002).** "Transforming classifier scores into accurate multiclass probability estimates." *Proceedings of KDD 2002*, pp. 694–699. DOI: 10.1145/775047.775151. [V-Crossref] It is the standard citation for **isotonic regression** (PAV) calibration in ML and for multiclass extension via binary decomposition. The earlier Zadrozny & Elkan (2001, ICML) paper on calibrating decision trees and naive Bayes (histogram binning) is [UNVERIFIED]. — [DOI](https://doi.org/10.1145/775047.775151)
- **Niculescu-Mizil, A. & Caruana, R. (2005).** "Predicting Good Probabilities with Supervised Learning." *Proceedings of ICML 2005*, pp. 625–632. DOI: 10.1145/1102351.1102430. [V-Crossref] It is an empirical comparison of Platt scaling vs. isotonic regression across learners. — [DOI](https://doi.org/10.1145/1102351.1102430)
- **Zhao, S., Kim, M. P., Sahoo, R., Ma, T. & Ermon, S. (2021).** "Calibrating Predictions to Decisions: A Novel Approach to Multi-Class Calibration." arXiv:2107.05719. [V-arXiv. Publication at NeurIPS 2021 is UNVERIFIED this session.] It defines **decision calibration**: predictions are calibrated relative to a class of loss functions or decision rules if a decision-maker who best-responds to the predictions correctly estimates their own expected loss. It also gives a recalibration algorithm for bounded-action decision classes. This is the closest theoretical match to "beliefs consumed by explicit decision rules with tunable values." — [arXiv](https://arxiv.org/abs/2107.05719)
- **Elmachtoub, A. N. & Grigas, P. (2022).** "Smart 'Predict, then Optimize'." *Management Science* 68(1):9–26. DOI: 10.1287/mnsc.2020.3922. arXiv:1710.08005. [V-Crossref, V-arXiv] It introduces the SPO loss (decision regret of a predicted cost vector in a downstream linear optimization) and a convex surrogate SPO+. It argues for training predictions on decision quality rather than prediction error. — [DOI](https://doi.org/10.1287/mnsc.2020.3922)
- **Donti, P. L., Amos, B. & Kolter, J. Z. (2017).** "Task-based End-to-end Model Learning in Stochastic Optimization." *NIPS 2017*, pp. 5484–5494. arXiv:1703.04529. [V-arXiv: the journal_ref field gives the venue and pages.] It trains probabilistic models end-to-end through a stochastic optimization layer, using task cost as the loss. — [arXiv](https://arxiv.org/abs/1703.04529)
- **Mandi, J., Kotary, J., Berden, S., Mulamba, M., Bucarey, V., Guns, T. & Fioretto, F. (2024).** "Decision-Focused Learning: Foundations, State of the Art, Benchmark and Future Opportunities." *JAIR* 80:1623–1701. DOI: 10.1613/jair.1.15320. [V-Crossref: the first six authors were checked. Fioretto as seventh author is from memory.] It is the current survey of decision-focused learning. — [DOI](https://doi.org/10.1613/jair.1.15320)

### Inferences
- **Two-layer evaluation:** score beliefs with strictly proper scores (log, Brier) plus calibration (ECE or reliability diagrams), and score decisions with risk/coverage or expected cost. This mirrors the decomposition in Gneiting & Raftery (scoring the forecast) vs. Berger/Elkan (scoring the decision). It is also justified by the DeGroot–Fienberg calibration/refinement decomposition.
- **Positioning against predict-then-optimize:** SPO and decision-focused learning *fuse* model and decision objective, so the model must be retrained when costs change. Our design keeps the belief value-agnostic and re-tunes values cheaply over recorded beliefs. The trade-off is that a misspecified or miscalibrated belief yields suboptimal plug-in decisions. Decision calibration (Zhao et al.) is the formal bridge: it says what calibration property is *sufficient* for our decoupling to be safe for a given class of rules.
- **Choosing a recalibration method:** temperature, Platt and isotonic recalibration can be presented as transformations *inside* the model layer, applied before the belief is emitted. They keep the rule layer unchanged.

### Gaps
- I did not verify the Platt (1999/2000) chapter details or the Zadrozny & Elkan (2001) ICML paper.
- I did not verify the NeurIPS 2021 venue for Zhao et al. or the PMLR pages for Guo et al.
- Not checked: Kull et al. (2017) beta calibration and (2019) Dirichlet calibration; Good (1952) log score, *JRSS B* 14(1):107–114; Murphy (1973) Brier decomposition. All are worth citing, but bibliographic details are unverified.

---

## Q5. Influence diagrams, decision networks, value of information

### Takeaway
Influence diagrams (Howard & Matheson 1984; reprinted 2005) are the classical graphical formalism for composing chance, decision and value nodes. Our "decision units compose into graphs" is a close relative. The differences are that our decision nodes hold *explicit pure rule expressions over beliefs*, rather than being solved for optimal policies, and our chance nodes are learned models. Pearl (1988) provides the Bayesian-network substrate. Howard (1966) and Shachter (1986) provide value of information and the evaluation algorithms.

### Cited Findings
- **Howard, R. A. & Matheson, J. E. (2005).** "Influence Diagrams." *Decision Analysis* 2(3):127–143. DOI: 10.1287/deca.1050.0020. [V-Crossref] This is a reprint of the original 1984 report: Howard & Matheson (1984), "Influence Diagrams," in R. A. Howard & J. E. Matheson (eds.), *Readings on the Principles and Applications of Decision Analysis*, Vol. II, pp. 719–762, Strategic Decisions Group, Menlo Park, CA. The 1984 details are UNVERIFIED this session but standard. It defines influence diagrams as DAGs with chance, decision and value nodes and informational arcs (what is known at decision time). — [DOI](https://doi.org/10.1287/deca.1050.0020)
- **Shachter, R. D. (1986).** "Evaluating Influence Diagrams." *Operations Research* 34(6):871–882. DOI: 10.1287/opre.34.6.871. [V-Crossref] It gives an algorithm (arc reversal and node removal) for solving influence diagrams directly. — [DOI](https://doi.org/10.1287/opre.34.6.871)
- **Pearl, J. (1988).** *Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference.* San Mateo, CA: Morgan Kaufmann. DOI: 10.1016/C2009-0-27609-4. [V-Crossref, book DOI registered by Elsevier] It is the foundational text on Bayesian networks and belief propagation. It also includes a decision-analytic chapter (domain knowledge). — [DOI](https://doi.org/10.1016/C2009-0-27609-4)
- **Howard, R. A. (1966).** "Information Value Theory." *IEEE Trans. SSC* 2(1):22–26. DOI: 10.1109/TSSC.1966.300074. [V-Crossref] It covers the expected value of perfect and imperfect information. — [DOI](https://doi.org/10.1109/TSSC.1966.300074)

### Inferences
- **Mapping our graph onto an influence diagram:**
  - A decision unit's belief corresponds to the posterior at a chance node, conditioned on evidence.
  - Its decision rule corresponds to a decision node with a *fixed, explicit* policy.
  - The values correspond to the utility node's parameters.
  - Composition of units corresponds to an influence diagram with sequential decisions, where one decision's output is an information arc into another.

  Classical ID solvers *derive* optimal policies. Our framing *specifies* policies as auditable expressions and then measures or tunes them. That is closer to "policy evaluation" than "policy optimization."
- **Value of information:** VOI gives a principled criterion for an "abstain/gather more evidence" action and for deciding where in a graph to spend model calls.

### Gaps
- I did not retrieve the 1984 SDG volume's page range directly. The 2005 *Decision Analysis* reprint is the verifiable citation.
- Not checked: Koller & Milch (2003), "Multi-agent influence diagrams," *Games and Economic Behavior* 45(1):181–221; Jensen & Nielsen, *Bayesian Networks and Decision Graphs* (2nd ed., Springer 2007); LIMIDs (Lauritzen & Nilsson 2001, *Management Science*). All are optional, and their details are unverified.

---

## Q6. Business decision management: OMG DMN and FEEL, rules engines, Enterprise Decision Management

### Takeaway
OMG DMN is the industry standard for exactly the kind of "decision logic separate from process and analytics" that our paper proposes. It defines:
- decision requirements graphs (decisions, input data, knowledge sources, business knowledge models);
- decision tables with hit policies;
- an expression language, FEEL.

DMN has had formal releases from 1.0 (September 2015) to 1.6 (September 2026), and 1.7 is in beta. Taylor & Raden (2007) articulated Enterprise Decision Management: automate operational "hidden decisions" by combining business rules with predictive analytics. The key difference from our work is that DMN decisions consume *crisp input data* and have no native notion of a *probabilistic belief*, calibrated scoring, or abstention as a first-class outcome. Our framing adds those.

### Cited Findings
- **OMG Decision Model and Notation (DMN)**, versions listed on the OMG spec page [V-web]. Specification URL: https://www.omg.org/spec/DMN/ — [OMG DMN](https://www.omg.org/spec/DMN/)

  | Version | Date | Status | URL |
  |---|---|---|---|
  | 1.0 | September 2015 | Formal | https://www.omg.org/spec/DMN/1.0 |
  | 1.1 | June 2016 | Formal | https://www.omg.org/spec/DMN/1.1 |
  | 1.2 | January 2019 | Formal | https://www.omg.org/spec/DMN/1.2 |
  | 1.3 | February 2021 | Formal | https://www.omg.org/spec/DMN/1.3 |
  | 1.4 | April 2023 | Formal | https://www.omg.org/spec/DMN/1.4 |
  | 1.5 | August 2024 | Formal | https://www.omg.org/spec/DMN/1.5 |
  | 1.6 | September 2026 | Formal | https://www.omg.org/spec/DMN/1.6 |
  | 1.7 Beta 1 | September 2026 | In process | https://www.omg.org/spec/DMN/1.7/Beta1 (OMG file ID dtc/26-06-01) |

  The OMG page says beta versions are informational only and that the formal version should be followed for compliance. Note: DMN 1.6 is very recent. Cite 1.5 or 1.6 depending on which version you reviewed, and give the exact version number.
- **FEEL ("Friendly Enough Expression Language")** is DMN's expression language. The expansion of the acronym, and FEEL being required at DMN Conformance Level 3, come from domain knowledge. The OMG landing page refers only to an "expression language" and does not name FEEL, so cite the specification PDF chapter on FEEL [UNVERIFIED at page level]. — [OMG DMN](https://www.omg.org/spec/DMN/)
- **DMN conformance levels:** DMN defines three incremental conformance levels, and claiming level N requires satisfying lower levels (per Red Hat documentation, a secondary source). — [Red Hat Decision Manager 7.1 DMN guide](https://access.redhat.com/documentation/de-de/red_hat_decision_manager/7.1/pdf/designing_a_decision_service_using_dmn_models/Red_Hat_Decision_Manager-7.1-Designing_a_decision_service_using_DMN_models-en-US.pdf)
- **DMN decision-table hit policies** [V-web via Camunda docs; the DMN 1.2 working draft confirms Priority and Output Order]:
  - **Single-hit policies:**
    - **U**nique (default): at most one rule may match.
    - **A**ny: multiple matches must give the same output.
    - **F**irst: return the first matching rule in rule order.
    - **P**riority: return the highest-priority output, ranked by the output-values list.
  - **Multiple-hit policies:**
    - **R**ule order: return all matches in rule order.
    - **O**utput order: return all matches sorted by output-value priority.
    - **C**ollect: return all matches unordered, optionally with the aggregators SUM, MIN, MAX and COUNT.

  — [Camunda 8 docs: hit policy](https://docs.camunda.io/docs/components/modeler/dmn/decision-table-hit-policy/); [Flowable DMN docs](https://flowable.com/open-source/docs/dmn/ch06-DMN-Introduction); [OMG DMN 1.2 issue draft](https://issues.omg.org/secure/attachment/13904/DMN12-97.odt)
- **Engine support is uneven:** Camunda's engine does not support the Priority and Output Order hit policies at runtime, although its modeler offers them. Users emulate them with sorted tables plus First or Rule Order (from Camunda community forum staff answers, a secondary source). — [Camunda forum](https://forum.camunda.io/t/does-camunda-support-priority-and-output-order-in-dmn/24909)
- **Rete algorithm:** Forgy, C. L. (1982). "Rete: A fast algorithm for the many pattern/many object pattern match problem." *Artificial Intelligence* 19(1):17–37. DOI: 10.1016/0004-3702(82)90020-0. [V-Crossref] Rete is the matching algorithm behind production-rule engines (OPS5, and lineage to Drools/CLIPS/Jess). — [DOI](https://doi.org/10.1016/0004-3702(82)90020-0)
- **Drools** (Apache KIE, formerly Red Hat/JBoss) is a production-rule engine that also implements DMN. **Camunda** provides a DMN engine and FEEL implementation. Red Hat Decision Manager documentation describes DMN modeling, and Camunda docs describe DMN decision tables and FEEL. [V-web for the existence of the DMN features. I did not check Drools' current DMN conformance level this session.] — [Red Hat DMN guide](https://access.redhat.com/documentation/de-de/red_hat_decision_manager/7.1/pdf/designing_a_decision_service_using_dmn_models/Red_Hat_Decision_Manager-7.1-Designing_a_decision_service_using_DMN_models-en-US.pdf); [Camunda docs](https://docs.camunda.io/docs/components/modeler/dmn/decision-table-hit-policy/)
- **Taylor, J. with Raden, N. (2007).** *Smart (Enough) Systems: How to Deliver Competitive Advantage by Automating Hidden Decisions.* Upper Saddle River, NJ: Prentice Hall. ISBN-13 978-0-13-234796-9; ISBN-10 0-13-234796-2. [V-web via library and bookseller records. Page count varies by record (404 or 432 pp.), and the publisher city is from memory.] It argues for automating high-volume operational decisions by combining business rules with predictive analytics and adaptive control. — [finna.fi library record](https://finna.fi/Record/3amk.104663); [bibsonomy](https://bibsonomy.org/bibtex/c500132f06513afc45b8c8f3c6f8121f); [Tenlong](https://www.tenlong.com.tw/products/9780132347969)
- **"Enterprise Decision Management" label:** I could not confirm on a primary page this session that the book is framed under the EDM label. Taylor's association with the term is well known, but treat it as [UNVERIFIED]. The book's blurb frames the topic as automating "hidden decisions." — [Tenlong](https://www.tenlong.com.tw/products/9780132347969)

### Inferences
- **What DMN offers prior art for:** DMN is direct prior art for:
  - decision units composed into graphs (the DRG/DRD);
  - explicit, business-owned decision logic separated from both process (BPMN) and analytics (the "analytics-to-rules" handoff in EDM);
  - a side-effect-free expression language (FEEL).

  Our paper should cite DMN as the closest *engineering* ancestor and state the deltas:
  - typed *probabilistic beliefs* as inputs, rather than crisp facts;
  - *abstain/defer* as a first-class outcome;
  - *proper scoring and calibration* of the belief layer;
  - *offline re-tuning of named values* over recorded beliefs, with risk/coverage/expected-cost metrics.
- **Hit policies vs. Bayes rules:** hit policies are a discrete, rule-precedence answer to "what if several conditions fire." Our decision rules over beliefs instead resolve via expected-loss minimization or explicit thresholds. A DMN table can encode a thresholded belief rule (for example, inputs p_fraud and cost bands with a First hit policy), so our approach is expressible in DMN but not native to it.

### Gaps
- I did not retrieve the DMN 1.5 or 1.6 specification PDFs, so FEEL chapter numbers, the formal conformance-level definitions and the hit-policy clause numbers are not page-verified. Cite the spec section after checking.
- I did not verify current Drools or Camunda DMN conformance claims (TCK results are at the DMN TCK project).
- I did not verify the "Enterprise Decision Management" naming in the book itself.

---

## Q7. Expression languages for safe rule evaluation: Google CEL

### Takeaway
CEL (Common Expression Language) is designed for exactly our "pure expression over beliefs plus explicit values" use case. It is non-Turing-complete, guaranteed to terminate, side-effect free, and evaluates in linear time (absent macros) with a specified cost model. It is gradually typed, and the host supplies variables and functions. It is used for policy and validation at scale: Kubernetes ValidatingAdmissionPolicy (stable since v1.30) and Envoy RBAC conditions. Firebase Security Rules and Google Cloud IAM Conditions are also reported adopters, per secondary sources. Python options include Google's official `cel-expr-python` (open-sourced March 2026, wrapping cel-cpp) and the pure-Python `cel-python` (Cloud Custodian).

### Cited Findings
- **CEL specification repository:** https://github.com/google/cel-spec. Its README says CEL "evaluates in linear time, is mutation free, and not Turing-complete." It is licensed Apache 2.0. [V-web] — [cel-spec README](https://github.com/google/cel-spec)
- **CEL language definition (langdef.md)** [V-web]:
  - **Terminating:** CEL is "terminating: CEL programs cannot loop forever."
  - **Cost is part of the spec:** "the time and space cost of evaluation is an essential part of the specification of the language." Without macros and concatenation, time and space are bounded O(P·I).
  - **Macro risk:** macros (has(), comprehensions such as all/exists/map/filter) are the only avenue for exponential behavior when nested or chained, and implementations may limit or disable them.
  - **No side effects:** "CEL functions have no observable side effects."
  - **Gradual typing:** the type checker is an optional phase that can reject ill-typed expressions, and runtime type safety is still enforced.
  - **Commutative && and ||:** unlike short-circuit operators, a runtime error in one operand is ignored if the other operand determines the result, and errors and unknowns "will not halt evaluation."
  - **Errors:** "There is no in-language representation of errors."

  — [CEL langdef](https://github.com/google/cel-spec/blob/master/doc/langdef.md)
- **cel.dev** (official site): CEL is "Non-Turing complete, and only accesses data provided by the host application," and it was "designed to evaluate safely and quickly (nanoseconds to microseconds) with predictible [sic] costs." [V-web] The site links the CEL Java Verifier and the spec now hosted under the `cel-expr` GitHub organization (github.com/cel-expr/cel-spec). — [cel.dev](https://cel.dev/)
- **Kubernetes ValidatingAdmissionPolicy:** stable since Kubernetes v1.30. "Validating admission policies use the Common Expression Language (CEL) to declare the validation rules of a policy." The docs describe it as "a declarative, in-process alternative to validating admission webhooks." [V-web] — [Kubernetes docs](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)
- **Envoy RBAC filter:** policies may include a `condition`, which is a CEL expression that must be satisfied for the policy to match. Envoy also has a CEL matcher type (`xds.type.matcher.v3.CelMatcher`). [V-web via Envoy documentation search results] — [Envoy RBAC docs](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/rbac_filter); [Envoy CEL matcher proto](https://www.envoyproxy.io/docs/envoy/latest/_sources/xds/type/matcher/v3/cel.proto.rst.txt)
- **Firebase and Google Cloud IAM:** a secondary source (a Buf blog post, as summarized by the search tool) lists Kubernetes admission control, Google Cloud IAM Conditions, Firebase Security Rules, Envoy routing and Protovalidate as CEL users. [Secondary only: Firebase's own docs were not retrieved. Treat "Firebase Security Rules are CEL-based" as UNVERIFIED from a primary source.] — [feedbagel summary of CEL applications](https://feedbagel.com/post/introduction-to-cel-common-expression-language-and-its-applications)
- **cel-expr-python (official Google, wraps the C++ implementation):** announced on the Google Open Source Blog on 3 March 2026 by Olena Huang for the CEL team. The repository is https://github.com/cel-expr/cel-python, and the import name is `cel_expr_python` (the PyPI name is not stated in the post). The announcement says CEL is "a powerful, non-Turing complete expression language designed for simplicity, speed, safety, and portability" and that "CEL expressions are side-effect free and terminate guaranteed." [V-web] — [Google Open Source Blog](https://opensource.googleblog.com/2026/03/announcing-cel-expr-python-the-common-expression-language-in-python-now-open-source.html)
- **cel-python (Cloud Custodian):** a pure-Python CEL implementation, PyPI `cel-python`. Its latest listed release is 0.5.0 (31 January 2026, Python ≥3.10). It was built as a security-policy filter for Cloud Custodian. [V-web via PyPI and mirror listings, as summarized by the search tool] — [PyPI cel-python](https://pypi.org/project/cel-python)
- **common-expression-language (PyPI):** Python bindings wrapping the Rust `cel-interpreter` crate. [Secondary, via search summary] — [PyPI common-expression-language](https://pypi.org/project/common-expression-language)

### Inferences
- **Why CEL suits our rule layer:** CEL's guarantees (termination, no side effects, host-provided data only, a specified cost model, optional static type checking) are exactly the properties needed to make a decision rule a *pure, auditable, re-evaluable function of (belief, values)*. Re-evaluating a recorded belief against new values is deterministic and cheap, and it is safe to run inside offline sweeps over large logs.
- **Positioning against FEEL:** CEL and FEEL occupy the same design niche (side-effect-free, embeddable expression languages for decisions). FEEL is tied to DMN decision tables and boxed expressions. CEL is a standalone embedded language with protobuf/JSON typing and wide infrastructure adoption. Choosing CEL is an engineering decision, and the paper could note that rules are portable to FEEL or DMN tables when they lie within its expressiveness.
- **Gradual typing and typed beliefs:** gradual type checking aligns with "typed questions → typed beliefs." A rule can be type-checked against the belief schema (for example, `belief.probs['fraud'] > values.threshold`) before deployment.

### Gaps
- I found no primary-source statement this session dating CEL's original release; it was open-sourced by Google around 2018, which is [UNVERIFIED].
- I found no peer-reviewed paper describing CEL. Cite the spec repository and cel.dev as technical references.
- I did not retrieve the Kubernetes CRD validation rules (`x-kubernetes-validations`) GA version (believed to be v1.29) or the documented CEL cost-budget limits.
- I did not verify Firebase Security Rules' CEL basis or Google Cloud IAM Conditions' use of CEL from primary documentation.
- The PyPI package name for `cel-expr-python` was not stated in the announcement.
