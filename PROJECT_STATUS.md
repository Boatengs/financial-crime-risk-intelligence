# Project Status

## Current phase
**Phase 3 — verified structural baseline and background-node enrichment**

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
- Labeled component size profile verified: both classes have median size 3 nodes; licit max 296 and suspicious max 30.
- Structural feature store built from all 121,810 labeled components with 19 complete structural features and zero nulls.
- First real-data structural baseline completed:
  - logistic regression average precision 0.026323 and ROC-AUC 0.545966;
  - random forest average precision 0.024107 and ROC-AUC 0.512885;
  - held-out positive-class rate 0.022699.
- Logistic regression achieved 1.8055x lift at the top 0.5% review budget (5 suspicious components in 122 reviews).
- Structural-only results documented as the benchmark to beat; published paper metrics remain explicitly separate.
- Investigator queue selection now defaults to the model with the best average precision instead of a hard-coded model.
- 3D figure generation retained as the project standard; layout handling updated to avoid Matplotlib tight-layout warnings.
- Background-node enrichment completed successfully on the 49.3M-row table:
  - 444,521 labeled node rows and 444,521 distinct labeled nodes;
  - 444,521 background matches and 444,521 distinct matched nodes;
  - zero missing labeled nodes and zero duplicate background matches;
  - all 43 node features aggregated by mean, population standard deviation, minimum, and maximum;
  - 172 component-level node-derived features created;
  - all 121,810 components retained, including all 2,763 positive components;
  - zero components without node-feature coverage.

### Next
- Regenerate the structural investigator queue / 3D figures using automatic best-model selection if not already done after the latest pull.
- Train logistic regression and random forest on `data/derived/component_features_node_enriched.parquet` into a separate `results/node_enriched/` directory.
- Build a separate node-enriched investigator queue and 3D figures.
- Compare node-enriched PR-AUC, ROC-AUC, and review-budget lift directly against the structural-only baseline.
- Add repeated splits or confidence intervals and calibration diagnostics before treating model performance as stable.
- Add 95 background-edge feature aggregates in a separate resource-controlled experiment because it must scan the 196.2M-edge table.
- Compare enriched baselines against published graph-model reference benchmarks.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D visuals only from verified, validated real-data outputs.
