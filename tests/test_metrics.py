import numpy as np

from financial_crime_risk_intelligence.metrics import review_budget_metrics


def test_review_budget_lift_is_high_when_positives_rank_first():
    y = np.array([1, 1, 0, 0, 0, 0])
    score = np.array([0.99, 0.90, 0.4, 0.3, 0.2, 0.1])
    result = review_budget_metrics(y, score, fractions=(1 / 3,))
    row = result.iloc[0]
    assert row["precision_at_budget"] == 1.0
    assert row["recall_at_budget"] == 1.0
    assert row["lift_at_budget"] > 1.0
