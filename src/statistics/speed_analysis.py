"""
Gold response speed analyzer.
Measures the velocity of information incorporation across time horizons:
first 5 minutes, first 1 hour, first 4 hours, first day, and remaining days of the trading week.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class SpeedAnalyzer:
    """
    Quantifies the temporal distribution of macroeconomic information pricing in Gold.
    """

    @classmethod
    def analyze_response_speed_by_event(
        cls,
        events_df: pd.DataFrame,
        min_weekly_move_pct: float = 0.002,  # 20 bps minimum move
    ) -> pd.DataFrame:
        """
        Computes the median percentage of the total weekly move achieved across time windows for each event type.
        """
        df = events_df.copy()
        speed_cols = ["speed_pct_5m", "speed_pct_1h", "speed_pct_4h", "speed_pct_1d", "speed_pct_remaining"]

        # Ensure speed columns exist
        available_speed_cols = [c for c in speed_cols if c in df.columns]
        if not available_speed_cols:
            return pd.DataFrame()

        # Filter out negligible weekly moves
        if "event_to_next_fri_return" in df.columns:
            valid = df[df["event_to_next_fri_return"].abs() >= min_weekly_move_pct]
        else:
            valid = df

        summary_rows = []
        for event_type, group in valid.groupby("event_type"):
            if len(group) < 5:
                continue

            row = {
                "event_type": event_type,
                "sample_size": len(group),
                "median_speed_5m_pct": float(group["speed_pct_5m"].median()) if "speed_pct_5m" in group else np.nan,
                "median_speed_1h_pct": float(group["speed_pct_1h"].median()) if "speed_pct_1h" in group else np.nan,
                "median_speed_4h_pct": float(group["speed_pct_4h"].median()) if "speed_pct_4h" in group else np.nan,
                "median_speed_1d_pct": float(group["speed_pct_1d"].median()) if "speed_pct_1d" in group else np.nan,
                "median_speed_remaining_pct": float(group["speed_pct_remaining"].median()) if "speed_pct_remaining" in group else np.nan,
            }

            # Classify pricing speed pattern
            h1_speed = row["median_speed_1h_pct"]
            if pd.notna(h1_speed):
                if h1_speed > 70.0:
                    row["pricing_profile"] = "immediate_repricing"
                elif h1_speed > 35.0:
                    row["pricing_profile"] = "balanced_repricing"
                else:
                    row["pricing_profile"] = "gradual_drift"
            else:
                row["pricing_profile"] = "unknown"

            summary_rows.append(row)

        return pd.DataFrame(summary_rows)
