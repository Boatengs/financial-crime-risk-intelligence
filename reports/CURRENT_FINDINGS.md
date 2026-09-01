# Current Findings

## Verified structural baseline

The repository has been run on the official locally downloaded Elliptic2 labeled universe. These are **project results**, not synthetic fixture metrics and not published-paper metrics.

### Evaluation setup
- 121,810 labeled connected components.
- 119,047 licit and 2,763 suspicious components.
- Positive-class prevalence: about 2.27%.
- Primary global metric: average precision / PR-AUC because of the severe class imbalance.

### Structural-only benchmark

The structural feature store contains 19 complete engineered features for all 121,810 labeled components. Licit and suspicious components are similar on basic topology, and structure alone provides weak discrimination.

| Model | Average precision | ROC-AUC |
|---|---:|---:|
| Logistic regression | 0.0263 | 0.5460 |
| Random forest | 0.0241 | 0.5129 |

For the stronger structural logistic model, the top 0.5% review budget captured 5 suspicious components in 122 reviews, with 4.10% precision and 1.81x lift versus random review.

## Validated node-enriched benchmark

The 49.3M-row background-node table was joined out-of-core to the 444,521 labeled nodes with perfect match integrity:
- 444,521 distinct labeled nodes matched exactly once;
- zero missing labeled nodes;
- zero duplicate background matches;
- all 43 anonymized node features were aggregated by mean, population standard deviation, minimum, and maximum;
- 172 node-derived component features were added;
- all 121,810 components and all 2,763 suspicious labels were retained.

### Initial split

Using the same 80/20 component-level split and modeling framework, the first node-enriched run produced:

| Model | Average precision | ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.1456 | 0.8820 | 0.0227 |
| Random forest | 0.5306 | 0.9266 | 0.0227 |

The random forest captured 117 suspicious components in the top 122 reviews (top 0.5%), corresponding to 95.90% precision, 21.16% recall, and 42.25x lift versus random review.

### Repeated-split validation

Five stratified 80/20 splits were run with seeds 11, 23, 42, 71, and 101.

| Model | PR-AUC mean ± SD | PR-AUC range | ROC-AUC mean ± SD | ROC-AUC range | Brier mean |
|---|---:|---:|---:|---:|---:|
| Logistic regression | 0.1435 ± 0.0043 | 0.1385–0.1498 | 0.8808 ± 0.0030 | 0.8773–0.8853 | 0.1431 |
| Random forest | 0.5279 ± 0.0081 | 0.5190–0.5392 | 0.9278 ± 0.0046 | 0.9220–0.9348 | 0.0150 |

The random-forest result is stable across the tested splits rather than being driven by seed 42 alone.

### Repeated investigator-budget validation

For the random forest:

| Review budget | Precision mean | Recall mean | Lift mean | Suspicious captured mean | Capture range |
|---|---:|---:|---:|---:|---:|
| 0.5% | 94.26% | 20.80% | 41.53x | 115.0 | 112–117 |
| 1% | 77.38% | 34.14% | 34.09x | 188.8 | 182–194 |
| 2% | 53.65% | 47.34% | 23.63x | 261.8 | 252–270 |
| 5% | 29.17% | 64.30% | 12.85x | 355.6 | 347–362 |
| 10% | 17.42% | 76.78% | 7.68x | 424.6 | 419–438 |

The high-lift queue behavior is therefore operationally stable across the tested random splits.

### Shuffled-label sanity check

Training labels were permuted while the held-out test labels remained real. Performance collapsed as expected:

| Model | Permuted-label PR-AUC | Permuted-label ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.0245 | 0.4990 | 0.0227 |
| Random forest | 0.0210 | 0.4861 | 0.0227 |

This collapse toward prevalence / chance discrimination is strong evidence that the validated node-enriched performance depends on the real feature-label relationship rather than surviving arbitrary labels.

### Current interpretation
1. Basic connected-component structure contains limited risk signal.
2. The anonymized node features add substantial, repeatable predictive signal, especially for the nonlinear random forest.
3. Random-forest PR-AUC is stable around 0.528 across five splits and review-budget lift remains very high at constrained investigator capacity.
4. The shuffled-label sanity check behaves correctly, materially increasing confidence in the result.
5. A final feature-dominance / target-proxy review remains appropriate because the node features are anonymized and the performance gain is large.
6. Raw scores remain research prioritization signals. They do not establish criminal activity, make legal determinations, or automate regulatory reporting.

The validated node-enriched random forest is now the primary project benchmark for the later 95-edge-feature experiment, subject to the final feature-dominance audit.