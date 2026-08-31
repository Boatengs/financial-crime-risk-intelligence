# Project Status

## Current phase
**Phase 2 — source verification and full-data readiness**

### Complete
- Dataset selection: Elliptic2.
- Decision framing: investigator prioritization under review constraints.
- Repository architecture pushed to `main`.
- Synthetic smoke-test fixture.
- Baseline feature engineering, modeling, and review-budget evaluation code.
- Data-source and licensing register.
- Local smoke test: unit tests and fixture pipeline pass.
- GitHub Actions CI: unit tests and end-to-end fixture pipeline pass.
- Official five-file layout verified against MITIBMxGraph/Elliptic2.
- Published dataset scale and paper benchmark metrics recorded as external references.
- Official preprocessing confirms `clId1`/`clId2` for background edges, `ccLabel` for labels, and positional cluster/component identifiers in the labeled-node file.

### Next
- Obtain the official Elliptic2 release from Kaggle without redistributing it.
- Run `src/inspect_elliptic2.py` on all five files and persist exact headers/types/row counts.
- Replace any remaining positional schema assumptions with verified header mappings.
- Build an out-of-core Parquet feature store for the labeled-subgraph universe first.
- Add structural, node-feature, and edge-feature aggregates that can be computed without loading the 196M-edge graph into pandas.
- Train calibrated baselines and benchmark PR-AUC / review-budget lift against published references.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings only from verified full-data outputs.
