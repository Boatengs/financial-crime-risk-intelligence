# Calibration Decision

## Decision

**Operational investigator ranking uses the raw node-enriched random-forest score.**

**Sigmoid calibration may be used only as an optional research probability estimate.** It is not required for ranking, and it must remain clearly separated from the raw priority score.

**Isotonic calibration is not selected for operational use** because its improvement in probability calibration comes with weaker PR-AUC and worse capture at the smallest review budgets.

## Held-out design

Calibration was evaluated with a strict 60/20/20 train/calibration/test split using seed 42:

- training rows: 73,086;
- calibration rows: 24,362;
- test rows: 24,362;
- training positives: 1,658;
- calibration positives: 552;
- test positives: 553;
- feature count: 192;
- test prevalence: 0.0226993.

The comparison therefore evaluates calibration on a test set that was not used to fit either the random forest or the calibration mapping.

## Probability-quality comparison

| Method | PR-AUC | ROC-AUC | Brier | Log loss | ECE |
|---|---:|---:|---:|---:|---:|
| Raw random forest | 0.507435 | 0.919154 | 0.015337 | 0.072548 | 0.008812 |
| Sigmoid | 0.507435 | 0.919154 | 0.015334 | 0.068664 | 0.002716 |
| Isotonic | 0.481282 | 0.918349 | 0.015155 | 0.065206 | 0.001389 |

Sigmoid calibration reduces ECE by about 69% relative to the raw score and improves log loss while leaving ranking metrics effectively unchanged. Its Brier-score improvement is very small.

Isotonic achieves the best Brier score, log loss, and ECE, but PR-AUC falls from about 0.5074 to 0.4813. Because investigator prioritization is the primary project objective, that trade-off is not accepted for the operational queue.

## Constrained-review comparison

Raw random forest and sigmoid calibration produce identical investigator-budget results across all tested budgets:

| Review budget | Reviews | Suspicious captured | Precision | Recall | Lift |
|---|---:|---:|---:|---:|---:|
| 0.5% | 122 | 113 | 92.62% | 20.43% | 40.80x |
| 1% | 244 | 186 | 76.23% | 33.63% | 33.58x |
| 2% | 488 | 249 | 51.02% | 45.03% | 22.48x |
| 5% | 1,219 | 350 | 28.71% | 63.29% | 12.65x |
| 10% | 2,437 | 410 | 16.82% | 74.14% | 7.41x |

Isotonic loses four suspicious components at the top 0.5% budget (109 vs 113) and one at the top 1% budget (185 vs 186), while tying the other tested budgets.

## Product semantics

The project therefore uses two distinct concepts:

1. **Priority score / rank:** the raw random-forest score, used to order cases for investigator review. It is not presented as a probability.
2. **Optional calibrated estimate:** a sigmoid-calibrated value that may be displayed in research analysis when a probability-like estimate is useful. It must be labeled as a calibrated research estimate, not as proof of suspicious activity.

The investigator queue uses capacity-based priority tiers (top 0.5%, 1%, 2%, 5%, 10%, then standard) rather than raw-score thresholds such as 0.90 or 0.75. This avoids implying that the uncalibrated ranking score has a literal probability interpretation.

## Safety and governance

Neither the raw priority score nor a calibrated estimate establishes criminal activity, makes a legal determination, or automates regulatory reporting. Both are research decision-support outputs intended to prioritize human review.
