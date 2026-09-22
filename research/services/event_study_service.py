"""
Event Study Research Service.
Computes institutional event study metrics across horizons:
+5m, +1h, +4h, +1D, and following-Friday close.
Always reports sample size N alongside medians, means, win rates, and reversal metrics.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from database.db_session import SessionLocal
from database.models import MacroEvent


class EventStudyService:
    """
    Headless research service for macroeconomic event reaction analysis.
    """

    HORIZONS = ["5m", "1h", "4h", "1d", "next_friday"]

    def __init__(self, events_df: Optional[pd.DataFrame] = None):
        if events_df is not None:
            self.events_df = events_df
        else:
            self.events_df = self._load_from_db_or_parquet()

    def _load_from_db_or_parquet(self) -> pd.DataFrame:
        db = SessionLocal()
        try:
            records = db.query(MacroEvent).all()
            if records:
                rows = []
                for r in records:
                    rows.append({
                        "event_id": r.event_id,
                        "event_type": r.event_type,
                        "country": r.country,
                        "publication_time": r.publication_time,
                        "observation_period": r.observation_period,
                        "previous_value": r.previous_value,
                        "consensus_value": r.consensus_value,
                        "actual_value": r.actual_value,
                        "surprise_absolute": r.surprise_absolute,
                        "surprise_percentage": r.surprise_percentage,
                        "surprise_zscore": r.surprise_zscore,
                        "surprise_bucket": r.surprise_bucket,
                        "importance": r.importance,
                        "source": r.source,
                        "vintage_mode": r.vintage_mode,
                        "is_synthetic": r.is_synthetic,
                    })
                df = pd.DataFrame(rows)
            else:
                import os
                pq_path = "data/processed/events_master.parquet"
                if os.path.exists(pq_path):
                    df = pd.read_parquet(pq_path)
                else:
                    df = pd.DataFrame()
            return df
        finally:
            db.close()

    def get_event_types(self) -> List[str]:
        """Returns sorted list of distinct macroeconomic event types."""
        if self.events_df.empty or "event_type" not in self.events_df.columns:
            return []
        return sorted(self.events_df["event_type"].dropna().unique().tolist())

    def get_events_list(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Returns individual event occurrences with surprises and timestamps."""
        df = self.events_df.copy()
        if df.empty:
            return []

        if event_type:
            df = df[df["event_type"] == event_type]
        if "publication_time" in df.columns:
            time_col = "publication_time"
        else:
            time_col = "timestamp"

        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        if start_date:
            df = df[df[time_col] >= pd.to_datetime(start_date, utc=True)]
        if end_date:
            df = df[df[time_col] <= pd.to_datetime(end_date, utc=True)]

        df = df.sort_values(by=time_col, ascending=False).head(limit)
        results = []
        for _, r in df.iterrows():
            item = {
                "event_id": r.get("event_id"),
                "event_type": r.get("event_type"),
                "country": r.get("country", "US"),
                "publication_time": str(r.get(time_col)),
                "actual_value": r.get("actual_value"),
                "consensus_value": r.get("consensus_value"),
                "previous_value": r.get("previous_value"),
                "surprise_absolute": r.get("surprise_absolute"),
                "surprise_zscore": r.get("surprise_zscore"),
                "surprise_bucket": r.get("surprise_bucket"),
                "importance": r.get("importance", "high"),
                "source": r.get("source", "BLS"),
                "vintage_mode": r.get("vintage_mode", "REAL_TIME_VINTAGE"),
            }
            results.append(item)
        return results

    def get_reaction_summary(self, event_type: str) -> Dict[str, Any]:
        """
        Calculates comprehensive horizon reactions for a specific event type.
        Returns N, median, mean, std, positive %, negative %, continuation %, reversal %.
        """
        # Load master events parquet which has the calculated window returns
        import os
        pq_path = "data/processed/events_master.parquet"
        if os.path.exists(pq_path):
            df = pd.read_parquet(pq_path)
        else:
            df = self.events_df.copy()

        if df.empty or "event_type" not in df.columns:
            return {"event_type": event_type, "sample_size": 0, "horizons": {}}

        sub = df[df["event_type"].str.lower() == event_type.lower()].copy()
        n = len(sub)
        if n == 0:
            return {"event_type": event_type, "sample_size": 0, "horizons": {}}

        horizon_metrics = {}
        for h in self.HORIZONS:
            ret_col = f"return_{h}"
            if ret_col in sub.columns:
                valid_series = sub[ret_col].dropna()
                valid_n = len(valid_series)
                if valid_n > 0:
                    med = float(valid_series.median() * 100.0)
                    mean_val = float(valid_series.mean() * 100.0)
                    std_val = float(valid_series.std() * 100.0) if valid_n > 1 else 0.0
                    pos_pct = float((valid_series > 0).mean() * 100.0)
                    neg_pct = float((valid_series < 0).mean() * 100.0)
                else:
                    med, mean_val, std_val, pos_pct, neg_pct = None, None, None, None, None

                horizon_metrics[h] = {
                    "valid_n": valid_n,
                    "median_pct": round(med, 2) if med is not None else None,
                    "mean_pct": round(mean_val, 2) if mean_val is not None else None,
                    "std_pct": round(std_val, 2) if std_val is not None else None,
                    "positive_response_pct": round(pos_pct, 1) if pos_pct is not None else None,
                    "negative_response_pct": round(neg_pct, 1) if neg_pct is not None else None,
                }

        # Reversal vs continuation frequencies
        rev_counts = {}
        if "reversal_classification" in sub.columns:
            rev_series = sub["reversal_classification"].dropna()
            total_rev = len(rev_series)
            if total_rev > 0:
                for k, count in rev_series.value_counts().items():
                    rev_counts[k] = {
                        "count": int(count),
                        "pct": round(float(count / total_rev * 100.0), 1),
                    }

        return {
            "event_type": event_type,
            "sample_size": n,
            "horizons": horizon_metrics,
            "reversal_dynamics": rev_counts,
        }
