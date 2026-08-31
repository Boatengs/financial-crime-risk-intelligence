# Model Validation

## External research benchmark

The Elliptic2 paper provides reference results for an 80/10/10 random train/validation/test split. These are **published reference benchmarks, not results from this repository**.

| Method | Test F1 | Test PR-AUC | Test ROC-AUC |
|---|---:|---:|---:|
| GNN-Seg | 0.398 | 0.026 | 0.537 |
| Sub2Vec | 0.944 | 0.022 | 0.496 |
| GLASS | 0.933 | 0.208 | 0.889 |

The authors report that the full experiment ran on a Linux server with 160 CPU cores and 1.2 TB RAM, without GPUs, and did not use the dataset's node/edge features because of memory constraints. This repository therefore treats scalable feature use and operational review-budget evaluation as a core engineering challenge rather than assuming the published setup can be reproduced cheaply.

## Verified project baseline: structural features only

The first real-data project baseline uses the official downloaded labeled universe and a stratified 80/20 train/test split with random state 42. It is **not directly comparable one-for-one with the paper's 80/10/10 protocol**, so published values remain reference points rather than leaderboard targets.

| Model | Average precision / PR-AUC | ROC-AUC | Held-out base rate |
|---|---:|---:|---:|
| Logistic regression | 0.026323 | 0.545966 | 0.022699 |
| Random forest | 0.024107 | 0.512885 | 0.022699 |

Operational review-budget results for logistic regression:

| Review budget | Reviews | Suspicious captured | Precision | Recall | Lift vs random |
|---|---:|---:|---:|---:|---:|
| 0.5% | 122 | 5 | 0.04098 | 0.00904 | 1.8055x |
| 1% | 244 | 9 | 0.03689 | 0.01627 | 1.6250x |
| 2% | 488 | 17 | 0.03484 | 0.03074 | 1.5347x |
| 5% | 1,219 | 42 | 0.03445 | 0.07595 | 1.5179x |
| 10% | 2,437 | 70 | 0.02872 | 0.12658 | 1.2654x |

Interpretation: component structure alone provides only weak discrimination. This is intentionally retained as the benchmark to beat when background node and edge features are added.

## Next validation evidence
- Hold split/model/evaluation settings stable while adding 43 background-node features.
- Measure incremental PR-AUC, ROC-AUC, and review-budget lift versus the structural-only baseline.
- Add repeated splits or confidence intervals before promoting any model result as stable.
- Add calibration diagnostics and an operational threshold analysis.
- Add feature stability / sensitivity and explainability outputs.
- Add 95 edge-feature aggregates in a separate resource-controlled experiment.
- Compare enriched baselines with the published graph-model reference benchmarks.
- Add a graph-native GLASS-style or equivalent benchmark when compute permits.
- Record resource profile: memory, wall-clock time, and storage footprint.

## Validation rule

Only metrics produced from the official Elliptic2 data by this repository may be labeled as project results. Synthetic fixture metrics validate code paths only, and published-paper metrics must remain clearly separated as external references.
