from __future__ import annotations

import argparse
import json
import random
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from financial_crime_risk_intelligence.metrics import review_budget_metrics


def parse_seeds(value: str) -> list[int]:
    seeds = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("Provide at least one integer seed")
    return seeds


def binary_metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    return {
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "brier_score": float(brier_score_loss(y_true, scores)),
        "base_rate": float(np.mean(y_true)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Train a lightweight graph-native benchmark on the labeled Elliptic2 subgraphs. "
            "The model is a directed dual-channel GraphSAGE graph classifier using the 43 node "
            "features and the labeled edges only."
        )
    )
    parser.add_argument("--nodes", default="data/derived/labeled_graph_nodes.parquet")
    parser.add_argument("--edges", default="data/derived/labeled_graph_edges.parquet")
    parser.add_argument("--components", default="data/derived/labeled_graph_components.parquet")
    parser.add_argument(
        "--reference-components",
        default="data/derived/component_features_node_enriched.parquet",
        help=(
            "Component store whose row order defines the split. Using the node-enriched store "
            "makes seed 42 match the existing random-forest 80/20 test split."
        ),
    )
    parser.add_argument(
        "--reference-scores",
        default="results/node_enriched/model_scored_cases.csv",
        help="Existing seed-42 scored cases used to audit exact test-component overlap.",
    )
    parser.add_argument("--results-dir", default="results/graph_native")
    parser.add_argument("--seeds", type=parse_seeds, default=parse_seeds("42"))
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--validation-fraction-of-train", type=float, default=0.20)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.20)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--max-epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--min-delta", type=float, default=1e-4)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    try:
        import torch
        from torch import nn
        import torch.nn.functional as F
        from torch_geometric.nn import SAGEConv, global_max_pool, global_mean_pool
    except ImportError as exc:
        raise SystemExit(
            "Graph dependencies are required. Install with: pip install -e '.[graph]'"
        ) from exc

    class DirectedGraphSAGE(nn.Module):
        def __init__(
            self,
            input_dim: int,
            hidden_dim: int,
            layers: int,
            dropout: float,
            component_count: int,
        ) -> None:
            super().__init__()
            if layers < 1:
                raise ValueError("layers must be at least 1")
            self.dropout = dropout
            self.component_count = component_count
            self.forward_convs = nn.ModuleList()
            self.reverse_convs = nn.ModuleList()
            self.merge_layers = nn.ModuleList()
            current_dim = input_dim
            for _ in range(layers):
                self.forward_convs.append(SAGEConv(current_dim, hidden_dim))
                self.reverse_convs.append(SAGEConv(current_dim, hidden_dim))
                self.merge_layers.append(nn.Linear(hidden_dim * 2, hidden_dim))
                current_dim = hidden_dim
            self.head = nn.Sequential(
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, 1),
            )

        def forward(self, x, edge_index, reverse_edge_index, component_index):
            for forward_conv, reverse_conv, merge in zip(
                self.forward_convs, self.reverse_convs, self.merge_layers
            ):
                forward_x = forward_conv(x, edge_index)
                reverse_x = reverse_conv(x, reverse_edge_index)
                x = merge(torch.cat([forward_x, reverse_x], dim=1))
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
            mean_pool = global_mean_pool(
                x, component_index, size=self.component_count
            )
            max_pool = global_max_pool(
                x, component_index, size=self.component_count
            )
            return self.head(torch.cat([mean_pool, max_pool], dim=1)).squeeze(1)

    def choose_device() -> str:
        if args.device == "cpu":
            return "cpu"
        if args.device == "cuda":
            if not torch.cuda.is_available():
                raise SystemExit("--device cuda requested but CUDA is unavailable")
            return "cuda"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def set_seed(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    paths = [Path(args.nodes), Path(args.edges), Path(args.components)]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit(
            f"Missing graph dataset files: {missing}. Run src/prepare_graph_native_dataset.py first."
        )

    nodes = pd.read_parquet(args.nodes)
    edges = pd.read_parquet(args.edges)
    components_source = pd.read_parquet(args.components)
    reference_path = Path(args.reference_components)
    if reference_path.exists():
        reference = pd.read_parquet(reference_path, columns=["component_id", "label"])
    else:
        reference = components_source[["component_id", "label"]].copy()

    if reference["component_id"].duplicated().any():
        raise SystemExit("Duplicate component_id values in reference component store")
    if nodes["node_id"].duplicated().any():
        raise SystemExit("Duplicate node_id values in graph node store")

    source_labels = components_source.set_index("component_id")["label"].astype(int)
    reference_labels = reference.set_index("component_id")["label"].astype(int)
    if set(source_labels.index) != set(reference_labels.index):
        raise SystemExit("Graph components do not match the reference component universe")
    aligned_source = source_labels.reindex(reference["component_id"].to_numpy()).to_numpy()
    if not np.array_equal(aligned_source, reference["label"].astype(int).to_numpy()):
        raise SystemExit("Graph component labels do not match the reference labels")

    component_ids = reference["component_id"].astype(np.int64).to_numpy()
    labels = reference["label"].astype(np.int64).to_numpy()
    component_to_index = pd.Series(
        np.arange(len(reference), dtype=np.int64), index=component_ids
    )

    feature_columns = sorted(
        [column for column in nodes.columns if column.startswith("node_feat_")]
    )
    if len(feature_columns) != 43:
        raise SystemExit(f"Expected 43 graph node features; found {len(feature_columns)}")

    node_ids = nodes["node_id"].astype(np.int64).to_numpy()
    node_to_index = pd.Series(np.arange(len(nodes), dtype=np.int64), index=node_ids)
    node_component_index = nodes["component_id"].map(component_to_index)
    if node_component_index.isna().any():
        raise SystemExit("Some graph nodes reference unknown components")
    node_component_index_np = node_component_index.to_numpy(dtype=np.int64)

    source_index = edges["source_node_id"].map(node_to_index)
    target_index = edges["target_node_id"].map(node_to_index)
    if source_index.isna().any() or target_index.isna().any():
        raise SystemExit("Some graph edges reference unknown graph nodes")
    edge_index_np = np.vstack(
        [source_index.to_numpy(dtype=np.int64), target_index.to_numpy(dtype=np.int64)]
    )

    raw_features = nodes[feature_columns].to_numpy(dtype=np.float32)
    if not np.isfinite(raw_features).all():
        raise SystemExit("Non-finite graph node feature values detected")

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    device = choose_device()
    print(
        f"Graph benchmark device={device}; nodes={len(nodes):,}; edges={len(edges):,}; "
        f"components={len(reference):,}; features={len(feature_columns)}"
    )

    edge_index = torch.as_tensor(edge_index_np, dtype=torch.long, device=device)
    reverse_edge_index = edge_index.flip(0)
    component_index_tensor = torch.as_tensor(
        node_component_index_np, dtype=torch.long, device=device
    )
    label_tensor = torch.as_tensor(labels, dtype=torch.float32, device=device)

    history_rows: list[dict] = []
    metric_rows: list[dict] = []
    budget_rows: list[pd.DataFrame] = []
    score_rows: list[pd.DataFrame] = []
    split_audits: list[dict] = []

    def scaled_feature_tensor(component_indices: np.ndarray):
        mask = np.isin(node_component_index_np, component_indices)
        means = raw_features[mask].mean(axis=0, dtype=np.float64)
        stds = raw_features[mask].std(axis=0, dtype=np.float64)
        stds = np.where(stds > 0, stds, 1.0)
        scaled = ((raw_features - means) / stds).astype(np.float32)
        return torch.as_tensor(scaled, dtype=torch.float32, device=device)

    def build_model() -> DirectedGraphSAGE:
        return DirectedGraphSAGE(
            input_dim=len(feature_columns),
            hidden_dim=args.hidden_dim,
            layers=args.layers,
            dropout=args.dropout,
            component_count=len(reference),
        ).to(device)

    def loss_for_indices(logits, indices: np.ndarray):
        y = label_tensor[indices]
        positives = float(y.sum().item())
        negatives = float(len(indices) - positives)
        pos_weight_value = negatives / positives if positives > 0 else 1.0
        pos_weight = torch.tensor(pos_weight_value, device=device)
        return F.binary_cross_entropy_with_logits(
            logits[indices], y, pos_weight=pos_weight
        )

    @torch.no_grad()
    def scores_for_indices(
        model: DirectedGraphSAGE,
        x_tensor,
        indices: np.ndarray,
    ) -> np.ndarray:
        model.eval()
        logits = model(
            x_tensor, edge_index, reverse_edge_index, component_index_tensor
        )
        return torch.sigmoid(logits[indices]).detach().cpu().numpy()

    for seed in args.seeds:
        set_seed(seed)
        all_indices = np.arange(len(reference), dtype=np.int64)
        train_indices, test_indices = train_test_split(
            all_indices,
            test_size=args.test_size,
            random_state=seed,
            stratify=labels,
        )
        fit_indices, validation_indices = train_test_split(
            train_indices,
            test_size=args.validation_fraction_of_train,
            random_state=seed,
            stratify=labels[train_indices],
        )

        exact_reference_match = None
        if seed == 42 and Path(args.reference_scores).exists():
            reference_scores = pd.read_csv(args.reference_scores)
            reference_rf = reference_scores.loc[
                reference_scores["model"].astype(str) == "random_forest", "component_id"
            ]
            expected_ids = set(reference_rf.astype(np.int64))
            actual_ids = set(component_ids[test_indices])
            exact_reference_match = expected_ids == actual_ids
            if not exact_reference_match:
                raise SystemExit(
                    "Seed-42 graph test components do not exactly match the existing RF test set"
                )

        split_audits.append(
            {
                "seed": seed,
                "train_components": int(len(train_indices)),
                "fit_components": int(len(fit_indices)),
                "validation_components": int(len(validation_indices)),
                "test_components": int(len(test_indices)),
                "train_positives": int(labels[train_indices].sum()),
                "validation_positives": int(labels[validation_indices].sum()),
                "test_positives": int(labels[test_indices].sum()),
                "seed42_exact_rf_test_component_match": exact_reference_match,
            }
        )

        # Phase 1: use an internal validation subset only to select the epoch count.
        x_fit_scaled = scaled_feature_tensor(fit_indices)
        model = build_model()
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=args.learning_rate,
            weight_decay=args.weight_decay,
        )
        best_validation_ap = -np.inf
        best_epoch = 1
        best_state = None
        stale_epochs = 0

        for epoch in range(1, args.max_epochs + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            logits = model(
                x_fit_scaled, edge_index, reverse_edge_index, component_index_tensor
            )
            loss = loss_for_indices(logits, fit_indices)
            loss.backward()
            optimizer.step()

            validation_scores = scores_for_indices(
                model, x_fit_scaled, validation_indices
            )
            validation_ap = float(
                average_precision_score(labels[validation_indices], validation_scores)
            )
            history_rows.append(
                {
                    "seed": seed,
                    "phase": "epoch_selection",
                    "epoch": epoch,
                    "training_loss": float(loss.detach().cpu().item()),
                    "validation_average_precision": validation_ap,
                }
            )

            if validation_ap > best_validation_ap + args.min_delta:
                best_validation_ap = validation_ap
                best_epoch = epoch
                best_state = deepcopy(model.state_dict())
                stale_epochs = 0
            else:
                stale_epochs += 1
            if stale_epochs >= args.patience:
                break

        del model, optimizer, x_fit_scaled, best_state
        if device == "cuda":
            torch.cuda.empty_cache()

        # Phase 2: retrain from scratch on the full 80% training split for the
        # selected epoch count, then evaluate once on the untouched 20% test set.
        set_seed(seed)
        x_train_scaled = scaled_feature_tensor(train_indices)
        final_model = build_model()
        final_optimizer = torch.optim.Adam(
            final_model.parameters(),
            lr=args.learning_rate,
            weight_decay=args.weight_decay,
        )
        for epoch in range(1, best_epoch + 1):
            final_model.train()
            final_optimizer.zero_grad(set_to_none=True)
            logits = final_model(
                x_train_scaled, edge_index, reverse_edge_index, component_index_tensor
            )
            loss = loss_for_indices(logits, train_indices)
            loss.backward()
            final_optimizer.step()
            history_rows.append(
                {
                    "seed": seed,
                    "phase": "full_train_replay",
                    "epoch": epoch,
                    "training_loss": float(loss.detach().cpu().item()),
                    "validation_average_precision": np.nan,
                }
            )

        test_scores = scores_for_indices(final_model, x_train_scaled, test_indices)
        y_test = labels[test_indices]
        metrics = binary_metrics(y_test, test_scores)
        metric_rows.append(
            {
                "seed": seed,
                "model": "directed_graphsage",
                "best_epoch": best_epoch,
                "validation_average_precision": best_validation_ap,
                **metrics,
            }
        )

        budgets = review_budget_metrics(y_test, test_scores)
        budgets.insert(0, "model", "directed_graphsage")
        budgets.insert(0, "seed", seed)
        budget_rows.append(budgets)

        scored = pd.DataFrame(
            {
                "seed": seed,
                "model": "directed_graphsage",
                "component_id": component_ids[test_indices],
                "label": y_test,
                "risk_score": test_scores,
            }
        ).sort_values("risk_score", ascending=False)
        score_rows.append(scored)

        print(
            f"seed={seed} best_epoch={best_epoch} "
            f"val_PR_AUC={best_validation_ap:.4f} test_PR_AUC={metrics['average_precision']:.4f} "
            f"test_ROC_AUC={metrics['roc_auc']:.4f}"
        )

        del final_model, final_optimizer, x_train_scaled
        if device == "cuda":
            torch.cuda.empty_cache()

    metrics_frame = pd.DataFrame(metric_rows)
    budgets_frame = pd.concat(budget_rows, ignore_index=True)
    scores_frame = pd.concat(score_rows, ignore_index=True)
    history_frame = pd.DataFrame(history_rows)

    metrics_frame.to_csv(results_dir / "graph_native_metrics.csv", index=False)
    budgets_frame.to_csv(results_dir / "graph_native_review_budget_metrics.csv", index=False)
    scores_frame.to_csv(results_dir / "graph_native_scored_cases.csv", index=False)
    history_frame.to_csv(results_dir / "graph_native_training_history.csv", index=False)

    if len(metrics_frame) > 1:
        summary = (
            metrics_frame.groupby("model")[["average_precision", "roc_auc", "brier_score"]]
            .agg(["mean", "std", "min", "max"])
            .reset_index()
        )
        summary.columns = [
            "model" if column[0] == "model" else f"{column[0]}_{column[1]}"
            for column in summary.columns.to_flat_index()
        ]
        summary.to_csv(results_dir / "graph_native_metrics_summary.csv", index=False)

    # Same-split comparison is only emitted when the existing seed-42 RF files exist.
    rf_metrics_path = Path("results/node_enriched/model_metrics.csv")
    rf_budgets_path = Path("results/node_enriched/review_budget_metrics.csv")
    graph_seed42 = metrics_frame.loc[metrics_frame["seed"] == 42]
    if rf_metrics_path.exists() and not graph_seed42.empty:
        rf_metrics = pd.read_csv(rf_metrics_path)
        rf_row = rf_metrics.loc[rf_metrics["model"] == "random_forest"]
        if not rf_row.empty:
            comparison = pd.DataFrame(
                [
                    {
                        "model": "node_enriched_random_forest",
                        "average_precision": float(rf_row.iloc[0]["average_precision"]),
                        "roc_auc": float(rf_row.iloc[0]["roc_auc"]),
                        "base_rate": float(rf_row.iloc[0]["base_rate"]),
                    },
                    {
                        "model": "directed_graphsage",
                        "average_precision": float(
                            graph_seed42.iloc[0]["average_precision"]
                        ),
                        "roc_auc": float(graph_seed42.iloc[0]["roc_auc"]),
                        "base_rate": float(graph_seed42.iloc[0]["base_rate"]),
                    },
                ]
            )
            comparison.to_csv(results_dir / "seed42_internal_comparison.csv", index=False)

    if rf_budgets_path.exists() and not graph_seed42.empty:
        rf_budget = pd.read_csv(rf_budgets_path)
        rf_budget = rf_budget.loc[rf_budget["model"] == "random_forest"].copy()
        graph_budget = budgets_frame.loc[budgets_frame["seed"] == 42].copy()
        rf_budget["benchmark"] = "node_enriched_random_forest"
        graph_budget["benchmark"] = "directed_graphsage"
        common_columns = [
            "benchmark",
            "review_fraction",
            "reviews",
            "suspicious_captured",
            "precision_at_budget",
            "recall_at_budget",
            "lift_at_budget",
        ]
        pd.concat(
            [rf_budget[common_columns], graph_budget[common_columns]],
            ignore_index=True,
        ).to_csv(results_dir / "seed42_budget_comparison.csv", index=False)

    manifest = {
        "status": "graph_native_benchmark_complete",
        "model": "directed_graphsage",
        "scope": (
            "Labeled-subgraph graph classifier using 444,521 labeled nodes, 367,137 labeled "
            "edges, and 43 node features. This is not a full-background-graph GLASS reproduction."
        ),
        "split": (
            "Seed-specific stratified 80/20 component split. Seed 42 is audited against the "
            "existing node-enriched random-forest test component set. Internal validation is "
            "used only to choose epoch count; the model is then retrained on the full 80% train split."
        ),
        "architecture": {
            "hidden_dim": args.hidden_dim,
            "layers": args.layers,
            "dropout": args.dropout,
            "direction_handling": "separate forward/reverse GraphSAGE channels merged per layer",
            "graph_pooling": "global mean plus global max",
        },
        "seeds": args.seeds,
        "device": device,
        "node_count": int(len(nodes)),
        "edge_count": int(len(edges)),
        "component_count": int(len(reference)),
        "node_feature_count": len(feature_columns),
        "split_audits": split_audits,
        "external_reference_note": (
            "Published GLASS results use the full Elliptic2 background graph and a different "
            "experimental setup; keep those published numbers separate from project results."
        ),
        "outputs": [
            "graph_native_metrics.csv",
            "graph_native_review_budget_metrics.csv",
            "graph_native_scored_cases.csv",
            "graph_native_training_history.csv",
            "seed42_internal_comparison.csv",
            "seed42_budget_comparison.csv",
        ],
    }
    (results_dir / "graph_native_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Wrote graph-native benchmark outputs to {results_dir}")


if __name__ == "__main__":
    main()
