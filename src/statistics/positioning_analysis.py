"""
Positioning and ETF flow predictive analysis engine.
Tests empirical relationships between CFTC COT positioning extremes, ETF flows, and forward weekly gold returns.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.statistics.event_study import EventStudyEngine


class PositioningAnalyzer:
    """
    Evaluates whether positioning and fund flows exhibit momentum or mean-reverting (contrarian) dynamics.
    """

    @classmethod
    def analyze_cot_positioning(
        cls,
        weekly_df: pd.DataFrame,
        fwd_return_col: str = "fwd_weekly_gold_return",
    ) -> pd.DataFrame:
        """
        Partitions weekly data by COT percentile tiers and evaluates forward weekly gold returns.
        """
        df = weekly_df.copy()
        if "net_spec_percentile" not in df.columns:
            return pd.DataFrame()

        conditions = [
            df["net_spec_percentile"] < 10.0,
            (df["net_spec_percentile"] >= 10.0) & (df["net_spec_percentile"] < 30.0),
            (df["net_spec_percentile"] >= 30.0) & (df["net_spec_percentile"] <= 70.0),
            (df["net_spec_percentile"] > 70.0) & (df["net_spec_percentile"] <= 90.0),
            df["net_spec_percentile"] > 90.0,
        ]
        labels = [
            "Extreme Short / Depressed (<10th %)",
            "Low Positioning (10th-30th %)",
            "Neutral Positioning (30th-70th %)",
            "Elevated Longs (70th-90th %)",
            "Crowded / Extreme Long (>90th %)",
        ]
        df["cot_tier"] = np.select(conditions, labels, default="Unknown")

        results = []
        for tier in labels:
            sub = df[df["cot_tier"] == tier]
            if len(sub) == 0:
                continue
            stat_dict = EventStudyEngine.compute_summary_statistics(sub[fwd_return_col].dropna())
            results.append({
                "positioning_tier": tier,
                "sample_size": stat_dict["n"],
                "fwd_median_return": stat_dict["median"],
                "fwd_mean_return": stat_dict["mean"],
                "ci_low": stat_dict["ci_low"],
                "ci_high": stat_dict["ci_high"],
                "positive_rate_pct": stat_dict["positive_rate"],
                "p_value": stat_dict["p_value_wilcoxon"],
            })

        return pd.DataFrame(results)

    @classmethod
    def analyze_etf_flows(
        cls,
        weekly_df: pd.DataFrame,
        fwd_return_col: str = "fwd_weekly_gold_return",
    ) -> pd.DataFrame:
        """
        Partitions weekly data by ETF flow percentiles and evaluates subsequent gold performance.
        """
        df = weekly_df.copy()
        pct_col = "etf_flow_percentile"
        if pct_col not in df.columns:
            return pd.DataFrame()

        conditions = [
            df[pct_col] < 20.0,
            (df[pct_col] >= 20.0) & (df[pct_col] <= 80.0),
            df[pct_col] > 80.0,
        ]
        labels = [
            "Heavy Outflows (<20th %)",
            "Moderate / Neutral Flows (20-80th %)",
            "Heavy Inflows (>80th %)",
        ]
        df["etf_flow_tier"] = np.select(conditions, labels, default="Unknown")

        results = []
        for tier in labels:
            sub = df[df["etf_flow_tier"] == tier]
            if len(sub) == 0:
                continue
            stat_dict = EventStudyEngine.compute_summary_statistics(sub[fwd_return_col].dropna())
            results.append({
                "etf_flow_tier": tier,
                "sample_size": stat_dict["n"],
                "fwd_median_return": stat_dict["median"],
                "fwd_mean_return": stat_dict["mean"],
                "ci_low": stat_dict["ci_low"],
                "ci_high": stat_dict["ci_high"],
                "positive_rate_pct": stat_dict["positive_rate"],
                "p_value": stat_dict["p_value_wilcoxon"],
            })

        return pd.DataFrame(results)
