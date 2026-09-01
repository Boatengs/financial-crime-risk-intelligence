# Project Status

## Current phase
**Phase 4 — edge-enriched model benchmarking**

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
- All 43 node features aggregated by mean, population standard deviation, minimum, and maximum into 172 component-level features.
- Initial node-enriched benchmark completed:
  - logistic regression PR-AUC 0.145578 / ROC-AUC 0.882008;
  - random forest PR-AUC 0.530556 / ROC-AUC 0.926611;
  - random forest top-0.5%: 117 suspicious components in 122 reviews, 95.90% precision, 42.25x lift.
- Five-seed repeated-split validation completed:
  - random forest PR-AUC mean 0.527917, SD 0.008117, range 0.519036–0.539170;
  - random forest ROC-AUC mean 0.927790, SD 0.004619;
  - random forest Brier score mean 0.015044.
- Repeated review-budget stability verified:
  - top 0.5% precision mean 94.26%, lift mean 41.53x, suspicious captured mean 115.0 (range 112–117);
  - top 1% precision mean 77.38%, lift mean 34.09x, suspicious captured mean 188.8.
- Shuffled-label sanity check passed:
  - random forest PR-AUC 0.020978 / ROC-AUC 0.486122 against 0.022699 prevalence.
- Final node validation gate passed:
  - repeated-split stability pass;
  - permutation sanity pass;
  - schema leakage audit pass;
  - top feature importance 5.20%;
  - top-10 cumulative importance 38.46%;
  - feature-dominance manual review not recommended by the gate.
- Validated node-enriched random forest promoted to the primary benchmark for the edge-feature experiment.
- Background-edge enrichment completed successfully on the 196.2M-row table:
  - 367,137 labeled edge rows and 367,137 distinct labeled edge keys;
  - zero duplicate labeled edge keys;
  - zero missing component mappings;
  - 367,137 background matches and 367,137 distinct matched edge keys;
  - zero missing labeled edges and zero duplicate background matches;
  - all 95 edge features aggregated by mean, population standard deviation, minimum, and maximum;
  - 380 component-level edge-derived features created;
  - all 121,810 components retained, including all 2,763 suspicious components;
  - zero components without edge-feature coverage;
  - zero rows with null edge aggregates.
- Edge-enriched feature store written to `data/derived/component_features_node_edge_enriched.parquet`.
- Investigator queue selection defaults to the highest-average-precision model.
- 3D visualization remains the project standard.

### Next
- Train logistic regression and random forest on `data/derived/component_features_node_edge_enriched.parquet` into a separate `results/node_edge_enriched/` directory.
- Build a separate edge-enriched investigator queue and 3D figures.
- Compare edge-enriched PR-AUC, ROC-AUC, and review-budget lift against the validated node benchmark (RF PR-AUC mean ~0.528; top-0.5% lift mean ~41.5x).
- If edge features materially improve the initial benchmark, run repeated-split / permutation validation using `src/validate_node_enriched_models.py --input data/derived/component_features_node_edge_enriched.parquet --results-dir results/node_edge_enriched_validation`.
- If edge features do not materially improve results, retain the simpler validated node model as the preferred operational baseline and document the negative incremental-value finding.
- Review calibration before presenting raw model scores as probabilities.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D comparative visuals only from verified, validated real-data outputs.
