"""
Market shock identification and forward drift engine.
Analyzes gold's subsequent 1-week response to large external market shocks (>2σ and >3σ moves)
in DXY, Real Yields, VIX, S&P 500, WTI Crude, and Gold itself.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from src.statistics.event_study import EventStudyEngine


class MarketShockAnalyzer:
    """
    Quantifies subsequent weekly gold returns following non-announcement macroeconomic shocks.
    """

    SHOCK_CONFIG = [
        {"asset": "dxy", "col": "dxy_weekly_return", "threshold": 2.0, "name": "DXY Surge (>+2 sigma)", "sign": "pos"},
        {"asset": "dxy", "col": "dxy_weekly_return", "threshold": -2.0, "name": "DXY Collapse (<-2 sigma)", "sign": "neg"},
        {"asset": "real_yield", "col": "real_yield_weekly_change", "threshold": 2.0, "name": "Real Yield Spike (>+2 sigma)", "sign": "pos"},
        {"asset": "real_yield", "col": "real_yield_weekly_change", "threshold": -2.0, "name": "Real Yield Collapse (<-2 sigma)", "sign": "neg"},
        {"asset": "vix", "col": "vix_weekly_change", "threshold": 2.0, "name": "VIX Panic Spike (>+2 sigma)", "sign": "pos"},
        {"asset": "spx", "col": "spx_weekly_return", "threshold": -3.0, "name": "S&P 500 Severe Selloff (<-3 sigma)", "sign": "neg"},
        {"asset": "wti", "col": "wti_weekly_return", "threshold": 3.0, "name": "WTI Oil Shock (>+3 sigma)", "sign": "pos"},
        {"asset": "gold", "col": "weekly_return", "threshold": 2.0, "name": "Gold Breakout (>+2 sigma)", "sign": "pos"},
        {"asset": "gold", "col": "weekly_return", "threshold": -2.0, "name": "Gold Flush (<-2 sigma)", "sign": "neg"},
    ]

    @classmethod
    def analyze_shocks(
        cls,
        weekly_df: pd.DataFrame,
        fwd_return_col: str = "fwd_weekly_gold_return",
    ) -> pd.DataFrame:
        """
        Scans weekly master dataset for extreme moves and computes subsequent forward 1-week gold performance.
        """
        df = weekly_df.copy()
        if fwd_return_col not in df.columns:
            df[fwd_return_col] = df["weekly_return"].shift(-1)

        results = []
        for cfg in cls.SHOCK_CONFIG:
            col = cfg["col"]
            if col not in df.columns:
                continue

            series = df[col].dropna()
            mean = series.mean()
            std = series.std()
            if std == 0:
                continue

            z = (df[col] - mean) / std

            if cfg["sign"] == "pos":
                mask = z >= abs(cfg["threshold"])
            else:
                mask = z <= -abs(cfg["threshold"])

            shock_weeks = df[mask]
            fwd_returns = shock_weeks[fwd_return_col].dropna()

            if len(fwd_returns) == 0:
                continue

            stat_dict = EventStudyEngine.compute_summary_statistics(fwd_returns)
            results.append({
                "shock_name": cfg["name"],
                "asset": cfg["asset"],
                "threshold_sigma": cfg["threshold"],
                "n_shocks": stat_dict["n"],
                "fwd_median_return": stat_dict["median"],
                "fwd_mean_return": stat_dict["mean"],
                "fwd_trimmed_mean": stat_dict["trimmed_mean_10"],
                "ci_low": stat_dict["ci_low"],
                "ci_high": stat_dict["ci_high"],
                "positive_rate_pct": stat_dict["positive_rate"],
                "p_value": stat_dict["p_value_wilcoxon"],
            })

        return pd.DataFrame(results)
