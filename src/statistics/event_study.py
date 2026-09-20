"""
Statistical event study engine.
Computes sample sizes, medians, means, 10% trimmed means, bootstrap 95% confidence intervals,
positive response rates, and non-parametric significance tests across event types, surprise sizes, and regimes.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Union
import numpy as np
import pandas as pd
from scipy import stats


class EventStudyEngine:
    """
    Reusable statistical engine for macroeconomic event studies.
    Employs robust statistics and non-parametric bootstrap resampling to protect against market return outliers.
    """

    @staticmethod
    def bootstrap_ci(
        data: Union[np.ndarray, pd.Series],
        n_boot: int = 2000,
        ci_level: float = 0.95,
        stat_func=np.median,
    ) -> tuple[float, float]:
        """
        Computes non-parametric bootstrap confidence interval for a given statistic function.
        """
        clean = np.asarray(data)
        clean = clean[~np.isnan(clean)]
        if len(clean) < 3:
            return (np.nan, np.nan)

        boot_stats = np.empty(n_boot)
        n = len(clean)
        for i in range(n_boot):
            sample = np.random.choice(clean, size=n, replace=True)
            boot_stats[i] = stat_func(sample)

        alpha = (1.0 - ci_level) / 2.0
        low = float(np.percentile(boot_stats, 100.0 * alpha))
        high = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha)))
        return (low, high)

    @classmethod
    def compute_summary_statistics(
        cls,
        series: pd.Series,
        n_boot: int = 2000,
    ) -> Dict[str, Any]:
        """
        Calculates a full suite of robust and classical statistics for a response return distribution.
        """
        clean = series.dropna()
        n = len(clean)
        if n == 0:
            return {
                "n": 0, "mean": np.nan, "median": np.nan, "trimmed_mean_10": np.nan,
                "std": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                "positive_rate": np.nan, "p_value_wilcoxon": np.nan,
            }

        mean_val = float(clean.mean())
        median_val = float(clean.median())
        trimmed_val = float(stats.trim_mean(clean, 0.10)) if n >= 5 else mean_val
        std_val = float(clean.std()) if n > 1 else 0.0

        ci_low, ci_high = cls.bootstrap_ci(clean, n_boot=n_boot, stat_func=np.median)
        pos_rate = float((clean > 0).mean() * 100.0)

        # Wilcoxon signed-rank test against 0
        if n >= 6 and (clean != 0).any():
            try:
                res = stats.wilcoxon(clean, alternative="two-sided")
                p_val = float(res.pvalue)
            except Exception:
                p_val = np.nan
        else:
            p_val = np.nan

        return {
            "n": n,
            "mean": mean_val,
            "median": median_val,
            "trimmed_mean_10": trimmed_val,
            "std": std_val,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "positive_rate": pos_rate,
            "p_value_wilcoxon": p_val,
        }

    @classmethod
    def run_event_study_by_type(
        cls,
        events_processed_df: pd.DataFrame,
        horizon_cols: Optional[List[str]] = None,
        min_sample_size: int = 5,
    ) -> pd.DataFrame:
        """
        Runs comprehensive event studies partitioned by event type.
        """
        if horizon_cols is None:
            horizon_cols = [
                "return_5m", "return_15m", "return_1h", "return_4h",
                "return_1d", "return_3d", "return_5d", "event_to_next_fri_return"
            ]

        results = []
        for event_type, group in events_processed_df.groupby("event_type"):
            if len(group) < min_sample_size:
                continue

            row = {"event_type": event_type, "sample_size": len(group)}
            for col in horizon_cols:
                if col in group.columns:
                    stats_dict = cls.compute_summary_statistics(group[col])
                    row[f"{col}_median"] = stats_dict["median"]
                    row[f"{col}_mean"] = stats_dict["mean"]
                    row[f"{col}_trimmed_10"] = stats_dict["trimmed_mean_10"]
                    row[f"{col}_ci_low"] = stats_dict["ci_low"]
                    row[f"{col}_ci_high"] = stats_dict["ci_high"]
                    row[f"{col}_pos_rate"] = stats_dict["positive_rate"]
                    row[f"{col}_p_val"] = stats_dict["p_value_wilcoxon"]

            # MFE and MAE on weekly horizon
            if "mfe_next_friday" in group.columns:
                row["mfe_weekly_median"] = group["mfe_next_friday"].median()
            if "mae_next_friday" in group.columns:
                row["mae_weekly_median"] = group["mae_next_friday"].median()

            results.append(row)

        return pd.DataFrame(results)

    @classmethod
    def run_event_study_by_surprise_bucket(
        cls,
        events_processed_df: pd.DataFrame,
        target_col: str = "event_to_next_fri_return",
    ) -> pd.DataFrame:
        """
        Analyzes whether larger macro surprises produce larger gold weekly responses.
        Buckets: extreme_negative (Z<-2), large_negative (-2<=Z<-1), neutral (-1<=Z<=1),
        large_positive (1<Z<=2), extreme_positive (Z>2).
        """
        df = events_processed_df.copy()
        if "surprise_bucket" not in df.columns and "surprise_zscore" in df.columns:
            from src.normalization.surprise_calculator import SurpriseCalculator
            df["surprise_bucket"] = df["surprise_zscore"].apply(SurpriseCalculator.bucket_surprise)

        results = []
        bucket_order = ["extreme_negative", "large_negative", "neutral", "large_positive", "extreme_positive"]
        
        for event_type, group in df.groupby("event_type"):
            if len(group) < 10:
                continue
            for b in bucket_order:
                sub = group[group["surprise_bucket"] == b]
                if len(sub) == 0:
                    continue
                stats_dict = cls.compute_summary_statistics(sub[target_col])
                results.append({
                    "event_type": event_type,
                    "surprise_bucket": b,
                    "sample_size": stats_dict["n"],
                    "median_weekly_return": stats_dict["median"],
                    "mean_weekly_return": stats_dict["mean"],
                    "trimmed_10_return": stats_dict["trimmed_mean_10"],
                    "ci_low": stats_dict["ci_low"],
                    "ci_high": stats_dict["ci_high"],
                    "positive_rate": stats_dict["positive_rate"],
                    "p_val": stats_dict["p_value_wilcoxon"],
                })

        return pd.DataFrame(results)

    @classmethod
    def run_directional_asymmetry_study(
        cls,
        events_processed_df: pd.DataFrame,
        target_col: str = "event_to_next_fri_return",
    ) -> pd.DataFrame:
        """
        Compares gold's weekly response to positive surprises vs negative surprises.
        Tests for market reaction asymmetry.
        """
        df = events_processed_df.copy()
        results = []

        for event_type, group in df.groupby("event_type"):
            pos_sub = group[group["surprise_zscore"] > 0.5]
            neg_sub = group[group["surprise_zscore"] < -0.5]

            if len(pos_sub) < 3 or len(neg_sub) < 3:
                continue

            pos_stats = cls.compute_summary_statistics(pos_sub[target_col])
            neg_stats = cls.compute_summary_statistics(neg_sub[target_col])

            # Mann-Whitney U test between positive and negative surprise responses
            try:
                mwu = stats.mannwhitneyu(pos_sub[target_col].dropna(), neg_sub[target_col].dropna(), alternative="two-sided")
                asymmetry_p_val = float(mwu.pvalue)
            except Exception:
                asymmetry_p_val = np.nan

            results.append({
                "event_type": event_type,
                "n_positive": pos_stats["n"],
                "median_pos_surprise_return": pos_stats["median"],
                "pos_surprise_win_rate": pos_stats["positive_rate"],
                "n_negative": neg_stats["n"],
                "median_neg_surprise_return": neg_stats["median"],
                "neg_surprise_win_rate": neg_stats["positive_rate"],
                "asymmetry_spread": pos_stats["median"] - neg_stats["median"],
                "asymmetry_p_value": asymmetry_p_val,
            })

        return pd.DataFrame(results)
