from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Summarize node-enriched validation outputs into a compact review gate."
    )
    parser.add_argument("--results-dir", default="results/node_enriched_validation")
    parser.add_argument(
        "--output", default="results/node_enriched_validation/validation_gate_summary.json"
    )
    args = parser.parse_args()

    results = Path(args.results_dir)
    required = {
        "audit": results / "data_leakage_audit.json",
        "metrics": results / "repeated_split_summary.csv",
        "budget": results / "repeated_budget_summary.csv",
        "permutation": results / "permutation_sanity.csv",
        "importance": results / "feature_importance_seed42.csv",
        "separation": results / "feature_class_separation.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing validation outputs: {missing}")

    audit = json.loads(required["audit"].read_text(encoding="utf-8"))
    metrics = pd.read_csv(required["metrics"])
    budget = pd.read_csv(required["budget"])
    permutation = pd.read_csv(required["permutation"])
    importance = pd.read_csv(required["importance"])
    separation = pd.read_csv(required["separation"])

    rf = metrics.loc[metrics["model"] == "random_forest"].iloc[0]
    rf_perm = permutation.loc[permutation["model"] == "random_forest"].iloc[0]
    rf_budget = budget.loc[
        (budget["model"] == "random_forest") & (budget["review_fraction"] == 0.005)
    ].iloc[0]

    base_rate = float(rf_perm["base_rate"])
    pr_mean = float(rf["average_precision_mean"])
    pr_std = float(rf["average_precision_std"])
    pr_min = float(rf["average_precision_min"])
    roc_mean = float(rf["roc_auc_mean"])

    stability_pass = bool(pr_std / pr_mean < 0.10 and pr_min > base_rate * 10)
    permutation_pass = bool(
        float(rf_perm["average_precision"]) <= base_rate * 2
        and abs(float(rf_perm["roc_auc"]) - 0.5) <= 0.10
    )
    schema_leakage_pass = bool(
        int(audit.get("duplicate_component_ids", 0)) == 0
        and int(audit.get("nonfinite_feature_values", 0)) == 0
        and not audit.get("potential_target_name_columns", [])
    )

    top_importance = importance.sort_values(
        "random_forest_importance", ascending=False
    ).head(15)
    top_separation = separation.sort_values(
        "abs_standardized_mean_difference", ascending=False
    ).head(15)

    top1_importance = float(top_importance.iloc[0]["random_forest_importance"])
    top10_importance = float(top_importance.head(10)["random_forest_importance"].sum())
    dominance_review = {
        "top_feature": str(top_importance.iloc[0]["feature"]),
        "top_feature_importance": top1_importance,
        "top_10_cumulative_importance": top10_importance,
        "manual_review_recommended": bool(top1_importance >= 0.50 or top10_importance >= 0.90),
    }

    summary = {
        "status": "hard_checks_pass" if stability_pass and permutation_pass and schema_leakage_pass else "review_required",
        "hard_checks": {
            "repeated_split_stability_pass": stability_pass,
            "permutation_sanity_pass": permutation_pass,
            "schema_leakage_audit_pass": schema_leakage_pass,
        },
        "random_forest_validation": {
            "average_precision_mean": pr_mean,
            "average_precision_std": pr_std,
            "average_precision_min": pr_min,
            "roc_auc_mean": roc_mean,
            "permuted_average_precision": float(rf_perm["average_precision"]),
            "permuted_roc_auc": float(rf_perm["roc_auc"]),
            "base_rate": base_rate,
            "top_0_5_percent_precision_mean": float(rf_budget["precision_at_budget_mean"]),
            "top_0_5_percent_lift_mean": float(rf_budget["lift_at_budget_mean"]),
            "top_0_5_percent_suspicious_captured_mean": float(rf_budget["suspicious_captured_mean"]),
        },
        "feature_dominance_review": dominance_review,
        "top_random_forest_features": top_importance[["feature", "random_forest_importance"]].to_dict(orient="records"),
        "top_class_separation_features": top_separation[["feature", "standardized_mean_difference", "abs_standardized_mean_difference"]].to_dict(orient="records"),
        "note": "Hard checks assess split stability, shuffled-label collapse, and obvious schema leakage. Because source features are anonymized, feature dominance remains a human-review item rather than an automatic leakage verdict.",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
