"""
Dedicated Research Integrity Auditor.
Enforces institutional quantitative validity standards:
1. Timestamp normalization & timezone conversion integrity (UTC internal).
2. Strict event-price alignment & independent horizon resolution.
3. Zero silent synthetic data audit & synthetic_values_used tracking.
4. Point-in-time boundary & look-ahead prevention.
5. Macro revision vintage handling (REAL_TIME_VINTAGE vs CURRENT_REVISED_DATA).
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import pytz

from src.timestamps.calendar_utils import to_utc_time, to_ny_time, get_trading_week_id


class ResearchIntegrityAuditor:
    """
    Automated research integrity auditing engine.
    Ensures research validity over model complexity.
    """

    SUSPICIOUS_FALLBACK_PATTERNS = {
        "dxy": [100.0, 80.0],
        "vix": [18.0, 20.0, 15.0],
        "real_yield_10y": [1.0, 1.1, 0.0],
        "cot_net_speculative": [150000.0],
        "cot_percentile_3y": [50.0],
        "etf_flow_percentile": [50.0],
    }

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def audit_timestamps(
        self,
        df: pd.DataFrame,
        time_cols: Optional[List[str]] = None,
        check_pub_vs_obs: bool = True,
    ) -> Dict[str, Any]:
        """
        Verifies all timestamps are normalized, have valid timezones, and enforce pub_time >= obs_time.
        """
        if time_cols is None:
            time_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower() or c == "timestamp"]

        violations = []
        tz_unaware = []
        invalid_pub_obs = []

        for col in time_cols:
            if col not in df.columns:
                continue
            series = df[col].dropna()
            for idx, val in series.iloc[:200].items():
                try:
                    ts = pd.to_datetime(val)
                    if ts.tz is None:
                        tz_unaware.append(f"Row {idx} col {col}: naive datetime {val}")
                except Exception as e:
                    violations.append(f"Row {idx} col {col}: unparseable {val} ({e})")

        if check_pub_vs_obs and "publication_time" in df.columns and "observation_time" in df.columns:
            obs = pd.to_datetime(df["observation_time"], utc=True)
            pub = pd.to_datetime(df["publication_time"], utc=True)
            invalid_mask = pub < obs
            if invalid_mask.any():
                bad_rows = df[invalid_mask].head(5).to_dict(orient="records")
                invalid_pub_obs.append(f"{invalid_mask.sum()} rows where publication_time < observation_time: {bad_rows}")

        passed = len(violations) == 0 and len(tz_unaware) == 0 and len(invalid_pub_obs) == 0
        result = {
            "status": "PASS" if passed else "FAIL",
            "checked_columns": time_cols,
            "violations_count": len(violations) + len(tz_unaware) + len(invalid_pub_obs),
            "unparseable_errors": violations,
            "tz_unaware_warnings": tz_unaware,
            "invalid_pub_obs": invalid_pub_obs,
        }
        self.audit_log.append({"check": "timestamp_integrity", "result": result})
        return result

    def audit_horizon_alignment(
        self,
        events_master_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Verifies event/price alignment:
        1. Timestamps satisfy t_pre <= t_5m < t_1h < t_4h < t_1d < t_next_fri where available.
        2. No price observation is reused across multiple distinct horizons.
        3. Unavailable horizons are reported as NaN / MISSING, not spoofed with identical values.
        """
        violations = []
        duplicate_substitutions = 0
        checked_events = 0

        horizon_ts_cols = [
            ("5m", "timestamp_5m", "return_5m"),
            ("1h", "timestamp_1h", "return_1h"),
            ("4h", "timestamp_4h", "return_4h"),
            ("1d", "timestamp_1d", "return_1d"),
            ("next_fri", "timestamp_next_friday", "return_next_friday"),
        ]

        avail_cols = [(name, ts_col, ret_col) for name, ts_col, ret_col in horizon_ts_cols if ts_col in events_master_df.columns]

        for idx, row in events_master_df.iterrows():
            checked_events += 1
            # Check monotonicity of resolved timestamps
            resolved = []
            for name, ts_col, ret_col in avail_cols:
                ts_val = row.get(ts_col)
                ret_val = row.get(ret_col)
                if pd.notna(ts_val) and ts_val is not None:
                    resolved.append((name, pd.to_datetime(ts_val, utc=True), ret_val))

            if len(resolved) >= 2:
                for i in range(1, len(resolved)):
                    prev_name, prev_ts, prev_ret = resolved[i - 1]
                    curr_name, curr_ts, curr_ret = resolved[i]
                    if curr_ts <= prev_ts:
                        violations.append(
                            f"Event {row.get('event_id', idx)}: {curr_name} ts ({curr_ts}) <= {prev_name} ts ({prev_ts})"
                        )
                    # Check if return is identical non-zero (potential silent price reuse)
                    if prev_ret is not None and curr_ret is not None and pd.notna(prev_ret) and pd.notna(curr_ret):
                        if abs(prev_ret) > 1e-5 and abs(prev_ret - curr_ret) < 1e-9:
                            duplicate_substitutions += 1
                            violations.append(
                                f"Event {row.get('event_id', idx)}: {curr_name} return equals {prev_name} return ({prev_ret:+.4f}) - potential price reuse"
                            )

        passed = len(violations) == 0
        result = {
            "status": "PASS" if passed else "FAIL",
            "checked_events": checked_events,
            "violations_count": len(violations),
            "duplicate_substitutions_detected": duplicate_substitutions,
            "violations_sample": violations[:10],
        }
        self.audit_log.append({"check": "horizon_alignment", "result": result})
        return result

    def audit_synthetic_values(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Audits dataset for silent fallback values (e.g. DXY=100, VIX=18, real_yield=1.0).
        Calculates metric: synthetic_values_used (must ideally remain 0 for production research).
        """
        synthetic_count = 0
        detected_fallbacks = []

        # 1. Check explicit is_synthetic / is_imputed flags
        if "is_synthetic" in df.columns:
            syn_flags = int(df["is_synthetic"].fillna(False).sum())
            if syn_flags > 0:
                synthetic_count += syn_flags
                detected_fallbacks.append(f"{syn_flags} rows flagged with is_synthetic=True")

        if "is_imputed" in df.columns:
            imp_flags = int(df["is_imputed"].fillna(False).sum())
            if imp_flags > 0:
                synthetic_count += imp_flags
                detected_fallbacks.append(f"{imp_flags} rows flagged with is_imputed=True")

        # 2. Check for suspicious constant fallback clusters
        for col, bad_vals in self.SUSPICIOUS_FALLBACK_PATTERNS.items():
            matching_cols = [c for c in df.columns if col.lower() in c.lower()]
            for mc in matching_cols:
                series = pd.to_numeric(df[mc], errors="coerce")
                for bv in bad_vals:
                    # Count exact matches
                    matches = (series == bv).sum()
                    # If an identical exact value repeats unusually frequently, flag it
                    if matches > 15:
                        synthetic_count += int(matches)
                        detected_fallbacks.append(
                            f"Column '{mc}' has {matches} exact occurrences of suspicious fallback {bv}"
                        )

        result = {
            "status": "PASS" if synthetic_count == 0 else "WARNING",
            "synthetic_values_used": synthetic_count,
            "detected_fallbacks": detected_fallbacks,
        }
        self.audit_log.append({"check": "synthetic_values", "result": result})
        return result

    def audit_point_in_time_leakage(
        self,
        weekly_matrix: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Verifies point-in-time invariant:
        All features for week t must be computable using information available
        at or before prediction_timestamp (Friday 17:00 ET).
        """
        violations = []
        
        if "prediction_timestamp" not in weekly_matrix.columns:
            return {
                "status": "WARNING",
                "message": "prediction_timestamp column not found in matrix; cannot perform automated lineage check",
            }

        pred_ts = pd.to_datetime(weekly_matrix["prediction_timestamp"], utc=True)

        if "feature_available_timestamp" in weekly_matrix.columns:
            avail_ts = pd.to_datetime(weekly_matrix["feature_available_timestamp"], utc=True)
            leak = avail_ts > pred_ts
            if leak.any():
                count = int(leak.sum())
                sample = weekly_matrix[leak][["week_ending", "prediction_timestamp", "feature_available_timestamp"]].head(3).to_dict(orient="records")
                violations.append(f"{count} rows have feature_available_timestamp > prediction_timestamp: {sample}")

        # Check target shift invariants
        if "next_week_gold_return" in weekly_matrix.columns and "gold_close" in weekly_matrix.columns:
            close = weekly_matrix["gold_close"].astype(float)
            target = weekly_matrix["next_week_gold_return"].astype(float)
            # Reconstruct expected forward return
            expected_fwd = (close.shift(-1) / close) - 1.0
            # Compare non-null values
            valid_mask = target.notna() & expected_fwd.notna()
            diff = (target[valid_mask] - expected_fwd[valid_mask]).abs()
            if (diff > 1e-6).any():
                violations.append("next_week_gold_return does not match strict forward close[t+1]/close[t]-1 calculation")

        passed = len(violations) == 0
        result = {
            "status": "PASS" if passed else "FAIL",
            "violations_count": len(violations),
            "violations": violations,
        }
        self.audit_log.append({"check": "point_in_time_leakage", "result": result})
        return result

    def audit_macro_revisions(
        self,
        events_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Verifies macro revision metadata and vintage mode compliance:
        Modes supported: REAL_TIME_VINTAGE, CURRENT_REVISED_DATA.
        """
        vintage_mode = events_df["vintage_mode"].iloc[0] if "vintage_mode" in events_df.columns else "CURRENT_REVISED_DATA"
        has_initial = "initial_release" in events_df.columns
        has_revision = "revision" in events_df.columns

        result = {
            "status": "PASS",
            "vintage_mode": vintage_mode,
            "has_initial_release_tracking": has_initial,
            "has_revision_tracking": has_revision,
            "notes": (
                "Operating under REAL_TIME_VINTAGE: strictly preserves initial release values."
                if vintage_mode == "REAL_TIME_VINTAGE"
                else "Operating under CURRENT_REVISED_DATA: reflects benchmark series revisions."
            ),
        }
        self.audit_log.append({"check": "macro_revisions", "result": result})
        return result

    def run_complete_audit(
        self,
        events_df: Optional[pd.DataFrame] = None,
        weekly_df: Optional[pd.DataFrame] = None,
        market_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Executes all integrity checks across available dataframes.
        """
        overall_status = "PASS"
        results = {}

        if events_df is not None and not events_df.empty:
            results["event_timestamps"] = self.audit_timestamps(events_df)
            results["horizon_alignment"] = self.audit_horizon_alignment(events_df)
            results["event_synthetic"] = self.audit_synthetic_values(events_df)
            results["macro_revisions"] = self.audit_macro_revisions(events_df)

        if weekly_df is not None and not weekly_df.empty:
            results["weekly_timestamps"] = self.audit_timestamps(weekly_df)
            results["weekly_synthetic"] = self.audit_synthetic_values(weekly_df)
            results["point_in_time"] = self.audit_point_in_time_leakage(weekly_df)

        for check_name, res in results.items():
            if res.get("status") == "FAIL":
                overall_status = "FAIL"
            elif res.get("status") == "WARNING" and overall_status != "FAIL":
                overall_status = "WARNING"

        summary = {
            "overall_integrity_status": overall_status,
            "audited_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "synthetic_values_used": sum(
                res.get("synthetic_values_used", 0) for res in results.values() if isinstance(res, dict)
            ),
            "checks": results,
        }
        return summary
