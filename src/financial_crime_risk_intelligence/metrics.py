from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def review_budget_metrics(y_true, y_score, fractions=(0.005, 0.01, 0.02, 0.05, 0.10)):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    if len(y_true) != len(y_score):
        raise ValueError("y_true and y_score must have the same length")
    if len(y_true) == 0:
        raise ValueError("inputs must be non-empty")

    order = np.argsort(-y_score)
    ranked = y_true[order]
    positives = int(y_true.sum())
    base_rate = positives / len(y_true)
    rows = []
    for fraction in fractions:
        k = max(1, min(len(y_true), math.ceil(len(y_true) * float(fraction))))
        captured = int(ranked[:k].sum())
        precision = captured / k
        recall = captured / positives if positives else 0.0
        lift = precision / base_rate if base_rate else 0.0
        rows.append(
            {
                "review_fraction": float(fraction),
                "reviews": k,
                "suspicious_captured": captured,
                "precision_at_budget": precision,
                "recall_at_budget": recall,
                "lift_at_budget": lift,
            }
        )
    return pd.DataFrame(rows)


def global_metrics(y_true, y_score):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    result = {"average_precision": float(average_precision_score(y_true, y_score))}
    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = float(roc_auc_score(y_true, y_score))
    else:
        result["roc_auc"] = float("nan")
    result["base_rate"] = float(y_true.mean())
    return result
