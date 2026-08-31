from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from financial_crime_risk_intelligence.features import component_structural_features
from financial_crime_risk_intelligence.metrics import global_metrics, review_budget_metrics
from financial_crime_risk_intelligence.modeling import fit_baselines


def fixture_pipeline(project: Path):
    nodes = pd.read_csv(project / "tests/nodes_fixture.csv")
    edges = pd.read_csv(project / "tests/edges_fixture.csv")
    labels = pd.read_csv(project / "tests/components_fixture.csv")
    features = component_structural_features(nodes, edges).merge(labels, on="component_id")

    # Add deterministic synthetic signal columns that mimic anonymized component aggregates.
    features["flow_dispersion"] = features["node_count"] * 0.4 + features["max_degree"] * 0.7
    features["path_complexity"] = features["edge_count"] / features["node_count"].clip(lower=1)

    train, test = train_test_split(features, test_size=0.35, random_state=42, stratify=features["label"])
    models, _ = fit_baselines(train, test)
    results = project / "results"
    results.mkdir(exist_ok=True)
    metric_rows, budget_rows, scored = [], [], []
    for result in models:
        metric_rows.append({"model": result.name, **global_metrics(test["label"], result.scores)})
        b = review_budget_metrics(test["label"], result.scores, fractions=(0.25, 0.5, 1.0))
        b.insert(0, "model", result.name)
        budget_rows.append(b)
        q = test[["component_id"]].copy()
        q["risk_score"] = result.scores
        q["model"] = result.name
        scored.append(q)
    pd.DataFrame(metric_rows).to_csv(results / "model_metrics.csv", index=False)
    pd.concat(budget_rows, ignore_index=True).to_csv(results / "review_budget_metrics.csv", index=False)
    pd.concat(scored, ignore_index=True).to_csv(results / "model_scored_cases.csv", index=False)
    subprocess.run([sys.executable, str(project / "src/build_investigator_queue.py")], check=True, cwd=project)
    subprocess.run([sys.executable, str(project / "src/generate_figures.py")], check=True, cwd=project)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--raw-dir")
    args = parser.parse_args()
    project = Path(args.project).resolve()

    if args.fixture:
        fixture_pipeline(project)
        print("Fixture pipeline complete")
        return
    if not args.raw_dir:
        raise SystemExit("Provide --fixture or --raw-dir data/raw/elliptic2")

    raw = Path(args.raw_dir)
    subprocess.run([sys.executable, str(project / "src/inspect_elliptic2.py"), "--raw-dir", str(raw)], check=True, cwd=project)
    subprocess.run([sys.executable, str(project / "src/build_feature_store.py"), "--raw-dir", str(raw)], check=True, cwd=project)
    subprocess.run([sys.executable, str(project / "src/train_baselines.py"), "--input", "data/derived/component_features.parquet"], check=True, cwd=project)
    subprocess.run([sys.executable, str(project / "src/build_investigator_queue.py")], check=True, cwd=project)
    subprocess.run([sys.executable, str(project / "src/generate_figures.py")], check=True, cwd=project)


if __name__ == "__main__":
    main()
