"""
Tail Risk and Excursion Probability Estimator.
Estimates the probability distribution over weekly directional and tail excursion outcomes:
- P(R > 0) [Calibrated Directional Probability]
- P(R > +1.0%) [Upper Tail Breakout Risk]
- P(R < -1.0%) [Lower Tail Flush Risk]
Conditioned on CFTC speculative positioning, technical extension, and scheduled macro calendar events.
Anchored to empirical base rates to prevent uncalibrated extreme probability distortion.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


class TailRiskEstimator:
    """
    Estimates calibrated probabilities for weekly directional and tail excursion events.
    """

    RISK_FEATURES = [
        "cot_percentile_3y",
        "gold_distance_20w",
        "vix_percentile",
        "major_event_next_week",
        "delta_real_yield_1w",
    ]

    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        # L2-regularized logistic models with shrinkage toward prior
        self.clf_up = LogisticRegression(C=0.1, max_iter=1000, random_state=42)
        self.clf_plus1 = LogisticRegression(C=0.05, max_iter=1000, random_state=42)
        self.clf_minus1 = LogisticRegression(C=0.05, max_iter=1000, random_state=42)
        self.base_rates_: Dict[str, float] = {}

    def fit(self, X: pd.DataFrame, y_return: pd.Series) -> "TailRiskEstimator":
        clean_idx = y_return.dropna().index
        X_sub = X.loc[clean_idx, self.RISK_FEATURES].copy()
        y_vals = y_return.loc[clean_idx].values

        y_up = (y_vals > 0.0).astype(int)
        y_plus1 = (y_vals > 0.01).astype(int)
        y_minus1 = (y_vals < -0.01).astype(int)

        self.base_rates_ = {
            "p_up": float(np.mean(y_up)),
            "p_plus1": float(np.mean(y_plus1)),
            "p_minus1": float(np.mean(y_minus1)),
        }

        X_mat = self.imputer.fit_transform(X_sub)
        X_scaled = self.scaler.fit_transform(X_mat)

        self.clf_up.fit(X_scaled, y_up)
        self.clf_plus1.fit(X_scaled, y_plus1)
        self.clf_minus1.fit(X_scaled, y_minus1)

        return self

    def predict_risk(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates shrinkage-calibrated probabilities for upcoming week.
        """
        X_sub = X[self.RISK_FEATURES].copy()
        X_mat = self.imputer.transform(X_sub)
        X_scaled = self.scaler.transform(X_mat)

        # Raw probabilities
        raw_p_up = self.clf_up.predict_proba(X_scaled)[0, 1] if len(self.clf_up.classes_) > 1 else self.base_rates_.get("p_up", 0.52)
        raw_p_plus1 = self.clf_plus1.predict_proba(X_scaled)[0, 1] if len(self.clf_plus1.classes_) > 1 else self.base_rates_.get("p_plus1", 0.25)
        raw_p_minus1 = self.clf_minus1.predict_proba(X_scaled)[0, 1] if len(self.clf_minus1.classes_) > 1 else self.base_rates_.get("p_minus1", 0.22)

        # Apply Bayesian shrinkage toward empirical base rates to prevent uncalibrated noise
        shrinkage_weight = 0.60  # 60% model estimate, 40% historical prior base rate
        p_up = float(shrinkage_weight * raw_p_up + (1.0 - shrinkage_weight) * self.base_rates_.get("p_up", 0.52))
        p_plus1 = float(shrinkage_weight * raw_p_plus1 + (1.0 - shrinkage_weight) * self.base_rates_.get("p_plus1", 0.25))
        p_minus1 = float(shrinkage_weight * raw_p_minus1 + (1.0 - shrinkage_weight) * self.base_rates_.get("p_minus1", 0.22))

        # Reversal risk flag (asymmetry from crowded positioning)
        cot_val = float(X["cot_percentile_3y"].iloc[0]) if "cot_percentile_3y" in X.columns else 50.0
        crowding_flag = "NEUTRAL"
        if cot_val >= 85.0:
            crowding_flag = "CROWDED_LONG (Elevated Reversal Downside Risk)"
        elif cot_val <= 15.0:
            crowding_flag = "CROWDED_SHORT (Short-Squeeze Upside Risk)"

        return {
            "p_up": round(p_up, 3),
            "p_down": round(1.0 - p_up, 3),
            "p_breakout_plus_1pct": round(p_plus1, 3),
            "p_flush_minus_1pct": round(p_minus1, 3),
            "unconditional_base_rate_p_up": round(self.base_rates_.get("p_up", 0.52), 3),
            "positioning_crowding_status": crowding_flag,
        }
