from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from financial_crime_risk_intelligence.metrics import review_budget_metrics
from financial_crime_risk_intelligence.modeling import feature_columns


def calibration_bins(y_true: np.ndarray, scores: np.ndarray, bins: int = 10) -> pd.DataFrame:
    edges = np.linspace(0.0, 1.0, bins + 1)
    work = pd.DataFrame({"y": y_true.astype(int), "score": scores.astype(float)})
    work["bin_id"] = pd.cut(
        work["score"],
        bins=edges,
        labels=False,
        include_lowest=True,
        right=True,
    )
    rows: list[dict] = []
    for bin_id in range(bins):
        group = work[work["bin_id"] == bin_id]
        lower = float(edges[bin_id])
        upper = float(edges[bin_id + 1])
        if group.empty:
            rows.append(
                {
                    "bin_id": bin_id,
                    "lower": lower,
                    "upper": upper,
                    "cases": 0,
                    "observed_rate": np.nan,
                    "mean_score": np.nan,
                    "absolute_gap": np.nan,
                }
            )
            continue
        observed = float(group["y"].mean())
        mean_score = float(group["score"].mean())
        rows.append(
            {
                "bin_id": bin_id,
                "lower": lower,
                "upper": upper,
                "cases": int(len(group)),
                "observed_rate": observed,
                "mean_score": mean_score,
                "absolute_gap": abs(observed - mean_score),
            }
        )
    return pd.DataFrame(rows)


def expected_calibration_error(table: pd.DataFrame) -> float:
    populated = table[table["cases"] > 0].copy()
    total = int(populated["cases"].sum())
    if total == 0:
        return float("nan")
    return float((populated["cases"] * populated["absolute_gap"]).sum() / total)


def metric_row(method: str, y_true: np.ndarray, scores: np.ndarray, bins: int) -> tuple[dict, pd.DataFrame]:
    table = calibration_bins(y_true, scores, bins=bins)
    row = {
        "method": method,
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "brier_score": float(brier_score_loss(y_true, scores)),
        "log_loss": float(log_loss(y_true, np.clip(scores, 1e-12, 1 - 1e-12))),
        "ece": expected_calibration_error(table),
        "base_rate": float(np.mean(y_true)),
    }
    table.insert(0, "method", method)
    return row, table


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare raw, sigmoid-calibrated, and isotonic-calibrated node-only random-forest "
            "scores using a fully held-out test set."
        )
    )
    parser.add_argument(
        "--input", default="data/derived/component_features_node_enriched.parquet"
    )
    parser.add_argument("--results-dir", default="results/node_calibration")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument(
        "--calibration-fraction-of-development",
        type=float,
        default=0.25,
        help=(
            "Fraction of the non-test development sample reserved for calibration. "
            "With test-size 0.20 and this value 0.25, the total split is 60/20/20 train/calibration/test."
        ),
    )
    parser.add_argument("--bins", type=int, default=10)
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Input feature store not found: {source}")

    frame = pd.read_parquet(source) if source.suffix == ".parquet" else pd.read_csv(source)
    required = {"component_id", "label"}
    if required - set(frame.columns):
        raise SystemExit("Expected component_id and label columns")
    if frame["component_id"].duplicated().any():
        raise SystemExit("Duplicate component_id values detected")

    cols = feature_columns(frame)
    X = frame[cols]
    y = frame["label"].astype(int)

    development, test = train_test_split(
        frame,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=y,
    )
    train, calibration = train_test_split(
        development,
        test_size=args.calibration_fraction_of_development,
        random_state=args.seed + 1,
        stratify=development["label"],
    )

    forest = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=args.seed,
        n_jobs=-1,
    )
    forest.fit(train[cols], train["label"].astype(int))

    calibration_raw = forest.predict_proba(calibration[cols])[:, 1]
    test_raw = forest.predict_proba(test[cols])[:, 1]
    calibration_y = calibration["label"].to_numpy(dtype=int)
    test_y = test["label"].to_numpy(dtype=int)

    # Platt-style sigmoid calibration fitted only on the calibration split.
    sigmoid = LogisticRegression(solver="lbfgs", max_iter=2000, random_state=args.seed)
    sigmoid.fit(calibration_raw.reshape(-1, 1), calibration_y)
    test_sigmoid = sigmoid.predict_proba(test_raw.reshape(-1, 1))[:, 1]

    # Non-parametric isotonic calibration, also fitted only on the calibration split.
    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(calibration_raw, calibration_y)
    test_isotonic = np.asarray(isotonic.predict(test_raw), dtype=float)

    score_sets = {
        "raw_random_forest": test_raw,
        "sigmoid": test_sigmoid,
        "isotonic": test_isotonic,
    }

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    metric_rows: list[dict] = []
    bin_tables: list[pd.DataFrame] = []
    budget_tables: list[pd.DataFrame] = []
    for method, scores in score_sets.items():
        row, bins = metric_row(method, test_y, scores, bins=args.bins)
        metric_rows.append(row)
        bin_tables.append(bins)

        budgets = review_budget_metrics(test_y, scores)
        budgets.insert(0, "method", method)
        budget_tables.append(budgets)

    metrics = pd.DataFrame(metric_rows).sort_values("brier_score")
    bins = pd.concat(bin_tables, ignore_index=True)
    budgets = pd.concat(budget_tables, ignore_index=True)

    metrics.to_csv(results_dir / "calibration_method_metrics.csv", index=False)
    bins.to_csv(results_dir / "calibration_bins.csv", index=False)
    budgets.to_csv(results_dir / "calibration_review_budget_metrics.csv", index=False)

    best = metrics.iloc[0]
    raw = metrics[metrics["method"] == "raw_random_forest"].iloc[0]
    summary = {
        "status": "calibration_validation_complete",
        "split": {
            "train_rows": int(len(train)),
            "calibration_rows": int(len(calibration)),
            "test_rows": int(len(test)),
            "train_positive_rows": int(train["label"].sum()),
            "calibration_positive_rows": int(calibration["label"].sum()),
            "test_positive_rows": int(test["label"].sum()),
            "seed": args.seed,
        },
        "feature_count": int(len(cols)),
        "best_brier_method": str(best["method"]),
        "best_brier_score": float(best["brier_score"]),
        "raw_brier_score": float(raw["brier_score"]),
        "raw_ece": float(raw["ece"]),
        "recommendation_rule": (
            "Keep raw random-forest scores for ranking unless calibration materially improves "
            "Brier/ECE without degrading PR-AUC or constrained-review metrics. Treat any calibrated "
            "score as a research probability estimate only after this held-out comparison."
        ),
        "outputs": [
            "calibration_method_metrics.csv",
            "calibration_bins.csv",
            "calibration_review_budget_metrics.csv",
        ],
    }
    (results_dir / "calibration_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Wrote calibration validation outputs to {results_dir}")


if __name__ == "__main__":
    main()
