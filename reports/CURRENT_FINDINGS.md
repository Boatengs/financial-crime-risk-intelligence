# Current Findings

## First verified real-data baseline: structural features only

The repository has now been run on the official locally downloaded Elliptic2 labeled universe. These are **project results**, not synthetic fixture metrics and not published-paper metrics.

### Evaluation setup
- 121,810 labeled connected components.
- 119,047 licit and 2,763 suspicious components.
- Structural component features only; the 43 background-node features and 95 background-edge features are not included in this baseline.
- Stratified 80/20 train/test split with random state 42.
- Positive-class rate in the held-out test set: 0.0226993 (about 2.27%).
- Primary global metric: average precision / PR-AUC because of the severe class imbalance.

### Structural feature-store validation
The structural feature store contains 19 engineered features for all 121,810 labeled components, with zero null labels and zero null feature values.

The class-level structural summaries are notably similar:

| Structural measure | Licit | Suspicious |
|---|---:|---:|
| Average node count | 3.6461 | 3.7879 |
| Median node count | 3.0 | 3.0 |
| Average edge count | 3.0138 | 3.0232 |
| Median edge count | 2.0 | 2.0 |
| Average edges per node | 0.7234 | 0.7134 |
| Average directed density | 0.3792 | 0.3613 |
| Average source nodes | 1.0644 | 1.0575 |
| Average sink nodes | 1.1700 | 1.1922 |

Suspicious components are slightly larger on average but do not exhibit a large separation from licit components on these basic topology measures. The structural overlap is consistent with the weak discrimination observed in the baseline models and strengthens the case for testing the anonymized node and edge features as incremental sources of signal.

### Global discrimination

| Model | Average precision | ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.0263 | 0.5460 | 0.0227 |
| Random forest | 0.0241 | 0.5129 | 0.0227 |

The structural-only signal is weak. Logistic regression is the stronger baseline, but its average precision is only modestly above the 2.27% positive-class prevalence. Random forest is close to random discrimination on this feature set.

### Investigator-budget behavior

For logistic regression:

| Review budget | Reviews | Suspicious captured | Precision | Recall | Lift vs random |
|---|---:|---:|---:|---:|---:|
| 0.5% | 122 | 5 | 4.10% | 0.90% | 1.81x |
| 1% | 244 | 9 | 3.69% | 1.63% | 1.62x |
| 2% | 488 | 17 | 3.48% | 3.07% | 1.53x |
| 5% | 1,219 | 42 | 3.45% | 7.59% | 1.52x |
| 10% | 2,437 | 70 | 2.87% | 12.66% | 1.27x |

The best observed lift occurs at the smallest review budget, but the absolute number of suspicious components captured is small. This result is useful as an operational baseline, not as evidence that structural features alone are sufficient for AML prioritization.

### Current interpretation
1. Basic connected-component structure contains limited but measurable risk signal.
2. The class-level structural summaries overlap heavily, which helps explain why structure alone performs poorly.
3. The weak global performance creates a credible benchmark for testing the value of the 43 anonymized node features and later the 95 edge features.
4. The next experiment should hold the split/model/evaluation framework stable and enrich only the feature set so the incremental value of node features can be measured directly.
5. Scores are research prioritization signals only. They do not establish criminal activity, make legal determinations, or automate regulatory reporting.

No portfolio-level claim should be made from this structural-only baseline alone.
