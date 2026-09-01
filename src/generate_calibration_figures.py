from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


PLOT_CONFIG = {"responsive": True, "displaylogo": False}


def write_plotly(fig, path: Path) -> None:
    fig.write_html(path, include_plotlyjs="cdn", full_html=True, config=PLOT_CONFIG)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Seaborn and Plotly 2D calibration figures.")
    parser.add_argument("--results-dir", default="results/node_calibration")
    parser.add_argument("--figures-dir", default="figures/calibration")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    metrics_path = results / "calibration_method_metrics.csv"
    budgets_path = results / "calibration_review_budget_metrics.csv"
    if not metrics_path.exists() or not budgets_path.exists():
        raise SystemExit(
            "Calibration outputs not found. Run src/validate_rf_calibration.py before generating figures."
        )

    metrics = pd.read_csv(metrics_path).copy()
    metrics["method_label"] = metrics["method"].str.replace("_", " ").str.title()
    budgets = pd.read_csv(budgets_path).copy()
    budgets["method_label"] = budgets["method"].str.replace("_", " ").str.title()
    budgets["review_budget_pct"] = budgets["review_fraction"] * 100

    quality_long = metrics.melt(
        id_vars=["method", "method_label"],
        value_vars=["brier_score", "log_loss", "ece"],
        var_name="metric",
        value_name="value",
    )
    quality_long["metric_label"] = quality_long["metric"].map(
        {"brier_score": "Brier score", "log_loss": "Log loss", "ece": "ECE"}
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(
        data=quality_long,
        x="metric_label",
        y="value",
        hue="method_label",
        ax=ax,
    )
    ax.set_yscale("log")
    ax.set_title("Held-out calibration quality — lower is better")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Error / loss (log scale)")
    ax.legend(title="Method")
    fig.savefig(figures / "calibration_quality.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.bar(
        quality_long,
        x="metric_label",
        y="value",
        color="method_label",
        barmode="group",
        log_y=True,
        labels={"metric_label": "Metric", "value": "Error / loss", "method_label": "Method"},
        title="Held-out calibration quality — lower is better",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "calibration_quality.html")

    ranking_long = metrics.melt(
        id_vars=["method", "method_label"],
        value_vars=["average_precision", "roc_auc"],
        var_name="metric",
        value_name="score",
    )
    ranking_long["metric_label"] = ranking_long["metric"].map(
        {"average_precision": "PR-AUC", "roc_auc": "ROC-AUC"}
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=ranking_long,
        x="metric_label",
        y="score",
        hue="method_label",
        ax=ax,
    )
    ax.set_ylim(0, 1)
    ax.set_title("Calibration trade-off — ranking quality")
    ax.set_xlabel("Ranking metric")
    ax.set_ylabel("Score")
    ax.legend(title="Method")
    fig.savefig(figures / "calibration_ranking_tradeoff.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.bar(
        ranking_long,
        x="metric_label",
        y="score",
        color="method_label",
        barmode="group",
        range_y=[0, 1],
        labels={"metric_label": "Ranking metric", "score": "Score", "method_label": "Method"},
        title="Calibration trade-off — ranking quality",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "calibration_ranking_tradeoff.html")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(
        data=budgets,
        x="review_budget_pct",
        y="suspicious_captured",
        hue="method_label",
        marker="o",
        linewidth=2.5,
        ax=ax,
    )
    ax.set_title("Held-out calibration methods — investigator capture")
    ax.set_xlabel("Review budget (% of held-out cases)")
    ax.set_ylabel("Suspicious components captured")
    ax.legend(title="Method")
    fig.savefig(figures / "calibration_review_capture.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    pfig = px.line(
        budgets,
        x="review_budget_pct",
        y="suspicious_captured",
        color="method_label",
        markers=True,
        hover_data={
            "precision_at_budget": ":.3f",
            "recall_at_budget": ":.3f",
            "lift_at_budget": ":.2f",
            "review_budget_pct": ":.1f",
        },
        labels={
            "review_budget_pct": "Review budget (%)",
            "suspicious_captured": "Suspicious components captured",
            "method_label": "Method",
        },
        title="Held-out calibration methods — investigator capture",
    )
    pfig.update_layout(template="plotly_white")
    write_plotly(pfig, figures / "calibration_review_capture.html")

    print(f"Wrote Seaborn PNG and Plotly HTML calibration figures to {figures}")


if __name__ == "__main__":
    main()
