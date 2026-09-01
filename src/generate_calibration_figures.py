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


def add_stems(
    fig: go.Figure,
    x: list[float],
    y: list[float],
    z: list[float],
    color: str,
    name: str,
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
            line={"color": color, "width": 5},
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
            marker={"size": 8, "color": color},
            text=hover,
            hovertemplate="%{text}<extra></extra>",
        )
    )


def save_metric_quality(metrics: pd.DataFrame, output: Path) -> None:
    methods = metrics["method"].astype(str).tolist()
    metric_names = ["brier_score", "log_loss", "ece"]
    metric_labels = ["Brier score", "Log loss", "ECE"]
    colors = palette(len(methods))
    fig = go.Figure()

    for method_index, (method, color) in enumerate(zip(methods, colors)):
        row = metrics.loc[metrics["method"].astype(str) == method].iloc[0]
        x = [float(method_index)] * len(metric_names)
        y = [float(i) for i in range(len(metric_names))]
        z = [float(row[name]) for name in metric_names]
        hover = [
            f"Method: {method}<br>Metric: {label}<br>Value: {value:.6f}"
            for label, value in zip(metric_labels, z)
        ]
        add_stems(fig, x, y, z, color, method.replace("_", " ").title(), hover)

    fig.update_layout(
        title="Held-out calibration quality — lower is better",
        scene={
            "xaxis": {"title": "Calibration method", "tickmode": "array", "tickvals": list(range(len(methods))), "ticktext": [m.replace("_", " ").title() for m in methods]},
            "yaxis": {"title": "Metric", "tickmode": "array", "tickvals": [0, 1, 2], "ticktext": metric_labels},
            "zaxis_title": "Error / loss",
            "camera": {"eye": {"x": 1.55, "y": -1.45, "z": 1.15}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
        legend={"orientation": "h"},
    )
    write_plotly(fig, output)


def save_ranking_quality(metrics: pd.DataFrame, output: Path) -> None:
    methods = metrics["method"].astype(str).tolist()
    metric_names = ["average_precision", "roc_auc"]
    metric_labels = ["PR-AUC", "ROC-AUC"]
    colors = palette(len(methods))
    fig = go.Figure()

    for method_index, (method, color) in enumerate(zip(methods, colors)):
        row = metrics.loc[metrics["method"].astype(str) == method].iloc[0]
        x = [float(method_index)] * len(metric_names)
        y = [0.0, 1.0]
        z = [float(row[name]) for name in metric_names]
        hover = [
            f"Method: {method}<br>Metric: {label}<br>Score: {value:.6f}"
            for label, value in zip(metric_labels, z)
        ]
        add_stems(fig, x, y, z, color, method.replace("_", " ").title(), hover)

    fig.update_layout(
        title="Calibration trade-off — ranking quality",
        scene={
            "xaxis": {"title": "Calibration method", "tickmode": "array", "tickvals": list(range(len(methods))), "ticktext": [m.replace("_", " ").title() for m in methods]},
            "yaxis": {"title": "Ranking metric", "tickmode": "array", "tickvals": [0, 1], "ticktext": metric_labels},
            "zaxis": {"title": "Score", "range": [0, 1]},
            "camera": {"eye": {"x": 1.55, "y": -1.45, "z": 1.15}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
        legend={"orientation": "h"},
    )
    write_plotly(fig, output)


def save_capture_surface(budgets: pd.DataFrame, output: Path) -> None:
    methods = list(dict.fromkeys(budgets["method"].astype(str)))
    fractions = sorted(float(v) for v in budgets["review_fraction"].unique())
    z_matrix: list[list[float]] = []
    hovertext: list[list[str]] = []

    for method in methods:
        subset = budgets[budgets["method"].astype(str) == method]
        row_values: list[float] = []
        row_hover: list[str] = []
        for fraction in fractions:
            row = subset.loc[subset["review_fraction"] == fraction]
            if row.empty:
                row_values.append(float("nan"))
                row_hover.append("")
                continue
            r = row.iloc[0]
            captured = float(r["suspicious_captured"])
            row_values.append(captured)
            row_hover.append(
                f"Method: {method}<br>Review budget: {fraction * 100:g}%"
                f"<br>Suspicious captured: {int(captured)}"
                f"<br>Precision: {float(r['precision_at_budget']):.2%}"
                f"<br>Recall: {float(r['recall_at_budget']):.2%}"
            )
        z_matrix.append(row_values)
        hovertext.append(row_hover)

    fig = go.Figure(
        data=[
            go.Surface(
                x=[fraction * 100 for fraction in fractions],
                y=list(range(len(methods))),
                z=z_matrix,
                text=hovertext,
                hovertemplate="%{text}<extra></extra>",
                colorscale="Viridis",
                showscale=True,
                colorbar={"title": "Captured"},
            )
        ]
    )
    fig.update_layout(
        title="Held-out calibration methods — investigator capture surface",
        scene={
            "xaxis_title": "Review budget (% of held-out cases)",
            "yaxis": {"title": "Calibration method", "tickmode": "array", "tickvals": list(range(len(methods))), "ticktext": [m.replace("_", " ").title() for m in methods]},
            "zaxis_title": "Suspicious components captured",
            "camera": {"eye": {"x": 1.6, "y": -1.55, "z": 1.15}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 55},
    )
    write_plotly(fig, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate interactive Plotly 3D calibration figures.")
    parser.add_argument("--results-dir", default="results/node_calibration")
    parser.add_argument("--figures-dir", default="figures/calibration")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)

    metrics_path = results / "calibration_method_metrics.csv"
    budgets_path = results / "calibration_review_budget_metrics.csv"
    if not metrics_path.exists() or not budgets_path.exists():
        raise SystemExit(
            "Calibration outputs not found. Run src/validate_rf_calibration.py before generating figures."
        )

    metrics = pd.read_csv(metrics_path)
    budgets = pd.read_csv(budgets_path)

    save_metric_quality(metrics, figures / "calibration_quality_3d.html")
    save_ranking_quality(metrics, figures / "calibration_ranking_tradeoff_3d.html")
    save_capture_surface(budgets, figures / "calibration_review_capture_3d.html")

    print(f"Wrote interactive Plotly 3D calibration figures to {figures}")


if __name__ == "__main__":
    main()
