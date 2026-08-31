from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class ModelResult:
    name: str
    model: object
    scores: np.ndarray


def feature_columns(frame: pd.DataFrame):
    excluded = {"component_id", "label"}
    return [c for c in frame.columns if c not in excluded and pd.api.types.is_numeric_dtype(frame[c])]


def fit_baselines(train: pd.DataFrame, test: pd.DataFrame, seed: int = 42):
    cols = feature_columns(train)
    X_train, y_train = train[cols], train["label"].astype(int)
    X_test = test[cols]

    logistic = Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)),
        ]
    )
    forest = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=-1,
    )

    logistic.fit(X_train, y_train)
    forest.fit(X_train, y_train)
    return [
        ModelResult("logistic_regression", logistic, logistic.predict_proba(X_test)[:, 1]),
        ModelResult("random_forest", forest, forest.predict_proba(X_test)[:, 1]),
    ], cols
