from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split

from financial_crime_risk_intelligence.metrics import global_metrics, review_budget_metrics
from financial_crime_risk_intelligence.modeling import feature_columns, fit_baselines


def parse_seeds(value: str) -> list[int]:
    seeds = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("Provide at least one integer seed")
    return seeds


def class_separation(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    neg = frame.loc[frame["label"] == 0, cols]
    pos = frame.loc[frame["label"] == 1, cols]
    neg_mean = neg.mean(axis=0)
    pos_mean = pos.mean(axis=0)
    pooled_sd = frame[cols].std(axis=0, ddof=0).replace(0, np.nan)
    smd = (pos_mean - neg_mean) / pooled_sd
    result = pd.DataFrame(
        {
            "feature": cols,
            "licit_mean": [float(neg_mean[c]) for c in cols],
            "suspicious_mean": [float(pos_mean[c]) for c in cols],
            "standardized_mean_difference": [float(smd[c]) if pd.notna(smd[c]) else 0.0 for c in cols],
        }
    )
    result["abs_standardized_mean_difference"] = result["standardized_mean_difference"].abs()
    return result.sort_values("abs_standardized_mean_difference", ascending=False)


def calibration_table(y_true: pd.Series, scores: np.ndarray, bins: int = 10) -> pd.DataFrame:
    work = pd.DataFrame({"y": np.asarray(y_true, dtype=int), "score": np.asarray(scores, dtype=float)})
    work["bin"] = pd.cut(work["score"], bins=np.linspace(0.0, 1.0, bins + 1), include_lowest=True)
    grouped = (
        work.groupby("bin", observed=False)
        .agg(cases=("y", "size"), observed_rate=("y", "mean"), mean_score=("score", "mean"))
        .reset_index()
    )
    grouped["bin"] = grouped["bin"].astype(str)
    return grouped


def main():
    parser = argparse.ArgumentParser(
        description="Stress-test node-enriched Elliptic2 baselines across repeated splits and a shuffled-label sanity check."
    )
    parser.add_argument(
        "--input", default="data/derived/component_features_node_enriched.parquet"
    )
    parser.add_argument("--results-dir", default="results/node_enriched_validation")
    parser.add_argument("--seeds", type=parse_seeds, default=parse_seeds("11,23,42,71,101"))
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--permutation-seed", type=int, default=42)
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Input feature store not found: {path}")

    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    if {"component_id", "label"} - set(frame.columns):
        raise SystemExit("Expected component_id and label columns")
    if frame["component_id"].duplicated().any():
        raise SystemExit("Duplicate component_id values detected; stop before model validation")
    if set(frame["label"].dropna().astype(int).unique()) != {0, 1}:
        raise SystemExit("Expected binary labels encoded as 0/1")

    cols = feature_columns(frame)
    nonfinite_count = int((~np.isfinite(frame[cols].to_numpy(dtype=float))).sum())
    if nonfinite_count:
        raise SystemExit(f"Detected {nonfinite_count:,} non-finite feature values")

    results = Path(args.results_dir)
    results.mkdir(parents=True, exist_ok=True)

    audit = {
        "rows": int(len(frame)),
        "positive_rows": int(frame["label"].sum()),
        "negative_rows": int((frame["label"] == 0).sum()),
        "feature_count": int(len(cols)),
        "duplicate_component_ids": int(frame["component_id"].duplicated().sum()),
        "nonfinite_feature_values": nonfinite_count,
        "seeds": args.seeds,
        "test_size": float(args.test_size),
    }

    suspicious_names = [
        c
        for c in cols
        if any(token in c.lower() for token in ("label", "target", "suspicious", "licit", "class"))
    ]
    audit["potential_target_name_columns"] = suspicious_names
    (results / "data_leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    separation = class_separation(frame, cols)
    separation.to_csv(results / "feature_class_separation.csv", index=False)

    metric_rows: list[dict] = []
    budget_rows: list[pd.DataFrame] = []
    seed42_models = None
    seed42_test = None
    seed42_cols = None

    for seed in args.seeds:
        train, test = train_test_split(
            frame,
            test_size=args.test_size,
            random_state=seed,
            stratify=frame["label"],
        )
        models, model_cols = fit_baselines(train, test, seed=seed)
        for result in models:
            gm = global_metrics(test["label"], result.scores)
            gm["brier_score"] = float(brier_score_loss(test["label"], result.scores))
            metric_rows.append({"seed": seed, "model": result.name, **gm})
            budgets = review_budget_metrics(test["label"], result.scores)
            budgets.insert(0, "model", result.name)
            budgets.insert(0, "seed", seed)
            budget_rows.append(budgets)

        if seed == 42:
            seed42_models = models
            seed42_test = test.copy()
            seed42_cols = model_cols

    metrics = pd.DataFrame(metric_rows)
    budgets = pd.concat(budget_rows, ignore_index=True)
    metrics.to_csv(results / "repeated_split_metrics.csv", index=False)
    budgets.to_csv(results / "repeated_budget_metrics.csv", index=False)

    metric_summary = (
        metrics.groupby("model")[["average_precision", "roc_auc", "brier_score"]]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
    )
    metric_summary.columns = [
        "model" if col[0] == "model" else f"{col[0]}_{col[1]}"
        for col in metric_summary.columns.to_flat_index()
    ]
    metric_summary.to_csv(results / "repeated_split_summary.csv", index=False)

    budget_summary = (
        budgets.groupby(["model", "review_fraction"])[
            ["precision_at_budget", "recall_at_budget", "lift_at_budget", "suspicious_captured"]
        ]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
    )
    budget_summary.columns = [
        col[0] if col[1] == "" else f"{col[0]}_{col[1]}"
        for col in budget_summary.columns.to_flat_index()
    ]
    budget_summary.to_csv(results / "repeated_budget_summary.csv", index=False)

    # Shuffled-label sanity check: preserve the real test labels while breaking
    # the feature/label relationship in the training set.
    pseed = args.permutation_seed
    train, test = train_test_split(
        frame,
        test_size=args.test_size,
        random_state=pseed,
        stratify=frame["label"],
    )
    perm_train = train.copy()
    rng = np.random.default_rng(pseed)
    perm_train["label"] = rng.permutation(perm_train["label"].to_numpy())
    perm_models, _ = fit_baselines(perm_train, test, seed=pseed)
    permutation_rows = []
    for result in perm_models:
        permutation_rows.append(
            {"model": result.name, **global_metrics(test["label"], result.scores)}
        )
    pd.DataFrame(permutation_rows).to_csv(results / "permutation_sanity.csv", index=False)

    if seed42_models is not None and seed42_test is not None and seed42_cols is not None:
        importance = pd.DataFrame({"feature": seed42_cols})
        for result in seed42_models:
            if result.name == "random_forest":
                importance["random_forest_importance"] = result.model.feature_importances_
            elif result.name == "logistic_regression":
                coef = result.model.named_steps["model"].coef_[0]
                importance["logistic_abs_coefficient"] = np.abs(coef)

            cal = calibration_table(seed42_test["label"], result.scores)
            cal.insert(0, "model", result.name)
            cal.to_csv(results / f"calibration_{result.name}.csv", index=False)

        sort_col = (
            "random_forest_importance"
            if "random_forest_importance" in importance.columns
            else importance.columns[-1]
        )
        importance.sort_values(sort_col, ascending=False).to_csv(
            results / "feature_importance_seed42.csv", index=False
        )

    summary = {
        "status": "validation_complete",
        "rows": audit["rows"],
        "positive_rows": audit["positive_rows"],
        "feature_count": audit["feature_count"],
        "seeds": args.seeds,
        "outputs": [
            "data_leakage_audit.json",
            "feature_class_separation.csv",
            "repeated_split_metrics.csv",
            "repeated_split_summary.csv",
            "repeated_budget_metrics.csv",
            "repeated_budget_summary.csv",
            "permutation_sanity.csv",
            "feature_importance_seed42.csv",
            "calibration_logistic_regression.csv",
            "calibration_random_forest.csv",
        ],
    }
    (results / "validation_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote validation outputs to {results}")


if __name__ == "__main__":
    main()
