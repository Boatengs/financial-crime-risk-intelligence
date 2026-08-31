from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def band(score: float) -> str:
    if score >= 0.90:
        return "critical"
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "elevated"
    return "standard"


def choose_model(scores_path: Path, requested_model: str | None) -> str:
    if requested_model:
        return requested_model

    metrics_path = scores_path.parent / "model_metrics.csv"
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path)
        if "average_precision" in metrics.columns and not metrics.empty:
            best = metrics.sort_values("average_precision", ascending=False).iloc[0]
            return str(best["model"])

    scores = pd.read_csv(scores_path, usecols=["model"])
    models = list(scores["model"].dropna().unique())
    if len(models) == 1:
        return str(models[0])
    raise SystemExit(
        "Could not choose a model automatically. Provide --model or place model_metrics.csv beside the scores file."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="results/model_scored_cases.csv")
    parser.add_argument(
        "--model",
        default=None,
        help="Model to queue. If omitted, selects the highest-average-precision model from model_metrics.csv.",
    )
    parser.add_argument("--output", default="results/investigator_queue.csv")
    args = parser.parse_args()

    scores_path = Path(args.scores)
    if not scores_path.exists():
        raise SystemExit(f"Scores file not found: {scores_path}")

    selected_model = choose_model(scores_path, args.model)
    frame = pd.read_csv(scores_path)
    available = set(frame["model"].dropna().astype(str))
    if selected_model not in available:
        raise SystemExit(
            f"Model {selected_model!r} not found in scores. Available models: {sorted(available)}"
        )

    frame = (
        frame[frame["model"].astype(str) == selected_model]
        .copy()
        .sort_values("risk_score", ascending=False)
    )
    frame.insert(0, "rank", range(1, len(frame) + 1))
    frame["risk_band"] = frame["risk_score"].map(band)
    frame["reason_1"] = "model-prioritized transaction subgraph"
    frame["reason_2"] = "review structural and feature evidence before escalation"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    print(f"Wrote {out} using {selected_model}")


if __name__ == "__main__":
    main()
