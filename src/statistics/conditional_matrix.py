"""
Conditional response matrix engine.
Builds 2D contingency matrices cross-tabulating event surprises against macro regimes
(e.g., CPI surprise buckets x Real Yield regime or NFP surprise x DXY regime).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


class ConditionalMatrixEngine:
    """
    Constructs multi-dimensional conditional response tables to uncover nonlinear macroeconomic dynamics.
    """

    @classmethod
    def build_conditional_matrix(
        cls,
        df: pd.DataFrame,
        event_type: str,
        regime_col: str = "regime_real_yield",
        surprise_col: str = "surprise_bucket",
        target_col: str = "event_to_next_fri_return",
        min_cell_size: int = 1,
    ) -> Dict[str, Any]:
        """
        Builds a 2D conditional response matrix for a specific event type.
        """
        sub = df[df["event_type"] == event_type].copy()
        if sub.empty:
            return {"median_matrix": pd.DataFrame(), "count_matrix": pd.DataFrame()}

        if surprise_col not in sub.columns and "surprise_zscore" in sub.columns:
            from src.normalization.surprise_calculator import SurpriseCalculator
            sub[surprise_col] = sub["surprise_zscore"].apply(SurpriseCalculator.bucket_surprise)

        # 2D Pivot for Median Return
        median_pivot = sub.pivot_table(
            index=surprise_col,
            columns=regime_col,
            values=target_col,
            aggfunc="median",
        )

        # 2D Pivot for Sample Size
        count_pivot = sub.pivot_table(
            index=surprise_col,
            columns=regime_col,
            values=target_col,
            aggfunc="count",
        ).fillna(0).astype(int)

        # 2D Pivot for Positive Rate
        pos_pivot = sub.pivot_table(
            index=surprise_col,
            columns=regime_col,
            values=target_col,
            aggfunc=lambda x: (x > 0).mean() * 100.0,
        )

        return {
            "event_type": event_type,
            "regime_variable": regime_col,
            "median_matrix": median_pivot,
            "count_matrix": count_pivot,
            "positive_rate_matrix": pos_pivot,
        }

    @classmethod
    def generate_all_conditional_matrices(
        cls,
        df: pd.DataFrame,
        key_events: Optional[List[str]] = None,
        regimes: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generates conditional matrices for all primary event types across all primary regimes.
        """
        if key_events is None:
            key_events = ["CPI", "Nonfarm Payrolls", "FOMC Rate Decision", "ISM Manufacturing", "PCE"]
        if regimes is None:
            regimes = ["regime_real_yield", "regime_dxy", "regime_vix", "regime_gold_trend"]

        matrix_catalog = {}
        for evt in key_events:
            matrix_catalog[evt] = {}
            for reg in regimes:
                if reg in df.columns:
                    mat = cls.build_conditional_matrix(df, evt, regime_col=reg)
                    matrix_catalog[evt][reg] = mat

        return matrix_catalog
