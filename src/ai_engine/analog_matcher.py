"""
Point-in-Time Historical Analog Matcher.
Strictly searches historical completed trading weeks prior to week t-2:
- Zero forward look-ahead bias
- Standardization computed exclusively on past observations
- Returns top-3 macroeconomic twins with their realized subsequent weekly moves
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional


class PointInTimeAnalogMatcher:
    """
    Identifies historical analog trading weeks with similar macroeconomic and market conditions.
    """

    MATCH_FEATURES = [
        "delta_real_yield_1w",
        "dxy_return_1w",
        "gold_return_1w",
        "vix",
    ]

    def find_analogs(
        self,
        target_row: pd.Series,
        historical_matrix: pd.DataFrame,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Searches historical records strictly prior to the target week.
        """
        target_week = target_row["week_ending"]
        target_idx = target_row.name if target_row.name is not None else len(historical_matrix) - 1

        # Strict Point-in-Time filter: candidate weeks must have completed at least 2 weeks prior
        # to ensure their forward target return was observable before target_week
        cutoff_idx = max(0, target_idx - 2)
        past_candidates = historical_matrix.loc[:cutoff_idx].dropna(
            subset=self.MATCH_FEATURES + ["next_week_gold_return"]
        ).copy()

        if len(past_candidates) < 10:
            return []

        past_vals = past_candidates[self.MATCH_FEATURES].astype(float)
        target_vals = target_row[self.MATCH_FEATURES].astype(float)

        # Standardize using PAST statistics ONLY
        means = past_vals.mean()
        stds = past_vals.std().replace(0, 1.0)

        norm_past = (past_vals - means) / stds
        norm_target = (target_vals - means) / stds

        # Euclidean distance
        diffs = norm_past.values - norm_target.values.reshape(1, -1)
        dists = np.sqrt((diffs.astype(float)**2).sum(axis=1))
        
        top_indices = np.argsort(dists)[:top_k]

        analogs = []
        for rank, k_idx in enumerate(top_indices, 1):
            actual_idx = past_candidates.index[k_idx]
            match_row = past_candidates.loc[actual_idx]
            dist_val = float(dists[k_idx])
            ret_val = float(match_row["next_week_gold_return"])
            
            # Determine regime context
            ry_reg = "Rising Yields" if match_row.get("real_yield_regime", 0) == 1 else ("Falling Yields" if match_row.get("real_yield_regime", 0) == -1 else "Neutral Yields")
            dxy_reg = "Stronger USD" if match_row.get("dxy_regime", 0) == 1 else ("Weaker USD" if match_row.get("dxy_regime", 0) == -1 else "Neutral USD")

            analogs.append({
                "rank": rank,
                "week_ending": str(match_row["week_ending"]),
                "distance": round(dist_val, 2),
                "realized_next_week_return": round(ret_val * 100, 2),
                "context": f"{ry_reg}, {dxy_reg}, VIX {match_row.get('vix', 18.0):.1f}",
            })

        return analogs
