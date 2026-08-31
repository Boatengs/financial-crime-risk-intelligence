# Model Validation

## External research benchmark

The Elliptic2 paper provides reference results for an 80/10/10 random train/validation/test split. These are **published reference benchmarks, not results from this repository**.

| Method | Test F1 | Test PR-AUC | Test ROC-AUC |
|---|---:|---:|---:|
| GNN-Seg | 0.398 | 0.026 | 0.537 |
| Sub2Vec | 0.944 | 0.022 | 0.496 |
| GLASS | 0.933 | 0.208 | 0.889 |

The authors report that the full experiment ran on a Linux server with 160 CPU cores and 1.2 TB RAM, without GPUs, and did not use the dataset's node/edge features because of memory constraints. This repository therefore treats scalable feature use and operational review-budget evaluation as a core engineering challenge rather than assuming the published setup can be reproduced cheaply.

## Planned evidence
- PR-AUC with confidence intervals or repeated splits.
- ROC-AUC as secondary context.
- precision / recall / lift at fixed review budgets.
- suspicious cases captured per 100 reviews.
- false-positive workload at fixed review capacity.
- confusion matrix at an operational threshold.
- calibration diagnostics.
- feature stability / model sensitivity.
- graph-model comparison against explainable baselines.
- resource profile: memory, wall-clock time, and storage footprint.

## Validation rule

No full-data metric should be published as a project result before the official Elliptic2 data has been processed by this repository. Synthetic fixture metrics validate code paths only.
