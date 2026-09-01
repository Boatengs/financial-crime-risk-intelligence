# Model Selection Memo

## Decision

**Preferred research decision-support model: node-enriched random forest.**

The selected model uses the validated structural component features plus 172 aggregates derived from the 43 anonymized background-node features. The 380 edge-derived aggregates are excluded from the preferred operational baseline because they increase engineering cost and feature dimensionality without improving the winning random forest.

## Evidence hierarchy

### Structural-only baseline
- Random-forest PR-AUC: 0.0241 on the seed-42 split.
- Structural logistic regression is slightly stronger but still weak, with PR-AUC 0.0263.
- Basic topology alone therefore provides limited discrimination.

### Validated node-enriched random forest
Five stratified 80/20 splits using seeds 11, 23, 42, 71, and 101:
- mean PR-AUC: **0.5279**;
- PR-AUC SD: **0.0081**;
- PR-AUC range: **0.5190–0.5392**;
- mean ROC-AUC: **0.9278**;
- mean Brier score: **0.0150**.

Operational review behavior:
- top 0.5%: 94.26% mean precision, 41.53x mean lift, 115.0 suspicious components captured on average;
- top 1%: 77.38% mean precision, 34.09x mean lift, 188.8 suspicious components captured on average;
- top 2%: 53.65% mean precision, 23.63x mean lift, 261.8 suspicious components captured on average;
- top 5%: 355.6 suspicious components captured on average;
- top 10%: 424.6 suspicious components captured on average.

Validation safeguards:
- shuffled-label RF PR-AUC 0.0210 against 0.0227 prevalence;
- shuffled-label ROC-AUC 0.4861;
- repeated-split stability passed;
- schema-leakage audit passed;
- feature-dominance review passed;
- top individual feature importance about 5.2%;
- top-10 cumulative importance about 38.5%.

### Node+edge random forest
The 196.2M-row background-edge scan matched all 367,137 labeled edges exactly once and produced 380 valid edge-derived component features. Data engineering integrity therefore passed; model degradation cannot be attributed to an incomplete edge join.

Across the same five validation seeds:
- mean PR-AUC: **0.5022**;
- PR-AUC SD: **0.0171**;
- mean ROC-AUC: **0.9247**;
- mean Brier score: **0.0157**.

Relative to node-only RF:
- mean PR-AUC is lower by about 0.0257, or 4.9%;
- PR-AUC variability is higher;
- ROC-AUC is slightly lower;
- Brier score is slightly worse;
- top-0.5% investigator performance is essentially tied;
- investigator capture is worse at 1%, 2%, 5%, and 10% review budgets.

## Interpretation

The edge experiment is a validated negative incremental-value result. The 95 anonymized edge features are not useless in every model family: they modestly improve logistic-regression PR-AUC. However, logistic regression remains substantially weaker than the random forest, and the edge features do not improve the model that best serves the project decision objective.

The preferred node-only feature set therefore offers the best combination of:
- validated PR-AUC;
- constrained-review lift;
- stability across random splits;
- lower dimensionality;
- lower recurring compute and storage cost;
- easier model governance and explanation.

## Operational framing

The selected model is for research prioritization only. Its scores rank connected transaction components for investigator review. Scores do **not** establish criminal activity, make legal determinations, identify real-world offenders, or automate regulatory reporting. Raw random-forest scores should not be described as calibrated probabilities unless calibration is explicitly validated.

## Next controls

1. Evaluate and, if warranted, calibrate the preferred random-forest scores.
2. Produce final 3D model-selection and investigator-capacity visuals.
3. Strengthen investigator-facing explanation outputs around feature contributions / reason codes without assigning unsupported semantics to anonymized features.
4. Add a graph-native benchmark when compute permits, clearly separated from the selected feature-engineered model.
