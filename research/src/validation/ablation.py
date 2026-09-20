"""
Sequential Information Layer Feature Ablation Engine.
Evaluates the incremental predictive power of feature layers A through G:
- Layer A: Gold Technicals only
- Layer B: Layer A + Rates & Breakevens
- Layer C: Layer B + FX (DXY)
- Layer D: Layer C + Macroeconomic Surprises
- Layer E: Layer D + Positioning & ETF Flows
- Layer F: Layer E + Cross-Asset Shocks & Regimes
- Layer G: Layer F + Transmission & Interaction Terms
Outputs quantitative ablation results and marginal improvements.
"""

from __future__ import annotations
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error

from research.src.models.estimators import PreprocessedEstimator
from sklearn.linear_model import RidgeCV


class FeatureAblationEngine:
    """
    Executes walk-forward evaluations across cumulative feature sets A through G.
    """

    def __init__(
        self,
        feature_matrix: pd.DataFrame,
        target_col: str = "next_week_gold_return",
    ):
        self.df = feature_matrix.copy()
        self.df["week_ending_dt"] = pd.to_datetime(self.df["week_ending"])
        self.df["year"] = self.df["week_ending_dt"].dt.year
        self.target_col = target_col
        self.layers = self._define_layers()

    def _define_layers(self) -> Dict[str, List[str]]:
        cols = self.df.columns

        # Layer A: Technicals
        layer_a = [c for c in [
            "gold_return_1w", "gold_return_4w", "gold_return_12w",
            "gold_ma_20w", "gold_ma_50w", "gold_distance_20w", "gold_distance_50w",
            "gold_trend", "gold_volatility_20w", "gold_momentum"
        ] if c in cols]

        # Layer B: Layer A + Rates & Breakevens
        rates = [c for c in [
            "real_10y_yield", "delta_real_yield_1w", "delta_real_yield_4w",
            "us10y", "us2y", "delta_nominal_yield_1w", "breakeven_10y",
            "delta_breakeven_1w", "yield_curve_2s10s", "delta_yield_curve_1w"
        ] if c in cols]
        layer_b = layer_a + rates

        # Layer C: Layer B + FX (DXY)
        fx = [c for c in ["dxy", "dxy_return_1w", "dxy_return_4w"] if c in cols]
        layer_c = layer_b + fx

        # Layer D: Layer C + Macro Surprises
        macro = [c for c in [
            "cpi_surprise", "cpi_zscore", "core_cpi_surprise", "core_cpi_zscore",
            "pce_surprise", "pce_zscore", "core_pce_surprise", "core_pce_zscore",
            "gdp_surprise", "gdp_zscore", "nfp_surprise", "nfp_zscore",
            "ism_surprise", "ism_zscore", "fomc_surprise", "fomc_zscore",
            "event_count", "high_impact_event_count", "major_event_this_week", "major_event_next_week",
            "is_cpi_week", "is_pce_week", "is_fomc_week", "is_nfp_week", "is_gdp_week",
            "is_ism_week", "is_multiple_event_week", "is_no_event_week"
        ] if c in cols]
        layer_d = layer_c + macro

        # Layer E: Layer D + Positioning & ETF Flows
        positioning = [c for c in [
            "cot_net_speculative", "cot_change_1w", "cot_percentile_3y",
            "etf_flow", "etf_flow_percentile", "etf_flow_change"
        ] if c in cols]
        layer_e = layer_d + positioning

        # Layer F: Layer E + Cross-Asset Shocks & Regimes
        shocks_regimes = [c for c in [
            "sp500_return_1w", "vix", "vix_change_1w", "vix_percentile",
            "hy_oas", "hy_oas_change_1w", "wti_return_1w", "silver_return_1w",
            "sp500_shock_z", "dxy_shock_z", "real_yield_shock_z", "vix_shock_z", "gold_shock_z",
            "sp500_shock_neg2s", "sp500_shock_neg3s", "dxy_shock_pos2s", "dxy_shock_neg2s",
            "real_yield_shock_pos2s", "real_yield_shock_neg2s", "vix_shock_pos2s",
            "real_yield_regime", "dxy_regime", "gold_trend_regime", "vix_regime",
            "equity_regime", "positioning_regime"
        ] if c in cols]
        layer_f = layer_e + shocks_regimes

        # Layer G: Layer F + Transmission & Interactions
        interactions = [c for c in [
            "yield_transmission", "dxy_transmission", "breakeven_transmission", "risk_transmission",
            "cpi_surprise_x_real_yield_regime", "cpi_surprise_x_dxy_regime", "cpi_surprise_x_gold_trend",
            "pce_surprise_x_real_yield_regime", "cot_percentile_x_gold_trend",
            "etf_flow_percentile_x_gold_trend", "vix_shock_x_sp500_return", "dxy_shock_x_real_yield_change"
        ] if c in cols]
        layer_g = layer_f + interactions

        return {
            "Layer A: Technicals": layer_a,
            "Layer B: + Rates & Breakevens": layer_b,
            "Layer C: + DXY": layer_c,
            "Layer D: + Macro Surprises": layer_d,
            "Layer E: + Positioning & Flows": layer_e,
            "Layer F: + Shocks & Regimes": layer_f,
            "Layer G: + Interactions": layer_g,
        }

    def run_ablation(self) -> pd.DataFrame:
        """Runs walk-forward across each cumulative information layer."""
        folds = [
            {"train_end": 2017, "test_start": 2018, "test_end": 2018},
            {"train_end": 2018, "test_start": 2019, "test_end": 2019},
            {"train_end": 2019, "test_start": 2020, "test_end": 2020},
            {"train_end": 2020, "test_start": 2021, "test_end": 2021},
            {"train_end": 2021, "test_start": 2022, "test_end": 2022},
            {"train_end": 2022, "test_start": 2023, "test_end": 2023},
            {"train_end": 2023, "test_start": 2024, "test_end": 2024},
            {"train_end": 2024, "test_start": 2025, "test_end": 2026},
        ]

        results = []
        prev_ic = None
        prev_sharpe = None

        for layer_name, feature_subset in self.layers.items():
            if not feature_subset:
                continue

            all_y_true = []
            all_y_pred = []

            for f in folds:
                train_mask = self.df["year"] <= f["train_end"]
                train_idx = self.df[train_mask].index[:-1]  # 1-week embargo
                test_mask = (self.df["year"] >= f["test_start"]) & (self.df["year"] <= f["test_end"])

                train_df = self.df.loc[train_idx].dropna(subset=[self.target_col])
                test_df = self.df[test_mask].dropna(subset=[self.target_col])

                if test_df.empty:
                    continue

                X_tr = train_df[feature_subset]
                y_tr = train_df[self.target_col]
                X_te = test_df[feature_subset]
                y_te = test_df[self.target_col]

                # Model: Regularized Ridge
                model = PreprocessedEstimator(RidgeCV(alphas=np.logspace(-2, 4, 15)), is_tree=False)
                try:
                    model.fit(X_tr, y_tr)
                    preds = model.predict(X_te)
                except Exception:
                    preds = np.zeros(len(test_df))

                all_y_true.extend(y_te.values)
                all_y_pred.extend(preds)

            y_t = np.array(all_y_true)
            y_p = np.array(all_y_pred)

            # Calculate OOS statistics
            da = np.mean((y_p > 0) == (y_t > 0)) * 100.0
            if np.std(y_p) > 1e-6:
                ic, p_val = spearmanr(y_p, y_t)
            else:
                ic, p_val = 0.0, 1.0

            rmse = np.sqrt(mean_squared_error(y_t, y_p))
            strat_ret = np.sign(y_p) * y_t
            sharpe = (np.mean(strat_ret) / np.std(strat_ret)) * np.sqrt(52) if np.std(strat_ret) > 1e-6 else 0.0

            delta_ic = (ic - prev_ic) if prev_ic is not None else 0.0
            delta_sharpe = (sharpe - prev_sharpe) if prev_sharpe is not None else 0.0
            prev_ic = ic
            prev_sharpe = sharpe

            results.append({
                "Layer": layer_name,
                "Feature_Count": len(feature_subset),
                "OOS_Directional_Accuracy": round(da, 2),
                "OOS_Information_Coefficient": round(ic, 4),
                "IC_p_value": round(p_val, 4),
                "Delta_IC": round(delta_ic, 4),
                "Annualized_Sharpe": round(sharpe, 2),
                "Delta_Sharpe": round(delta_sharpe, 2),
                "RMSE": round(rmse, 4),
            })

        return pd.DataFrame(results)
