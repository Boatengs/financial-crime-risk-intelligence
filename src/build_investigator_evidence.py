from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def evidence_text(feature: str, value: float, percentile: float, zscore: float, importance: float) -> str:
    direction = "above" if zscore >= 0 else "below"
    if percentile >= 0.5:
        tail_text = f"top {(1.0 - percentile) * 100:.1f}%"
    else:
        tail_text = f"bottom {percentile * 100:.1f}%"
    return (
        f"{feature}: value={value:.4g}; {percentile * 100:.1f}th percentile "
        f"({tail_text}); {abs(zscore):.2f} SD {direction} overall mean; "
        f"global RF importance={importance:.2%}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Attach case-specific statistical evidence to the preferred investigator queue. "
            "Evidence describes unusual values among globally important features; it is not a causal explanation."
        )
    )
    parser.add_argument(
        "--queue",
        default="results/node_enriched/investigator_queue.csv",
        help="Capacity-ranked investigator queue built from the preferred node-only random forest.",
    )
    parser.add_argument(
        "--features",
        default="data/derived/component_features_node_enriched.parquet",
        help="Node-enriched component feature store.",
    )
    parser.add_argument(
        "--importance",
        default="results/node_enriched_validation/feature_importance_seed42.csv",
        help="Validated seed-42 global feature-importance table.",
    )
    parser.add_argument(
        "--output",
        default="results/node_enriched/investigator_queue_explained.csv",
    )
    parser.add_argument(
        "--long-output",
        default="results/node_enriched/investigator_evidence_long.csv",
        help="Structured long-form evidence table for analysis and visualization.",
    )
    parser.add_argument("--global-top-n", type=int, default=15)
    parser.add_argument("--evidence-count", type=int, default=3)
    args = parser.parse_args()

    queue_path = Path(args.queue)
    feature_path = Path(args.features)
    importance_path = Path(args.importance)
    for path in (queue_path, feature_path, importance_path):
        if not path.exists():
            raise SystemExit(f"Required input not found: {path}")

    queue = pd.read_csv(queue_path)
    if "component_id" not in queue.columns:
        raise SystemExit("Queue must contain component_id")

    features = pd.read_parquet(feature_path)
    if {"component_id", "label"} - set(features.columns):
        raise SystemExit("Feature store must contain component_id and label")
    if features["component_id"].duplicated().any():
        raise SystemExit("Duplicate component_id values detected in feature store")

    importance = pd.read_csv(importance_path)
    required_importance = {"feature", "random_forest_importance"}
    if required_importance - set(importance.columns):
        raise SystemExit(
            "Importance table must contain feature and random_forest_importance columns"
        )

    importance = (
        importance.dropna(subset=["feature", "random_forest_importance"])
        .sort_values("random_forest_importance", ascending=False)
        .head(args.global_top_n)
        .copy()
    )
    candidate_features = [f for f in importance["feature"].astype(str) if f in features.columns]
    if not candidate_features:
        raise SystemExit("None of the globally important features exist in the feature store")

    imp_map = dict(
        zip(
            importance["feature"].astype(str),
            importance["random_forest_importance"].astype(float),
        )
    )

    numeric = features[candidate_features].astype(float)
    means = numeric.mean(axis=0)
    stds = numeric.std(axis=0, ddof=0).replace(0.0, np.nan)
    percentiles = numeric.rank(method="average", pct=True)
    zscores = (numeric - means) / stds
    zscores = zscores.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    stats = pd.DataFrame({"component_id": features["component_id"].to_numpy()})
    for feature in candidate_features:
        stats[f"__value__{feature}"] = numeric[feature].to_numpy(dtype=float)
        stats[f"__pct__{feature}"] = percentiles[feature].to_numpy(dtype=float)
        stats[f"__z__{feature}"] = zscores[feature].to_numpy(dtype=float)

    merged = queue.merge(stats, on="component_id", how="left", validate="many_to_one")
    missing = int(merged[f"__value__{candidate_features[0]}"].isna().sum())
    if missing:
        raise SystemExit(f"{missing:,} queued components could not be matched to the feature store")

    evidence_columns = [f"evidence_{i}" for i in range(1, args.evidence_count + 1)]
    evidence_rows: list[list[str]] = []
    long_rows: list[dict] = []

    queue_metadata = [
        column
        for column in ("rank", "component_id", "priority_band", "risk_score", "model", "score_type")
        if column in merged.columns
    ]

    for _, row in merged.iterrows():
        candidates: list[tuple[float, str, str, float, float, float, float]] = []
        for feature in candidate_features:
            value = float(row[f"__value__{feature}"])
            pct = float(row[f"__pct__{feature}"])
            z = float(row[f"__z__{feature}"])
            imp = float(imp_map[feature])
            evidence_score = imp * abs(z)
            text = evidence_text(feature, value, pct, z, imp)
            candidates.append((evidence_score, feature, text, value, pct, z, imp))

        candidates.sort(key=lambda item: item[0], reverse=True)
        selected = candidates[: args.evidence_count]
        texts = [item[2] for item in selected]
        texts.extend([""] * (args.evidence_count - len(texts)))
        evidence_rows.append(texts)

        base = {column: row[column] for column in queue_metadata}
        for evidence_rank, item in enumerate(selected, start=1):
            evidence_score, feature, _, value, pct, z, imp = item
            long_rows.append(
                {
                    **base,
                    "evidence_rank": evidence_rank,
                    "feature": feature,
                    "feature_value": value,
                    "percentile": pct,
                    "zscore": z,
                    "absolute_zscore": abs(z),
                    "global_random_forest_importance": imp,
                    "evidence_score": evidence_score,
                }
            )

    evidence_frame = pd.DataFrame(evidence_rows, columns=evidence_columns, index=merged.index)
    output = pd.concat([merged, evidence_frame], axis=1)

    helper_prefixes = ("__value__", "__pct__", "__z__")
    helper_cols = [c for c in output.columns if c.startswith(helper_prefixes)]
    output = output.drop(columns=helper_cols)
    output["evidence_method"] = (
        "top globally important node features ranked by feature_importance x absolute standardized deviation"
    )
    output["evidence_note"] = (
        "Statistical review cues only. Features are anonymized; evidence does not establish causality, "
        "criminal activity, or a legal/regulatory determination."
    )

    out = Path(args.output)
    long_out = Path(args.long_output)
    out.parent.mkdir(parents=True, exist_ok=True)
    long_out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out, index=False)
    pd.DataFrame(long_rows).to_csv(long_out, index=False)

    print(
        f"Wrote {out} with {args.evidence_count} case-specific evidence cues for "
        f"{len(output):,} queued components"
    )
    print(f"Wrote structured evidence table to {long_out}")


if __name__ == "__main__":
    main()
