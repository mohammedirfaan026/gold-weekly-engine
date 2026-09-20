"""
Feature dictionary generator.
Generates comprehensive metadata and lineage for every feature in the research matrix:
data source, publication lag, point-in-time vintage status (EXACT_PIT vs POTENTIAL_REVISION_BIAS),
transformation formula, and economic rationale.
"""

from __future__ import annotations
import os
import pandas as pd


class FeatureDictionaryGenerator:
    """Creates the formal quantitative feature dictionary for auditability and lineage."""

    def __init__(self, feature_matrix: Optional[pd.DataFrame] = None):
        self.feature_matrix = feature_matrix

    @staticmethod
    def generate_dictionary() -> pd.DataFrame:
        features_meta = [
            # Targets
            {"feature_name": "next_week_gold_return", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t+1) / Close(t) - 1.0", "description": "Primary research prediction target: Gold return over week t+1."},
            {"feature_name": "next_week_gold_direction", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "sign(next_week_gold_return)", "description": "Directional return indicator (+1, -1, 0)."},
            {"feature_name": "target_p_up", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "1 if return > 0 else 0", "description": "Binary flag: Next week positive return."},
            {"feature_name": "target_p_plus_1pct", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "1 if return > 0.01 else 0", "description": "Binary flag: Next week upside breakout > +1.0%."},
            {"feature_name": "target_p_minus_1pct", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "1 if return < -0.01 else 0", "description": "Binary flag: Next week downside selloff < -1.0%."},
            {"feature_name": "next_week_gold_volatility", "category": "TARGET", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "Next Friday 17:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(High(t+1) - Low(t+1)) / Close(t)", "description": "Next week realized weekly high-low range volatility."},

            # Gold Technical State
            {"feature_name": "gold_return_1w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t) / Close(t-1) - 1.0", "description": "Gold return during week t."},
            {"feature_name": "gold_return_4w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t) / Close(t-4) - 1.0", "description": "Gold 4-week rolling return."},
            {"feature_name": "gold_return_12w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t) / Close(t-12) - 1.0", "description": "Gold quarterly rolling return."},
            {"feature_name": "gold_distance_20w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t) / MA_20w(t) - 1.0", "description": "Distance to 20-week moving average."},
            {"feature_name": "gold_distance_50w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Close(t) / MA_50w(t) - 1.0", "description": "Distance to 50-week moving average."},
            {"feature_name": "gold_trend", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "sign(Close - MA20w) if sign(MA20w - MA50w) matches else 0", "description": "Trend alignment (+1 Bullish, -1 Bearish, 0 Sideways)."},
            {"feature_name": "gold_volatility_20w", "category": "GOLD_TECHNICAL", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours (Fri 17:00 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "std(ret_1w, 20w) * sqrt(52)", "description": "20-week annualized realized volatility."},

            # Rates & Breakevens
            {"feature_name": "real_10y_yield", "category": "RATES_BREAKEVENS", "data_source": "FRED (DFII10)",
             "observation_frequency": "Daily", "publication_lag": "12 hours (Fri close pub Sat AM)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of 10Y TIPS", "description": "10-Year TIPS Real Yield level."},
            {"feature_name": "delta_real_yield_1w", "category": "RATES_BREAKEVENS", "data_source": "FRED (DFII10)",
             "observation_frequency": "Weekly", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "TIPS(t) - TIPS(t-1)", "description": "1-week change in 10-Year TIPS real yield."},
            {"feature_name": "delta_real_yield_4w", "category": "RATES_BREAKEVENS", "data_source": "FRED (DFII10)",
             "observation_frequency": "Weekly", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "TIPS(t) - TIPS(t-4)", "description": "4-week change in 10-Year TIPS real yield."},
            {"feature_name": "us10y", "category": "RATES_BREAKEVENS", "data_source": "FRED (DGS10)",
             "observation_frequency": "Daily", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of 10Y Treasury", "description": "10-Year US Nominal Treasury Yield."},
            {"feature_name": "us2y", "category": "RATES_BREAKEVENS", "data_source": "FRED (DGS2)",
             "observation_frequency": "Daily", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of 2Y Treasury", "description": "2-Year US Nominal Treasury Yield."},
            {"feature_name": "breakeven_10y", "category": "RATES_BREAKEVENS", "data_source": "FRED",
             "observation_frequency": "Daily", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "us10y - real_10y_yield", "description": "10-Year Breakeven Inflation Rate."},
            {"feature_name": "delta_breakeven_1w", "category": "RATES_BREAKEVENS", "data_source": "FRED",
             "observation_frequency": "Weekly", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "breakeven(t) - breakeven(t-1)", "description": "1-week change in 10Y Breakeven Inflation."},
            {"feature_name": "yield_curve_2s10s", "category": "RATES_BREAKEVENS", "data_source": "FRED",
             "observation_frequency": "Daily", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "us10y - us2y", "description": "2s10s Treasury yield curve slope."},

            # FX
            {"feature_name": "dxy", "category": "FX", "data_source": "ICE / Yahoo",
             "observation_frequency": "Daily", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of US Dollar Index", "description": "US Dollar Index level."},
            {"feature_name": "dxy_return_1w", "category": "FX", "data_source": "ICE / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "DXY(t) / DXY(t-1) - 1.0", "description": "1-week return in US Dollar Index."},
            {"feature_name": "dxy_return_4w", "category": "FX", "data_source": "ICE / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "DXY(t) / DXY(t-4) - 1.0", "description": "4-week return in US Dollar Index."},

            # Risk & Equities
            {"feature_name": "sp500_return_1w", "category": "RISK_EQUITIES", "data_source": "S&P / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "SPX(t) / SPX(t-1) - 1.0", "description": "S&P 500 1-week return."},
            {"feature_name": "vix", "category": "RISK_EQUITIES", "data_source": "Cboe / Yahoo",
             "observation_frequency": "Daily", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of VIX", "description": "Cboe Volatility Index level."},
            {"feature_name": "vix_change_1w", "category": "RISK_EQUITIES", "data_source": "Cboe / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "VIX(t) - VIX(t-1)", "description": "1-week change in VIX level."},
            {"feature_name": "vix_percentile", "category": "RISK_EQUITIES", "data_source": "Cboe / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "expanding_quantile(VIX)", "description": "Point-in-time expanding percentile of VIX."},
            {"feature_name": "hy_oas", "category": "RISK_EQUITIES", "data_source": "FRED (BAMLH0A0HYM2)",
             "observation_frequency": "Daily", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Level of US High Yield Option-Adjusted Spread", "description": "US High Yield Credit Spread."},

            # Positioning & Flows
            {"feature_name": "cot_net_speculative", "category": "POSITIONING", "data_source": "CFTC",
             "observation_frequency": "Weekly (Tuesday obs)", "publication_lag": "72 hours (Published Friday 15:30 ET)", "vintage_status": "EXACT_PIT",
             "transformation_formula": "NonComm_Long - NonComm_Short", "description": "CFTC COMEX Gold net speculative contracts."},
            {"feature_name": "cot_percentile_3y", "category": "POSITIONING", "data_source": "CFTC",
             "observation_frequency": "Weekly", "publication_lag": "72 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "expanding_quantile(cot_net_spec)", "description": "Expanding percentile of COT net speculative positioning."},
            {"feature_name": "cot_change_1w", "category": "POSITIONING", "data_source": "CFTC",
             "observation_frequency": "Weekly", "publication_lag": "72 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "cot_net_spec(t) - cot_net_spec(t-1)", "description": "1-week change in COT net speculative contracts."},
            {"feature_name": "etf_flow", "category": "POSITIONING", "data_source": "GLD / IAU",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Sum of GLD + IAU estimated net weekly flows ($M)", "description": "Physical Gold ETF weekly fund flows."},
            {"feature_name": "etf_flow_percentile", "category": "POSITIONING", "data_source": "GLD / IAU",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "expanding_quantile(etf_flow)", "description": "Expanding percentile of weekly ETF flows."},

            # Macroeconomic Surprises (Point-in-Time expanding Z-score)
            {"feature_name": "cpi_surprise", "category": "MACRO_SURPRISE", "data_source": "BLS",
             "observation_frequency": "Monthly", "publication_lag": "Published 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "Actual - Consensus", "description": "CPI headline monthly surprise."},
            {"feature_name": "cpi_zscore", "category": "MACRO_SURPRISE", "data_source": "BLS",
             "observation_frequency": "Monthly", "publication_lag": "Published 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "surprise / expanding_std(prior_surprises)", "description": "CPI standardized surprise Z-score."},
            {"feature_name": "pce_surprise", "category": "MACRO_SURPRISE", "data_source": "BEA",
             "observation_frequency": "Monthly", "publication_lag": "Published 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "Actual - Consensus", "description": "PCE headline monthly surprise."},
            {"feature_name": "pce_zscore", "category": "MACRO_SURPRISE", "data_source": "BEA",
             "observation_frequency": "Monthly", "publication_lag": "Published 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "surprise / expanding_std(prior_surprises)", "description": "PCE standardized surprise Z-score."},
            {"feature_name": "nfp_surprise", "category": "MACRO_SURPRISE", "data_source": "BLS",
             "observation_frequency": "Monthly", "publication_lag": "Published First Fri 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "Actual - Consensus (k)", "description": "Nonfarm Payrolls employment surprise."},
            {"feature_name": "nfp_zscore", "category": "MACRO_SURPRISE", "data_source": "BLS",
             "observation_frequency": "Monthly", "publication_lag": "Published First Fri 08:30 ET", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "surprise / expanding_std(prior_surprises)", "description": "Nonfarm Payrolls standardized surprise Z-score."},
            {"feature_name": "fomc_surprise", "category": "MACRO_SURPRISE", "data_source": "Federal Reserve",
             "observation_frequency": "8 meetings/year", "publication_lag": "Published Wed 14:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Actual - Consensus Rate", "description": "FOMC rate decision surprise."},
            {"feature_name": "ism_surprise", "category": "MACRO_SURPRISE", "data_source": "ISM",
             "observation_frequency": "Monthly", "publication_lag": "Published 10:00 ET", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Actual - Consensus", "description": "ISM Manufacturing PMI surprise."},

            # Regimes (Point-in-Time Expanding Quantiles)
            {"feature_name": "real_yield_regime", "category": "REGIME", "data_source": "FRED",
             "observation_frequency": "Weekly", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "-1 if d_TIPS_4w <= Q33 else (+1 if >= Q67 else 0)", "description": "Real Yield Regime (-1 Falling, 0 Neutral, +1 Rising)."},
            {"feature_name": "dxy_regime", "category": "REGIME", "data_source": "ICE / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "-1 if dxy_ret_4w <= Q33 else (+1 if >= Q67 else 0)", "description": "DXY Regime (-1 Weakening, 0 Neutral, +1 Strengthening)."},
            {"feature_name": "gold_trend_regime", "category": "REGIME", "data_source": "COMEX/LBMA",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "gold_trend", "description": "Gold Trend Regime (-1 Bearish, 0 Sideways, +1 Bullish)."},
            {"feature_name": "vix_regime", "category": "REGIME", "data_source": "Cboe / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "-1 if vix_pct < 25 else (+1 if > 75 else 0)", "description": "VIX Volatility Regime (-1 Low, 0 Normal, +1 High)."},
            {"feature_name": "equity_regime", "category": "REGIME", "data_source": "S&P / Yahoo",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "-1 if SPX_1w <= Q33 else (+1 if >= Q67 else 0)", "description": "Equity Market Regime (-1 Risk Off, 0 Neutral, +1 Risk On)."},
            {"feature_name": "positioning_regime", "category": "REGIME", "data_source": "CFTC",
             "observation_frequency": "Weekly", "publication_lag": "72 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "Tiers from -2 (Extreme Short) to +2 (Extreme Long)", "description": "CFTC COT Speculative Positioning Regime."},

            # Cross-Asset Shocks (Point-in-Time Expanding Std Dev)
            {"feature_name": "sp500_shock_z", "category": "CROSS_ASSET_SHOCK", "data_source": "S&P",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(SPX_ret_1w - exp_mean) / exp_std", "description": "Standardized expanding shock score for S&P 500."},
            {"feature_name": "dxy_shock_z", "category": "CROSS_ASSET_SHOCK", "data_source": "ICE",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(DXY_ret_1w - exp_mean) / exp_std", "description": "Standardized expanding shock score for US Dollar Index."},
            {"feature_name": "real_yield_shock_z", "category": "CROSS_ASSET_SHOCK", "data_source": "FRED",
             "observation_frequency": "Weekly", "publication_lag": "12 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(d_TIPS_1w - exp_mean) / exp_std", "description": "Standardized expanding shock score for 10Y TIPS yield."},
            {"feature_name": "vix_shock_z", "category": "CROSS_ASSET_SHOCK", "data_source": "Cboe",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(d_VIX_1w - exp_mean) / exp_std", "description": "Standardized expanding shock score for VIX."},

            # Interactions
            {"feature_name": "cpi_surprise_x_real_yield_regime", "category": "INTERACTION", "data_source": "Engine",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "cpi_zscore * real_yield_regime", "description": "CPI surprise conditioned on Real Yield regime."},
            {"feature_name": "cpi_surprise_x_dxy_regime", "category": "INTERACTION", "data_source": "Engine",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "POTENTIAL_REVISION_BIAS",
             "transformation_formula": "cpi_zscore * dxy_regime", "description": "CPI surprise conditioned on DXY regime."},
            {"feature_name": "cot_percentile_x_gold_trend", "category": "INTERACTION", "data_source": "Engine",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "(cot_pct / 100) * gold_trend", "description": "COT Positioning conditioned on Gold Trend."},
            {"feature_name": "vix_shock_x_sp500_return", "category": "INTERACTION", "data_source": "Engine",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "vix_shock_z * sp500_return_1w", "description": "VIX Panic shock interaction with equity selloff."},
            {"feature_name": "dxy_shock_x_real_yield_change", "category": "INTERACTION", "data_source": "Engine",
             "observation_frequency": "Weekly", "publication_lag": "0 hours", "vintage_status": "EXACT_PIT",
             "transformation_formula": "dxy_shock_z * delta_real_yield_1w", "description": "DXY currency shock interaction with Real Yield move."},
        ]
        return pd.DataFrame(features_meta)

    @classmethod
    def save_dictionary(cls, output_path: str = "research/features/feature_dictionary.csv") -> pd.DataFrame:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df = cls.generate_dictionary()
        df.to_csv(output_path, index=False)
        return df
