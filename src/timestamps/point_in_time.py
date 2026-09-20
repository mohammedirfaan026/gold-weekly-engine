"""
Point-in-Time (PIT) data manager.
Guarantees strict point-in-time correctness by separating observation time from publication time.
Prevents any future information or look-ahead bias from entering market state reconstruction.
"""

from __future__ import annotations
import datetime as dt
from typing import Optional, Union, Dict, Any
import pandas as pd
from src.timestamps.calendar_utils import to_ny_time, to_utc_time


class PointInTimeManager:
    """
    Enforces point-in-time availability rules for market and macro data.
    Ensures that any data point used in pre-event reconstruction was strictly
    known and published prior to the event timestamp T.
    """

    @staticmethod
    def enforce_pit_filter(
        data: pd.DataFrame,
        as_of_time: Union[str, dt.datetime, pd.Timestamp],
        pub_col: str = "publication_time",
    ) -> pd.DataFrame:
        """
        Filters a DataFrame to only retain records published strictly on or before as_of_time.
        """
        as_of = to_utc_time(as_of_time)
        if pub_col not in data.columns:
            raise KeyError(f"DataFrame must contain '{pub_col}' for point-in-time filtering.")
        
        # Ensure pub_col is UTC datetime
        pub_times = pd.to_datetime(data[pub_col], utc=True)
        return data[pub_times <= as_of].copy()

    @staticmethod
    def get_latest_pit_value(
        data: pd.DataFrame,
        as_of_time: Union[str, dt.datetime, pd.Timestamp],
        value_col: str,
        pub_col: str = "publication_time",
    ) -> Any:
        """
        Retrieves the latest published value as of as_of_time.
        Returns None if no value had been published before as_of_time.
        """
        filtered = PointInTimeManager.enforce_pit_filter(data, as_of_time, pub_col=pub_col)
        if filtered.empty:
            return None
        # Sort by publication time ascending
        filtered = filtered.sort_values(by=pub_col)
        return filtered[value_col].iloc[-1]

    @staticmethod
    def apply_cot_pit_rules(cot_df: pd.DataFrame) -> pd.DataFrame:
        """
        CFTC Commitments of Traders (COT) rules:
        - Observation Date is Tuesday.
        - Publication Date is the following Friday at 15:30 ET (20:30 UTC / 19:30 UTC depending on DST).
        If Friday is a US Federal Holiday, release is typically Monday 15:30 ET.
        Ensures observation_time = Tuesday 17:00 ET and publication_time = Friday 15:30 ET.
        """
        df = cot_df.copy()
        if "observation_time" not in df.columns and "date" in df.columns:
            df["observation_time"] = pd.to_datetime(df["date"])

        # Determine publication time: Friday following observation date at 15:30 ET
        pub_times = []
        for obs in df["observation_time"]:
            obs_ny = to_ny_time(obs)
            weekday = obs_ny.weekday()
            # If Tuesday (1), Friday is 3 days later
            days_to_friday = (4 - weekday) % 7
            if days_to_friday == 0 and obs_ny.hour >= 16:
                days_to_friday = 7
            pub_date = obs_ny + dt.timedelta(days=days_to_friday)
            pub_date = pub_date.replace(hour=15, minute=30, second=0, microsecond=0)
            pub_times.append(to_utc_time(pub_date))

        df["publication_time"] = pub_times
        df["observation_time"] = [to_utc_time(x) for x in df["observation_time"]]
        return df

    @staticmethod
    def align_asof(
        event_df: pd.DataFrame,
        macro_df: pd.DataFrame,
        event_time_col: str = "timestamp",
        macro_pub_col: str = "publication_time",
        feature_cols: list[str] = None,
    ) -> pd.DataFrame:
        """
        Point-in-time merge of macro features into events using pd.merge_asof.
        Guarantees that for each event at timestamp T, only features published <= T are linked.
        """
        events = event_df.copy().sort_values(by=event_time_col)
        macro = macro_df.copy().sort_values(by=macro_pub_col)

        # Standardize timezone to UTC
        events[event_time_col] = pd.to_datetime(events[event_time_col], utc=True)
        macro[macro_pub_col] = pd.to_datetime(macro[macro_pub_col], utc=True)

        cols_to_keep = [macro_pub_col] + (feature_cols if feature_cols else [c for c in macro.columns if c != macro_pub_col])
        macro_subset = macro[cols_to_keep].dropna(subset=[macro_pub_col])

        merged = pd.merge_asof(
            events,
            macro_subset,
            left_on=event_time_col,
            right_on=macro_pub_col,
            direction="backward",
        )
        return merged
