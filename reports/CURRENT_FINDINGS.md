# Current Findings

## Evaluation frame

The project uses the locally downloaded Elliptic2 labeled universe:
- 121,810 labeled connected components;
- 119,047 licit and 2,763 suspicious components;
- positive prevalence about 2.27%;
- PR-AUC is the primary global metric because of severe class imbalance;
- investigator-budget precision, recall, lift, and suspicious cases captured are the primary operational metrics.

These are **project results**, not synthetic fixture metrics and not published-paper metrics.

## Structural-only benchmark

The 19-feature structural store is complete and contains zero nulls, but basic component topology provides little discrimination.

| Model | PR-AUC | ROC-AUC |
|---|---:|---:|
| Logistic regression | 0.0263 | 0.5460 |
| Random forest | 0.0241 | 0.5129 |

For the stronger structural logistic model, the top 0.5% review budget captured only 5 suspicious components in 122 reviews, with 4.10% precision and 1.81x lift.

## Validated node-enriched benchmark

All 444,521 labeled nodes matched exactly once against the 49.3M-row background-node table. All 43 anonymized node features were aggregated by mean, population standard deviation, minimum, and maximum, producing 172 component-level node features while retaining all 121,810 components.

Five stratified 80/20 splits validated the node-enriched random forest:

| Measure | Result |
|---|---:|
| Mean PR-AUC | 0.5279 |
| PR-AUC SD | 0.0081 |
| PR-AUC range | 0.5190–0.5392 |
| Mean ROC-AUC | 0.9278 |
| Mean Brier score | 0.0150 |
| Top 0.5% precision | 94.26% |
| Top 0.5% lift | 41.53x |
| Suspicious captured in top 0.5% | 115.0 mean |
| Suspicious captured in top 1% | 188.8 mean |
| Suspicious captured in top 2% | 261.8 mean |

A shuffled-label sanity check collapsed random-forest performance to PR-AUC 0.0210 and ROC-AUC 0.4861 against a 0.0227 test prevalence. Repeated-split stability, permutation sanity, schema-leakage, and feature-dominance checks passed. The largest RF feature accounts for about 5.2% of total importance and the top 10 for about 38.5%.

## Edge-feature ablation

All 367,137 labeled edges matched exactly once against the 196.2M-row background-edge table on `(clId1, clId2, txId)`. All 95 anonymized edge features were aggregated into 380 component-level edge features with zero missing edge coverage and zero null aggregates.

The engineering pipeline was successful, but the additional features did not improve the strongest model.

| Measure | Node-only RF | Node+edge RF |
|---|---:|---:|
| Mean PR-AUC | 0.5279 | 0.5022 |
| PR-AUC SD | 0.0081 | 0.0171 |
| Mean ROC-AUC | 0.9278 | 0.9247 |
| Mean Brier score | 0.0150 | 0.0157 |
| Top 0.5% precision | 94.26% | 94.10% |
| Top 1% suspicious captured | 188.8 | 179.2 |
| Top 2% suspicious captured | 261.8 | 252.6 |
| Top 5% suspicious captured | 355.6 | 344.2 |
| Top 10% suspicious captured | 424.6 | 421.2 |

The node+edge RF loses about 4.9% relative PR-AUC and is less stable across splits. The 0.5% review point is effectively tied, while node-only performs better at every larger tested review budget.

**Final model-selection decision: use the node-enriched random forest.**

The edge experiment is a validated negative incremental-value finding: considerably more data engineering and model dimensionality did not create more investigator value.

## Held-out calibration validation

Probability calibration was evaluated with a strict 60/20/20 train/calibration/test design using the preferred 192-feature node-enriched store.

| Method | PR-AUC | ROC-AUC | Brier | Log loss | ECE |
|---|---:|---:|---:|---:|---:|
| Raw RF | 0.507435 | 0.919154 | 0.015337 | 0.072548 | 0.008812 |
| Sigmoid | 0.507435 | 0.919154 | 0.015334 | 0.068664 | 0.002716 |
| Isotonic | 0.481282 | 0.918349 | 0.015155 | 0.065206 | 0.001389 |

Sigmoid calibration reduces ECE by about 69% relative to the raw score and improves log loss without changing PR-AUC, ROC-AUC, or any tested constrained-review result. Raw RF and sigmoid both capture 113 suspicious components in the top 122 reviews, 186 in the top 244, and 249 in the top 488.

Isotonic produces the best Brier score, log loss, and ECE, but it reduces PR-AUC to 0.4813 and captures only 109 suspicious components in the top 122 reviews. That trade-off is not acceptable for the primary investigator-prioritization objective.

## Final score semantics

The project uses two distinct outputs:

1. **Raw RF priority score:** the operational ranking signal used to order investigator review. It is not a literal suspicious-activity probability.
2. **Optional sigmoid-calibrated estimate:** a research probability estimate that may be used when probability-like interpretation is helpful. It remains decision support only and is not evidence of criminal activity.

The investigator queue therefore uses **capacity-based priority tiers** rather than raw-score thresholds:
- tier 1: top 0.5%;
- tier 2: top 1%;
- tier 3: top 2%;
- tier 4: top 5%;
- tier 5: top 10%;
- standard: remaining cases.

This prevents labels such as `critical` or `high` from implying an unsupported probability interpretation.

## Current interpretation

1. Basic graph structure alone contains little useful prioritization signal.
2. Node-derived features provide substantial, repeatable investigator value.
3. Edge-derived aggregates add engineering cost but do not improve the winning model.
4. The node-enriched random forest is the preferred research decision-support model.
5. Ranking performance is the primary product requirement; sigmoid calibration is optional and does not replace the raw ranking signal.
6. Raw model scores must not be presented as literal suspicious-activity probabilities.
7. Scores prioritize human review only. They do not establish criminal activity, make legal determinations, or automate regulatory reporting.

The remaining product-hardening work is to regenerate the final queue with capacity-based tiers, create final 3D model-selection/calibration visuals, and replace placeholder reason text with case-specific evidence-based explanations that do not over-interpret anonymized source features.
