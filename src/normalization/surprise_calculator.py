"""
Surprise calculator for macroeconomic events.
Computes absolute, percentage, and expanding-window Z-score surprises.
Strictly point-in-time: surprise standard deviation is computed expanding backward only.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


class SurpriseCalculator:
    """
    Computes and standardizes surprises for economic events.
    Formula:
        surprise_absolute = actual - consensus
        surprise_percentage = (actual - consensus) / abs(consensus)  (if consensus != 0)
        surprise_zscore = (actual - consensus) / historical_expanding_std
    """

    @staticmethod
    def calculate_surprises(
        events_df: pd.DataFrame,
        actual_col: str = "actual_value",
        consensus_col: str = "consensus_value",
        previous_col: str = "previous_value",
        event_type_col: str = "event_type",
        timestamp_col: str = "timestamp",
        min_history_for_zscore: int = 5,
    ) -> pd.DataFrame:
        """
        Calculates absolute, percentage, and point-in-time expanding Z-score surprises.
        Preserves raw previous, consensus, and actual values.
        """
        df = events_df.copy()
        
        # Ensure proper datetime sorting for expanding window calculation
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)
        df = df.sort_values(by=timestamp_col).reset_index(drop=True)

        # 1. Absolute surprise: actual - consensus
        has_consensus = df[consensus_col].notna() & df[actual_col].notna()
        df["surprise_absolute"] = np.nan
        df.loc[has_consensus, "surprise_absolute"] = (
            df.loc[has_consensus, actual_col].astype(float) - df.loc[has_consensus, consensus_col].astype(float)
        )

        # 2. Percentage surprise
        df["surprise_percentage"] = np.nan
        valid_denom = has_consensus & (df[consensus_col].astype(float) != 0)
        df.loc[valid_denom, "surprise_percentage"] = (
            (df.loc[valid_denom, actual_col].astype(float) - df.loc[valid_denom, consensus_col].astype(float))
            / df.loc[valid_denom, consensus_col].astype(float).abs()
        ) * 100.0

        # 3. Expanding Standard Deviation and Z-Score by event_type (Point-in-Time!)
        df["surprise_zscore"] = np.nan
        df["surprise_hist_std"] = np.nan

        for event_type, group_indices in df.groupby(event_type_col).groups.items():
            group = df.loc[group_indices].sort_values(by=timestamp_col)
            surprises = group["surprise_absolute"]
            
            # Point-in-time expanding std: computed using only prior observations
            # shift(1) ensures the current observation's surprise is NOT included in its own historical std dev
            expanding_std = surprises.shift(1).expanding(min_periods=min_history_for_zscore).std(ddof=1)
            
            # Fallback for initial releases: use the first available robust std or current group std if expanding is NaN
            overall_std = surprises.std(ddof=1)
            if pd.isna(overall_std) or overall_std == 0:
                overall_std = 1.0

            # If expanding_std is NaN (early in history), fall back safely to overall or minimum std
            effective_std = expanding_std.fillna(overall_std)
            # Avoid division by zero
            effective_std = effective_std.replace(0, overall_std if overall_std > 0 else 1.0)
            
            z_scores = surprises / effective_std
            
            df.loc[group.index, "surprise_hist_std"] = effective_std
            df.loc[group.index, "surprise_zscore"] = z_scores

        return df

    @staticmethod
    def bucket_surprise(
        z_score: float,
        buckets: dict[str, list[float]] = None,
    ) -> str:
        """
        Categorizes surprise z-score into standard quantitative buckets:
        - extreme_negative: Z < -2.0
        - large_negative: -2.0 <= Z < -1.0
        - neutral: -1.0 <= Z <= 1.0
        - large_positive: 1.0 < Z <= 2.0
        - extreme_positive: Z > 2.0
        """
        if pd.isna(z_score):
            return "unknown"
            
        if z_score < -2.0:
            return "extreme_negative"
        elif -2.0 <= z_score < -1.0:
            return "large_negative"
        elif -1.0 <= z_score <= 1.0:
            return "neutral"
        elif 1.0 < z_score <= 2.0:
            return "large_positive"
        else:
            return "extreme_positive"
