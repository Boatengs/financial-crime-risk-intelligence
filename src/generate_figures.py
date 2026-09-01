from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


PLOT_CONFIG = {"responsive": True, "displaylogo": False}


def save_pair(fig, seaborn_path: Path, plotly_path: Path) -> None:
    fig.savefig(seaborn_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    # Plotly figure is written separately by the caller.


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Seaborn and Plotly 2D project figures.")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    budget_path = results / "review_budget_metrics.csv"
    if budget_path.exists():
        df = pd.read_csv(budget_path).copy()
        df["review_budget_pct"] = df["review_fraction"] * 100
        df["model_label"] = df["model"].str.replace("_", " ").str.title()

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(
            data=df,
            x="review_budget_pct",
            y="lift_at_budget",
            hue="model_label",
            marker="o",
            linewidth=2.5,
            ax=ax,
        )
        ax.set_title("Investigator lift by review budget")
        ax.set_xlabel("Review budget (% of held-out cases)")
        ax.set_ylabel("Lift vs random review")
        ax.legend(title="Model")
        save_pair(fig, figures / "review_budget_curve.png", figures / "review_budget_curve.html")

        pfig = px.line(
            df,
            x="review_budget_pct",
            y="lift_at_budget",
            color="model_label",
            markers=True,
            hover_data={
                "precision_at_budget": ":.3f",
                "recall_at_budget": ":.3f",
                "suspicious_captured": True,
                "review_budget_pct": ":.1f",
                "lift_at_budget": ":.2f",
            },
            labels={
                "review_budget_pct": "Review budget (%)",
                "lift_at_budget": "Lift vs random review",
                "model_label": "Model",
            },
            title="Investigator lift by review budget",
        )
        pfig.update_layout(template="plotly_white", legend_title_text="Model")
        pfig.write_html(
            figures / "review_budget_curve.html",
            include_plotlyjs="cdn",
            full_html=True,
            config=PLOT_CONFIG,
        )

    queue_path = results / "investigator_queue.csv"
    if queue_path.exists():
        q = pd.read_csv(queue_path)
        band_column = "priority_band" if "priority_band" in q.columns else "risk_band"
        if band_column == "priority_band":
            bands = [
                "tier_1_top_0_5pct",
                "tier_2_top_1pct",
                "tier_3_top_2pct",
                "tier_4_top_5pct",
                "tier_5_top_10pct",
                "standard",
            ]
            labels = ["Top 0.5%", "0.5–1%", "1–2%", "2–5%", "5–10%", "Standard"]
        else:
            bands = ["critical", "high", "elevated", "standard"]
            labels = [b.title() for b in bands]

        counts = q[band_column].value_counts().reindex(bands, fill_value=0)
        queue_summary = pd.DataFrame({"priority_tier": labels, "cases": counts.to_numpy()})

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=queue_summary, x="priority_tier", y="cases", ax=ax)
        ax.set_title("Investigator queue by review-capacity priority tier")
        ax.set_xlabel("Priority tier")
        ax.set_ylabel("Cases")
        ax.tick_params(axis="x", rotation=20)
        save_pair(fig, figures / "priority_queue_summary.png", figures / "priority_queue_summary.html")

        pfig = px.bar(
            queue_summary,
            x="priority_tier",
            y="cases",
            text_auto=",.0f",
            labels={"priority_tier": "Priority tier", "cases": "Cases"},
            title="Investigator queue by review-capacity priority tier",
        )
        pfig.update_layout(template="plotly_white")
        pfig.write_html(
            figures / "priority_queue_summary.html",
            include_plotlyjs="cdn",
            full_html=True,
            config=PLOT_CONFIG,
        )

    print(f"Wrote Seaborn PNG and Plotly HTML figures to {figures}")


if __name__ == "__main__":
    main()
