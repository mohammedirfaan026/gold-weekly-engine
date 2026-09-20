"""
Data Freshness and Vintage Auditor for Gold AI Engine.
Tracks observation cutoffs, publication timestamps, and data pipeline latencies
to prevent look-ahead bias and protect against stale or future-vintage data.
"""

from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


SERIES_CONFIGS = {
    "gold_spot": {
        "path": "data/market/gold_spot_1d.parquet",
        "max_age_days": 3.5,
        "required_cols": ["close"],
    },
    "real_yield_10y": {
        "path": "data/macro/real_yield_10y.parquet",
        "max_age_days": 4.5,
        "required_cols": ["value"],
    },
    "dxy_index": {
        "path": "data/market/dxy_1d.parquet",
        "max_age_days": 3.5,
        "required_cols": ["close"],
    },
    "vix_index": {
        "path": "data/market/vix_1d.parquet",
        "max_age_days": 3.5,
        "required_cols": ["close"],
    },
    "hy_oas": {
        "path": "data/macro/hy_oas.parquet",
        "max_age_days": 4.5,
        "required_cols": ["value"],
    },
    "weekly_master": {
        "path": "data/weekly/gold_weekly_master.parquet",
        "max_age_days": 3.5,
        "required_cols": ["close", "real_yield_10y", "dxy_close"],
    },
}


class DataFreshnessChecker:
    """Audits data freshness, observation timestamps, and publication lags."""

    def __init__(
        self,
        base_dir: Optional[str | Path] = None,
        custom_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.base_dir = Path(base_dir) if base_dir else Path(".")
        self.configs = custom_configs or SERIES_CONFIGS

    def check_freshness(
        self, as_of_date: Optional[datetime | str] = None
    ) -> Dict[str, Any]:
        """
        Inspects each core parquet dataset and determines freshness and PIT status.
        Fails closed if any critical series is missing, stale, or future-dated.
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
        critical_errors: List[str] = []

        for name, cfg in self.configs.items():
            rel_path = cfg["path"]
            max_age = cfg.get("max_age_days", 3.5)
            required_cols = cfg.get("required_cols", [])
            full_path = self.base_dir / rel_path

            if not full_path.exists():
                series_status[name] = {
                    "path": str(rel_path),
                    "exists": False,
                    "latest_observation": None,
                    "publication_timestamp": None,
                    "lag_days": 999.0,
                    "max_permitted_age_days": max_age,
                    "status": "MISSING",
                    "safe_to_use": False,
                    "reason": "Parquet file does not exist on disk.",
                }
                all_usable = False
                stale_series.append(name)
                critical_errors.append(f"{name}: File missing ({rel_path})")
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
                        "max_permitted_age_days": max_age,
                        "status": "EMPTY",
                        "safe_to_use": False,
                        "reason": "Parquet table is empty.",
                    }
                    all_usable = False
                    stale_series.append(name)
                    critical_errors.append(f"{name}: Table is empty")
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
                        "max_permitted_age_days": max_age,
                        "status": "NO_DATE_COL",
                        "safe_to_use": False,
                        "reason": "No recognizable date/timestamp column found.",
                    }
                    all_usable = False
                    critical_errors.append(f"{name}: No timestamp column")
                    continue

                latest_raw = df[date_col].iloc[-1]
                latest_dt = pd.to_datetime(latest_raw, utc=True).to_pydatetime()

                pub_dt = None
                if "publication_time" in df.columns and pd.notna(df["publication_time"].iloc[-1]):
                    pub_dt = pd.to_datetime(df["publication_time"].iloc[-1], utc=True).to_pydatetime()

                # Check partial / incomplete latest row
                tail_row = df.iloc[-1]
                missing_cols = [c for c in required_cols if c in df.columns and pd.isna(tail_row[c])]
                if missing_cols:
                    series_status[name] = {
                        "path": str(rel_path),
                        "exists": True,
                        "latest_observation": latest_dt.strftime("%Y-%m-%d %H:%M UTC"),
                        "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M UTC") if pub_dt else "N/A",
                        "lag_days": 0.0,
                        "max_permitted_age_days": max_age,
                        "status": "PARTIAL_ROW_ERROR",
                        "safe_to_use": False,
                        "reason": f"Latest row contains NaN in required fields: {missing_cols}",
                    }
                    all_usable = False
                    critical_errors.append(f"{name}: Missing required columns in tail row ({missing_cols})")
                    continue

                # Check future timestamp (future vintage error)
                if latest_dt > ref_dt:
                    series_status[name] = {
                        "path": str(rel_path),
                        "exists": True,
                        "latest_observation": latest_dt.strftime("%Y-%m-%d %H:%M UTC"),
                        "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M UTC") if pub_dt else "N/A",
                        "lag_days": 0.0,
                        "max_permitted_age_days": max_age,
                        "status": "FUTURE_VINTAGE_ERROR",
                        "safe_to_use": False,
                        "reason": f"Observation timestamp {latest_dt} is in future relative to cutoff {ref_dt}",
                    }
                    all_usable = False
                    critical_errors.append(f"{name}: Future-dated observation")
                    continue

                # Check publication timestamp > ref_dt
                if pub_dt and pub_dt > ref_dt:
                    series_status[name] = {
                        "path": str(rel_path),
                        "exists": True,
                        "latest_observation": latest_dt.strftime("%Y-%m-%d %H:%M UTC"),
                        "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M UTC"),
                        "lag_days": 0.0,
                        "max_permitted_age_days": max_age,
                        "status": "FUTURE_PUB_ERROR",
                        "safe_to_use": False,
                        "reason": f"Publication timestamp {pub_dt} occurs after prediction cutoff {ref_dt}",
                    }
                    all_usable = False
                    critical_errors.append(f"{name}: Publication timestamp after prediction cutoff")
                    continue

                lag_days = max(0.0, (ref_dt - latest_dt).total_seconds() / 86400.0)

                # Classify status based on max permitted age:
                if lag_days <= max_age:
                    status = "FRESH"
                    safe = True
                elif lag_days <= (max_age + 1.5):
                    status = "WARNED"
                    safe = True
                else:
                    status = "STALE"
                    safe = False
                    stale_series.append(name)
                    all_usable = False
                    critical_errors.append(f"{name}: Data is stale ({lag_days:.1f} days old > max {max_age} days)")

                series_status[name] = {
                    "path": str(rel_path),
                    "exists": True,
                    "latest_observation": latest_dt.strftime("%Y-%m-%d %H:%M UTC"),
                    "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M UTC") if pub_dt else "N/A",
                    "lag_days": round(lag_days, 1),
                    "max_permitted_age_days": max_age,
                    "status": status,
                    "safe_to_use": safe,
                    "reason": "OK" if safe else f"Age exceeds maximum permitted threshold ({max_age} days)",
                }

            except Exception as e:
                series_status[name] = {
                    "path": str(rel_path),
                    "exists": True,
                    "latest_observation": None,
                    "publication_timestamp": None,
                    "lag_days": 999.0,
                    "max_permitted_age_days": max_age,
                    "status": f"ERROR",
                    "safe_to_use": False,
                    "reason": f"Exception reading parquet: {str(e)}",
                }
                all_usable = False
                stale_series.append(name)
                critical_errors.append(f"{name}: Error {str(e)}")

        return {
            "reference_timestamp": ref_dt.strftime("%Y-%m-%d %H:%M UTC"),
            "is_usable": all_usable,
            "stale_series": stale_series,
            "critical_errors": critical_errors,
            "series": series_status,
        }

    def format_freshness_table(self, report: Dict[str, Any]) -> str:
        """Renders an institutional Markdown table of data freshness."""
        lines = [
            f"Observation Reference: {report['reference_timestamp']}",
            f"Pipeline Status      : {'OPERATIONAL (All Fresh & Validated)' if report['is_usable'] else 'DEGRADED / CRITICAL DATA VINTAGE ISSUES'}",
            "",
            "| Series Identifier | Latest Observation | Pub Timestamp | Age (Days) | Max Age | Safe? | Status |",
            "|---|---|---|---:|---:|:---:|:---:|",
        ]
        for name, item in report["series"].items():
            obs = item.get("latest_observation") or "MISSING"
            pub = item.get("publication_timestamp") or "N/A"
            age = f"{item.get('lag_days', 999.0):.1f}"
            max_age = f"{item.get('max_permitted_age_days', 3.5):.1f}"
            safe_str = "YES" if item.get("safe_to_use", False) else "NO"
            st = item.get("status", "UNKNOWN")
            lines.append(f"| `{name}` | {obs} | {pub} | {age} | {max_age} | {safe_str} | **{st}** |")

        if report.get("critical_errors"):
            lines.append("")
            lines.append("**Critical Pipeline Guardrail Violations:**")
            for err in report["critical_errors"]:
                lines.append(f"- {err}")

        return "\n".join(lines)
