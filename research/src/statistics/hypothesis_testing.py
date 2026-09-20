"""
Multiple Testing Control, Hypothesis Ledger, and Structural Break Analysis.
Implements:
1. Benjamini-Hochberg (FDR) and Bonferroni corrections for all researched relationships
2. Block bootstrapping (2,000 resamples) for OOS Information Coefficients and Sharpe Ratios
3. Structural break detection (pre/post 2020 and 2022) to verify regime stability
Outputs:
- research/statistics/hypothesis_ledger.csv
- research/statistics/bootstrap_results.csv
- research/statistics/multiple_testing.csv
"""

from __future__ import annotations
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ttest_ind, pearsonr
from sklearn.linear_model import LinearRegression


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Computes Benjamini-Hochberg False Discovery Rate adjusted q-values."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    q_values = np.zeros(n)
    running_min = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = min(1.0, sorted_p[i] * n / rank)
        running_min = min(running_min, q)
        q_values[sorted_indices[i]] = running_min
        
    return q_values


class HypothesisTestingEngine:
    """
    Manages the empirical hypothesis ledger and tests statistical significance with rigorous FDR control.
    """

    def __init__(
        self,
        feature_matrix: pd.DataFrame,
        oos_results: Optional[pd.DataFrame] = None,
        target_col: str = "next_week_gold_return",
    ):
        self.matrix = feature_matrix.copy()
        self.oos_results = oos_results
        self.target_col = target_col

    def build_hypothesis_ledger(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Tests the 12 core quantitative relationships discovered during empirical research.
        Applies Benjamini-Hochberg and Bonferroni corrections.
        """
        hypotheses = [
            {
                "id": "H01",
                "name": "Real Yield Inverse Effect",
                "feature": "delta_real_yield_1w",
                "expected_sign": -1,
                "description": "Rising 10Y TIPS real yields predict lower next-week gold returns.",
            },
            {
                "id": "H02",
                "name": "DXY Dollar Inverse Effect",
                "feature": "dxy_return_1w",
                "expected_sign": -1,
                "description": "Rising USD index predicts lower next-week gold returns.",
            },
            {
                "id": "H03",
                "name": "Gold Trend Momentum",
                "feature": "gold_trend",
                "expected_sign": 1,
                "description": "Positive gold trend (Close > 20w MA > 50w MA) predicts positive next-week return.",
            },
            {
                "id": "H04",
                "name": "VIX Shock Safe Haven",
                "feature": "vix_shock_z",
                "expected_sign": 1,
                "description": "Surging volatility (>2 sigma VIX spike) predicts positive gold safe-haven response.",
            },
            {
                "id": "H05",
                "name": "Equity Crash Shock",
                "feature": "sp500_shock_neg2s",
                "expected_sign": 1,
                "description": "Severe S&P 500 weekly drawdown (<= -2 sigma) leads to positive gold response.",
            },
            {
                "id": "H06",
                "name": "COT Speculative Reversal",
                "feature": "cot_percentile_3y",
                "expected_sign": -1,
                "description": "Extreme net speculative positioning (>90th pctile) leads to mean-reverting downward pressure.",
            },
            {
                "id": "H07",
                "name": "ETF Flow Persistence",
                "feature": "etf_flow",
                "expected_sign": 1,
                "description": "Positive physical gold ETF weekly net inflows predict positive next-week return.",
            },
            {
                "id": "H08",
                "name": "CPI Upside Surprise",
                "feature": "cpi_zscore",
                "expected_sign": 1,
                "description": "Higher-than-expected CPI inflation surprise produces positive gold return.",
            },
            {
                "id": "H09",
                "name": "NFP Upside Surprise",
                "feature": "nfp_zscore",
                "expected_sign": -1,
                "description": "Strong Nonfarm Payrolls report raises Fed hike expectations, depressing gold.",
            },
            {
                "id": "H10",
                "name": "FOMC Decision Surprise",
                "feature": "fomc_zscore",
                "expected_sign": -1,
                "description": "Hawkish Fed rate surprise depresses gold.",
            },
            {
                "id": "H11",
                "name": "Breakeven Inflation Expansion",
                "feature": "delta_breakeven_1w",
                "expected_sign": 1,
                "description": "Rising 10Y breakeven inflation expectations support gold prices.",
            },
            {
                "id": "H12",
                "name": "1-Week Mean Reversion",
                "feature": "gold_return_1w",
                "expected_sign": -1,
                "description": "Negative auto-correlation in raw weekly gold return (short-term mean reversion).",
            },
        ]

        df = self.matrix.dropna(subset=[self.target_col])
        y = df[self.target_col].values

        ledger_rows = []
        raw_pvals = []

        for h in hypotheses:
            feat = h["feature"]
            if feat not in df.columns:
                continue

            x = df[feat].fillna(0.0).values
            n_obs = len(x)

            # Spearman rank correlation
            if np.std(x) > 1e-6:
                corr, p_val = spearmanr(x, y)
            else:
                corr, p_val = 0.0, 1.0

            raw_pvals.append(p_val)
            t_stat = corr * np.sqrt((n_obs - 2) / max(1e-6, 1.0 - corr**2))

            ledger_rows.append({
                "hypothesis_id": h["id"],
                "hypothesis_name": h["name"],
                "feature": feat,
                "sample_size": n_obs,
                "expected_sign": h["expected_sign"],
                "observed_correlation": round(corr, 4),
                "t_statistic": round(t_stat, 2),
                "raw_p_value": p_val,
                "description": h["description"],
            })

        ledger_df = pd.DataFrame(ledger_rows)
        p_arr = np.array(raw_pvals)

        # Multiple testing adjustments
        bh_qvals = benjamini_hochberg(p_arr)
        bonferroni_pvals = np.clip(p_arr * len(p_arr), 0.0, 1.0)

        ledger_df["fdr_adjusted_q_val"] = np.round(bh_qvals, 4)
        ledger_df["bonferroni_p_val"] = np.round(bonferroni_pvals, 4)
        ledger_df["raw_p_value"] = np.round(ledger_df["raw_p_value"], 4)

        # Statistical conclusion & Evidence Quality
        status = []
        evidence_quality = []
        for _, row in ledger_df.iterrows():
            obs_sign = 1 if row["observed_correlation"] > 0 else -1
            sign_match = (obs_sign == row["expected_sign"])
            q_val = row["fdr_adjusted_q_val"]

            if sign_match and q_val < 0.05:
                status.append("REJECT_NULL (Confirmed)")
                evidence_quality.append("STRONG")
            elif sign_match and q_val < 0.15:
                status.append("MARGINAL_CONFIRMATION")
                evidence_quality.append("MODERATE")
            elif sign_match and q_val >= 0.15:
                status.append("FAIL_TO_REJECT (Underpowered)")
                evidence_quality.append("WEAK")
            else:
                status.append("REJECTED_CONTRARY_SIGN")
                evidence_quality.append("REJECTED")

        ledger_df["statistical_verdict"] = status
        ledger_df["evidence_quality"] = evidence_quality

        # Summary multiple testing table
        mt_df = ledger_df[["hypothesis_id", "hypothesis_name", "observed_correlation", "raw_p_value", "fdr_adjusted_q_val", "bonferroni_p_val", "evidence_quality"]].copy()

        return ledger_df, mt_df

    def run_block_bootstrap(
        self,
        series_pred: np.ndarray,
        series_true: np.ndarray,
        block_size: int = 8,
        n_bootstraps: int = 2000,
    ) -> Dict[str, Any]:
        """
        Executes stationary/block bootstrap to construct 95% confidence intervals for IC and Sharpe.
        """
        n = len(series_true)
        if n < block_size * 2:
            return {"ic_mean": 0.0, "ic_ci_lower": 0.0, "ic_ci_upper": 0.0, "sharpe_ci_lower": 0.0, "sharpe_ci_upper": 0.0}

        rng = np.random.default_rng(seed=42)
        n_blocks = int(np.ceil(n / block_size))

        boot_ics = []
        boot_sharpes = []

        for _ in range(n_bootstraps):
            start_indices = rng.integers(0, n - block_size + 1, size=n_blocks)
            sampled_idx = []
            for s in start_indices:
                sampled_idx.extend(range(s, s + block_size))
            sampled_idx = sampled_idx[:n]

            y_p = series_pred[sampled_idx]
            y_t = series_true[sampled_idx]

            if np.std(y_p) > 1e-6 and np.std(y_t) > 1e-6:
                ic_val, _ = spearmanr(y_p, y_t)
            else:
                ic_val = 0.0
            boot_ics.append(ic_val)

            strat = np.sign(y_p) * y_t
            if np.std(strat) > 1e-6:
                sh = (np.mean(strat) / np.std(strat)) * np.sqrt(52)
            else:
                sh = 0.0
            boot_sharpes.append(sh)

        return {
            "n_bootstraps": n_bootstraps,
            "block_size": block_size,
            "ic_mean": float(np.mean(boot_ics)),
            "ic_ci_lower": float(np.percentile(boot_ics, 2.5)),
            "ic_ci_upper": float(np.percentile(boot_ics, 97.5)),
            "sharpe_mean": float(np.mean(boot_sharpes)),
            "sharpe_ci_lower": float(np.percentile(boot_sharpes, 2.5)),
            "sharpe_ci_upper": float(np.percentile(boot_sharpes, 97.5)),
            "p_ic_positive": float(np.mean(np.array(boot_ics) > 0.0)),
        }

    def test_structural_breaks(self) -> pd.DataFrame:
        """
        Evaluates parameter stability and regime shifts pre/post 2020 (COVID) and pre/post 2022 (Rate Hike Cycle).
        """
        df = self.matrix.dropna(subset=[self.target_col]).copy()
        df["year"] = pd.to_datetime(df["week_ending"]).dt.year
        y = df[self.target_col]

        break_tests = []
        features_to_test = ["delta_real_yield_1w", "dxy_return_1w", "gold_return_1w", "etf_flow"]

        # 1. 2020 Break (Pre: 2010-2019 vs Post: 2020-2026)
        sub_pre2020 = df[df["year"] < 2020]
        sub_post2020 = df[df["year"] >= 2020]

        # 2. 2022 Break (Pre: 2010-2021 vs Post: 2022-2026)
        sub_pre2022 = df[df["year"] < 2022]
        sub_post2022 = df[df["year"] >= 2022]

        for feat in features_to_test:
            if feat not in df.columns:
                continue

            # Beta pre/post 2020
            lr_pre20 = LinearRegression().fit(sub_pre2020[[feat]].fillna(0), sub_pre2020[self.target_col])
            lr_post20 = LinearRegression().fit(sub_post2020[[feat]].fillna(0), sub_post2020[self.target_col])
            corr_pre20, _ = spearmanr(sub_pre2020[feat].fillna(0), sub_pre2020[self.target_col])
            corr_post20, _ = spearmanr(sub_post2020[feat].fillna(0), sub_post2020[self.target_col])

            # Beta pre/post 2022
            lr_pre22 = LinearRegression().fit(sub_pre2022[[feat]].fillna(0), sub_pre2022[self.target_col])
            lr_post22 = LinearRegression().fit(sub_post2022[[feat]].fillna(0), sub_post2022[self.target_col])
            corr_pre22, _ = spearmanr(sub_pre2022[feat].fillna(0), sub_pre2022[self.target_col])
            corr_post22, _ = spearmanr(sub_post2022[feat].fillna(0), sub_post2022[self.target_col])

            break_tests.append({
                "feature": feat,
                "corr_pre_2020": round(corr_pre20, 4),
                "corr_post_2020": round(corr_post20, 4),
                "delta_corr_2020": round(corr_post20 - corr_pre20, 4),
                "beta_pre_2020": round(float(lr_pre20.coef_[0]), 4),
                "beta_post_2020": round(float(lr_post20.coef_[0]), 4),
                "corr_pre_2022": round(corr_pre22, 4),
                "corr_post_2022": round(corr_post22, 4),
                "delta_corr_2022": round(corr_post22 - corr_pre22, 4),
                "regime_shift_detected": "YES" if abs(corr_post22 - corr_pre22) > 0.10 else "NO",
            })

        return pd.DataFrame(break_tests)
