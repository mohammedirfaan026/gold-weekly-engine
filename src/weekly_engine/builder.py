"""
Weekly master research dataset builder.
Synthesizes the core weekly research dataset where each row is a discrete trading week (Friday to Friday),
integrating Gold OHLCV, multi-asset macro weekly changes, COT positioning, ETF flows, and aggregated macro events.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import get_trading_week_id, to_utc_time
from src.weekly_engine.aggregator import WeeklyEventAggregator
from src.normalization.cleaner import DataCleaner


class WeeklyDatasetBuilder:
    """
    Constructs the institutional weekly research dataset for Gold.
    """

    def __init__(self, data_dir: str = "data/weekly"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    @classmethod
    def build_weekly_dataset(
        cls,
        gold_daily_df: pd.DataFrame,
        macro_daily_df: pd.DataFrame,
        events_df: pd.DataFrame,
        cot_df: Optional[pd.DataFrame] = None,
        etf_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Constructs the comprehensive Friday-to-Friday master dataset.
        """
        gold = gold_daily_df.copy()
        gold["timestamp"] = pd.to_datetime(gold["timestamp"], utc=True)
        gold["week_ending"] = gold["timestamp"].apply(get_trading_week_id)

        # 1. Resample Gold to Weekly OHLCV (Friday close)
        weekly_gold = gold.groupby("week_ending").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).reset_index()

        weekly_gold["weekly_return"] = (weekly_gold["close"] / weekly_gold["close"].shift(1)) - 1.0
        weekly_gold["weekly_range"] = (weekly_gold["high"] - weekly_gold["low"]) / weekly_gold["low"]
        weekly_gold["weekly_volatility"] = (weekly_gold["high"] - weekly_gold["low"]) / weekly_gold["close"]

        # 2. Resample Multi-Asset Macro to Weekly Changes
        macro = macro_daily_df.copy()
        time_col = "time" if "time" in macro.columns else "timestamp"
        macro["time"] = pd.to_datetime(macro[time_col], utc=True)
        macro["week_ending"] = macro["time"].apply(get_trading_week_id)

        # Take the last available value of each week
        weekly_macro = macro.groupby("week_ending").last().reset_index()
        if "time" in weekly_macro.columns:
            weekly_macro = weekly_macro.drop(columns=["time"])

        # Compute weekly returns and changes
        if "dxy_close" in weekly_macro.columns:
            weekly_macro["dxy_weekly_return"] = weekly_macro["dxy_close"].pct_change(1)
        if "real_yield_10y" in weekly_macro.columns:
            weekly_macro["real_yield_weekly_change"] = weekly_macro["real_yield_10y"].diff(1)
        if "vix" in weekly_macro.columns:
            weekly_macro["vix_weekly_change"] = weekly_macro["vix"].diff(1)
        if "spx_close" in weekly_macro.columns:
            weekly_macro["spx_weekly_return"] = weekly_macro["spx_close"].pct_change(1)
        if "ndx_close" in weekly_macro.columns:
            weekly_macro["ndx_weekly_return"] = weekly_macro["ndx_close"].pct_change(1)
        if "wti_close" in weekly_macro.columns:
            weekly_macro["wti_weekly_return"] = weekly_macro["wti_close"].pct_change(1)
        if "hy_oas" in weekly_macro.columns:
            weekly_macro["hy_oas_weekly_change"] = weekly_macro["hy_oas"].diff(1)

        # Merge Gold and Macro
        master = pd.merge(weekly_gold, weekly_macro, on="week_ending", how="left")

        # 3. Merge COT positioning (strictly on publication_time <= week_ending)
        if cot_df is not None and not cot_df.empty:
            cot = cot_df.copy()
            cot["pub_week"] = pd.to_datetime(cot["publication_time"], utc=True).apply(get_trading_week_id)
            cot_weekly = cot.groupby("pub_week").last().reset_index()
            cot_cols = [
                "pub_week", "net_spec_position", "net_spec_pct_oi",
                "net_spec_1w_change", "net_spec_4w_change", "net_spec_percentile"
            ]
            cot_sub = cot_weekly[[c for c in cot_cols if c in cot_weekly.columns]]
            master = pd.merge(master, cot_sub, left_on="week_ending", right_on="pub_week", how="left")
            if "pub_week" in master.columns:
                master = master.drop(columns=["pub_week"])

        # 4. Merge ETF flows
        if etf_df is not None and not etf_df.empty:
            etf = etf_df.copy()
            etf["week_ending"] = pd.to_datetime(etf["timestamp"], utc=True).apply(get_trading_week_id)
            etf_weekly = etf.groupby("week_ending").agg({
                "total_gold_etf_flow_m": "sum",
                "etf_flow_percentile": "last",
            }).reset_index().rename(columns={"total_gold_etf_flow_m": "etf_weekly_flow_usd_m"})
            master = pd.merge(master, etf_weekly, on="week_ending", how="left")

        # 5. Aggregate Macro Events for Each Week
        week_endings = [pd.Timestamp(w, tz="UTC") for w in master["week_ending"]]
        events_aggregated = WeeklyEventAggregator.aggregate_all_weeks(events_df, week_endings)
        master = pd.merge(master, events_aggregated, on="week_ending", how="left")

        # 6. Flag Market Shocks (> 2 sigma moves)
        for asset, col in [
            ("gold", "weekly_return"),
            ("dxy", "dxy_weekly_return"),
            ("real_yield", "real_yield_weekly_change"),
            ("vix", "vix_weekly_change"),
            ("spx", "spx_weekly_return"),
            ("wti", "wti_weekly_return"),
        ]:
            if col in master.columns:
                series = master[col].dropna()
                mean = series.mean()
                std = series.std()
                if std > 0:
                    z = (master[col] - mean) / std
                    master[f"shock_2sigma_{asset}"] = (z.abs() >= 2.0).astype(int)
                    master[f"shock_3sigma_{asset}"] = (z.abs() >= 3.0).astype(int)

        # Composite shock flag
        shock_cols = [c for c in master.columns if c.startswith("shock_2sigma_")]
        if shock_cols:
            master["major_market_shock"] = (master[shock_cols].sum(axis=1) > 0).astype(int)
        else:
            master["major_market_shock"] = 0

        # Forward 1-week gold return for research studies
        master["fwd_weekly_gold_return"] = master["weekly_return"].shift(-1)

        return master
