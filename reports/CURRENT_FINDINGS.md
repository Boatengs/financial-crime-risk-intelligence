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

### Shuffled-label sanity check and final gate

Training labels were permuted while the held-out test labels remained real. Random-forest performance collapsed to PR-AUC 0.0210 and ROC-AUC 0.4861 against a 0.0227 test prevalence. Repeated-split stability, permutation sanity, and schema-leakage checks all passed. Feature importance was not excessively concentrated: the top feature accounted for about 5.20% of total importance and the top 10 for about 38.46%.

The validated node-enriched random forest is therefore a credible decision-support benchmark rather than a single favorable split.

## Edge-feature enrichment

The 367,137 labeled edges were matched against the 196,215,606-row background-edge table using the full `(clId1, clId2, txId)` key. Match integrity passed exactly:
- 367,137 labeled edge rows and 367,137 distinct labeled edge keys;
- zero duplicate labeled edge keys;
- zero missing component IDs;
- 367,137 background matches and 367,137 distinct matched edge keys;
- zero missing labeled edges;
- zero duplicate background matches.

All 95 anonymized edge features were aggregated by mean, population standard deviation, minimum, and maximum, yielding 380 component-level edge-derived features. The node+edge feature store retains all 121,810 components and all 2,763 suspicious labels, with zero components lacking edge-feature coverage and zero null edge aggregates.

### Repeated node+edge validation

Five stratified 80/20 splits were run on the node+edge feature store using the same seed set as the node-only validation.

| Model | PR-AUC mean ± SD | PR-AUC range | ROC-AUC mean ± SD | Brier mean |
|---|---:|---:|---:|---:|
| Logistic regression | 0.1531 ± 0.0045 | 0.1471–0.1590 | 0.8773 ± 0.0041 | 0.1325 |
| Random forest | 0.5022 ± 0.0171 | 0.4877–0.5286 | 0.9247 ± 0.0027 | 0.0157 |

Edge features modestly improve logistic-regression PR-AUC relative to node-only logistic regression, but logistic regression remains materially weaker than the random forest. For the winning model family, the node+edge random forest is worse than the node-only random forest on the primary metric.

### Node-only vs node+edge random forest

| Measure | Node-only RF | Node+edge RF | Direction |
|---|---:|---:|---|
| Mean PR-AUC | 0.5279 | 0.5022 | Worse with edges |
| PR-AUC SD | 0.0081 | 0.0171 | Less stable with edges |
| Mean ROC-AUC | 0.9278 | 0.9247 | Slightly worse with edges |
| Mean Brier score | 0.0150 | 0.0157 | Slightly worse with edges |
| Top 0.5% precision | 94.26% | 94.10% | Essentially tied |
| Top 0.5% suspicious captured | 115.0 | 114.8 | Essentially tied |
| Top 1% precision | 77.38% | 73.44% | Worse with edges |
| Top 1% suspicious captured | 188.8 | 179.2 | Worse with edges |
| Top 2% precision | 53.65% | 51.76% | Worse with edges |
| Top 2% suspicious captured | 261.8 | 252.6 | Worse with edges |
| Top 5% suspicious captured | 355.6 | 344.2 | Worse with edges |
| Top 10% suspicious captured | 424.6 | 421.2 | Worse with edges |

Mean node+edge RF PR-AUC is about 0.0257 lower than node-only, a relative degradation of roughly 4.9%. The 0.5% review point is effectively tied, but node-only is better at every larger tested review budget. The edge-enriched random forest is also less stable across splits and has a slightly worse Brier score.

## Final model-selection decision

**Preferred research decision-support model: node-enriched random forest.**

This choice is supported by three considerations:
1. **Predictive value:** the node-only random forest has the highest validated PR-AUC.
2. **Operational value:** it captures more suspicious components at 1%, 2%, 5%, and 10% review budgets while matching the edge model at 0.5%.
3. **Parsimony and engineering cost:** the edge stage required scanning 196.2M rows and adding 380 features but did not improve the strongest model.

The edge experiment is therefore a validated negative incremental-value result: more data and more features did not automatically create more investigator value. This is an important engineering and model-governance conclusion, not a failed experiment.

## Raw-score calibration diagnostic

The seed-42 node-only random-forest reliability table shows that the raw score is useful for ranking but should not yet be presented as a literal suspicious-activity probability.

The 10 equal-width score bins show:
- in the lowest `(0.0, 0.1]` band, 22,873 cases have a mean score of about 1.42% and an observed suspicious rate of about 0.78%, so the model is mildly over-confident at the low end;
- in the `(0.5, 0.6]` band, the mean score is about 54.2% while the observed suspicious rate is 77.8%;
- in the `(0.6, 0.7]` band, the mean score is about 64.4% while the observed suspicious rate is 90.9%;
- the `(0.8, 0.9]` and `(0.9, 1.0]` bands are 100% suspicious in this held-out split, but contain only 31 and 37 cases respectively.

The weighted 10-bin expected calibration error from this table is about 0.009, so aggregate calibration is not poor. However, calibration error is uneven across the score range and the high-score bins are small. That makes probability language too strong even though the ranking signal is excellent.

`src/validate_rf_calibration.py` therefore evaluates the preferred node-only random forest on a fully held-out 60/20/20 train/calibration/test design. It compares the raw score with sigmoid (Platt-style) and isotonic calibration and reports Brier score, log loss, ECE, PR-AUC, ROC-AUC, and constrained-review metrics.

### Current interpretation
1. Basic connected-component structure contains limited risk signal.
2. The anonymized node features add substantial, repeatable predictive signal, especially for the nonlinear random forest.
3. The node-only random forest remains strong across repeated splits and constrained review budgets.
4. The edge feature pipeline is technically correct but does not improve the preferred random forest and makes it less stable on PR-AUC.
5. The preferred model should therefore retain structural + node-derived features and exclude the 380 edge aggregates from the operational baseline.
6. Raw random-forest outputs should remain ranking scores unless the held-out calibration experiment supports a calibrated probability layer.
7. Scores do not establish criminal activity, make legal determinations, or automate regulatory reporting.

The next project stage should evaluate held-out calibration, generate final 3D model-selection and calibration visuals, harden investigator-facing explanation outputs, and keep any graph-native benchmark clearly separated from the validated feature-engineered baseline.
