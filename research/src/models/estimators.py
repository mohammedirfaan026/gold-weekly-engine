"""
Machine Learning Estimators for Gold Predictive Research.
Implements:
1. Linear / Penalized Models: Ridge, Lasso, ElasticNet
2. Non-linear / Tree-based Models: Random Forest, HistGradientBoosting
3. Probability Estimators for directional P(R > 0) and tail events P(R > +1%), P(R < -1%)
All scalers and imputers are strictly fit inside the training split.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin
from sklearn.linear_model import RidgeCV, LassoCV, ElasticNetCV, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


class PreprocessedEstimator:
    """Wraps an imputer, scaler, and estimator with strict fit_transform isolation."""
    def __init__(self, estimator: Any, is_tree: bool = False):
        self.estimator = estimator
        self.is_tree = is_tree
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler() if not is_tree else None
        self.feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "PreprocessedEstimator":
        self.feature_names_ = list(X.columns)
        X_mat = self.imputer.fit_transform(X)
        if self.scaler is not None:
            X_mat = self.scaler.fit_transform(X_mat)
        self.estimator.fit(X_mat, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_mat = self.imputer.transform(X[self.feature_names_])
        if self.scaler is not None:
            X_mat = self.scaler.transform(X_mat)
        return self.estimator.predict(X_mat)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_mat = self.imputer.transform(X[self.feature_names_])
        if self.scaler is not None:
            X_mat = self.scaler.transform(X_mat)
        if hasattr(self.estimator, "predict_proba"):
            return self.estimator.predict_proba(X_mat)
        # Fallback for regression models: map expected return to probability using sigmoid
        preds = self.estimator.predict(X_mat)
        scale = np.std(preds) if np.std(preds) > 1e-5 else 0.01
        p1 = 1.0 / (1.0 + np.exp(-preds / scale))
        return np.column_stack([1.0 - p1, p1])

    def get_feature_importances(self) -> pd.Series:
        """Extracts normalized feature importance or standardized coefficient magnitude."""
        if hasattr(self.estimator, "coef_"):
            coef = np.abs(self.estimator.coef_)
            if coef.ndim > 1:
                coef = coef[0]
            total = np.sum(coef) if np.sum(coef) > 0 else 1.0
            return pd.Series(coef / total, index=self.feature_names_)
        elif hasattr(self.estimator, "feature_importances_"):
            fi = self.estimator.feature_importances_
            total = np.sum(fi) if np.sum(fi) > 0 else 1.0
            return pd.Series(fi / total, index=self.feature_names_)
        return pd.Series(0.0, index=self.feature_names_)


def get_ml_models() -> Dict[str, PreprocessedEstimator]:
    """Factory returning all primary candidate ML models."""
    models = {
        "Ridge": PreprocessedEstimator(
            RidgeCV(alphas=np.logspace(-2, 4, 15)),
            is_tree=False,
        ),
        "Lasso": PreprocessedEstimator(
            LassoCV(alphas=np.logspace(-4, 1, 15), max_iter=5000, tol=1e-3, random_state=42),
            is_tree=False,
        ),
        "ElasticNet": PreprocessedEstimator(
            ElasticNetCV(l1_ratio=[0.1, 0.5, 0.7, 0.9], alphas=np.logspace(-4, 1, 10), max_iter=5000, tol=1e-3, random_state=42),
            is_tree=False,
        ),
        "RandomForest": PreprocessedEstimator(
            RandomForestRegressor(n_estimators=100, max_depth=4, min_samples_leaf=5, random_state=42, n_jobs=-1),
            is_tree=True,
        ),
        "HistGradientBoosting": PreprocessedEstimator(
            HistGradientBoostingRegressor(max_iter=100, max_depth=3, min_samples_leaf=10, learning_rate=0.03, random_state=42),
            is_tree=True,
        ),
    }
    return models


class MultiTargetClassifier:
    """
    Simultaneously fits classifiers for:
    - P(R > 0) [Direction]
    - P(R > +1%) [Upper Tail Shock]
    - P(R < -1%) [Lower Tail Shock]
    """
    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.model_up = LogisticRegression(C=0.1, max_iter=1000, random_state=42)
        self.model_plus1 = LogisticRegression(C=0.05, max_iter=1000, random_state=42)
        self.model_minus1 = LogisticRegression(C=0.05, max_iter=1000, random_state=42)
        self.feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y_return: pd.Series) -> "MultiTargetClassifier":
        self.feature_names_ = list(X.columns)
        clean_idx = y_return.dropna().index
        X_clean = X.loc[clean_idx]
        y_clean = y_return.loc[clean_idx]

        X_mat = self.imputer.fit_transform(X_clean)
        X_mat = self.scaler.fit_transform(X_mat)

        y_up = (y_clean > 0.0).astype(int)
        y_plus1 = (y_clean > 0.01).astype(int)
        y_minus1 = (y_clean < -0.01).astype(int)

        self.model_up.fit(X_mat, y_up)
        self.model_plus1.fit(X_mat, y_plus1)
        self.model_minus1.fit(X_mat, y_minus1)
        return self

    def predict_probabilities(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        X_mat = self.imputer.transform(X[self.feature_names_])
        X_mat = self.scaler.transform(X_mat)

        # Probabilities of class 1
        p_up = self.model_up.predict_proba(X_mat)[:, 1] if len(self.model_up.classes_) > 1 else np.full(len(X), 0.5)
        p_plus1 = self.model_plus1.predict_proba(X_mat)[:, 1] if len(self.model_plus1.classes_) > 1 else np.full(len(X), 0.2)
        p_minus1 = self.model_minus1.predict_proba(X_mat)[:, 1] if len(self.model_minus1.classes_) > 1 else np.full(len(X), 0.2)

        return {
            "p_up": p_up,
            "p_plus_1pct": p_plus1,
            "p_minus_1pct": p_minus1,
        }
