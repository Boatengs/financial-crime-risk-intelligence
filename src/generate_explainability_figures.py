from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns


PLOT_CONFIG = {"responsive": True, "displaylogo": False}


def write_plotly(fig: go.Figure, path: Path) -> None:
    fig.write_html(path, include_plotlyjs="cdn", full_html=True, config=PLOT_CONFIG)


def save_global_importance(importance: pd.DataFrame, figures: Path, top_n: int) -> None:
    data = (
        importance.dropna(subset=["feature", "random_forest_importance"])
        .sort_values("random_forest_importance", ascending=False)
        .head(top_n)
        .sort_values("random_forest_importance", ascending=True)
        .copy()
    )

    plt.figure(figsize=(10, 7))
    sns.barplot(data=data, x="random_forest_importance", y="feature")
    plt.xlabel("Random-forest feature importance")
    plt.ylabel("Anonymized feature")
    plt.title(f"Top {len(data)} global features — preferred node-only random forest")
    plt.tight_layout()
    plt.savefig(figures / "global_feature_importance.png", dpi=180, bbox_inches="tight")
    plt.close()

    plotly_data = data.sort_values("random_forest_importance", ascending=False)
    fig = px.bar(
        plotly_data,
        x="random_forest_importance",
        y="feature",
        orientation="h",
        title=f"Top {len(plotly_data)} global features — preferred node-only random forest",
        labels={
            "random_forest_importance": "Random-forest feature importance",
            "feature": "Anonymized feature",
        },
        hover_data={"random_forest_importance": ":.4f"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"l": 150})
    write_plotly(fig, figures / "global_feature_importance.html")


def save_priority_evidence_frequency(evidence: pd.DataFrame, figures: Path, top_n: int) -> None:
    tier1 = evidence[evidence["priority_band"].astype(str) == "tier_1_top_0_5pct"].copy()
    if tier1.empty:
        raise SystemExit("No tier_1_top_0_5pct rows found in evidence table")

    counts = (
        tier1["feature"]
        .value_counts()
        .head(top_n)
        .rename_axis("feature")
        .reset_index(name="evidence_mentions")
    )

    plt.figure(figsize=(10, 7))
    sns.barplot(
        data=counts.sort_values("evidence_mentions", ascending=True),
        x="evidence_mentions",
        y="feature",
    )
    plt.xlabel("Evidence mentions among top-0.5% queued components")
    plt.ylabel("Anonymized feature")
    plt.title("Most frequent review cues in the highest-priority queue")
    plt.tight_layout()
    plt.savefig(figures / "top_priority_evidence_frequency.png", dpi=180, bbox_inches="tight")
    plt.close()

    fig = px.bar(
        counts,
        x="evidence_mentions",
        y="feature",
        orientation="h",
        title="Most frequent review cues in the highest-priority queue",
        labels={
            "evidence_mentions": "Evidence mentions among top-0.5% queued components",
            "feature": "Anonymized feature",
        },
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"l": 150})
    write_plotly(fig, figures / "top_priority_evidence_frequency.html")


def save_top_case_heatmap(evidence: pd.DataFrame, figures: Path, top_cases: int) -> None:
    top_component_ids = (
        evidence[["rank", "component_id"]]
        .drop_duplicates()
        .sort_values("rank")
        .head(top_cases)["component_id"]
        .tolist()
    )
    subset = evidence[evidence["component_id"].isin(top_component_ids)].copy()

    feature_order = (
        subset.groupby("feature")["evidence_score"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    pivot = subset.pivot_table(
        index="component_id",
        columns="feature",
        values="zscore",
        aggfunc="first",
    )
    pivot = pivot.reindex(index=top_component_ids, columns=feature_order)

    plt.figure(figsize=(max(10, len(feature_order) * 0.9), max(7, top_cases * 0.42)))
    sns.heatmap(pivot, center=0, cmap="vlag", linewidths=0.3, cbar_kws={"label": "Z-score"})
    plt.xlabel("Case-specific evidence feature")
    plt.ylabel("Component ID (rank order)")
    plt.title(f"Top {len(top_component_ids)} queued components — selected evidence deviations")
    plt.tight_layout()
    plt.savefig(figures / "top_case_evidence_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close()

    hover = subset.pivot_table(
        index="component_id",
        columns="feature",
        values="percentile",
        aggfunc="first",
    ).reindex(index=top_component_ids, columns=feature_order)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.to_numpy(dtype=float),
            x=feature_order,
            y=[str(value) for value in top_component_ids],
            colorscale="RdBu",
            zmid=0,
            colorbar={"title": "Z-score"},
            customdata=hover.to_numpy(dtype=float),
            hovertemplate=(
                "Component: %{y}<br>Feature: %{x}<br>Z-score: %{z:.2f}"
                "<br>Percentile: %{customdata:.1%}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"Top {len(top_component_ids)} queued components — selected evidence deviations",
        xaxis_title="Case-specific evidence feature",
        yaxis_title="Component ID (rank order)",
        margin={"l": 90, "r": 30, "b": 130, "t": 60},
    )
    write_plotly(fig, figures / "top_case_evidence_heatmap.html")


def save_evidence_strength_vs_rank(evidence: pd.DataFrame, figures: Path) -> None:
    case_summary = (
        evidence.groupby(["rank", "component_id", "priority_band", "risk_score"], as_index=False)
        .agg(
            mean_evidence_score=("evidence_score", "mean"),
            max_absolute_zscore=("absolute_zscore", "max"),
        )
        .sort_values("rank")
    )
    top10pct = case_summary[case_summary["rank"] <= max(1, int(len(case_summary) * 0.10))].copy()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=top10pct,
        x="rank",
        y="mean_evidence_score",
        hue="priority_band",
        s=28,
        alpha=0.75,
    )
    plt.xlabel("Investigator queue rank")
    plt.ylabel("Mean evidence score")
    plt.title("Evidence strength across the top 10% of the investigator queue")
    plt.legend(title="Priority tier", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(figures / "evidence_strength_by_rank.png", dpi=180, bbox_inches="tight")
    plt.close()

    fig = px.scatter(
        top10pct,
        x="rank",
        y="mean_evidence_score",
        color="priority_band",
        hover_data={
            "component_id": True,
            "risk_score": ":.4f",
            "max_absolute_zscore": ":.2f",
        },
        title="Evidence strength across the top 10% of the investigator queue",
        labels={
            "rank": "Investigator queue rank",
            "mean_evidence_score": "Mean evidence score",
            "priority_band": "Priority tier",
        },
    )
    write_plotly(fig, figures / "evidence_strength_by_rank.html")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 2D Seaborn and Plotly investigator explainability figures."
    )
    parser.add_argument(
        "--evidence",
        default="results/node_enriched/investigator_evidence_long.csv",
    )
    parser.add_argument(
        "--importance",
        default="results/node_enriched_validation/feature_importance_seed42.csv",
    )
    parser.add_argument("--figures-dir", default="figures/explainability")
    parser.add_argument("--top-features", type=int, default=12)
    parser.add_argument("--top-cases", type=int, default=20)
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    importance_path = Path(args.importance)
    for path in (evidence_path, importance_path):
        if not path.exists():
            raise SystemExit(f"Required input not found: {path}")

    evidence = pd.read_csv(evidence_path)
    importance = pd.read_csv(importance_path)
    required_evidence = {
        "rank",
        "component_id",
        "priority_band",
        "risk_score",
        "feature",
        "zscore",
        "absolute_zscore",
        "percentile",
        "evidence_score",
    }
    missing = required_evidence - set(evidence.columns)
    if missing:
        raise SystemExit(f"Evidence table missing columns: {sorted(missing)}")
    if {"feature", "random_forest_importance"} - set(importance.columns):
        raise SystemExit("Importance table missing feature/random_forest_importance")

    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    save_global_importance(importance, figures, args.top_features)
    save_priority_evidence_frequency(evidence, figures, args.top_features)
    save_top_case_heatmap(evidence, figures, args.top_cases)
    save_evidence_strength_vs_rank(evidence, figures)

    print(f"Wrote Seaborn PNG and Plotly HTML explainability figures to {figures}")


if __name__ == "__main__":
    main()
