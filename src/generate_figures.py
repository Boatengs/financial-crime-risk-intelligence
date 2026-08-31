from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
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
        fig, ax = plt.subplots(figsize=(8, 5))
        for model, group in df.groupby("model"):
            ax.plot(group["review_fraction"] * 100, group["lift_at_budget"], marker="o", label=model)
        ax.set_xlabel("Review budget (% of cases)")
        ax.set_ylabel("Lift vs random review")
        ax.set_title("Investigation lift by review budget")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures / "review_budget_curve.svg")
        plt.close(fig)

    queue_path = results / "investigator_queue.csv"
    if queue_path.exists():
        q = pd.read_csv(queue_path)
        counts = q["risk_band"].value_counts().reindex(["critical", "high", "elevated", "standard"], fill_value=0)
        fig, ax = plt.subplots(figsize=(7, 4))
        counts.plot(kind="bar", ax=ax)
        ax.set_ylabel("Cases")
        ax.set_title("Investigator queue by risk band")
        fig.tight_layout()
        fig.savefig(figures / "risk_queue_summary.svg")
        plt.close(fig)


if __name__ == "__main__":
    main()
