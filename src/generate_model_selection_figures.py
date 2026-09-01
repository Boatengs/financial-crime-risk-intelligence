from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import seaborn as sns


PLOT_CONFIG = {"responsive": True, "displaylogo": False}


def palette(n: int) -> list[str]:
    return sns.color_palette("deep", n_colors=max(1, n)).as_hex()


def write_plotly(fig: go.Figure, path: Path) -> None:
    fig.write_html(path, include_plotlyjs="cdn", full_html=True, config=PLOT_CONFIG)


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate interactive Plotly 3D visuals for final model selection."
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
    stage_files = [structural_metrics, node_metrics, edge_metrics]
    colors = palette(len(models))

    fig = go.Figure()
    for model_index, (model, color) in enumerate(zip(models, colors)):
        pr_auc = [read_model_metric(path, model, "average_precision") for path in stage_files]
        roc_auc = [read_model_metric(path, model, "roc_auc") for path in stage_files]
        fig.add_trace(
            go.Scatter3d(
                x=list(range(len(stages))),
                y=[float(model_index)] * len(stages),
                z=pr_auc,
                mode="lines+markers",
                name=model.replace("_", " ").title(),
                line={"color": color, "width": 8},
                marker={"color": color, "size": 7},
                text=[
                    f"Stage: {stage}<br>Model: {model.replace('_', ' ')}<br>PR-AUC: {ap:.4f}<br>ROC-AUC: {roc:.4f}"
                    for stage, ap, roc in zip(stages, pr_auc, roc_auc)
                ],
                hovertemplate="%{text}<extra></extra>",
            )
        )
    fig.update_layout(
        title="Feature-stage model comparison — matched seed-42 split",
        scene={
            "xaxis": {"title": "Feature stage", "tickmode": "array", "tickvals": [0, 1, 2], "ticktext": stages},
            "yaxis": {
                "title": "Model",
                "tickmode": "array",
                "tickvals": [0, 1],
                "ticktext": ["Logistic regression", "Random forest"],
            },
            "zaxis_title": "PR-AUC / average precision",
            "camera": {"eye": {"x": 1.5, "y": -1.6, "z": 1.15}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
        legend={"orientation": "h"},
    )
    write_plotly(fig, figures / "feature_stage_pr_auc_3d.html")

    node_summary_path = results / "node_enriched_validation" / "repeated_split_summary.csv"
    edge_summary_path = results / "node_edge_enriched_validation" / "repeated_split_summary.csv"
    node_budget_path = results / "node_enriched_validation" / "repeated_budget_summary.csv"
    edge_budget_path = results / "node_edge_enriched_validation" / "repeated_budget_summary.csv"
    validation_required = [node_summary_path, edge_summary_path, node_budget_path, edge_budget_path]
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
    roc_means = [
        read_repeated_metric(node_summary_path, "random_forest", "roc_auc_mean"),
        read_repeated_metric(edge_summary_path, "random_forest", "roc_auc_mean"),
    ]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=[0, 1],
                y=ap_stds,
                z=ap_means,
                mode="lines+markers+text",
                text=validation_stages,
                textposition="top center",
                marker={"size": 9, "color": palette(2)},
                line={"width": 6},
                customdata=roc_means,
                hovertemplate=(
                    "Feature set: %{text}<br>Mean PR-AUC: %{z:.4f}"
                    "<br>PR-AUC SD: %{y:.4f}<br>Mean ROC-AUC: %{customdata:.4f}<extra></extra>"
                ),
            )
        ]
    )
    fig.update_layout(
        title="Validated random-forest model selection",
        scene={
            "xaxis": {"title": "Feature set", "tickmode": "array", "tickvals": [0, 1], "ticktext": validation_stages},
            "yaxis_title": "PR-AUC standard deviation",
            "zaxis_title": "Mean PR-AUC",
            "camera": {"eye": {"x": 1.45, "y": -1.45, "z": 1.2}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
        showlegend=False,
    )
    write_plotly(fig, figures / "validated_rf_pr_auc_3d.html")

    node_budget = pd.read_csv(node_budget_path)
    edge_budget = pd.read_csv(edge_budget_path)
    node_rf = node_budget.loc[node_budget["model"] == "random_forest"].sort_values("review_fraction")
    edge_rf = edge_budget.loc[edge_budget["model"] == "random_forest"].sort_values("review_fraction")

    fig = go.Figure()
    for stage_index, (label, frame, color) in enumerate(
        zip(["Node only", "Node + edge"], [node_rf, edge_rf], palette(2))
    ):
        review_pct = frame["review_fraction"].to_numpy(dtype=float) * 100
        lift = frame["lift_at_budget_mean"].to_numpy(dtype=float)
        captured = frame["suspicious_captured_mean"].to_numpy(dtype=float)
        fig.add_trace(
            go.Scatter3d(
                x=review_pct,
                y=[float(stage_index)] * len(frame),
                z=lift,
                mode="lines+markers",
                name=label,
                line={"color": color, "width": 8},
                marker={"color": color, "size": 7},
                customdata=captured,
                hovertemplate=(
                    f"Feature set: {label}<br>Review budget: %{{x:.1f}}%"
                    "<br>Mean lift: %{z:.2f}x<br>Mean suspicious captured: %{customdata:.1f}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title="Validated investigator lift — node-only vs node+edge",
        scene={
            "xaxis_title": "Review budget (% of held-out cases)",
            "yaxis": {"title": "Feature set", "tickmode": "array", "tickvals": [0, 1], "ticktext": ["Node only", "Node + edge"]},
            "zaxis_title": "Mean lift vs random review",
            "camera": {"eye": {"x": 1.55, "y": -1.55, "z": 1.15}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
        legend={"orientation": "h"},
    )
    write_plotly(fig, figures / "validated_review_lift_comparison_3d.html")

    print(f"Wrote interactive Plotly 3D model-selection figures to {figures}")


if __name__ == "__main__":
    main()
