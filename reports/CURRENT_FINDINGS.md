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

## Edge-feature enrichment

The 367,137 labeled edges were matched against the 196,215,606-row background-edge table using the full `(clId1, clId2, txId)` key. Match integrity passed exactly:
- 367,137 labeled edge rows and 367,137 distinct labeled edge keys;
- zero duplicate labeled edge keys;
- zero missing component IDs;
- 367,137 background matches and 367,137 distinct matched edge keys;
- zero missing labeled edges;
- zero duplicate background matches.

All 95 anonymized edge features were aggregated by mean, population standard deviation, minimum, and maximum, yielding 380 component-level edge-derived features. The node+edge feature store retains all 121,810 components and all 2,763 suspicious labels, with zero components lacking edge-feature coverage and zero null edge aggregates.

### Initial node+edge benchmark

On the same seed-42 80/20 split used for the node benchmark:

| Model | Node-only PR-AUC | Node+edge PR-AUC | Node-only ROC-AUC | Node+edge ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic regression | 0.1456 | 0.1513 | 0.8820 | 0.8732 |
| Random forest | 0.5306 | 0.4877 | 0.9266 | 0.9254 |

The combined edge features slightly improve logistic-regression PR-AUC but reduce its ROC-AUC. More importantly, the winning random forest becomes worse on the primary metric: PR-AUC falls by about 0.0429 absolute (roughly 8% relative) while ROC-AUC remains essentially flat.

For the random forest, investigator-budget performance also weakens:

| Review budget | Node-only suspicious captured | Node+edge suspicious captured | Node-only precision | Node+edge precision | Node-only lift | Node+edge lift |
|---|---:|---:|---:|---:|---:|---:|
| 0.5% | 117 | 114 | 95.90% | 93.44% | 42.25x | 41.17x |
| 1% | 190 | 176 | 77.87% | 72.13% | 34.30x | 31.78x |
| 2% | 262 | 242 | 53.69% | 49.59% | 23.65x | 21.85x |
| 5% | 357 | 339 | 29.29% | 27.81% | 12.90x | 12.25x |
| 10% | 421 | 420 | 17.28% | 17.23% | 7.61x | 7.59x |

This is a meaningful negative incremental-value finding: the expensive 95-edge-feature enrichment is technically sound but does not improve the strongest model on the matched split. The validated node-only random forest therefore remains the preferred operational benchmark unless repeated-split validation shows a materially different pattern.

### Current interpretation
1. Basic connected-component structure contains limited risk signal.
2. The anonymized node features add substantial and repeatable predictive signal, especially for the nonlinear random forest.
3. Random-forest PR-AUC is stable around 0.528 across five node-only splits, with strong constrained-review lift.
4. Shuffled-label performance collapses to chance, schema leakage checks pass, and no single node feature dominates the forest.
5. Adding 380 edge-derived aggregates increases dimensionality and engineering cost but reduces seed-42 random-forest PR-AUC and low-budget capture.
6. The node-only random forest is currently the preferred model because it is both simpler and better on the primary operational metrics.
7. Raw model scores remain ranking signals rather than calibrated probabilities until calibration is explicitly validated.
8. Scores do not establish criminal activity, make legal determinations, or automate regulatory reporting.

The next validation step is to repeat the node+edge benchmark across the same five seeds. If the degradation persists, the project should retain the node-only model and present the edge experiment as evidence that more features do not necessarily create more decision value.
