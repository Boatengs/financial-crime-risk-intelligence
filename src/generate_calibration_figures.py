from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_metric_bars(metrics: pd.DataFrame, output: Path) -> None:
    methods = metrics["method"].tolist()
    metric_names = ["brier_score", "log_loss", "ece"]
    metric_labels = ["Brier", "Log loss", "ECE"]

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")

    xpos, ypos, zpos, dx, dy, dz = [], [], [], [], [], []
    for i, method in enumerate(methods):
        row = metrics.loc[metrics["method"] == method].iloc[0]
        for j, metric in enumerate(metric_names):
            xpos.append(i)
            ypos.append(j)
            zpos.append(0.0)
            dx.append(0.55)
            dy.append(0.55)
            dz.append(float(row[metric]))

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, shade=True)
    ax.set_xticks(np.arange(len(methods)) + 0.275)
    ax.set_xticklabels(methods, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(metric_labels)) + 0.275)
    ax.set_yticklabels(metric_labels)
    ax.set_zlabel("Error / loss")
    ax.set_title("Held-out calibration quality — lower is better")
    ax.view_init(elev=24, azim=-58)
    fig.subplots_adjust(left=0.03, right=0.95, bottom=0.16, top=0.90)
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_ranking_bars(metrics: pd.DataFrame, output: Path) -> None:
    methods = metrics["method"].tolist()
    metric_names = ["average_precision", "roc_auc"]
    metric_labels = ["PR-AUC", "ROC-AUC"]

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")

    xpos, ypos, zpos, dx, dy, dz = [], [], [], [], [], []
    for i, method in enumerate(methods):
        row = metrics.loc[metrics["method"] == method].iloc[0]
        for j, metric in enumerate(metric_names):
            xpos.append(i)
            ypos.append(j)
            zpos.append(0.0)
            dx.append(0.55)
            dy.append(0.55)
            dz.append(float(row[metric]))

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, shade=True)
    ax.set_xticks(np.arange(len(methods)) + 0.275)
    ax.set_xticklabels(methods, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(metric_labels)) + 0.275)
    ax.set_yticklabels(metric_labels)
    ax.set_zlabel("Score")
    ax.set_zlim(0, 1)
    ax.set_title("Calibration trade-off — ranking quality")
    ax.view_init(elev=24, azim=-58)
    fig.subplots_adjust(left=0.03, right=0.95, bottom=0.16, top=0.90)
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)


def save_capture_bars(budgets: pd.DataFrame, output: Path) -> None:
    methods = list(dict.fromkeys(budgets["method"].astype(str)))
    fractions = sorted(budgets["review_fraction"].unique())

    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(111, projection="3d")

    xpos, ypos, zpos, dx, dy, dz = [], [], [], [], [], []
    for i, method in enumerate(methods):
        subset = budgets[budgets["method"].astype(str) == method]
        for j, fraction in enumerate(fractions):
            row = subset.loc[subset["review_fraction"] == fraction]
            if row.empty:
                continue
            xpos.append(j)
            ypos.append(i)
            zpos.append(0.0)
            dx.append(0.55)
            dy.append(0.55)
            dz.append(float(row.iloc[0]["suspicious_captured"]))

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, shade=True)
    ax.set_xticks(np.arange(len(fractions)) + 0.275)
    ax.set_xticklabels([f"{fraction * 100:g}%" for fraction in fractions])
    ax.set_yticks(np.arange(len(methods)) + 0.275)
    ax.set_yticklabels(methods)
    ax.set_xlabel("Review budget")
    ax.set_zlabel("Suspicious components captured")
    ax.set_title("Held-out calibration methods — investigator capture")
    ax.view_init(elev=24, azim=-58)
    fig.subplots_adjust(left=0.03, right=0.95, bottom=0.12, top=0.90)
    fig.savefig(output, format="svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 3D calibration comparison figures.")
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

    save_metric_bars(metrics, figures / "calibration_quality_3d.svg")
    save_ranking_bars(metrics, figures / "calibration_ranking_tradeoff_3d.svg")
    save_capture_bars(budgets, figures / "calibration_review_capture_3d.svg")

    print(f"Wrote 3D calibration figures to {figures}")


if __name__ == "__main__":
    main()
