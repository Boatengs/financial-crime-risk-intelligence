from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


PLOT_CONFIG = {"responsive": True, "displaylogo": False}


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


def write_plotly(fig, path: Path) -> None:
    fig.write_html(path, include_plotlyjs="cdn", full_html=True, config=PLOT_CONFIG)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Seaborn and Plotly 2D visuals for final model selection."
    )
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures/model_selection")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

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

    rows: list[dict[str, float | str]] = []
    for stage, path in zip(stages, stage_files):
        for model in models:
            rows.append(
                {
                    "feature_stage": stage,
                    "model": model.replace("_", " ").title(),
                    "pr_auc": read_model_metric(path, model, "average_precision"),
                    "roc_auc": read_model_metric(path, model, "roc_auc"),
                }
            )
    stage_df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(
        data=stage_df,
        x="feature_stage",
        y="pr_auc",
        hue="model",
        marker="o",
        linewidth=2.5,
        ax=ax,
    )
    ax.set_title("Feature-stage model comparison — matched seed-42 split")
    ax.set_xlabel("Feature stage")
    ax.set_ylabel("PR-AUC / average precision")
    ax.tick_params(axis="x", rotation=12)
    ax.legend(title="Model")
    fig.savefig(figures / "feature_stage_pr_auc.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.line(
        stage_df,
        x="feature_stage",
        y="pr_auc",
        color="model",
        markers=True,
        hover_data={"roc_auc": ":.4f", "pr_auc": ":.4f"},
        labels={
            "feature_stage": "Feature stage",
            "pr_auc": "PR-AUC / average precision",
            "model": "Model",
            "roc_auc": "ROC-AUC",
        },
        title="Feature-stage model comparison — matched seed-42 split",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "feature_stage_pr_auc.html")

    node_summary_path = results / "node_enriched_validation" / "repeated_split_summary.csv"
    edge_summary_path = results / "node_edge_enriched_validation" / "repeated_split_summary.csv"
    node_budget_path = results / "node_enriched_validation" / "repeated_budget_summary.csv"
    edge_budget_path = results / "node_edge_enriched_validation" / "repeated_budget_summary.csv"
    validation_required = [node_summary_path, edge_summary_path, node_budget_path, edge_budget_path]
    missing_validation = [str(p) for p in validation_required if not p.exists()]
    if missing_validation:
        raise SystemExit(f"Missing validation files: {missing_validation}")

    validation_df = pd.DataFrame(
        {
            "feature_set": ["Node only", "Node + edge"],
            "pr_auc_mean": [
                read_repeated_metric(node_summary_path, "random_forest", "average_precision_mean"),
                read_repeated_metric(edge_summary_path, "random_forest", "average_precision_mean"),
            ],
            "pr_auc_std": [
                read_repeated_metric(node_summary_path, "random_forest", "average_precision_std"),
                read_repeated_metric(edge_summary_path, "random_forest", "average_precision_std"),
            ],
            "roc_auc_mean": [
                read_repeated_metric(node_summary_path, "random_forest", "roc_auc_mean"),
                read_repeated_metric(edge_summary_path, "random_forest", "roc_auc_mean"),
            ],
        }
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=validation_df, x="feature_set", y="pr_auc_mean", ax=ax)
    ax.errorbar(
        x=range(len(validation_df)),
        y=validation_df["pr_auc_mean"],
        yerr=validation_df["pr_auc_std"],
        fmt="none",
        capsize=6,
        linewidth=1.5,
    )
    ax.set_title("Validated random-forest model selection")
    ax.set_xlabel("Feature set")
    ax.set_ylabel("Mean PR-AUC")
    fig.savefig(figures / "validated_rf_pr_auc.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.bar(
        validation_df,
        x="feature_set",
        y="pr_auc_mean",
        error_y="pr_auc_std",
        hover_data={"roc_auc_mean": ":.4f", "pr_auc_mean": ":.4f", "pr_auc_std": ":.4f"},
        labels={
            "feature_set": "Feature set",
            "pr_auc_mean": "Mean PR-AUC",
            "roc_auc_mean": "Mean ROC-AUC",
            "pr_auc_std": "PR-AUC SD",
        },
        title="Validated random-forest model selection",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "validated_rf_pr_auc.html")

    node_budget = pd.read_csv(node_budget_path)
    edge_budget = pd.read_csv(edge_budget_path)
    node_rf = node_budget.loc[node_budget["model"] == "random_forest"].copy()
    node_rf["feature_set"] = "Node only"
    edge_rf = edge_budget.loc[edge_budget["model"] == "random_forest"].copy()
    edge_rf["feature_set"] = "Node + edge"
    budget_df = pd.concat([node_rf, edge_rf], ignore_index=True)
    budget_df["review_budget_pct"] = budget_df["review_fraction"] * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(
        data=budget_df,
        x="review_budget_pct",
        y="lift_at_budget_mean",
        hue="feature_set",
        marker="o",
        linewidth=2.5,
        ax=ax,
    )
    ax.set_title("Validated investigator lift — node-only vs node+edge")
    ax.set_xlabel("Review budget (% of held-out cases)")
    ax.set_ylabel("Mean lift vs random review")
    ax.legend(title="Feature set")
    fig.savefig(figures / "validated_review_lift_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.line(
        budget_df,
        x="review_budget_pct",
        y="lift_at_budget_mean",
        color="feature_set",
        markers=True,
        hover_data={
            "suspicious_captured_mean": ":.1f",
            "precision_at_budget_mean": ":.3f",
            "recall_at_budget_mean": ":.3f",
            "lift_at_budget_mean": ":.2f",
        },
        labels={
            "review_budget_pct": "Review budget (%)",
            "lift_at_budget_mean": "Mean lift vs random review",
            "feature_set": "Feature set",
            "suspicious_captured_mean": "Mean suspicious captured",
        },
        title="Validated investigator lift — node-only vs node+edge",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "validated_review_lift_comparison.html")

    print(f"Wrote Seaborn PNG and Plotly HTML model-selection figures to {figures}")


if __name__ == "__main__":
    main()
