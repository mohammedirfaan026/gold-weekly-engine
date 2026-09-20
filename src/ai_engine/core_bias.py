"""
Macro Core Bias Estimator.
Low-dimensional regularized Bayesian/Ridge model with economic sign constraints:
- Real yield changes penalize gold (beta <= 0)
- DXY return penalizes gold (beta <= 0)
- Breakeven inflation supports gold (beta >= 0)
- Moving average trend alignment supports gold (beta >= 0)
Produces a bounded Weekly Bias Score in [-1.0, +1.0] and categorical regime label.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


class MacroBiasEstimator:
    """
    Estimates gold weekly directional bias score based strictly on core macro-financial transmission variables.
    """

    CORE_FEATURES = [
        "delta_real_yield_1w",
        "dxy_return_1w",
        "delta_breakeven_1w",
        "gold_distance_20w",
        "hy_oas_change_1w",
        "vix_percentile",
    ]

    def __init__(self, predictive_mode: bool = False):
        self.predictive_mode = predictive_mode
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.model = BayesianRidge(max_iter=1000)
        self.target_mean_ = 0.0
        self.target_std_ = 0.02
        self.feature_names_: List[str] = self.CORE_FEATURES.copy()

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MacroBiasEstimator":
        clean_idx = y.dropna().index
        X_df = X.loc[clean_idx].copy()
        for c in self.CORE_FEATURES:
            if c not in X_df.columns:
                X_df[c] = 0.0
        X_sub = X_df[self.CORE_FEATURES].copy()
        y_sub = y.loc[clean_idx].values

        self.target_mean_ = float(np.mean(y_sub))
        self.target_std_ = float(np.std(y_sub)) if np.std(y_sub) > 1e-5 else 0.02

        X_mat = X_sub.fillna(0.0).values
        X_scaled = self.scaler.fit_transform(X_mat)

        self.model.fit(X_scaled, y_sub)

        # Enforce economic monotonicity bounds on coefficients if not in predictive mode
        if not self.predictive_mode:
            coefs = self.model.coef_.copy()
            coefs[0] = min(0.0, coefs[0])
            coefs[1] = min(0.0, coefs[1])
            coefs[2] = max(0.0, coefs[2])
            coefs[3] = max(0.0, coefs[3])
            self.model.coef_ = coefs

        return self

    def predict_bias(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Computes the weekly bias score in [-1.0, +1.0] and driver attribution for an observation.
        """
        X_df = X.copy()
        for c in self.CORE_FEATURES:
            if c not in X_df.columns:
                X_df[c] = 0.0
        X_sub = X_df[self.CORE_FEATURES].copy()
        X_mat = X_sub.fillna(0.0).values
        X_scaled = self.scaler.transform(X_mat)

        expected_returns = self.model.predict(X_scaled)
        
        # Continuous bias score via tanh: normalized by empirical standard deviation
        # +0.5 std dev above mean -> tanh(0.5) ~ 0.46
        scale = self.target_std_ if self.target_std_ > 1e-4 else 0.02
        z_scores = (expected_returns - self.target_mean_) / scale
        bias_scores = np.tanh(z_scores * 0.75)  # calibrated scaling

        results = []
        for i in range(len(X)):
            score = float(bias_scores[i])
            exp_ret = float(expected_returns[i])
            
            # Categorize bias
            if score >= 0.40:
                category = "STRONG_BULLISH"
            elif score >= 0.15:
                category = "MILD_BULLISH"
            elif score <= -0.40:
                category = "STRONG_BEARISH"
            elif score <= -0.15:
                category = "MILD_BEARISH"
            else:
                category = "NEUTRAL"

            # Driver contributions: feature_scaled * coefficient
            contribs = {}
            for j, f in enumerate(self.CORE_FEATURES):
                contribs[f] = float(X_scaled[i, j] * self.model.coef_[j])

            # Top driver
            sorted_drivers = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)

            results.append({
                "bias_score": round(score, 3),
                "bias_category": category,
                "expected_return": round(exp_ret, 4),
                "drivers": sorted_drivers,
            })

        return results[0] if len(results) == 1 else results
