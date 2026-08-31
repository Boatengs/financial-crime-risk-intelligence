from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from financial_crime_risk_intelligence.metrics import global_metrics, review_budget_metrics
from financial_crime_risk_intelligence.modeling import fit_baselines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    path = Path(args.input)
    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    train, test = train_test_split(
        frame, test_size=0.20, random_state=42, stratify=frame["label"]
    )
    models, _ = fit_baselines(train, test)

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    metric_rows = []
    budget_rows = []
    queue_rows = []
    for result in models:
        gm = global_metrics(test["label"], result.scores)
        metric_rows.append({"model": result.name, **gm})
        budgets = review_budget_metrics(test["label"], result.scores)
        budgets.insert(0, "model", result.name)
        budget_rows.append(budgets)
        q = test[["component_id"]].copy()
        q["risk_score"] = result.scores
        q["model"] = result.name
        queue_rows.append(q.sort_values("risk_score", ascending=False))

    pd.DataFrame(metric_rows).to_csv(results_dir / "model_metrics.csv", index=False)
    pd.concat(budget_rows, ignore_index=True).to_csv(results_dir / "review_budget_metrics.csv", index=False)
    pd.concat(queue_rows, ignore_index=True).to_csv(results_dir / "model_scored_cases.csv", index=False)
    print(f"Wrote results to {results_dir}")


if __name__ == "__main__":
    main()
