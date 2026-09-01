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

The high-lift queue behavior is operationally stable across the tested random splits.

### Shuffled-label sanity check

Training labels were permuted while the held-out test labels remained real. Performance collapsed as expected:

| Model | Permuted-label PR-AUC | Permuted-label ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.0245 | 0.4990 | 0.0227 |
| Random forest | 0.0210 | 0.4861 | 0.0227 |

This collapse toward prevalence / chance discrimination is strong evidence that the validated node-enriched performance depends on the real feature-label relationship rather than surviving arbitrary labels.

### Final validation gate

The compact validation gate reports `hard_checks_pass`:
- repeated-split stability: pass;
- permutation sanity: pass;
- schema leakage audit: pass.

Feature-importance concentration is not excessive. The largest random-forest feature, `node_feat_28_max`, contributes about 5.20% of total importance, while the top 10 features together contribute about 38.46%. The gate therefore does not recommend manual leakage review based on feature dominance.

The strongest class-separation signals are concentrated around anonymized node features 28 and 29. `node_feat_29_max`, `node_feat_29_sd`, and `node_feat_29_mean` have standardized mean differences of about 1.23, 1.21, and 1.21 respectively. Because the source variables are anonymized, these patterns can be described quantitatively but should not be assigned unsupported semantic meaning.

### Current interpretation
1. Basic connected-component structure contains limited risk signal.
2. The anonymized node features add substantial and repeatable predictive signal, especially for the nonlinear random forest.
3. Random-forest PR-AUC is stable around 0.528 across five splits, and review-budget lift remains very high at constrained investigator capacity.
4. Shuffled-label performance collapses to chance, schema leakage checks pass, and no single feature dominates the forest.
5. The validated node-enriched random forest is the primary project benchmark for the edge-feature experiment.
6. Raw model scores remain ranking signals rather than calibrated probabilities until calibration is explicitly validated.
7. Scores do not establish criminal activity, make legal determinations, or automate regulatory reporting.

## Edge-feature enrichment: engineering validation complete

The 367,137 labeled edges were matched against the 196,215,606-row background-edge table using the full `(clId1, clId2, txId)` key. The audit passed exactly:
- 367,137 labeled edge rows and 367,137 distinct labeled edge keys;
- zero duplicate labeled edge keys;
- zero missing component IDs;
- 367,137 background matches and 367,137 distinct matched edge keys;
- zero missing labeled edges;
- zero duplicate background matches.

All 95 anonymized edge features were aggregated by mean, population standard deviation, minimum, and maximum, yielding 380 component-level edge-derived features. The node+edge feature store retains all 121,810 components and all 2,763 suspicious labels, with zero components lacking edge-feature coverage and zero null edge aggregates.

This means the edge-enriched dataset is technically valid for modeling. The next question is not data integrity but incremental value: whether the 380 edge-derived features improve PR-AUC and constrained-review lift beyond the validated node benchmark, or simply add model complexity.

No edge-enriched performance claim is reported yet.
