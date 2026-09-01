# Project Status

## Current phase
**Phase 4 — edge-enriched benchmark validation**

### Complete
- Dataset selection: Elliptic2.
- Decision framing: investigator prioritization under review constraints.
- Repository architecture pushed to `main`.
- Synthetic smoke-test fixture and CI.
- Official five-file layout and downloaded-release schema verified.
- Verified local row counts:
  - 49,299,864 background nodes;
  - 196,215,606 background edges;
  - 121,810 labeled connected components;
  - 444,521 labeled nodes;
  - 367,137 labeled edges.
- Verified feature layout: 43 anonymized node features and 95 anonymized edge features.
- Actual downloaded labels verified: 119,047 `licit` components and 2,763 `suspicious` components.
- Labeled-universe integrity verified: zero missing source nodes, zero missing target nodes, and zero cross-component edges.
- Structural feature store built with 19 complete features and zero nulls.
- Structural benchmark completed:
  - logistic regression PR-AUC 0.026323 / ROC-AUC 0.545966;
  - random forest PR-AUC 0.024107 / ROC-AUC 0.512885;
  - logistic regression top-0.5% lift 1.8055x.
- Background-node enrichment completed with perfect 444,521-node match integrity.
- All 43 node features aggregated into 172 component-level features.
- Initial node-enriched benchmark completed:
  - logistic regression PR-AUC 0.145578 / ROC-AUC 0.882008;
  - random forest PR-AUC 0.530556 / ROC-AUC 0.926611;
  - random forest top-0.5%: 117 suspicious components in 122 reviews, 95.90% precision, 42.25x lift.
- Five-seed node-only validation completed:
  - random forest PR-AUC mean 0.527917, SD 0.008117, range 0.519036–0.539170;
  - random forest ROC-AUC mean 0.927790, SD 0.004619;
  - top-0.5% precision mean 94.26%, lift mean 41.53x, suspicious captured mean 115.0;
  - shuffled-label PR-AUC 0.020978 / ROC-AUC 0.486122 against 0.022699 prevalence;
  - final stability, permutation, schema-leakage, and feature-dominance gates passed.
- Validated node-enriched random forest is the primary benchmark.
- Background-edge enrichment completed successfully on the 196.2M-row table:
  - 367,137 labeled edge rows and 367,137 distinct labeled edge keys;
  - zero duplicate labeled keys, missing component IDs, missing labeled edges, or duplicate background matches;
  - all 95 edge features aggregated into 380 component-level edge-derived features;
  - all 121,810 components retained, including all 2,763 suspicious components;
  - zero components without edge coverage and zero null edge aggregates.
- Initial node+edge benchmark completed on the same seed-42 split:
  - logistic regression PR-AUC 0.151296 / ROC-AUC 0.873186;
  - random forest PR-AUC 0.487667 / ROC-AUC 0.925434.
- Edge features do **not** improve the winning random forest on the matched split:
  - RF PR-AUC falls from 0.530556 node-only to 0.487667 node+edge;
  - top-0.5% suspicious captured falls from 117 to 114;
  - top-1% suspicious captured falls from 190 to 176;
  - top-2% suspicious captured falls from 262 to 242;
  - ROC-AUC remains essentially flat.
- Initial conclusion: the 95-edge-feature experiment is technically successful but adds complexity without improving the primary operational model.
- Investigator queue selection defaults to the highest-average-precision model.
- 3D visualization remains the project standard.

### Next
- Run repeated-split / permutation validation on `data/derived/component_features_node_edge_enriched.parquet` using the same five seeds as the validated node benchmark.
- Write validation outputs to a separate `results/node_edge_enriched_validation/` directory.
- Compare repeated node+edge PR-AUC, ROC-AUC, Brier score, and review-budget lift against the validated node-only benchmark.
- If node+edge underperformance persists, formally retain the simpler node-only random forest as the preferred operational model and present the edge stage as a negative incremental-value finding.
- Review calibration before presenting raw model scores as probabilities.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready 3D comparative visuals from the validated model-selection story: structure vs node vs node+edge.
