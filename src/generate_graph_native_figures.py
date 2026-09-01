from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


PLOTLY_CONFIG = {"responsive": True, "displaylogo": False}


def label_model(value: str) -> str:
    labels = {
        "node_enriched_random_forest": "Node-enriched random forest",
        "directed_graphsage": "Directed GraphSAGE",
    }
    return labels.get(value, value.replace("_", " ").title())


def save_model_quality(comparison: pd.DataFrame, output_dir: Path) -> None:
    frame = comparison[["model", "average_precision", "roc_auc"]].copy()
    frame["model"] = frame["model"].map(label_model)
    long = frame.melt(
        id_vars="model",
        value_vars=["average_precision", "roc_auc"],
        var_name="metric",
        value_name="score",
    )
    long["metric"] = long["metric"].map(
        {"average_precision": "PR-AUC", "roc_auc": "ROC-AUC"}
    )

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(data=long, x="metric", y="score", hue="model", ax=ax)
    ax.set_title("Matched seed-42 model quality")
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(output_dir / "model_quality_comparison.png", dpi=180)
    plt.close(fig)

    pfig = px.bar(
        long,
        x="metric",
        y="score",
        color="model",
        barmode="group",
        title="Matched seed-42 model quality",
        labels={"metric": "", "score": "Score", "model": "Model"},
        text_auto=".3f",
    )
    pfig.update_yaxes(range=[0, 1])
    pfig.write_html(
        output_dir / "model_quality_comparison.html",
        include_plotlyjs="cdn",
        full_html=True,
        config=PLOTLY_CONFIG,
    )


def prepare_budget_frame(budgets: pd.DataFrame) -> pd.DataFrame:
    frame = budgets.copy()
    frame["benchmark"] = frame["benchmark"].map(label_model)
    frame["review_budget_pct"] = frame["review_fraction"].astype(float) * 100
    return frame.sort_values(["benchmark", "review_budget_pct"])


def save_capture_curve(budgets: pd.DataFrame, output_dir: Path) -> None:
    frame = prepare_budget_frame(budgets)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.lineplot(
        data=frame,
        x="review_budget_pct",
        y="suspicious_captured",
        hue="benchmark",
        marker="o",
        ax=ax,
    )
    ax.set_title("Suspicious components captured by review budget")
    ax.set_xlabel("Review budget (% of held-out components)")
    ax.set_ylabel("Suspicious components captured")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(output_dir / "suspicious_capture_by_budget.png", dpi=180)
    plt.close(fig)

    pfig = px.line(
        frame,
        x="review_budget_pct",
        y="suspicious_captured",
        color="benchmark",
        markers=True,
        title="Suspicious components captured by review budget",
        labels={
            "review_budget_pct": "Review budget (% of held-out components)",
            "suspicious_captured": "Suspicious components captured",
            "benchmark": "Model",
        },
        hover_data={
            "precision_at_budget": ":.2%",
            "recall_at_budget": ":.2%",
            "lift_at_budget": ":.2f",
        },
    )
    pfig.write_html(
        output_dir / "suspicious_capture_by_budget.html",
        include_plotlyjs="cdn",
        full_html=True,
        config=PLOTLY_CONFIG,
    )


def save_lift_curve(budgets: pd.DataFrame, output_dir: Path) -> None:
    frame = prepare_budget_frame(budgets)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.lineplot(
        data=frame,
        x="review_budget_pct",
        y="lift_at_budget",
        hue="benchmark",
        marker="o",
        ax=ax,
    )
    ax.set_title("Investigator lift versus random review")
    ax.set_xlabel("Review budget (% of held-out components)")
    ax.set_ylabel("Lift vs random review (×)")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(output_dir / "lift_by_budget.png", dpi=180)
    plt.close(fig)

    pfig = px.line(
        frame,
        x="review_budget_pct",
        y="lift_at_budget",
        color="benchmark",
        markers=True,
        title="Investigator lift versus random review",
        labels={
            "review_budget_pct": "Review budget (% of held-out components)",
            "lift_at_budget": "Lift vs random review (×)",
            "benchmark": "Model",
        },
        hover_data={
            "suspicious_captured": True,
            "precision_at_budget": ":.2%",
            "recall_at_budget": ":.2%",
        },
    )
    pfig.write_html(
        output_dir / "lift_by_budget.html",
        include_plotlyjs="cdn",
        full_html=True,
        config=PLOTLY_CONFIG,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 2D Seaborn and Plotly views for the graph-native benchmark."
    )
    parser.add_argument("--results-dir", default="results/graph_native")
    parser.add_argument("--figures-dir", default="figures/graph_native")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.figures_dir)
    comparison_path = results_dir / "seed42_internal_comparison.csv"
    budget_path = results_dir / "seed42_budget_comparison.csv"
    missing = [str(path) for path in (comparison_path, budget_path) if not path.exists()]
    if missing:
        raise SystemExit(f"Missing graph benchmark outputs: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison = pd.read_csv(comparison_path)
    budgets = pd.read_csv(budget_path)

    save_model_quality(comparison, output_dir)
    save_capture_curve(budgets, output_dir)
    save_lift_curve(budgets, output_dir)

    print(f"Wrote Seaborn PNG and Plotly HTML graph benchmark figures to {output_dir}")


if __name__ == "__main__":
    main()
