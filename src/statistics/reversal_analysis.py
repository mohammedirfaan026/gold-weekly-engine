"""
Reversal and continuation analysis engine.
Evaluates the stability and persistence of initial market reactions vs final weekly closes.
Classifies responses into: initial continuation, partial reversal, full reversal, and muted initial.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class ReversalAnalyzer:
    """
    Measures how often initial post-event reactions persist into the weekly close versus reversing.
    """

    @classmethod
    def analyze_reversals_by_event(
        cls,
        events_df: pd.DataFrame,
        classification_col: str = "reversal_classification",
    ) -> pd.DataFrame:
        """
        Generates reversal frequency and performance breakdowns by event type.
        """
        df = events_df.copy()
        if classification_col not in df.columns:
            return pd.DataFrame()

        results = []
        for event_type, group in df.groupby("event_type"):
            total_n = len(group)
            if total_n < 5:
                continue

            counts = group[classification_col].value_counts()
            pcts = (counts / total_n) * 100.0

            continuation_pct = float(pcts.get("initial_continuation", 0.0))
            full_reversal_pct = float(pcts.get("full_reversal", 0.0))
            partial_reversal_pct = float(pcts.get("partial_reversal", 0.0))
            muted_pct = float(pcts.get("muted_initial", 0.0))

            results.append({
                "event_type": event_type,
                "total_events": total_n,
                "continuation_rate_pct": continuation_pct,
                "full_reversal_rate_pct": full_reversal_pct,
                "partial_reversal_rate_pct": partial_reversal_pct,
                "muted_reaction_pct": muted_pct,
                "continuation_to_reversal_ratio": (
                    continuation_pct / (full_reversal_pct + 0.001)
                ),
            })

        return pd.DataFrame(results)
