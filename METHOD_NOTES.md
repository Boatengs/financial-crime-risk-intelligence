# Method Notes

## Unit of analysis
The principal unit is a labeled transaction **subgraph / connected component**, not an individual transaction.

## Baselines
Two intentionally interpretable baselines are included:
- class-weighted logistic regression,
- class-weighted random forest.

The project should establish a credible baseline before introducing graph neural networks.

## Imbalance
Accuracy is not a decision metric. The primary global metric is PR-AUC. Operational evaluation uses top-K review budgets.

## Review-budget metrics
For review budget `K`:
- precision@K = suspicious cases among the top K / K,
- recall@K = suspicious cases among the top K / total suspicious cases,
- lift@K = precision@K / base suspicious rate.

## Explainability
Reason codes are derived from structural statistics and model feature contributions/importances. They are descriptive model reasons, not legal conclusions.

## Validation controls
- fixed random seeds,
- stratified holdout split,
- no target leakage into feature construction,
- schema and row-count manifest,
- deterministic fixture CI,
- explicit caveat when full-dataset compute has not been run.
