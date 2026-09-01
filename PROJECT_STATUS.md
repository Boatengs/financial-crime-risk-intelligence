# Project Status

## Current phase
**Phase 4 — validated node benchmark and background-edge enrichment**

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
- Final validation gate passed:
  - repeated-split stability pass;
  - permutation sanity pass;
  - schema leakage audit pass;
  - top feature importance 5.20%;
  - top-10 cumulative importance 38.46%;
  - feature-dominance manual review not recommended by the gate.
- Validated node-enriched random forest promoted to the primary benchmark for the edge-feature experiment.
- Resource-controlled edge-enrichment script added at `src/enrich_edge_features.py`.
- Edge-enrichment design:
  - full-key match on `(clId1, clId2, txId)`;
  - strict audit for duplicate labeled keys, missing component mappings, unmatched labeled edges, and duplicate background matches;
  - all 95 edge features aggregated by mean, population standard deviation, minimum, and maximum;
  - 380 component-level edge-derived features;
  - explicit zero coverage handling for components without matched edges.
- Investigator queue selection defaults to the highest-average-precision model.
- 3D visualization remains the project standard.

### Next
- Pull the latest repository changes.
- Run `src/enrich_edge_features.py --raw-dir data/raw/elliptic2` locally. This is the heaviest CSV scan so far because it must process the 196.2M-row background-edge table with 95 feature columns.
- Inspect `results/edge_feature_enrichment_profile.json` before model fitting.
- Require exact one-to-one labeled-edge coverage or stop and diagnose the match audit.
- If the edge audit passes, train logistic regression and random forest on `data/derived/component_features_node_edge_enriched.parquet` into a separate results directory.
- Compare edge-enriched PR-AUC, ROC-AUC, calibration, and review-budget lift against the validated node benchmark (RF PR-AUC mean ~0.528; top-0.5% lift mean ~41.5x).
- Run repeated-split / permutation validation on the winning edge-enriched model before making portfolio claims.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D comparative visuals only from verified, validated real-data outputs.
