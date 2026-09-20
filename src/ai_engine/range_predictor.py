"""
Quantile Range and Volatility Corridor Predictor.
Uses Quantile Gradient Boosting to forecast the forward weekly price envelope:
- 10th percentile expected low (support)
- 50th percentile expected center price
- 90th percentile expected high (resistance)
- Expected dollar trading corridor (+/- $X)
Conditioned on realized volatility, expanding VIX percentile, and scheduled macro calendar events.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer


class WeeklyRangePredictor:
    """
    Predicts the expected high-low price corridor and weekly volatility range for gold.
    """

    RANGE_FEATURES = [
        "gold_volatility_20w",
        "vix",
        "vix_percentile",
        "major_event_next_week",
        "gold_distance_20w",
    ]

    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        # Quantile regressors for weekly high percentage excursion (High / Close - 1)
        self.high_q90 = GradientBoostingRegressor(loss="quantile", alpha=0.90, n_estimators=60, max_depth=3, random_state=42)
        self.high_q50 = GradientBoostingRegressor(loss="quantile", alpha=0.50, n_estimators=60, max_depth=3, random_state=42)
        # Quantile regressors for weekly low percentage excursion (1 - Low / Close)
        self.low_q90 = GradientBoostingRegressor(loss="quantile", alpha=0.90, n_estimators=60, max_depth=3, random_state=42)
        self.low_q50 = GradientBoostingRegressor(loss="quantile", alpha=0.50, n_estimators=60, max_depth=3, random_state=42)

    def fit(self, X: pd.DataFrame, df_weekly: pd.DataFrame) -> "WeeklyRangePredictor":
        """
        Fits quantile regressors using historical weekly high and low excursions.
        """
        clean_idx = X.dropna(subset=self.RANGE_FEATURES).index
        X_sub = X.loc[clean_idx, self.RANGE_FEATURES].copy()
        
        gold_close = df_weekly.loc[clean_idx, "close"].astype(float)
        next_high = df_weekly["high"].shift(-1).loc[clean_idx].astype(float)
        next_low = df_weekly["low"].shift(-1).loc[clean_idx].astype(float)

        # Excursion fractions
        y_high = ((next_high - gold_close) / gold_close).clip(lower=0.0).fillna(0.015)
        y_low = ((gold_close - next_low) / gold_close).clip(lower=0.0).fillna(0.015)

        X_mat = self.imputer.fit_transform(X_sub)

        self.high_q90.fit(X_mat, y_high)
        self.high_q50.fit(X_mat, y_high)
        self.low_q90.fit(X_mat, y_low)
        self.low_q50.fit(X_mat, y_low)

        return self

    def predict_range(self, X: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """
        Forecasts expected high, center, low, and range bounds for the upcoming week.
        """
        X_sub = X[self.RANGE_FEATURES].copy()
        X_mat = self.imputer.transform(X_sub)

        high_90 = float(self.high_q90.predict(X_mat)[0])
        high_50 = float(self.high_q50.predict(X_mat)[0])
        low_90 = float(self.low_q90.predict(X_mat)[0])
        low_50 = float(self.low_q50.predict(X_mat)[0])

        # Enforce realistic bounds
        high_90 = max(0.005, high_90)
        low_90 = max(0.005, low_90)

        expected_high = current_price * (1.0 + high_90)
        expected_low = current_price * (1.0 - low_90)
        expected_center = current_price * (1.0 + (high_50 - low_50) / 2.0)
        dollar_range = expected_high - expected_low
        pct_range = (dollar_range / current_price) * 100.0

        return {
            "current_gold_price": round(current_price, 2),
            "expected_high_90pct": round(expected_high, 2),
            "expected_center": round(expected_center, 2),
            "expected_low_10pct": round(expected_low, 2),
            "expected_dollar_range": round(dollar_range, 2),
            "expected_range_pct": round(pct_range, 2),
            "upside_excursion_pct": round(high_90 * 100, 2),
            "downside_excursion_pct": round(low_90 * 100, 2),
        }
