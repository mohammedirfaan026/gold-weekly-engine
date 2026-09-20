"""
Weekly event aggregator.
Captures and aggregates multiple macro events occurring within the same trading week.
Preserves event counts, sequences, surprise vectors, and flags without assuming a single cause for weekly moves.
"""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import get_trading_week_id, to_ny_time


class WeeklyEventAggregator:
    """
    Aggregates all macro releases occurring in each discrete trading week (previous Friday close to next Friday close).
    """

    @classmethod
    def aggregate_week_events(cls, week_events: pd.DataFrame) -> Dict[str, Any]:
        """
        Aggregates events for a single trading week.
        """
        if week_events.empty:
            return {
                "event_count": 0,
                "high_impact_count": 0,
                "cpi_present": 0,
                "nfp_present": 0,
                "fomc_present": 0,
                "pce_present": 0,
                "gdp_present": 0,
                "ism_present": 0,
                "major_cb_present": 0,
                "largest_positive_macro_surprise": 0.0,
                "largest_negative_macro_surprise": 0.0,
                "largest_absolute_surprise": 0.0,
                "event_surprise_sum": 0.0,
                "event_sequence": "none",
                "event_surprise_vector": json.dumps({}),
            }

        # Event counts & flags
        count = len(week_events)
        high_imp = int((week_events["importance"] == "high").sum())

        event_types = week_events["event_type"].tolist()
        cpi_present = int(any("CPI" in et for et in event_types))
        nfp_present = int(any("Payroll" in et or "NFP" in et for et in event_types))
        fomc_present = int(any("FOMC" in et for et in event_types))
        pce_present = int(any("PCE" in et for et in event_types))
        gdp_present = int(any("GDP" in et for et in event_types))
        ism_present = int(any("ISM" in et for et in event_types))
        major_cb = int(any("FOMC" in et or "ECB" in et or "BOJ" in et for et in event_types))

        # Surprises (Z-scores)
        z_scores = week_events["surprise_zscore"].dropna()
        if not z_scores.empty:
            largest_pos = float(z_scores[z_scores > 0].max()) if (z_scores > 0).any() else 0.0
            largest_neg = float(z_scores[z_scores < 0].min()) if (z_scores < 0).any() else 0.0
            largest_abs = float(z_scores.abs().max())
            surprise_sum = float(z_scores.sum())
        else:
            largest_pos = 0.0
            largest_neg = 0.0
            largest_abs = 0.0
            surprise_sum = 0.0

        # Event sequence and surprise vector
        seq_parts = []
        vec_dict = {}
        sorted_evts = week_events.sort_values(by="timestamp")
        for _, row in sorted_evts.iterrows():
            ts_ny = to_ny_time(row["timestamp"])
            day_name = ts_ny.strftime("%a")
            etype = row["event_type"]
            z = row.get("surprise_zscore")
            z_str = f"{z:+.2f}z" if pd.notna(z) else "no_cons"
            seq_parts.append(f"{day_name}:{etype}({z_str})")
            if pd.notna(z):
                vec_dict[etype] = float(z)

        return {
            "event_count": count,
            "high_impact_count": high_imp,
            "cpi_present": cpi_present,
            "nfp_present": nfp_present,
            "fomc_present": fomc_present,
            "pce_present": pce_present,
            "gdp_present": gdp_present,
            "ism_present": ism_present,
            "major_cb_present": major_cb,
            "largest_positive_macro_surprise": largest_pos,
            "largest_negative_macro_surprise": largest_neg,
            "largest_absolute_surprise": largest_abs,
            "event_surprise_sum": surprise_sum,
            "event_sequence": " -> ".join(seq_parts) if seq_parts else "none",
            "event_surprise_vector": json.dumps(vec_dict),
        }

    @classmethod
    def aggregate_all_weeks(
        cls,
        events_df: pd.DataFrame,
        week_endings: List[pd.Timestamp],
    ) -> pd.DataFrame:
        """
        Aggregates events mapped across all trading week Friday endpoints.
        """
        evts = events_df.copy()
        evts["week_ending"] = evts["timestamp"].apply(get_trading_week_id)

        grouped = evts.groupby("week_ending")
        aggregated_rows = []

        for we in week_endings:
            we_str = we.strftime("%Y-%m-%d")
            if we_str in grouped.groups:
                w_sub = grouped.get_group(we_str)
                row_agg = cls.aggregate_week_events(w_sub)
            else:
                row_agg = cls.aggregate_week_events(pd.DataFrame())

            row_agg["week_ending"] = we_str
            aggregated_rows.append(row_agg)

        return pd.DataFrame(aggregated_rows)
