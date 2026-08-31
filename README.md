# Financial Crime Risk Intelligence

**Elliptic2 blockchain AML → scalable graph ingestion → laundering-pattern detection → explainable alert scoring → investigator queue → workload trade-offs**

This project is designed as an investigator-oriented anti-money-laundering (AML) analytics system rather than a one-off fraud classifier. The primary benchmark is **Elliptic2**, a large public financial-crime graph dataset containing roughly **49.3M node clusters, 196.2M transaction edges, and 121,810 labeled subgraphs**, of which only **2,763 are suspicious**. The labels are at the subgraph level, which makes the problem closer to real AML case triage than row-level transaction classification.

> The project does **not** redistribute Elliptic2. Download the dataset from its original Kaggle source and follow its CC BY-NC-ND 4.0 license.

## Decision question

> Given a very large, highly imbalanced transaction network, which connected transaction patterns should investigators review first, why were they prioritized, and how much suspicious activity can be captured under a constrained review budget?

## Why this is difficult

- **Scale:** the full background graph is tens of millions of entities and hundreds of millions of directed edges.
- **Graph structure:** laundering behavior is expressed through multi-transaction patterns, not isolated rows.
- **Class imbalance:** suspicious subgraphs are only about 2.27% of the labeled population.
- **Operational objective:** investigators cannot review every alert, so model quality must be measured at realistic review budgets.
- **Explainability:** a useful alert must show its structural and feature-level reasons, not only a probability.

## Architecture

```text
Elliptic2 raw CSVs
    |
    v
src/inspect_elliptic2.py
    | schema + row-count manifest
    v
src/build_feature_store.py
    | component-level graph + feature aggregates
    v
src/train_baselines.py
    | logistic regression + random forest baselines
    | PR-AUC + precision/recall/lift @ review budget
    v
src/build_investigator_queue.py
    | prioritized cases + review context
    v
src/generate_figures.py
    | executive risk + workload views
    v
reports/ and results/
```

An optional graph-learning track can benchmark subgraph models such as GLASS/GNNSeg against the tabular/structural baselines, but the repository keeps the operational analytics layer independent of any single model family.

## Primary outputs

- `results/model_metrics.csv`
- `results/review_budget_metrics.csv`
- `results/investigator_queue.csv`
- `figures/review_budget_curve.svg`
- `figures/risk_queue_summary.svg`
- `reports/CURRENT_FINDINGS.md`
- `reports/MODEL_VALIDATION.md`
- `reports/INVESTIGATOR_WORKFLOW.md`

## Fast local smoke test

The repository includes a small synthetic fixture so the pipeline logic can be tested without downloading the full dataset.

```bash
python -m pip install -e ".[dev]"
python run_pipeline.py --fixture
pytest
```

## Full Elliptic2 workflow

1. Download Elliptic2 from the official Kaggle dataset page.
2. Place the five CSV files in `data/raw/elliptic2/`:
   - `background_edges.csv`
   - `background_nodes.csv`
   - `connected_components.csv`
   - `edges.csv`
   - `nodes.csv`
3. Run:

```bash
python run_pipeline.py --raw-dir data/raw/elliptic2
```

The ingestion layer is intentionally DuckDB/Parquet-oriented so the full graph does not need to be loaded into pandas at once.

## Evaluation philosophy

Because AML is highly imbalanced and investigation capacity is constrained, **PR-AUC is the primary global metric**. The more important operational metrics are:

- precision at top *K* investigations,
- recall at top *K*,
- lift versus random review,
- suspicious cases captured per 100 reviews,
- false-positive workload,
- stability across time-aware and repeated holdout splits once the full dataset is connected.

ROC-AUC is reported only as a secondary diagnostic.

## Compliance framing

This is a research and portfolio decision-support system. It does not make legal determinations, file SARs, identify real people, or claim that model scores constitute proof of criminal activity. Current U.S. AML guidance emphasizes risk-based monitoring and useful prioritization rather than generating low-value noise.

## Data and research sources

See `sources/SOURCE_REGISTER.md` for the dataset, official implementation guide, research paper, and regulatory references.
