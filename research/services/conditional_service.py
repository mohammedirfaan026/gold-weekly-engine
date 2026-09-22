"""
Conditional Reaction & Historical Analogs Engine.
Executes multi-factor conditional research queries across:
- Macro event surprises (e.g. CPI > +1σ)
- Real Yield regimes / direction
- Dollar (DXY) regimes / direction
- Gold technical trend (bullish, bearish, sideways)
- Volatility regime (VIX low/normal/high)
- CFTC Positioning regime (crowded long, neutral, depressed)

Generates empirical conditional return distributions (N, median, mean, positive %, tail probabilities, histogram bins).
"""

from __future__ import annotations

import os
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class ConditionalReactionService:
    """
    Headless research service for conditional historical market distributions.
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
            # Fallback to weekly master
            alt_path = "data/weekly/gold_weekly_master.parquet"
            if os.path.exists(alt_path):
                self._df = pd.read_parquet(alt_path)
            else:
                self._df = pd.DataFrame()
        return self._df

    def query_conditional_distribution(
        self,
        event_filter: Optional[str] = None,          # "cpi", "nfp", "fomc", etc.
        min_surprise_z: Optional[float] = None,       # e.g. 1.0
        max_surprise_z: Optional[float] = None,       # e.g. -1.0
        real_yield_regime: Optional[str] = None,      # "rising", "falling", "neutral"
        dxy_regime: Optional[str] = None,             # "strengthening", "weakening", "neutral"
        gold_trend: Optional[str] = None,             # "bullish", "bearish", "sideways"
        vix_regime: Optional[str] = None,             # "high", "normal", "low"
        positioning_regime: Optional[str] = None,     # "extreme_long", "neutral", "extreme_short"
    ) -> Dict[str, Any]:
        """
        Filters historical weeks matching multi-dimensional conditions and calculates
        empirical forward distribution of next-week gold returns.
        """
        df = self._load_data().copy()
        if df.empty:
            return {"sample_size": 0, "status": "NO_DATA"}

        mask = pd.Series(True, index=df.index)

        # 1. Event Surprise filter
        if event_filter:
            z_col = f"{event_filter.lower()}_zscore"
            if z_col in df.columns:
                if min_surprise_z is not None:
                    mask &= (df[z_col] >= min_surprise_z)
                if max_surprise_z is not None:
                    mask &= (df[z_col] <= max_surprise_z)
            else:
                # Fallback to largest_absolute_surprise or event flag
                flag_col = f"is_{event_filter.lower()}_week"
                if flag_col in df.columns:
                    mask &= (df[flag_col] == 1)

        # 2. Real Yield Regime filter
        if real_yield_regime:
            ry_val = 1 if real_yield_regime == "rising" else (-1 if real_yield_regime == "falling" else 0)
            if "real_yield_regime" in df.columns:
                mask &= (df["real_yield_regime"] == ry_val)
            elif "delta_real_yield_1w" in df.columns:
                if real_yield_regime == "rising":
                    mask &= (df["delta_real_yield_1w"] > 0)
                elif real_yield_regime == "falling":
                    mask &= (df["delta_real_yield_1w"] < 0)

        # 3. DXY Regime filter
        if dxy_regime:
            dxy_val = 1 if dxy_regime == "strengthening" else (-1 if dxy_regime == "weakening" else 0)
            if "dxy_regime" in df.columns:
                mask &= (df["dxy_regime"] == dxy_val)
            elif "dxy_return_1w" in df.columns:
                if dxy_regime == "strengthening":
                    mask &= (df["dxy_return_1w"] > 0)
                elif dxy_regime == "weakening":
                    mask &= (df["dxy_return_1w"] < 0)

        # 4. Gold Trend filter
        if gold_trend:
            trend_val = 1 if gold_trend == "bullish" else (-1 if gold_trend == "bearish" else 0)
            if "gold_trend" in df.columns:
                mask &= (df["gold_trend"] == trend_val)
            elif "regime_gold_trend" in df.columns:
                mask &= (df["regime_gold_trend"].astype(str) == gold_trend)

        # 5. VIX Regime filter
        if vix_regime:
            vix_val = 1 if vix_regime == "high" else (-1 if vix_regime == "low" else 0)
            if "vix_regime" in df.columns:
                mask &= (df["vix_regime"] == vix_val)
            elif "vix" in df.columns:
                if vix_regime == "high":
                    mask &= (df["vix"] > 22.0)
                elif vix_regime == "low":
                    mask &= (df["vix"] < 15.0)

        # 6. Positioning Regime filter
        if positioning_regime:
            if "cot_percentile_3y" in df.columns:
                if positioning_regime == "extreme_long":
                    mask &= (df["cot_percentile_3y"] >= 80.0)
                elif positioning_regime == "extreme_short":
                    mask &= (df["cot_percentile_3y"] <= 20.0)
                elif positioning_regime == "neutral":
                    mask &= (df["cot_percentile_3y"] > 20.0) & (df["cot_percentile_3y"] < 80.0)

        matched_df = df[mask].copy()
        n = len(matched_df)

        ret_col = "next_week_gold_return" if "next_week_gold_return" in matched_df.columns else "fwd_weekly_gold_return"
        if ret_col not in matched_df.columns or n == 0:
            return {
                "matched_count": n,
                "conditions": {
                    "event_filter": event_filter,
                    "min_surprise_z": min_surprise_z,
                    "max_surprise_z": max_surprise_z,
                    "real_yield_regime": real_yield_regime,
                    "dxy_regime": dxy_regime,
                    "gold_trend": gold_trend,
                    "vix_regime": vix_regime,
                    "positioning_regime": positioning_regime,
                },
                "distribution": None,
                "sample_observations": [],
            }

        returns = matched_df[ret_col].dropna() * 100.0  # in percentage points
        valid_n = len(returns)

        if valid_n == 0:
            return {
                "matched_count": 0,
                "distribution": None,
                "sample_observations": [],
            }

        # Distribution statistics
        med_ret = float(returns.median())
        mean_ret = float(returns.mean())
        std_ret = float(returns.std()) if valid_n > 1 else 0.0
        pos_pct = float((returns > 0).mean() * 100.0)
        p_plus_1 = float((returns > 1.0).mean() * 100.0)
        p_minus_1 = float((returns < -1.0).mean() * 100.0)

        # Build histogram bins
        counts, bin_edges = np.histogram(returns, bins=min(12, max(5, valid_n // 3)))
        histogram = []
        for i in range(len(counts)):
            histogram.append({
                "bin_start": round(float(bin_edges[i]), 2),
                "bin_end": round(float(bin_edges[i+1]), 2),
                "count": int(counts[i]),
            })

        # Recent sample observations
        sample_obs = []
        show_cols = ["week_ending", "gold_close", ret_col]
        for c in ["delta_real_yield_1w", "dxy_return_1w", "vix_close", "cot_percentile_3y"]:
            if c in matched_df.columns:
                show_cols.append(c)

        for _, r in matched_df.sort_values(by="week_ending", ascending=False).head(10).iterrows():
            sample_obs.append({
                "week_ending": str(r["week_ending"]),
                "gold_close": float(r.get("gold_close", 0.0)),
                "next_week_return_pct": round(float(r[ret_col] * 100.0), 2) if pd.notna(r.get(ret_col)) else None,
                "delta_real_yield": round(float(r.get("delta_real_yield_1w", 0.0)), 2) if pd.notna(r.get("delta_real_yield_1w")) else None,
                "dxy_return_pct": round(float(r.get("dxy_return_1w", 0.0) * 100.0), 2) if pd.notna(r.get("dxy_return_1w")) else None,
                "vix": round(float(r.get("vix_close", 0.0)), 1) if pd.notna(r.get("vix_close")) else None,
            })

        return {
            "matched_count": valid_n,
            "conditions": {
                "event_filter": event_filter,
                "min_surprise_z": min_surprise_z,
                "max_surprise_z": max_surprise_z,
                "real_yield_regime": real_yield_regime,
                "dxy_regime": dxy_regime,
                "gold_trend": gold_trend,
                "vix_regime": vix_regime,
                "positioning_regime": positioning_regime,
            },
            "distribution": {
                "median_pct": round(med_ret, 2),
                "mean_pct": round(mean_ret, 2),
                "std_pct": round(std_ret, 2),
                "positive_response_pct": round(pos_pct, 1),
                "probability_greater_plus_1pct": round(p_plus_1, 1),
                "probability_less_minus_1pct": round(p_minus_1, 1),
                "histogram": histogram,
            },
            "sample_observations": sample_obs,
        }
