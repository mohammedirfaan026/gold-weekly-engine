"""
Benchmark Baseline Models for Gold Predictive Research.
Implements the 6 reference baselines against which all ML models must be evaluated:
1. Historical Expanding Mean
2. Previous Week's Return (Lag 1 persistence / AR(1))
3. Gold Trend Only (20w / 50w MA sign)
4. Real Yield Change Only (expanding OLS on delta_real_yield_1w)
5. DXY Return Only (expanding OLS on dxy_return_1w)
6. Macro Features Only (Ridge regression on macro event surprises only)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from sklearn.linear_model import Ridge, LinearRegression


class BaseBenchmarkModel:
    """Base class providing uniform fit/predict interface."""
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseBenchmarkModel":
        raise NotImplementedError
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError
        
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


class HistoricalMeanBaseline(BaseBenchmarkModel):
    """
    Baseline 1: Expanding Historical Mean.
    Predicts constant mean and historical positive return frequency from training sample.
    """
    def __init__(self):
        self.mean_return_ = 0.0
        self.prob_up_ = 0.5

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "HistoricalMeanBaseline":
        clean_y = pd.Series(y).dropna()
        if len(clean_y) > 0:
            self.mean_return_ = float(clean_y.mean())
            self.prob_up_ = float((clean_y > 0.0).mean())
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.mean_return_)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        p1 = np.full(len(X), self.prob_up_)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])


class LagReturnBaseline(BaseBenchmarkModel):
    """
    Baseline 2: Previous Week's Return (AR(1) Auto-regressive persistence).
    Fits an OLS slope on gold_return_1w -> next_week_gold_return.
    """
    def __init__(self):
        self.intercept_ = 0.0
        self.coef_ = 0.0
        self.prob_up_base_ = 0.5

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LagReturnBaseline":
        feature = "gold_return_1w"
        clean_df = pd.DataFrame({"x": X[feature], "y": y}).dropna()
        if len(clean_df) > 10 and clean_df["x"].std() > 1e-6:
            lr = LinearRegression().fit(clean_df[["x"]], clean_df["y"])
            self.intercept_ = float(lr.intercept_)
            self.coef_ = float(lr.coef_[0])
        else:
            self.intercept_ = float(clean_df["y"].mean()) if len(clean_df) > 0 else 0.0
            self.coef_ = 0.0
        self.prob_up_base_ = float((clean_df["y"] > 0.0).mean()) if len(clean_df) > 0 else 0.5
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        x_vals = X["gold_return_1w"].fillna(0.0).values
        return self.intercept_ + self.coef_ * x_vals

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        # Approximate probability using logistic sigmoid on normalized forecast
        scale = np.std(preds) if np.std(preds) > 1e-5 else 0.01
        p1 = 1.0 / (1.0 + np.exp(-preds / scale))
        return np.column_stack([1.0 - p1, p1])


class GoldTrendBaseline(BaseBenchmarkModel):
    """
    Baseline 3: Gold Trend Only (20w / 50w MA sign).
    Estimates average return conditional on gold_trend regime (+1, 0, -1).
    """
    def __init__(self):
        self.regime_means_ = {1: 0.002, 0: 0.000, -1: -0.001}
        self.regime_probs_ = {1: 0.55, 0: 0.50, -1: 0.45}
        self.global_mean_ = 0.001

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "GoldTrendBaseline":
        col = "gold_trend" if "gold_trend" in X.columns else "gold_trend_regime"
        clean_df = pd.DataFrame({"trend": X[col], "y": y}).dropna()
        if len(clean_df) > 0:
            self.global_mean_ = float(clean_df["y"].mean())
            for reg in [1, 0, -1]:
                sub = clean_df[clean_df["trend"] == reg]
                if len(sub) >= 5:
                    self.regime_means_[reg] = float(sub["y"].mean())
                    self.regime_probs_[reg] = float((sub["y"] > 0.0).mean())
                else:
                    self.regime_means_[reg] = self.global_mean_
                    self.regime_probs_[reg] = float((clean_df["y"] > 0.0).mean())
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        col = "gold_trend" if "gold_trend" in X.columns else "gold_trend_regime"
        trends = X[col].fillna(0).astype(int)
        return np.array([self.regime_means_.get(t, self.global_mean_) for t in trends])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        col = "gold_trend" if "gold_trend" in X.columns else "gold_trend_regime"
        trends = X[col].fillna(0).astype(int)
        p1 = np.array([self.regime_probs_.get(t, 0.50) for t in trends])
        return np.column_stack([1.0 - p1, p1])


class RealYieldBaseline(BaseBenchmarkModel):
    """
    Baseline 4: Real Yield Change Only.
    Single-variable linear regression on delta_real_yield_1w.
    """
    def __init__(self):
        self.intercept_ = 0.0
        self.coef_ = -0.01  # Economic prior: yields up -> gold down

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RealYieldBaseline":
        col = "delta_real_yield_1w"
        clean_df = pd.DataFrame({"x": X[col], "y": y}).dropna()
        if len(clean_df) > 10 and clean_df["x"].std() > 1e-6:
            lr = LinearRegression().fit(clean_df[["x"]], clean_df["y"])
            self.intercept_ = float(lr.intercept_)
            self.coef_ = float(lr.coef_[0])
        elif len(clean_df) > 0:
            self.intercept_ = float(clean_df["y"].mean())
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        x_vals = X["delta_real_yield_1w"].fillna(0.0).values
        return self.intercept_ + self.coef_ * x_vals

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        scale = np.std(preds) if np.std(preds) > 1e-5 else 0.01
        p1 = 1.0 / (1.0 + np.exp(-preds / scale))
        return np.column_stack([1.0 - p1, p1])


class DXYReturnBaseline(BaseBenchmarkModel):
    """
    Baseline 5: DXY Return Only.
    Single-variable linear regression on dxy_return_1w.
    """
    def __init__(self):
        self.intercept_ = 0.0
        self.coef_ = -0.05  # Economic prior: DXY up -> gold down

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "DXYReturnBaseline":
        col = "dxy_return_1w"
        clean_df = pd.DataFrame({"x": X[col], "y": y}).dropna()
        if len(clean_df) > 10 and clean_df["x"].std() > 1e-6:
            lr = LinearRegression().fit(clean_df[["x"]], clean_df["y"])
            self.intercept_ = float(lr.intercept_)
            self.coef_ = float(lr.coef_[0])
        elif len(clean_df) > 0:
            self.intercept_ = float(clean_df["y"].mean())
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        x_vals = X["dxy_return_1w"].fillna(0.0).values
        return self.intercept_ + self.coef_ * x_vals

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        scale = np.std(preds) if np.std(preds) > 1e-5 else 0.01
        p1 = 1.0 / (1.0 + np.exp(-preds / scale))
        return np.column_stack([1.0 - p1, p1])


class MacroOnlyBaseline(BaseBenchmarkModel):
    """
    Baseline 6: Macro Features Only.
    Regularized Ridge regression on macro surprise features only.
    """
    def __init__(self, alpha: float = 10.0):
        self.alpha = alpha
        self.model = Ridge(alpha=self.alpha)
        self.macro_cols_ = [
            "cpi_surprise", "cpi_zscore", "nfp_surprise", "nfp_zscore",
            "gdp_surprise", "gdp_zscore", "fomc_surprise", "fomc_zscore",
            "ism_surprise", "ism_zscore", "pce_surprise", "pce_zscore"
        ]

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MacroOnlyBaseline":
        cols = [c for c in self.macro_cols_ if c in X.columns]
        clean_X = X[cols].fillna(0.0)
        clean_y = y.loc[clean_X.index].fillna(0.0)
        if len(cols) > 0 and len(clean_X) > 10:
            self.model.fit(clean_X, clean_y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        cols = [c for c in self.macro_cols_ if c in X.columns]
        if not cols:
            return np.zeros(len(X))
        clean_X = X[cols].fillna(0.0)
        return self.model.predict(clean_X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        scale = np.std(preds) if np.std(preds) > 1e-5 else 0.01
        p1 = 1.0 / (1.0 + np.exp(-preds / scale))
        return np.column_stack([1.0 - p1, p1])


def get_all_baselines() -> Dict[str, BaseBenchmarkModel]:
    """Factory returning all 6 standard benchmark instances."""
    return {
        "Baseline 1: Historical Mean": HistoricalMeanBaseline(),
        "Baseline 2: Lag Return (AR1)": LagReturnBaseline(),
        "Baseline 3: Gold Trend Only": GoldTrendBaseline(),
        "Baseline 4: Real Yield Only": RealYieldBaseline(),
        "Baseline 5: DXY Return Only": DXYReturnBaseline(),
        "Baseline 6: Macro Surprises Only": MacroOnlyBaseline(),
    }
