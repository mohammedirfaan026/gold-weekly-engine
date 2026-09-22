"""
Regime Engine Research Service.
Defines, computes, and tracks documented macroeconomic & market regimes:
1. Rates (10Y TIPS Real Yield 4-week change): falling, neutral, rising
2. USD (Dollar Index 4-week return): weakening, neutral, strengthening
3. Volatility (VIX index percentiles): low (<25th), normal (25-75th), high (>75th)
4. Gold Trend (Price vs 20W & 50W moving averages): bullish, bearish, sideways
5. Positioning (CFTC COT Net Speculative percentiles): extreme short (<10th), depressed (<30th), neutral, elevated (>70th), extreme long (>90th)
6. Growth / Credit (HY OAS spread 4-week delta): compressing, stable, widening
"""

from __future__ import annotations

import os
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class RegimeDefinition:
    """Explicit metadata and rules for a regime dimension."""
    def __init__(
        self,
        name: str,
        description: str,
        underlying_metric: str,
        lookback: str,
        threshold_rules: Dict[str, str],
    ):
        self.name = name
        self.description = description
        self.underlying_metric = underlying_metric
        self.lookback = lookback
        self.threshold_rules = threshold_rules

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "underlying_metric": self.underlying_metric,
            "lookback": self.lookback,
            "threshold_rules": self.threshold_rules,
        }


REGIME_DEFINITIONS: Dict[str, RegimeDefinition] = {
    "real_yield": RegimeDefinition(
        name="Real Yield Regime (TIPS 10Y)",
        description="Tracks monetary tightening vs easing impulse through 4-week change in 10-year US TIPS real yield.",
        underlying_metric="delta_real_yield_4w",
        lookback="Rolling 3 years (750 business days) or 150 weeks",
        threshold_rules={
            "falling": "Change <= 33.3rd empirical percentile (monetary easing tailwind for gold)",
            "neutral": "Change between 33.3rd and 66.7th percentiles",
            "rising": "Change >= 66.7th percentile (monetary tightening headwind for gold)",
        },
    ),
    "dxy": RegimeDefinition(
        name="USD Regime (Dollar Index)",
        description="Tracks trade-weighted global dollar strength or weakness across G10 currencies over 4 weeks.",
        underlying_metric="dxy_return_4w",
        lookback="Rolling 3 years (750 business days)",
        threshold_rules={
            "weakening": "Return <= 33.3rd empirical percentile",
            "neutral": "Return between 33.3rd and 66.7th percentiles",
            "strengthening": "Return >= 66.7th percentile",
        },
    ),
    "gold_trend": RegimeDefinition(
        name="Gold Technical Trend",
        description="Dual moving-average institutional trend filter comparing spot close against 20-week and 50-week MAs.",
        underlying_metric="Close vs MA20w vs MA50w",
        lookback="20 weeks / 50 weeks",
        threshold_rules={
            "bullish": "Close > MA20w AND MA20w > MA50w",
            "bearish": "Close < MA20w AND MA20w < MA50w",
            "sideways": "All transitional states where MAs or price are cross-meshed",
        },
    ),
    "vix": RegimeDefinition(
        name="Market Risk / Volatility Regime",
        description="Implied volatility state in US equities reflecting systemic risk appetite vs panic.",
        underlying_metric="Cboe VIX Level",
        lookback="Rolling 3 years (expanding percentile)",
        threshold_rules={
            "low": "VIX < 25th percentile (~13.5) - complacent market",
            "normal": "VIX between 25th and 75th percentiles (~13.5 - 21.0)",
            "high": "VIX > 75th percentile (>21.0) - heightened market stress / safe haven demand",
        },
    ),
    "positioning": RegimeDefinition(
        name="CFTC COT Speculative Positioning",
        description="Institutional positioning cycle from CFTC Commitments of Traders non-commercial net futures contracts.",
        underlying_metric="cot_percentile_3y",
        lookback="Rolling 3 years (156 weeks)",
        threshold_rules={
            "extreme_short": "Net spec percentile < 10% (contrarian bullish exhaustion)",
            "depressed": "Net spec percentile 10% - 30%",
            "neutral": "Net spec percentile 30% - 70%",
            "elevated": "Net spec percentile 70% - 90%",
            "extreme_long": "Net spec percentile > 90% (crowded long, vulnerable to liquidation)",
        },
    ),
}


class RegimeService:
    """
    Headless research service for regime state resolution and historical distribution analysis.
    """

    def __init__(self, weekly_matrix_path: str = "research/features/feature_matrix.parquet"):
        self.weekly_matrix_path = weekly_matrix_path
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        if os.path.exists(self.weekly_matrix_path):
            self._df = pd.read_parquet(self.weekly_matrix_path)
        else:
            alt_path = "data/weekly/gold_weekly_master.parquet"
            if os.path.exists(alt_path):
                self._df = pd.read_parquet(alt_path)
            else:
                self._df = pd.DataFrame()
        return self._df

    def get_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Returns documented definitions and calculation rules for all regimes."""
        return {k: v.to_dict() for k, v in REGIME_DEFINITIONS.items()}

    def get_current_regimes(self) -> Dict[str, Any]:
        """Resolves the latest observed market regime across all dimensions."""
        df = self._load_data()
        if df.empty:
            return {}

        latest = df.sort_values(by="week_ending").iloc[-1]
        
        # 1. Real yield regime
        ry_val = latest.get("real_yield_regime", 0)
        ry_label = "rising" if ry_val == 1 else ("falling" if ry_val == -1 else "neutral")

        # 2. DXY regime
        dxy_val = latest.get("dxy_regime", 0)
        dxy_label = "strengthening" if dxy_val == 1 else ("weakening" if dxy_val == -1 else "neutral")

        # 3. Gold trend
        trend_val = latest.get("gold_trend", 0)
        trend_label = "bullish" if trend_val == 1 else ("bearish" if trend_val == -1 else "sideways")

        # 4. VIX regime
        vix_val = latest.get("vix_regime", 0)
        vix_label = "high" if vix_val == 1 else ("low" if vix_val == -1 else "normal")

        # 5. Positioning regime
        cot_pct = float(latest.get("cot_percentile_3y", 50.0))
        if cot_pct > 90.0:
            pos_label = "extreme_long"
        elif cot_pct > 70.0:
            pos_label = "elevated"
        elif cot_pct < 10.0:
            pos_label = "extreme_short"
        elif cot_pct < 30.0:
            pos_label = "depressed"
        else:
            pos_label = "neutral"

        return {
            "week_ending": str(latest["week_ending"]),
            "prediction_timestamp": str(latest.get("prediction_timestamp")),
            "gold_price": float(latest.get("gold_close", 0.0)),
            "regimes": {
                "real_yield": {
                    "label": ry_label,
                    "value": round(float(latest.get("real_yield_10y", 0.0)), 2),
                    "delta_4w": round(float(latest.get("delta_real_yield_4w", 0.0)), 2),
                },
                "dxy": {
                    "label": dxy_label,
                    "value": round(float(latest.get("dxy_close", 0.0)), 2),
                    "return_4w_pct": round(float(latest.get("dxy_return_4w", 0.0) * 100.0), 2),
                },
                "gold_trend": {
                    "label": trend_label,
                    "ma_20w": round(float(latest.get("gold_ma_20w", 0.0)), 1),
                    "ma_50w": round(float(latest.get("gold_ma_50w", 0.0)), 1),
                },
                "vix": {
                    "label": vix_label,
                    "value": round(float(latest.get("vix_close", 0.0)), 1),
                },
                "positioning": {
                    "label": pos_label,
                    "cot_percentile": round(cot_pct, 1),
                },
            },
            "composite_macro_state": f"{ry_label.upper()} Real Yields + {dxy_label.upper()} Dollar",
        }

    def get_historical_frequencies(self) -> Dict[str, Dict[str, Any]]:
        """Calculates historical frequency distributions for all regime states."""
        df = self._load_data()
        if df.empty:
            return {}

        total = len(df)
        frequencies = {}

        # Real yield
        if "real_yield_regime" in df.columns:
            counts = df["real_yield_regime"].map({1: "rising", 0: "neutral", -1: "falling"}).value_counts()
            frequencies["real_yield"] = {
                k: {"count": int(v), "pct": round(float(v / total * 100.0), 1)} for k, v in counts.items()
            }

        # DXY
        if "dxy_regime" in df.columns:
            counts = df["dxy_regime"].map({1: "strengthening", 0: "neutral", -1: "weakening"}).value_counts()
            frequencies["dxy"] = {
                k: {"count": int(v), "pct": round(float(v / total * 100.0), 1)} for k, v in counts.items()
            }

        # Gold trend
        if "gold_trend" in df.columns:
            counts = df["gold_trend"].map({1: "bullish", 0: "sideways", -1: "bearish"}).value_counts()
            frequencies["gold_trend"] = {
                k: {"count": int(v), "pct": round(float(v / total * 100.0), 1)} for k, v in counts.items()
            }

        # VIX
        if "vix_regime" in df.columns:
            counts = df["vix_regime"].map({1: "high", 0: "normal", -1: "low"}).value_counts()
            frequencies["vix"] = {
                k: {"count": int(v), "pct": round(float(v / total * 100.0), 1)} for k, v in counts.items()
            }

        return frequencies
