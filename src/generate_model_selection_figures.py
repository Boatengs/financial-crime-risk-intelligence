from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def read_model_metric(path: Path, model: str, metric: str) -> float:
    frame = pd.read_csv(path)
    row = frame.loc[frame["model"] == model]
    if row.empty:
        raise SystemExit(f"Model {model!r} not found in {path}")
    return float(row.iloc[0][metric])


def read_repeated_metric(path: Path, model: str, metric: str) -> float:
    frame = pd.read_csv(path)
    row = frame.loc[frame["model"] == model]
    if row.empty:
        raise SystemExit(f"Model {model!r} not found in {path}")
    return float(row.iloc[0][metric])


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D comparison visuals for final Financial Crime Risk Intelligence model selection."
    )
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures/model_selection")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)

    structural_metrics = results / "model_metrics.csv"
    node_metrics = results / "node_enriched" / "model_metrics.csv"
    edge_metrics = results / "node_edge_enriched" / "model_metrics.csv"

    required = [structural_metrics, node_metrics, edge_metrics]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"Missing model metric files: {missing}")

    stages = ["Structure", "Structure + node", "Structure + node + edge"]
    models = ["logistic_regression", "random_forest"]
    x = np.arange(len(stages), dtype=float)
    y = np.arange(len(models), dtype=float)
    dx = 0.55
    dy = 0.55

    stage_files = [structural_metrics, node_metrics, edge_metrics]
    bars_x: list[float] = []
    bars_y: list[float] = []
    bars_z: list[float] = []
    heights: list[float] = []
    for stage_index, path in enumerate(stage_files):
        for model_index, model in enumerate(models):
            bars_x.append(float(stage_index))
            bars_y.append(float(model_index))
            bars_z.append(0.0)
            heights.append(read_model_metric(path, model, "average_precision"))

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.bar3d(
        np.asarray(bars_x),
        np.asarray(bars_y),
        np.asarray(bars_z),
        np.full(len(heights), dx),
        np.full(len(heights), dy),
        np.asarray(heights),
        shade=True,
    )
    ax.set_xticks(x + dx / 2)
    ax.set_xticklabels(stages, rotation=12, ha="right")
    ax.set_yticks(y + dy / 2)
    ax.set_yticklabels(["Logistic", "Random forest"])
    ax.set_zlabel("PR-AUC / average precision")
    ax.set_title("3D feature-stage model comparison — matched seed-42 split")
    ax.view_init(elev=24, azim=-55)
    fig.subplots_adjust(left=0.02, right=0.93, bottom=0.14, top=0.90)
    fig.savefig(figures / "feature_stage_pr_auc_3d.svg", bbox_inches="tight")
    plt.close(fig)

    node_summary_path = results / "node_enriched_validation" / "repeated_split_summary.csv"
    edge_summary_path = results / "node_edge_enriched_validation" / "repeated_split_summary.csv"
    node_budget_path = results / "node_enriched_validation" / "repeated_budget_summary.csv"
    edge_budget_path = results / "node_edge_enriched_validation" / "repeated_budget_summary.csv"

    validation_required = [
        node_summary_path,
        edge_summary_path,
        node_budget_path,
        edge_budget_path,
    ]
    missing_validation = [str(p) for p in validation_required if not p.exists()]
    if missing_validation:
        raise SystemExit(f"Missing validation files: {missing_validation}")

    validation_stages = ["Node only", "Node + edge"]
    ap_means = [
        read_repeated_metric(node_summary_path, "random_forest", "average_precision_mean"),
        read_repeated_metric(edge_summary_path, "random_forest", "average_precision_mean"),
    ]
    ap_stds = [
        read_repeated_metric(node_summary_path, "random_forest", "average_precision_std"),
        read_repeated_metric(edge_summary_path, "random_forest", "average_precision_std"),
    ]

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection="3d")
    sx = np.arange(2, dtype=float)
    sy = np.zeros(2, dtype=float)
    ax.bar3d(sx, sy, np.zeros(2), np.full(2, 0.55), np.full(2, 0.55), np.asarray(ap_means), shade=True)
    for idx, (mean, sd) in enumerate(zip(ap_means, ap_stds)):
        ax.plot(
            [idx + 0.275, idx + 0.275],
            [0.275, 0.275],
            [mean - sd, mean + sd],
            linewidth=2,
        )
    ax.set_xticks(sx + 0.275)
    ax.set_xticklabels(validation_stages)
    ax.set_yticks([])
    ax.set_zlabel("Mean PR-AUC")
    ax.set_title("3D validated random-forest model selection")
    ax.view_init(elev=24, azim=-55)
    fig.subplots_adjust(left=0.04, right=0.93, bottom=0.12, top=0.90)
    fig.savefig(figures / "validated_rf_pr_auc_3d.svg", bbox_inches="tight")
    plt.close(fig)

    node_budget = pd.read_csv(node_budget_path)
    edge_budget = pd.read_csv(edge_budget_path)
    node_rf = node_budget.loc[node_budget["model"] == "random_forest"].sort_values("review_fraction")
    edge_rf = edge_budget.loc[edge_budget["model"] == "random_forest"].sort_values("review_fraction")

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    for stage_index, (label, frame) in enumerate(
        [("Node only", node_rf), ("Node + edge", edge_rf)]
    ):
        xvals = frame["review_fraction"].to_numpy(dtype=float) * 100
        yvals = np.full(len(frame), stage_index, dtype=float)
        zvals = frame["lift_at_budget_mean"].to_numpy(dtype=float)
        ax.plot(xvals, yvals, zvals, marker="o", label=label)

    ax.set_xlabel("Review budget (% of held-out cases)")
    ax.set_ylabel("Feature stage")
    ax.set_zlabel("Mean lift vs random review")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Node only", "Node + edge"])
    ax.set_title("3D validated investigator lift: node-only vs node+edge")
    ax.view_init(elev=25, azim=-58)
    ax.legend(loc="upper right")
    fig.subplots_adjust(left=0.02, right=0.92, bottom=0.10, top=0.90)
    fig.savefig(figures / "validated_review_lift_comparison_3d.svg", bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote 3D model-selection figures to {figures}")


if __name__ == "__main__":
    main()
