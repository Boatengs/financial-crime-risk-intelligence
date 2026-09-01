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


def add_stem_trace(
    fig: go.Figure,
    x: list[float],
    y: list[float],
    z: list[float],
    name: str,
    color: str,
    hover: list[str],
) -> None:
    line_x: list[float | None] = []
    line_y: list[float | None] = []
    line_z: list[float | None] = []
    for xv, yv, zv in zip(x, y, z):
        line_x.extend([xv, xv, None])
        line_y.extend([yv, yv, None])
        line_z.extend([0.0, zv, None])
    fig.add_trace(
        go.Scatter3d(
            x=line_x,
            y=line_y,
            z=line_z,
            mode="lines",
            line={"color": color, "width": 6},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            name=name,
            marker={"size": 7, "color": color, "opacity": 0.92},
            text=hover,
            hovertemplate="%{text}<extra></extra>",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate interactive Plotly 3D project figures.")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)

    budget_path = results / "review_budget_metrics.csv"
    if budget_path.exists():
        df = pd.read_csv(budget_path)
        models = list(df["model"].drop_duplicates())
        colors = palette(len(models))
        fig = go.Figure()
        for model_index, (model, color) in enumerate(zip(models, colors)):
            group = df[df["model"] == model].sort_values("review_fraction")
            review_pct = group["review_fraction"].to_numpy(dtype=float) * 100
            yvals = [float(model_index)] * len(group)
            lift = group["lift_at_budget"].to_numpy(dtype=float)
            hover = [
                (
                    f"Model: {model}<br>Review budget: {budget:.1f}%"
                    f"<br>Lift: {lift_value:.2f}x<br>Precision: {precision:.2%}"
                    f"<br>Recall: {recall:.2%}<br>Suspicious captured: {captured}"
                )
                for budget, lift_value, precision, recall, captured in zip(
                    review_pct,
                    lift,
                    group["precision_at_budget"],
                    group["recall_at_budget"],
                    group["suspicious_captured"],
                )
            ]
            fig.add_trace(
                go.Scatter3d(
                    x=review_pct,
                    y=yvals,
                    z=lift,
                    mode="lines+markers",
                    name=model.replace("_", " ").title(),
                    line={"color": color, "width": 7},
                    marker={"color": color, "size": 6},
                    text=hover,
                    hovertemplate="%{text}<extra></extra>",
                )
            )
        fig.update_layout(
            title="Investigator lift by review budget",
            scene={
                "xaxis_title": "Review budget (% of held-out cases)",
                "yaxis": {
                    "title": "Model",
                    "tickmode": "array",
                    "tickvals": list(range(len(models))),
                    "ticktext": [m.replace("_", " ").title() for m in models],
                },
                "zaxis_title": "Lift vs random review",
                "camera": {"eye": {"x": 1.55, "y": -1.55, "z": 1.15}},
            },
            margin={"l": 0, "r": 0, "b": 0, "t": 55},
            legend={"orientation": "h"},
        )
        write_plotly(fig, figures / "review_budget_curve_3d.html")

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
        colors = palette(len(bands))
        fig = go.Figure()
        for index, (band_name, label, count, color) in enumerate(
            zip(bands, labels, counts.to_numpy(dtype=float), colors)
        ):
            add_stem_trace(
                fig,
                [float(index)],
                [0.0],
                [float(count)],
                label,
                color,
                [f"Priority tier: {label}<br>Cases: {int(count):,}"],
            )
        fig.update_layout(
            title="Investigator queue by review-capacity priority tier",
            scene={
                "xaxis": {
                    "title": "Priority tier",
                    "tickmode": "array",
                    "tickvals": list(range(len(labels))),
                    "ticktext": labels,
                },
                "yaxis": {"title": "Queue layer", "showticklabels": False},
                "zaxis_title": "Cases",
                "camera": {"eye": {"x": 1.55, "y": -1.45, "z": 1.1}},
            },
            margin={"l": 0, "r": 0, "b": 0, "t": 55},
            showlegend=False,
        )
        write_plotly(fig, figures / "priority_queue_summary_3d.html")

    print(f"Wrote interactive Plotly 3D figures to {figures}")


if __name__ == "__main__":
    main()
