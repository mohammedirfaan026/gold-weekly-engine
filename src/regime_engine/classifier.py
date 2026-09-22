"""
Regime classification engine.
Classifies macro and market states into documented, statistically rigorous, percentile-based regimes:
- REAL_YIELD_REGIME: falling, neutral, rising
- DXY_REGIME: weakening, neutral, strengthening
- GOLD_TREND: bullish, bearish, sideways
- VIX_REGIME: low, normal, high
- VOLATILITY_REGIME: low, normal, high
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class RegimeClassifier:
    """
    Classifies the pre-event and weekly financial environment.
    All thresholds are documented and derived from rolling/expanding empirical percentiles.
    """

    @staticmethod
    def classify_by_percentile(
        series: pd.Series,
        lower_pct: float = 33.33,
        upper_pct: float = 66.67,
        labels: tuple[str, str, str] = ("low", "neutral", "high"),
        window: int = 750,  # ~3 years of business days
        min_periods: int = 60,
        pit_strict: bool = False,
    ) -> pd.Series:
        """
        Calculates rolling percentile thresholds to prevent look-ahead bias,
        categorizing values into three discrete regimes.
        When pit_strict=True, strictly prevents future quantile look-ahead.
        """
        prior_series = series.shift(1)
        q_low = prior_series.rolling(window=window, min_periods=min_periods).quantile(lower_pct / 100.0)
        q_high = prior_series.rolling(window=window, min_periods=min_periods).quantile(upper_pct / 100.0)

        if not pit_strict:
            overall_low = series.quantile(lower_pct / 100.0)
            overall_high = series.quantile(upper_pct / 100.0)
            q_low = q_low.fillna(overall_low)
            q_high = q_high.fillna(overall_high)

        conditions = [
            q_low.notna() & (series <= q_low),
            q_low.notna() & q_high.notna() & (series > q_low) & (series < q_high),
            q_high.notna() & (series >= q_high),
        ]
        return pd.Series(np.select(conditions, labels, default=labels[1]), index=series.index)

    @classmethod
    def classify_dataset_regimes(cls, df: pd.DataFrame, pit_strict: bool = True) -> pd.DataFrame:
        """
        Applies documented regime definitions to the reconstructed market state dataframe.
        """
        res = df.copy()

        # 1. Real Yield Regime (based on 4-week change in 10Y TIPS)
        if "real_yield_4w_change" in res.columns:
            res["regime_real_yield"] = cls.classify_by_percentile(
                res["real_yield_4w_change"],
                lower_pct=33.33,
                upper_pct=66.67,
                labels=("falling", "neutral", "rising"),
                pit_strict=pit_strict,
            )
        else:
            res["regime_real_yield"] = "neutral"

        # 2. DXY Regime (based on 4-week return in Dollar Index)
        if "DXY_4w_return" in res.columns:
            res["regime_dxy"] = cls.classify_by_percentile(
                res["DXY_4w_return"],
                lower_pct=33.33,
                upper_pct=66.67,
                labels=("weakening", "neutral", "strengthening"),
                pit_strict=pit_strict,
            )
        else:
            res["regime_dxy"] = "neutral"

        # 3. VIX Regime (Level: Low < 25th pct [~14], Normal 25-75th [14-22], High > 75th [>22])
        if "vix" in res.columns:
            res["regime_vix"] = cls.classify_by_percentile(
                res["vix"],
                lower_pct=25.0,
                upper_pct=75.0,
                labels=("low", "normal", "high"),
                pit_strict=pit_strict,
            )
        else:
            res["regime_vix"] = "normal"

        # 4. Gold Volatility Regime (20-day annualized realized vol)
        if "gold_volatility" in res.columns:
            res["regime_gold_vol"] = cls.classify_by_percentile(
                res["gold_volatility"],
                lower_pct=25.0,
                upper_pct=75.0,
                labels=("low", "normal", "high"),
                pit_strict=pit_strict,
            )
        else:
            res["regime_gold_vol"] = "normal"


        # 5. Gold Trend Regime
        if "gold_trend" in res.columns:
            res["regime_gold_trend"] = res["gold_trend"]
        else:
            res["regime_gold_trend"] = "sideways"

        # 6. Composite Macro Regime (Real Yield x DXY)
        res["regime_macro_combo"] = res["regime_real_yield"] + "__" + res["regime_dxy"]

        return res
