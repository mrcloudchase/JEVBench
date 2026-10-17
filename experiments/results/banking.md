# banking

n = 300 items per architecture, one run each.

| architecture | accuracy | accuracy_ci95 | coverage | selective_accuracy | selective_accuracy_ci95 | macro_f1_acted | ece | calls_per_item | tokens_per_item | usd_per_1k_items | latency_ms_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| single | 0.847 | (0.8, 0.883) | 1.0 | 0.847 | (0.8, 0.883) | 0.811 | 0.059 | 1.0 | 1686 | 0.0708 | 113 |
| gated | 0.837 | (0.793, 0.877) | 0.96 | 0.872 | (0.83, 0.906) | 0.81 | 0.057 | 1.0 | 1686 | 0.0708 | 112 |
| panel | 0.86 | (0.817, 0.897) | 0.997 | 0.863 | (0.823, 0.9) | 0.832 | 0.044 | 3.0 | 5117 | 0.2149 | 165 |
| panel_pool | 0.86 | (0.817, 0.897) | 1.0 | 0.86 | (0.817, 0.897) | 0.829 | 0.061 | 3.0 | 5117 | 0.2149 | 165 |
| escalation | 0.85 | (0.807, 0.887) | 0.997 | 0.853 | (0.809, 0.89) | 0.812 | 0.066 | 1.04 | 1761 | 0.0739 | 117 |
| chain | 0.85 | (0.81, 0.887) | 1.0 | 0.85 | (0.81, 0.887) | 0.808 | 0.078 | 2.0 | 2123 | 0.0892 | 215 |
| iterative | 0.85 | (0.807, 0.89) | 1.0 | 0.85 | (0.807, 0.89) | 0.815 | 0.075 | 1.04 | 1826 | 0.0767 | 114 |

Paired accuracy delta versus the single decision on the same items (abstentions count as wrong):

| architecture | delta | ci95 | items changed |
|---|---|---|---|
| gated | -0.010 | (-0.027, 0.003) | 5 |
| panel | +0.013 | (-0.003, 0.033) | 8 |
| panel_pool | +0.013 | (-0.003, 0.033) | 8 |
| escalation | +0.003 | (-0.01, 0.017) | 5 |
| chain | +0.003 | (-0.017, 0.023) | 9 |
| iterative | +0.003 | (-0.01, 0.02) | 5 |

Selective prediction curve of the single decision (confidence floor tau):

| tau | coverage | selective_accuracy |
|---|---|---|
| 0.0 | 1.0 | 0.847 |
| 0.2 | 1.0 | 0.847 |
| 0.4 | 0.98 | 0.864 |
| 0.5 | 0.953 | 0.878 |
| 0.6 | 0.903 | 0.897 |
| 0.7 | 0.88 | 0.905 |
| 0.8 | 0.833 | 0.924 |
| 0.9 | 0.747 | 0.964 |
| 0.95 | 0.68 | 0.975 |

Extras: {"escalation_rate": 0.043, "mean_rounds": 1.04, "panel_unanimous_rate": 0.947, "single_replicates": {"runs": 3, "accuracies": [0.847, 0.85, 0.843], "accuracy_range": 0.007, "items_agreeing_across_runs": 0.973, "mean_confidence_spread": 0.015}}
