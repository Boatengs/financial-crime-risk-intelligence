# Project Status

## Current phase
**Phase 2 — verified labeled universe and structural baseline preparation**

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
- Structural component feature store uses the verified schema and out-of-core DuckDB processing.
- Compact structural feature-store profiler added so large Parquet outputs do not need to be shared.
- Visualization requirement set to 3D by default; current figure generator produces 3D review-budget and investigator-queue views.

### Next
- Build the structural component feature store from all 121,810 labeled components.
- Run `src/profile_feature_store.py` and validate feature completeness / class counts.
- Train first real-data explainable baselines and capture PR-AUC / review-budget lift.
- Add background-node feature aggregates by joining the 444,521 labeled nodes to the 49.3M-node background table.
- Add background-edge feature aggregates in a separate staged job because it must scan the 196.2M-edge table and 95 feature columns.
- Compare enriched baselines against the published graph-model reference benchmarks.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D visuals only from verified full-data outputs.
