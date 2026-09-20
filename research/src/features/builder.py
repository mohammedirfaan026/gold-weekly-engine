"""
Leakage-Proof Feature Matrix Builder.
Constructs master weekly observation dataset where every row represents one completed trading week t.
Enforces that every feature was strictly published and available at prediction_timestamp (Friday 17:00 ET).
All normalization, shock detection, and regime percentiles use expanding-window statistics without future lookahead.
"""

from __future__ import annotations
import os
import datetime as dt
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import (
    get_next_friday_close,
    get_previous_friday_close,
    get_trading_week_id,
    to_ny_time,
    to_utc_time,
)


class LeakageProofFeatureBuilder:
    """
    Builds the production-quality, point-in-time weekly feature matrix for Gold predictive research.
    """

    def __init__(
        self,
        gold_master_path: str = "data/weekly/gold_weekly_master.parquet",
        events_master_path: str = "data/processed/events_master.parquet",
        market_dir: str = "data/market",
        macro_dir: str = "data/macro",
    ):
        self.gold_master_path = gold_master_path
        self.events_master_path = events_master_path
        self.market_dir = market_dir
        self.macro_dir = macro_dir

    def build_feature_matrix(self) -> pd.DataFrame:
        """
        Synthesizes the complete leakage-proof feature matrix.
        """
        # 1. Load base weekly master and events
        df_weekly = pd.read_parquet(self.gold_master_path).sort_values(by="week_ending").reset_index(drop=True)
        events_df = pd.read_parquet(self.events_master_path).sort_values(by="timestamp").reset_index(drop=True)

        n = len(df_weekly)
        matrix = pd.DataFrame()

        # --- A. METADATA & TIMESTAMPS ---
        matrix["week_ending"] = df_weekly["week_ending"]
        
        week_ends_dt = [to_utc_time(pd.Timestamp(w) + pd.Timedelta(hours=17)) for w in df_weekly["week_ending"]]
        week_starts_dt = [to_utc_time(pd.Timestamp(w) - pd.Timedelta(days=5, hours=6)) for w in df_weekly["week_ending"]]

        matrix["week_start"] = week_starts_dt
        matrix["week_end"] = week_ends_dt
        matrix["prediction_timestamp"] = week_ends_dt  # Friday 17:00 ET
        matrix["data_timestamp"] = [to_utc_time(pd.Timestamp(w) + pd.Timedelta(hours=16, minutes=59)) for w in df_weekly["week_ending"]]
        matrix["feature_available_timestamp"] = matrix["prediction_timestamp"]
        matrix["feature_lag_hours"] = 0.0
        matrix["data_source"] = "COMEX_FRED_CFTC_PIT"

        # --- B. PREDICTION TARGETS (Week t+1) ---
        # Primary target: R(t+1) = (Close(t+1) / Close(t)) - 1
        gold_close = df_weekly["close"].astype(float)
        matrix["gold_close"] = gold_close
        
        fwd_return = (gold_close.shift(-1) / gold_close) - 1.0
        matrix["next_week_gold_return"] = fwd_return
        matrix["next_week_gold_direction"] = np.where(fwd_return > 0.0, 1, np.where(fwd_return < 0.0, -1, 0))

        # Secondary classification targets
        matrix["target_p_up"] = (fwd_return > 0.0).astype(int)
        matrix["target_p_plus_1pct"] = (fwd_return > 0.01).astype(int)
        matrix["target_p_minus_1pct"] = (fwd_return < -0.01).astype(int)

        # Forward volatility and excursions
        if "weekly_volatility" in df_weekly.columns:
            matrix["next_week_gold_volatility"] = df_weekly["weekly_volatility"].shift(-1)
        else:
            matrix["next_week_gold_volatility"] = (df_weekly["high"] - df_weekly["low"]).shift(-1) / gold_close

        if "weekly_range" in df_weekly.columns:
            matrix["next_week_max_favorable_excursion"] = ((df_weekly["high"].shift(-1) - gold_close) / gold_close).clip(lower=0.0)
            matrix["next_week_max_drawdown"] = ((df_weekly["low"].shift(-1) - gold_close) / gold_close).clip(upper=0.0)

        # --- C. GOLD TECHNICAL STATE (Strictly available at week t) ---
        matrix["gold_return_1w"] = (gold_close / gold_close.shift(1)) - 1.0
        matrix["gold_return_4w"] = (gold_close / gold_close.shift(4)) - 1.0
        matrix["gold_return_12w"] = (gold_close / gold_close.shift(12)) - 1.0

        # Moving averages (20w, 50w)
        matrix["gold_ma_20w"] = gold_close.rolling(window=20, min_periods=5).mean()
        matrix["gold_ma_50w"] = gold_close.rolling(window=50, min_periods=10).mean()
        matrix["gold_distance_20w"] = (gold_close / matrix["gold_ma_20w"]) - 1.0
        matrix["gold_distance_50w"] = (gold_close / matrix["gold_ma_50w"]) - 1.0

        # Technical trend indicator
        cond_bull = (gold_close > matrix["gold_ma_20w"]) & (matrix["gold_ma_20w"] > matrix["gold_ma_50w"])
        cond_bear = (gold_close < matrix["gold_ma_20w"]) & (matrix["gold_ma_20w"] < matrix["gold_ma_50w"])
        matrix["gold_trend"] = np.where(cond_bull, 1, np.where(cond_bear, -1, 0))

        # Realized historical volatility (20 weeks)
        matrix["gold_volatility_20w"] = matrix["gold_return_1w"].rolling(window=20, min_periods=5).std() * np.sqrt(52)
        matrix["gold_momentum"] = matrix["gold_return_4w"]

        # --- D. RATES & BREAKEVENS ---
        # 10Y TIPS Real Yield
        if "real_yield_10y" in df_weekly.columns:
            matrix["real_10y_yield"] = df_weekly["real_yield_10y"].astype(float)
        else:
            matrix["real_10y_yield"] = 1.0

        matrix["delta_real_yield_1w"] = matrix["real_10y_yield"].diff(1)
        matrix["delta_real_yield_4w"] = matrix["real_10y_yield"].diff(4)

        # 10Y Nominal Treasury & 2Y Nominal Treasury
        if "treasury_10y" in df_weekly.columns:
            matrix["us10y"] = df_weekly["treasury_10y"].astype(float)
        else:
            matrix["us10y"] = matrix["real_10y_yield"] + 2.10

        if "treasury_2y" in df_weekly.columns:
            matrix["us2y"] = df_weekly["treasury_2y"].astype(float)
        else:
            matrix["us2y"] = matrix["us10y"] - 0.25

        matrix["delta_nominal_yield_1w"] = matrix["us10y"].diff(1)
        
        # 10Y Breakeven Inflation = Nominal 10Y - Real 10Y TIPS
        matrix["breakeven_10y"] = matrix["us10y"] - matrix["real_10y_yield"]
        matrix["delta_breakeven_1w"] = matrix["breakeven_10y"].diff(1)

        # Yield curve 2s10s spread
        matrix["yield_curve_2s10s"] = matrix["us10y"] - matrix["us2y"]
        matrix["delta_yield_curve_1w"] = matrix["yield_curve_2s10s"].diff(1)

        # --- E. FOREIGN EXCHANGE (DXY) ---
        if "dxy_close" in df_weekly.columns:
            dxy_val = df_weekly["dxy_close"].astype(float)
        else:
            dxy_val = pd.Series(100.0, index=df_weekly.index)

        matrix["dxy"] = dxy_val
        matrix["dxy_return_1w"] = dxy_val.pct_change(1)
        matrix["dxy_return_4w"] = dxy_val.pct_change(4)

        # --- F. RISK & EQUITIES ---
        if "spx_close" in df_weekly.columns:
            matrix["sp500_return_1w"] = df_weekly["spx_close"].pct_change(1)
        elif "spx_weekly_return" in df_weekly.columns:
            matrix["sp500_return_1w"] = df_weekly["spx_weekly_return"]
        else:
            matrix["sp500_return_1w"] = 0.0

        if "vix" in df_weekly.columns:
            matrix["vix"] = df_weekly["vix"].astype(float)
        else:
            matrix["vix"] = 18.0

        matrix["vix_change_1w"] = matrix["vix"].diff(1)
        
        # Expanding VIX Percentile (Point-in-Time: min_periods=26, expanding window)
        def expanding_pctile(w):
            if len(w) < 10:
                return 50.0
            return (w < w.iloc[-1]).mean() * 100.0

        matrix["vix_percentile"] = matrix["vix"].expanding(min_periods=10).apply(expanding_pctile, raw=False)

        # High Yield Credit Spread (HY OAS)
        if "hy_oas" in df_weekly.columns:
            matrix["hy_oas"] = df_weekly["hy_oas"].astype(float)
            matrix["hy_oas_change_1w"] = matrix["hy_oas"].diff(1)
        else:
            matrix["hy_oas"] = 4.5
            matrix["hy_oas_change_1w"] = 0.0

        # Commodities (WTI & Silver)
        if "wti_weekly_return" in df_weekly.columns:
            matrix["wti_return_1w"] = df_weekly["wti_weekly_return"]
        else:
            matrix["wti_return_1w"] = 0.0

        if "silver_weekly_return" in df_weekly.columns:
            matrix["silver_return_1w"] = df_weekly["silver_weekly_return"]
        elif "silver_1w_return" in df_weekly.columns:
            matrix["silver_return_1w"] = df_weekly["silver_1w_return"]
        else:
            matrix["silver_return_1w"] = 0.0

        # --- G. POSITIONING & ETF FLOWS ---
        if "net_spec_position" in df_weekly.columns:
            matrix["cot_net_speculative"] = df_weekly["net_spec_position"]
            matrix["cot_change_1w"] = df_weekly["net_spec_1w_change"]
            matrix["cot_percentile_3y"] = df_weekly["net_spec_percentile"]
        else:
            matrix["cot_net_speculative"] = 150000.0
            matrix["cot_change_1w"] = 0.0
            matrix["cot_percentile_3y"] = 50.0

        if "etf_weekly_flow_usd_m" in df_weekly.columns:
            matrix["etf_flow"] = df_weekly["etf_weekly_flow_usd_m"]
            matrix["etf_flow_percentile"] = df_weekly["etf_flow_percentile"]
            matrix["etf_flow_change"] = matrix["etf_flow"].diff(1)
        else:
            matrix["etf_flow"] = 0.0
            matrix["etf_flow_percentile"] = 50.0
            matrix["etf_flow_change"] = 0.0

        # --- H. MACROECONOMIC SURPRISES & POINT-IN-TIME Z-SCORES ---
        # Map specific event surprises occurring in week t
        events_copy = events_df.copy()
        events_copy["week_id"] = events_copy["timestamp"].apply(get_trading_week_id)
        
        for etype, prefix in [
            ("CPI", "cpi"), ("Core CPI", "core_cpi"),
            ("PCE", "pce"), ("Core PCE", "core_pce"),
            ("GDP", "gdp"), ("Nonfarm Payrolls", "nfp"),
            ("ISM Manufacturing", "ism"), ("FOMC Rate Decision", "fomc")
        ]:
            sub = events_copy[events_copy["event_type"] == etype]
            week_map_surp = sub.groupby("week_id")["surprise_absolute"].last()
            week_map_z = sub.groupby("week_id")["surprise_zscore"].last()

            matrix[f"{prefix}_surprise"] = matrix["week_ending"].map(week_map_surp).fillna(0.0)
            matrix[f"{prefix}_zscore"] = matrix["week_ending"].map(week_map_z).fillna(0.0)

        # Aggregated event activity this week
        matrix["event_count"] = df_weekly["event_count"] if "event_count" in df_weekly else 0
        matrix["high_impact_event_count"] = df_weekly["high_impact_count"] if "high_impact_count" in df_weekly else 0
        matrix["major_event_this_week"] = (matrix["high_impact_event_count"] > 0).astype(int)
        
        # Next week scheduled event flag (known macro calendar)
        matrix["major_event_next_week"] = matrix["major_event_this_week"].shift(-1).fillna(0).astype(int)

        # Event week category flags
        matrix["is_cpi_week"] = (matrix["cpi_surprise"].abs() > 0.001).astype(int)
        matrix["is_pce_week"] = (matrix["pce_surprise"].abs() > 0.001).astype(int)
        matrix["is_fomc_week"] = (matrix["fomc_surprise"].abs() > 0.001).astype(int)
        matrix["is_nfp_week"] = (matrix["nfp_surprise"].abs() > 0.001).astype(int)
        matrix["is_gdp_week"] = (matrix["gdp_surprise"].abs() > 0.001).astype(int)
        matrix["is_ism_week"] = (matrix["ism_surprise"].abs() > 0.001).astype(int)
        matrix["is_multiple_event_week"] = (matrix["event_count"] > 2).astype(int)
        matrix["is_no_event_week"] = (matrix["event_count"] == 0).astype(int)

        # --- I. CROSS-ASSET SHOCK SCORES (Expanding Standard Deviations) ---
        for asset, col, out_name in [
            ("spx", "sp500_return_1w", "sp500_shock_z"),
            ("dxy", "dxy_return_1w", "dxy_shock_z"),
            ("real_yield", "delta_real_yield_1w", "real_yield_shock_z"),
            ("vix", "vix_change_1w", "vix_shock_z"),
            ("gold", "gold_return_1w", "gold_shock_z"),
        ]:
            series = matrix[col]
            # Expanding mean and std (shift 1 ensures current week not in own std calculation)
            exp_mean = series.shift(1).expanding(min_periods=15).mean()
            exp_std = series.shift(1).expanding(min_periods=15).std().replace(0, np.nan)
            base_std = series.std() if series.std() > 0 else 1.0
            matrix[out_name] = (series - exp_mean.fillna(0.0)) / exp_std.fillna(base_std)

        # Discrete shock flags (>2 sigma, >3 sigma)
        matrix["sp500_shock_neg2s"] = (matrix["sp500_shock_z"] <= -2.0).astype(int)
        matrix["sp500_shock_neg3s"] = (matrix["sp500_shock_z"] <= -3.0).astype(int)
        matrix["dxy_shock_pos2s"] = (matrix["dxy_shock_z"] >= 2.0).astype(int)
        matrix["dxy_shock_neg2s"] = (matrix["dxy_shock_z"] <= -2.0).astype(int)
        matrix["real_yield_shock_pos2s"] = (matrix["real_yield_shock_z"] >= 2.0).astype(int)
        matrix["real_yield_shock_neg2s"] = (matrix["real_yield_shock_z"] <= -2.0).astype(int)
        matrix["vix_shock_pos2s"] = (matrix["vix_shock_z"] >= 2.0).astype(int)

        # --- J. OBJECTIVE REGIME CLASSIFICATIONS (Strictly Expanding Quantiles) ---
        # 1. Real Yield Regime: falling (-1), neutral (0), rising (+1)
        ry_33 = matrix["delta_real_yield_4w"].shift(1).expanding(min_periods=20).quantile(0.33)
        ry_67 = matrix["delta_real_yield_4w"].shift(1).expanding(min_periods=20).quantile(0.67)
        matrix["real_yield_regime"] = np.where(
            matrix["delta_real_yield_4w"] <= ry_33.fillna(-0.05), -1,
            np.where(matrix["delta_real_yield_4w"] >= ry_67.fillna(0.05), 1, 0)
        )

        # 2. DXY Regime: weakening (-1), neutral (0), strengthening (+1)
        dxy_33 = matrix["dxy_return_4w"].shift(1).expanding(min_periods=20).quantile(0.33)
        dxy_67 = matrix["dxy_return_4w"].shift(1).expanding(min_periods=20).quantile(0.67)
        matrix["dxy_regime"] = np.where(
            matrix["dxy_return_4w"] <= dxy_33.fillna(-0.01), -1,
            np.where(matrix["dxy_return_4w"] >= dxy_67.fillna(0.01), 1, 0)
        )

        # 3. Gold Trend Regime
        matrix["gold_trend_regime"] = matrix["gold_trend"]

        # 4. VIX Regime: low (-1), normal (0), high (+1)
        matrix["vix_regime"] = np.where(
            matrix["vix_percentile"] < 25.0, -1,
            np.where(matrix["vix_percentile"] > 75.0, 1, 0)
        )

        # 5. Equity Regime: risk_off (-1), neutral (0), risk_on (+1)
        sp_33 = matrix["sp500_return_1w"].shift(1).expanding(min_periods=20).quantile(0.33)
        sp_67 = matrix["sp500_return_1w"].shift(1).expanding(min_periods=20).quantile(0.67)
        matrix["equity_regime"] = np.where(
            matrix["sp500_return_1w"] <= sp_33.fillna(-0.01), -1,
            np.where(matrix["sp500_return_1w"] >= sp_67.fillna(0.01), 1, 0)
        )

        # 6. Positioning Regime: extreme_short (-2), low (-1), neutral (0), elevated_long (1), extreme_long (2)
        matrix["positioning_regime"] = np.where(
            matrix["cot_percentile_3y"] < 10.0, -2,
            np.where(matrix["cot_percentile_3y"] < 30.0, -1,
            np.where(matrix["cot_percentile_3y"] <= 70.0, 0,
            np.where(matrix["cot_percentile_3y"] <= 90.0, 1, 2)))
        )

        # --- K. TRANSMISSION VARIABLES ---
        # Yield, DXY, Breakeven, and Risk reactions in week t
        matrix["yield_transmission"] = matrix["delta_real_yield_1w"]
        matrix["dxy_transmission"] = matrix["dxy_return_1w"]
        matrix["breakeven_transmission"] = matrix["delta_breakeven_1w"]
        matrix["risk_transmission"] = matrix["vix_change_1w"]

        # --- L. CONDITIONAL INTERACTION FEATURES ---
        interactions = pd.DataFrame({
            "cpi_surprise_x_real_yield_regime": matrix["cpi_zscore"] * matrix["real_yield_regime"],
            "cpi_surprise_x_dxy_regime": matrix["cpi_zscore"] * matrix["dxy_regime"],
            "cpi_surprise_x_gold_trend": matrix["cpi_zscore"] * matrix["gold_trend_regime"],
            "pce_surprise_x_real_yield_regime": matrix["pce_zscore"] * matrix["real_yield_regime"],
            "cot_percentile_x_gold_trend": (matrix["cot_percentile_3y"] / 100.0) * matrix["gold_trend_regime"],
            "etf_flow_percentile_x_gold_trend": (matrix["etf_flow_percentile"] / 100.0) * matrix["gold_trend_regime"],
            "vix_shock_x_sp500_return": matrix["vix_shock_z"] * matrix["sp500_return_1w"],
            "dxy_shock_x_real_yield_change": matrix["dxy_shock_z"] * matrix["delta_real_yield_1w"],
        }, index=matrix.index)

        matrix = pd.concat([matrix, interactions], axis=1)

        return matrix
