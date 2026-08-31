from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures")
    args = parser.parse_args()

    results = Path(args.results_dir)
    figures = Path(args.figures_dir)
    figures.mkdir(parents=True, exist_ok=True)

    budget_path = results / "review_budget_metrics.csv"
    if budget_path.exists():
        df = pd.read_csv(budget_path)
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection="3d")
        models = list(df["model"].drop_duplicates())
        for model_index, model in enumerate(models):
            group = df[df["model"] == model].sort_values("review_fraction")
            x = group["review_fraction"].to_numpy() * 100
            y = np.full(len(group), model_index, dtype=float)
            z = group["lift_at_budget"].to_numpy()
            ax.plot(x, y, z, marker="o", label=model)
        ax.set_xlabel("Review budget (% of cases)", labelpad=10)
        ax.set_ylabel("Model", labelpad=12)
        ax.set_zlabel("Lift vs random review", labelpad=10)
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels(models)
        ax.set_title("3D investigation lift by review budget", pad=18)
        ax.view_init(elev=24, azim=-58)
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
        fig.subplots_adjust(left=0.04, right=0.82, bottom=0.08, top=0.90)
        fig.savefig(figures / "review_budget_curve_3d.svg", bbox_inches="tight")
        plt.close(fig)

    queue_path = results / "investigator_queue.csv"
    if queue_path.exists():
        q = pd.read_csv(queue_path)
        bands = ["critical", "high", "elevated", "standard"]
        counts = q["risk_band"].value_counts().reindex(bands, fill_value=0)
        x = np.arange(len(bands), dtype=float)
        y = np.zeros(len(bands), dtype=float)
        z = np.zeros(len(bands), dtype=float)
        dx = np.full(len(bands), 0.65)
        dy = np.full(len(bands), 0.65)
        dz = counts.to_numpy(dtype=float)

        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection="3d")
        ax.bar3d(x, y, z, dx, dy, dz, shade=True)
        ax.set_xticks(x + dx / 2)
        ax.set_xticklabels(bands, rotation=12)
        ax.set_yticks([])
        ax.set_zlabel("Cases", labelpad=10)
        ax.set_title("3D investigator queue by risk band", pad=18)
        ax.view_init(elev=24, azim=-55)
        fig.subplots_adjust(left=0.04, right=0.94, bottom=0.10, top=0.90)
        fig.savefig(figures / "risk_queue_summary_3d.svg", bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
