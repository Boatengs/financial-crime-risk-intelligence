# Codebase Guide

- `run_pipeline.py` — orchestrates fixture or Elliptic2 execution.
- `src/financial_crime_risk_intelligence/metrics.py` — review-budget metrics.
- `src/financial_crime_risk_intelligence/features.py` — structural feature helpers.
- `src/financial_crime_risk_intelligence/modeling.py` — baseline models.
- `src/inspect_elliptic2.py` — profiles the five official CSV files with DuckDB.
- `src/build_feature_store.py` — scalable component feature-store builder.
- `src/train_baselines.py` — baseline training and evaluation.
- `src/build_investigator_queue.py` — ranked review queue and risk bands.
- `src/generate_figures.py` — reviewer-facing figures.
- `tests/` — fast deterministic smoke tests.
- `sources/SOURCE_REGISTER.md` — dataset/research/regulatory provenance.
