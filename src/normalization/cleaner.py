"""
Data cleaner and alignment utilities.
Ensures price integrity, handles weekend/holiday gaps, and prepares clean time series.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


class DataCleaner:
    """Cleans, validates, and aligns market and macro time series."""

    @staticmethod
    def validate_ohlc(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates OHLC consistency:
        - Low <= Open, Close, High
        - High >= Open, Close, Low
        - Prices > 0
        """
        clean = df.copy()
        for col in ["open", "high", "low", "close"]:
            if col in clean.columns:
                clean[col] = pd.to_numeric(clean[col], errors="coerce")
                # Remove zero or negative prices
                clean.loc[clean[col] <= 0, col] = np.nan

        if all(c in clean.columns for c in ["open", "high", "low", "close"]):
            # Reconcile High and Low bounds if minor exchange anomalies exist
            clean["high"] = clean[["open", "high", "low", "close"]].max(axis=1)
            clean["low"] = clean[["open", "high", "low", "close"]].min(axis=1)

        return clean

    @staticmethod
    def align_to_business_days(
        df: pd.DataFrame,
        date_col: str = "date",
        fill_method: str = "ffill",
        max_fill_days: int = 5,
    ) -> pd.DataFrame:
        """
        Aligns daily data to standard business day frequency (Mon-Fri).
        Uses forward-fill up to max_fill_days to accommodate holidays without look-ahead bias.
        """
        clean = df.copy()
        clean[date_col] = pd.to_datetime(clean[date_col])
        clean = clean.sort_values(by=date_col).drop_duplicates(subset=[date_col])
        clean = clean.set_index(date_col)

        # Full business day index
        bdate_range = pd.date_range(start=clean.index.min(), end=clean.index.max(), freq="B")
        reindexed = clean.reindex(bdate_range)
        
        if fill_method == "ffill":
            reindexed = reindexed.ffill(limit=max_fill_days)

        reindexed.index.name = date_col
        return reindexed.reset_index()

    @staticmethod
    def calculate_returns(series: pd.Series, periods: int = 1, method: str = "simple") -> pd.Series:
        """
        Calculates simple or log returns over specified periods.
        """
        if method == "log":
            return np.log(series / series.shift(periods))
        return (series / series.shift(periods)) - 1.0
