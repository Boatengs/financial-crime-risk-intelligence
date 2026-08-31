# Project Status

## Current phase
**Phase 1 — architecture and reproducible baseline**

### Complete
- Dataset selection: Elliptic2.
- Decision framing: investigator prioritization under review constraints.
- Repository architecture pushed to `main`.
- Synthetic smoke-test fixture.
- Baseline feature engineering, modeling, and review-budget evaluation code.
- Data-source and licensing register.
- Local smoke test: unit tests and fixture pipeline pass.

### Next
- Download and schema-profile the official Elliptic2 release.
- Validate field mappings against official files.
- Build Parquet feature store on the labeled-subgraph universe.
- Train calibrated baselines and benchmark PR-AUC / review-budget lift.
- Add graph-native benchmark on a compute-appropriate subset or full graph.
- Produce portfolio-ready evidence and figures only from verified outputs.
