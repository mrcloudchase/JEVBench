# claims

n = 300 items per architecture, one run each.

| architecture | accuracy | accuracy_ci95 | coverage | selective_accuracy | selective_accuracy_ci95 | macro_f1_acted | ece | calls_per_item | tokens_per_item | usd_per_1k_items | latency_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| single | 0.603 | (0.543, 0.657) | 1.0 | 0.603 | (0.543, 0.657) | 0.591 | 0.166 | 1.0 | 424 | 0.0178 | 95 |
| gated | 0.5 | (0.44, 0.557) | 0.737 | 0.679 | (0.611, 0.742) | 0.641 | 0.185 | 1.0 | 424 | 0.0178 | 100 |
| panel | 0.583 | (0.527, 0.637) | 0.993 | 0.587 | (0.534, 0.638) | 0.566 | 0.123 | 3.0 | 1342 | 0.0564 | 148 |
| panel_pool | 0.573 | (0.517, 0.627) | 1.0 | 0.573 | (0.517, 0.627) | 0.544 | 0.148 | 3.0 | 1342 | 0.0564 | 148 |
| escalation | 0.527 | (0.473, 0.583) | 0.85 | 0.62 | (0.561, 0.678) | 0.587 | 0.201 | 1.26 | 543 | 0.0228 | 117 |
| chain | 0.637 | (0.583, 0.69) | 1.0 | 0.637 | (0.583, 0.69) | 0.631 | 0.189 | 2.0 | 937 | 0.0393 | 210 |
| contrastive | 0.593 | (0.537, 0.647) | 1.0 | 0.593 | (0.537, 0.647) | 0.577 | 0.142 | 2.12 | 972 | 0.0408 | 133 |
| iterative | 0.533 | (0.48, 0.59) | 0.84 | 0.635 | (0.575, 0.694) | 0.606 | 0.185 | 1.42 | 675 | 0.0284 | 107 |

Paired accuracy delta versus the single decision on the same items (abstentions count as wrong):

| architecture | delta | ci95 | items changed |
|---|---|---|---|
| gated | -0.103 | (-0.14, -0.07) | 31 |
| panel | -0.020 | (-0.047, 0.007) | 16 |
| panel_pool | -0.030 | (-0.06, 0.0) | 19 |
| escalation | -0.077 | (-0.107, -0.047) | 23 |
| chain | +0.033 | (0.007, 0.06) | 18 |
| contrastive | -0.010 | (-0.033, 0.013) | 11 |
| iterative | -0.070 | (-0.1, -0.043) | 21 |

Selective prediction curve of the single decision (confidence floor tau):

| tau | coverage | selective_accuracy |
|---|---|---|
| 0.0 | 1.0 | 0.603 |
| 0.2 | 0.973 | 0.61 |
| 0.4 | 0.85 | 0.631 |
| 0.5 | 0.733 | 0.677 |
| 0.6 | 0.65 | 0.697 |
| 0.7 | 0.59 | 0.701 |
| 0.8 | 0.497 | 0.718 |
| 0.9 | 0.38 | 0.781 |
| 0.95 | 0.31 | 0.796 |

Extras: {"escalation_rate": 0.257, "contested_rate": 0.12, "mean_rounds": 1.42, "panel_unanimous_rate": 0.8, "single_replicates": {"runs": 3, "accuracies": [0.603, 0.607, 0.603], "accuracy_range": 0.004, "items_agreeing_across_runs": 0.977, "mean_confidence_spread": 0.041}}
