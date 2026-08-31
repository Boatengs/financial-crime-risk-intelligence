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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="results/model_scored_cases.csv")
    parser.add_argument("--model", default="random_forest")
    parser.add_argument("--output", default="results/investigator_queue.csv")
    args = parser.parse_args()

    frame = pd.read_csv(args.scores)
    frame = frame[frame["model"] == args.model].copy().sort_values("risk_score", ascending=False)
    frame.insert(0, "rank", range(1, len(frame) + 1))
    frame["risk_band"] = frame["risk_score"].map(band)
    frame["reason_1"] = "model-prioritized transaction subgraph"
    frame["reason_2"] = "review structural and feature evidence before escalation"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
