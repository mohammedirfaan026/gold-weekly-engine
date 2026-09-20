"""
Data Freshness and Vintage Auditor for Gold AI Engine.
Tracks observation cutoffs, publication timestamps, and data pipeline latencies
to prevent look-ahead bias and protect against stale data in production inference.
"""

from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


SERIES_PATHS = {
    "gold_spot": "data/market/gold_spot_1d.parquet",
    "real_yield_10y": "data/macro/real_yield_10y.parquet",
    "dxy_index": "data/market/dxy_1d.parquet",
    "vix_index": "data/market/vix_1d.parquet",
    "hy_oas": "data/macro/hy_oas.parquet",
    "weekly_master": "data/weekly/gold_weekly_master.parquet",
}


class DataFreshnessChecker:
    """Audits data freshness, observation timestamps, and publication lags."""

    def __init__(self, base_dir: Optional[str | Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(".")

    def check_freshness(
        self, as_of_date: Optional[datetime | str] = None
    ) -> Dict[str, Any]:
        """
        Inspects each core parquet dataset and determines freshness status.
        as_of_date defaults to current UTC time or specified prediction timestamp.
        """
        if as_of_date is None:
            ref_dt = datetime.now(timezone.utc)
        elif isinstance(as_of_date, str):
            ref_dt = pd.to_datetime(as_of_date, utc=True).to_pydatetime()
        else:
            ref_dt = as_of_date.astimezone(timezone.utc) if as_of_date.tzinfo else as_of_date.replace(tzinfo=timezone.utc)

        series_status: Dict[str, Dict[str, Any]] = {}
        all_usable = True
        stale_series: List[str] = []

        for name, rel_path in SERIES_PATHS.items():
            full_path = self.base_dir / rel_path
            if not full_path.exists():
                series_status[name] = {
                    "path": str(rel_path),
                    "exists": False,
                    "latest_observation": None,
                    "publication_timestamp": None,
                    "lag_days": 999.0,
                    "status": "MISSING",
                }
                all_usable = False
                stale_series.append(name)
                continue

            try:
                df = pd.read_parquet(full_path)
                if df.empty:
                    series_status[name] = {
                        "path": str(rel_path),
                        "exists": True,
                        "latest_observation": None,
                        "publication_timestamp": None,
                        "lag_days": 999.0,
                        "status": "EMPTY",
                    }
                    all_usable = False
                    stale_series.append(name)
                    continue

                # Identify date/timestamp column
                date_col = None
                for candidate in ["timestamp", "date", "week_ending", "time"]:
                    if candidate in df.columns:
                        date_col = candidate
                        break

                if date_col is None:
                    series_status[name] = {
                        "path": str(rel_path),
                        "exists": True,
                        "latest_observation": None,
                        "publication_timestamp": None,
                        "lag_days": 999.0,
                        "status": "NO_DATE_COL",
                    }
                    continue

                latest_raw = df[date_col].iloc[-1]
                latest_dt = pd.to_datetime(latest_raw, utc=True).to_pydatetime()

                pub_dt = None
                if "publication_time" in df.columns and pd.notna(df["publication_time"].iloc[-1]):
                    pub_dt = pd.to_datetime(df["publication_time"].iloc[-1], utc=True).to_pydatetime()

                lag_days = max(0.0, (ref_dt - latest_dt).total_seconds() / 86400.0)

                # Classify status:
                # <= 3.5 days -> FRESH (e.g. Friday close evaluated through Monday open)
                # 3.5 to 5.5 days -> WARNED (holiday weekend)
                # > 5.5 days -> STALE
                if lag_days <= 3.5:
                    status = "FRESH"
                elif lag_days <= 5.5:
                    status = "WARNED"
                else:
                    status = "STALE"
                    stale_series.append(name)
                    all_usable = False

                series_status[name] = {
                    "path": str(rel_path),
                    "exists": True,
                    "latest_observation": latest_dt.strftime("%Y-%m-%d %H:%M UTC"),
                    "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M UTC") if pub_dt else "N/A",
                    "lag_days": round(lag_days, 1),
                    "status": status,
                }

            except Exception as e:
                series_status[name] = {
                    "path": str(rel_path),
                    "exists": True,
                    "latest_observation": None,
                    "publication_timestamp": None,
                    "lag_days": 999.0,
                    "status": f"ERROR: {str(e)}",
                }
                all_usable = False
                stale_series.append(name)

        return {
            "reference_timestamp": ref_dt.strftime("%Y-%m-%d %H:%M UTC"),
            "is_usable": all_usable,
            "stale_series": stale_series,
            "series": series_status,
        }

    def format_freshness_table(self, report: Dict[str, Any]) -> str:
        """Renders an institutional Markdown table of data freshness."""
        lines = [
            f"Observation Reference: {report['reference_timestamp']}",
            f"Pipeline Status      : {'OPERATIONAL (All Fresh)' if report['is_usable'] else 'DEGRADED / STALE DATA DETECTED'}",
            "",
            "| Series Identifier | Latest Observation | Pub Timestamp | Age (Days) | Status |",
            "|---|---|---|---:|:---:|",
        ]
        for name, item in report["series"].items():
            obs = item.get("latest_observation") or "MISSING"
            pub = item.get("publication_timestamp") or "N/A"
            age = f"{item.get('lag_days', 999.0):.1f}"
            st = item.get("status", "UNKNOWN")
            lines.append(f"| `{name}` | {obs} | {pub} | {age} | **{st}** |")

        return "\n".join(lines)
