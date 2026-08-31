# Project Status

## Current phase
**Phase 3 — node-enriched benchmark validation**

### Complete
- Dataset selection: Elliptic2.
- Decision framing: investigator prioritization under review constraints.
- Repository architecture pushed to `main`.
- Synthetic smoke-test fixture.
- Baseline modeling and review-budget evaluation code.
- Data-source and licensing register.
- Local smoke test: unit tests and fixture pipeline pass.
- GitHub Actions CI: unit tests and end-to-end fixture pipeline pass.
- Official five-file layout verified against MITIBMxGraph/Elliptic2.
- Local schema profiling completed on the official downloaded release.
- Verified local row counts:
  - 49,299,864 background nodes.
  - 196,215,606 background edges.
  - 121,810 labeled connected components.
  - 444,521 labeled nodes.
  - 367,137 labeled edges.
- Verified feature layout: 43 anonymized node features and 95 anonymized edge features.
- Exact identifiers locked in config: `ccId`, `ccLabel`, `clId`, `clId1`, `clId2`, `txId`.
- Actual downloaded labels verified: 119,047 `licit` components and 2,763 `suspicious` components.
- Labeled-universe integrity verified: zero missing source nodes, zero missing target nodes, and zero cross-component edges.
- Structural feature store built from all 121,810 labeled components with 19 complete structural features and zero nulls.
- First real-data structural baseline completed:
  - logistic regression average precision 0.026323 and ROC-AUC 0.545966;
  - random forest average precision 0.024107 and ROC-AUC 0.512885;
  - logistic regression achieved 1.8055x lift at the top 0.5% review budget (5 suspicious components in 122 reviews).
- Background-node enrichment completed successfully:
  - all 444,521 labeled nodes matched exactly once to the 49.3M-row background-node table;
  - zero missing labeled nodes and zero duplicate background matches;
  - all 43 node features aggregated by mean, population standard deviation, minimum, and maximum;
  - 172 component-level node-derived features created;
  - all 121,810 components retained, including all 2,763 positive components;
  - zero components without node-feature coverage.
- First node-enriched single-split benchmark completed:
  - logistic regression average precision 0.145578 and ROC-AUC 0.882008;
  - random forest average precision 0.530556 and ROC-AUC 0.926611;
  - random forest top-0.5% review budget: 117 suspicious components in 122 reviews, 95.90% precision, 21.16% recall, 42.25x lift;
  - random forest top-1% review budget: 190 suspicious components in 244 reviews, 77.87% precision, 34.36% recall, 34.30x lift.
- Investigator queue selection defaults to the model with the best average precision.
- 3D visualization remains the project standard.
- Repeated-split / leakage / calibration validation harness added at `src/validate_node_enriched_models.py`.

### Next
- Run `src/validate_node_enriched_models.py` on the node-enriched feature store.
- Inspect repeated-split average precision, ROC-AUC, Brier score, and review-budget stability.
- Confirm shuffled-label performance collapses toward the ~2.27% base rate.
- Inspect `feature_class_separation.csv` and `feature_importance_seed42.csv` for excessive dominance or suspicious target-proxy behavior.
- Review calibration tables before interpreting raw model probabilities as risk probabilities.
- Only after these checks pass, build the 95 background-edge feature aggregates in a resource-controlled experiment over the 196.2M-edge table.
- Compare edge-enriched results against the validated node-enriched benchmark and published graph-model references.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D visuals only from verified, validated real-data outputs.
