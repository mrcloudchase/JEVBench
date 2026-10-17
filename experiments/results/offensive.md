# offensive

n = 300 items per architecture, one run each.

| architecture | accuracy | accuracy_ci95 | coverage | selective_accuracy | selective_accuracy_ci95 | macro_f1_acted | ece | calls_per_item | tokens_per_item | usd_per_1k_items | latency_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| single | 0.793 | (0.747, 0.837) | 1.0 | 0.793 | (0.747, 0.837) | 0.751 | 0.13 | 1.0 | 369 | 0.0155 | 106 |
| gated | 0.687 | (0.633, 0.737) | 0.823 | 0.834 | (0.789, 0.879) | 0.78 | 0.082 | 1.0 | 369 | 0.0155 | 108 |
| panel | 0.813 | (0.77, 0.857) | 1.0 | 0.813 | (0.77, 0.857) | 0.776 | 0.148 | 3.0 | 1178 | 0.0495 | 158 |
| panel_pool | 0.81 | (0.763, 0.853) | 1.0 | 0.81 | (0.763, 0.853) | 0.77 | 0.121 | 3.0 | 1178 | 0.0495 | 158 |
| escalation | 0.72 | (0.67, 0.767) | 0.87 | 0.828 | (0.782, 0.874) | 0.781 | 0.079 | 1.17 | 439 | 0.0185 | 121 |
| chain | 0.753 | (0.703, 0.803) | 1.0 | 0.753 | (0.703, 0.803) | 0.735 | 0.142 | 2.0 | 844 | 0.0354 | 226 |
| contrastive | 0.803 | (0.76, 0.847) | 1.0 | 0.803 | (0.76, 0.847) | 0.768 | 0.153 | 2.04 | 804 | 0.0338 | 127 |
| iterative | 0.733 | (0.683, 0.783) | 0.893 | 0.821 | (0.772, 0.866) | 0.774 | 0.075 | 1.28 | 527 | 0.0221 | 110 |

Paired accuracy delta versus the single decision on the same items (abstentions count as wrong):

| architecture | delta | ci95 | items changed |
|---|---|---|---|
| gated | -0.107 | (-0.143, -0.073) | 32 |
| panel | +0.020 | (0.0, 0.04) | 10 |
| panel_pool | +0.017 | (-0.003, 0.037) | 9 |
| escalation | -0.073 | (-0.107, -0.043) | 24 |
| chain | -0.040 | (-0.083, 0.003) | 46 |
| contrastive | +0.010 | (-0.013, 0.033) | 13 |
| iterative | -0.060 | (-0.09, -0.03) | 24 |

Selective prediction curve of the single decision (confidence floor tau):

| tau | coverage | selective_accuracy |
|---|---|---|
| 0.0 | 1.0 | 0.793 |
| 0.2 | 0.937 | 0.811 |
| 0.4 | 0.863 | 0.822 |
| 0.5 | 0.83 | 0.827 |
| 0.6 | 0.787 | 0.835 |
| 0.7 | 0.717 | 0.86 |
| 0.8 | 0.64 | 0.88 |
| 0.9 | 0.537 | 0.919 |
| 0.95 | 0.473 | 0.937 |

Extras: {"escalation_rate": 0.17, "contested_rate": 0.04, "mean_rounds": 1.28, "panel_unanimous_rate": 0.937, "single_replicates": {"runs": 3, "accuracies": [0.793, 0.803, 0.803], "accuracy_range": 0.01, "items_agreeing_across_runs": 0.977, "mean_confidence_spread": 0.035}}
