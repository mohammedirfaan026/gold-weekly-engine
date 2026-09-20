"""
Market state reconstruction engine.
Reconstructs the multi-asset market state immediately prior to every event timestamp T.
Eliminates look-ahead bias by only utilizing information strictly closed/published before T.
"""

from __future__ import annotations
import os
from typing import Dict, Optional, List
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import to_utc_time


class MarketStateReconstructor:
    """
    Computes comprehensive pre-event indicators across Gold, Dollar, Real Yields,
    Equities, Volatility, Commodities, Credit, and Positioning.
    """

    @staticmethod
    def compute_gold_features(gold_daily: pd.DataFrame) -> pd.DataFrame:
        """
        Computes rolling technical, volatility, and trend features on Gold daily series.
        """
        df = gold_daily.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Returns over multiple horizons (business days: 1d, 3d, 5d/1w, 10d/2w, 20d/4w)
        df["gold_return_1d"] = close.pct_change(1)
        df["gold_return_3d"] = close.pct_change(3)
        df["gold_return_1w"] = close.pct_change(5)
        df["gold_return_2w"] = close.pct_change(10)
        df["gold_return_4w"] = close.pct_change(20)

        # Moving averages (20 weeks = 100 days; 50 weeks = 250 days)
        df["gold_ma_20w"] = close.rolling(window=100, min_periods=20).mean()
        df["gold_ma_50w"] = close.rolling(window=250, min_periods=50).mean()
        df["gold_distance_20w_ma"] = (close / df["gold_ma_20w"]) - 1.0
        df["gold_distance_50w_ma"] = (close / df["gold_ma_50w"]) - 1.0

        # Realized Volatility: 20-day annualized std dev of log returns
        log_ret = np.log(close / close.shift(1))
        df["gold_volatility"] = log_ret.rolling(window=20, min_periods=10).std() * np.sqrt(252)

        # Average True Range (ATR 14 days)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["gold_ATR"] = tr.rolling(window=14, min_periods=5).mean()
        df["gold_ATR_pct"] = df["gold_ATR"] / close

        # Drawdown from 52-week (252 days) rolling high
        rolling_high = high.rolling(window=252, min_periods=40).max()
        df["gold_drawdown"] = (close / rolling_high) - 1.0

        # Trend classification
        # Bullish: close > 20w MA and 20w MA > 50w MA
        # Bearish: close < 20w MA and 20w MA < 50w MA
        # Sideways otherwise
        conditions = [
            (close > df["gold_ma_20w"]) & (df["gold_ma_20w"] > df["gold_ma_50w"]),
            (close < df["gold_ma_20w"]) & (df["gold_ma_20w"] < df["gold_ma_50w"]),
        ]
        choices = ["bullish", "bearish"]
        df["gold_trend"] = np.select(conditions, choices, default="sideways")

        return df

    @staticmethod
    def compute_macro_market_features(
        dxy_df: pd.DataFrame,
        real_yield_df: pd.DataFrame,
        vix_df: pd.DataFrame,
        spx_df: pd.DataFrame,
        ndx_df: pd.DataFrame,
        wti_df: pd.DataFrame,
        silver_df: pd.DataFrame,
        copper_df: pd.DataFrame,
        hy_oas_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Computes rolling returns and changes for multi-asset macro features.
        """
        # Standardize daily timestamps
        def prep(df: pd.DataFrame, val_col: str = "close") -> pd.DataFrame:
            res = df.copy()
            time_col = "timestamp" if "timestamp" in res.columns else "observation_time" if "observation_time" in res.columns else "date"
            res["time"] = pd.to_datetime(res[time_col], utc=True)
            res = res.sort_values(by="time").drop_duplicates(subset=["time"]).reset_index(drop=True)
            col = "value" if "value" in res.columns else "close" if "close" in res.columns else val_col
            return res[["time", col]].rename(columns={col: val_col})

        dxy = prep(dxy_df, "dxy_close")
        dxy["DXY_1d_return"] = dxy["dxy_close"].pct_change(1)
        dxy["DXY_1w_return"] = dxy["dxy_close"].pct_change(5)
        dxy["DXY_4w_return"] = dxy["dxy_close"].pct_change(20)
        dxy_ma = dxy["dxy_close"].rolling(50).mean()
        dxy["DXY_trend"] = np.where(dxy["dxy_close"] > dxy_ma, "strengthening", "weakening")

        ry = prep(real_yield_df, "real_yield_10y")
        ry["real_yield_1w_change"] = ry["real_yield_10y"].diff(5)
        ry["real_yield_4w_change"] = ry["real_yield_10y"].diff(20)
        ry["real_yield_trend"] = np.where(ry["real_yield_4w_change"] > 0.05, "rising", np.where(ry["real_yield_4w_change"] < -0.05, "falling", "neutral"))

        vix = prep(vix_df, "vix")
        vix["VIX_1w_change"] = vix["vix"].diff(5)

        spx = prep(spx_df, "spx_close")
        spx["SPX_1w_return"] = spx["spx_close"].pct_change(5)

        ndx = prep(ndx_df, "ndx_close")
        ndx["NDX_1w_return"] = ndx["ndx_close"].pct_change(5)

        wti = prep(wti_df, "wti_close")
        wti["WTI_1w_return"] = wti["wti_close"].pct_change(5)

        silver = prep(silver_df, "silver_close")
        silver["silver_1w_return"] = silver["silver_close"].pct_change(5)

        copper = prep(copper_df, "copper_close")
        copper["copper_1w_return"] = copper["copper_close"].pct_change(5)

        hy = prep(hy_oas_df, "hy_oas")
        hy["HY_OAS_1w_change"] = hy["hy_oas"].diff(5)

        # Merge all into single daily macro snapshot
        macro_daily = dxy
        for sub in [ry, vix, spx, ndx, wti, silver, copper, hy]:
            macro_daily = pd.merge(macro_daily, sub, on="time", how="outer")

        macro_daily = macro_daily.sort_values(by="time").ffill().reset_index(drop=True)
        return macro_daily

    @classmethod
    def reconstruct_all_event_states(
        cls,
        events_df: pd.DataFrame,
        gold_features_df: pd.DataFrame,
        macro_features_df: pd.DataFrame,
        cot_df: Optional[pd.DataFrame] = None,
        etf_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Merges exact pre-event market state snapshot for each event using point-in-time merge_asof.
        """
        events = events_df.copy().sort_values(by="timestamp").reset_index(drop=True)
        events["timestamp"] = pd.to_datetime(events["timestamp"], utc=True)

        # 1. Merge Gold daily features (backward asof, matching latest daily close prior to event)
        gold_feats = gold_features_df.copy().sort_values(by="timestamp").reset_index(drop=True)
        gold_feats["timestamp"] = pd.to_datetime(gold_feats["timestamp"], utc=True)
        gold_cols = [
            "timestamp", "gold_return_1d", "gold_return_3d", "gold_return_1w",
            "gold_return_2w", "gold_return_4w", "gold_distance_20w_ma",
            "gold_distance_50w_ma", "gold_volatility", "gold_ATR",
            "gold_ATR_pct", "gold_drawdown", "gold_trend"
        ]
        gold_subset = gold_feats[[c for c in gold_cols if c in gold_feats.columns]]

        merged = pd.merge_asof(
            events,
            gold_subset,
            on="timestamp",
            direction="backward",
        )

        # 2. Merge Macro market features
        macro_feats = macro_features_df.copy().sort_values(by="time").reset_index(drop=True)
        macro_feats["time"] = pd.to_datetime(macro_feats["time"], utc=True)

        merged = pd.merge_asof(
            merged,
            macro_feats,
            left_on="timestamp",
            right_on="time",
            direction="backward",
        )
        if "time" in merged.columns:
            merged = merged.drop(columns=["time"])

        # 3. Merge COT positioning strictly on publication_time <= event timestamp
        if cot_df is not None and not cot_df.empty:
            cot = cot_df.copy().sort_values(by="publication_time").reset_index(drop=True)
            cot["publication_time"] = pd.to_datetime(cot["publication_time"], utc=True)
            cot_cols = [
                "publication_time", "net_spec_position", "net_spec_pct_oi",
                "net_spec_1w_change", "net_spec_4w_change", "net_spec_percentile"
            ]
            cot_sub = cot[[c for c in cot_cols if c in cot.columns]]

            merged = pd.merge_asof(
                merged,
                cot_sub,
                left_on="timestamp",
                right_on="publication_time",
                direction="backward",
            )
            if "publication_time" in merged.columns:
                merged = merged.drop(columns=["publication_time"])

        # 4. Merge ETF flows
        if etf_df is not None and not etf_df.empty:
            etf = etf_df.copy().sort_values(by="timestamp").reset_index(drop=True)
            etf["timestamp"] = pd.to_datetime(etf["timestamp"], utc=True)
            etf_cols = ["timestamp", "total_gold_etf_flow_m", "etf_flow_direction", "etf_flow_percentile"]
            etf_sub = etf[[c for c in etf_cols if c in etf.columns]]

            merged = pd.merge_asof(
                merged,
                etf_sub,
                on="timestamp",
                direction="backward",
            )

        return merged
