# Graph-Native Benchmark

## Purpose

The validated node-enriched random forest remains the current operational benchmark. This stage asks a separate question:

> Does explicit message passing over the labeled transaction subgraphs add decision value beyond component-level feature aggregation when both methods are evaluated on the same held-out components?

The first project graph baseline is intentionally smaller than a full GLASS reproduction so it can be run on the labeled subgraph universe without loading the entire 196.2M-edge background graph into a graph-learning framework.

## Internal project benchmark

`src/prepare_graph_native_dataset.py` prepares:

- 444,521 labeled nodes;
- 367,137 labeled directed edges;
- 121,810 labeled connected components;
- 43 node features recovered from `background_nodes.csv`.

It scans `background_nodes.csv` once to recover labeled-node features. It does **not** scan `background_edges.csv`.

`src/train_graph_native_baseline.py` trains a graph classifier with:

- separate forward and reverse GraphSAGE message-passing channels;
- 43 standardized node features;
- two message-passing layers by default;
- global mean + global max graph pooling;
- class-weighted binary cross-entropy;
- an internal validation subset used only to select the training epoch count;
- retraining on the full 80% training split before final test evaluation.

For seed 42, the script verifies that the 20% test component IDs exactly match the existing node-enriched random-forest test component set. This makes the project comparison directly interpretable at the same review budgets.

## Metrics

The graph benchmark reports the same decision metrics used elsewhere in the project:

- PR-AUC / average precision as the primary global metric;
- ROC-AUC as a secondary diagnostic;
- Brier score as a score-quality diagnostic;
- precision, recall, lift, and suspicious components captured at 0.5%, 1%, 2%, 5%, and 10% review budgets.

## External GLASS reference

The Elliptic2 paper reports GLASS test PR-AUC of approximately 0.208 and ROC-AUC of approximately 0.889 under its published experimental setup. The official Elliptic2 preprocessing guide uses the full background graph for GLASS/GNNSeg inputs.

Those published values are **external reference benchmarks**, not project results. They should not be directly compared to the project GraphSAGE or random-forest metrics because the graph scope, split procedure, feature usage, and training setup differ.

The paper also reports that node and edge features were not used in its GLASS experiments because the full graph was too large for that feature-rich setup. In contrast, the project GraphSAGE baseline deliberately uses the 43 labeled-node features on the much smaller labeled-subgraph universe.

## Interpretation rules

- A graph model score is a prioritization signal, not proof of criminal activity.
- If the graph model underperforms the node-enriched random forest, that is a valid negative result; graph complexity is not automatically decision value.
- If the graph model improves ranking, repeated-seed validation is required before changing the preferred model.
- Published GLASS numbers remain in a separate external-reference section until a true full-background-graph reproduction is run.

## Local workflow

```bash
pip install -e '.[graph]'

python src/prepare_graph_native_dataset.py \
  --raw-dir data/raw/elliptic2

python src/train_graph_native_baseline.py \
  --seeds 42 \
  --device cpu
```

Inspect:

```bash
cat results/graph_native/graph_dataset_profile.json
cat results/graph_native/graph_native_metrics.csv
cat results/graph_native/seed42_internal_comparison.csv
cat results/graph_native/seed42_budget_comparison.csv
```

If seed 42 is competitive, the next validation step is to rerun the graph model across the same five seeds used for the node-enriched random forest.
