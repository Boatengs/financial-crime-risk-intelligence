# Current Findings

## Verified structural baseline

The repository has been run on the official locally downloaded Elliptic2 labeled universe. These are **project results**, not synthetic fixture metrics and not published-paper metrics.

### Evaluation setup
- 121,810 labeled connected components.
- 119,047 licit and 2,763 suspicious components.
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

Suspicious components are slightly larger on average but do not exhibit a large separation from licit components on these basic topology measures.

### Structural-only discrimination

| Model | Average precision | ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.0263 | 0.5460 | 0.0227 |
| Random forest | 0.0241 | 0.5129 | 0.0227 |

For the stronger structural logistic model, the top 0.5% review budget captured 5 suspicious components in 122 reviews, with 4.10% precision and 1.81x lift versus random review.

The structural-only signal is weak and serves as the benchmark to beat.

## Provisional node-enriched benchmark

The 49.3M-row background-node table was joined out-of-core to the 444,521 labeled nodes with perfect match integrity:
- 444,521 distinct labeled nodes matched exactly once;
- zero missing labeled nodes;
- zero duplicate background matches;
- all 43 anonymized node features were aggregated by mean, population standard deviation, minimum, and maximum;
- 172 node-derived component features were added;
- all 121,810 components and all 2,763 suspicious labels were retained.

Using the same 80/20 split and modeling framework, the first node-enriched run produced:

| Model | Average precision | ROC-AUC | Test base rate |
|---|---:|---:|---:|
| Logistic regression | 0.1456 | 0.8820 | 0.0227 |
| Random forest | 0.5306 | 0.9266 | 0.0227 |

The random forest result is dramatically stronger than the structural baseline. At the top 0.5% review budget it captured 117 suspicious components in 122 reviews, corresponding to 95.90% precision, 21.16% recall, and 42.25x lift versus random review. At the top 1% it captured 190 suspicious components in 244 reviews, with 77.87% precision and 34.36% recall.

### Validation status

These node-enriched metrics are **provisional until stress-tested**. The magnitude of the improvement is large enough that the project will not treat the single-split result as portfolio-grade evidence yet.

Before adding the 95 edge features or publishing headline claims, the repository requires:
1. repeated stratified train/test splits across multiple seeds;
2. a shuffled-label sanity check that should collapse performance toward the class prevalence;
3. feature-name and feature-value leakage audits;
4. feature-stability / dominant-feature inspection;
5. calibration diagnostics and review-budget stability across splits.

`src/validate_node_enriched_models.py` implements this validation stage and writes all outputs to `results/node_enriched_validation/`.

### Current interpretation
1. Basic connected-component structure contains limited risk signal.
2. The anonymized node features appear to contain substantial incremental signal, especially for the nonlinear random-forest model.
3. The random-forest gain is large enough that validation is now more important than immediately adding more features.
4. If repeated-split and permutation checks confirm the signal, the node-enriched model becomes the primary benchmark for the later 95-edge-feature experiment.
5. Scores are research prioritization signals only. They do not establish criminal activity, make legal determinations, or automate regulatory reporting.

No final portfolio claim should be made from the single-split node-enriched result alone.
