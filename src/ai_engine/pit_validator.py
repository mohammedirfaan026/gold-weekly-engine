"""
Point-in-Time (PIT) Feature Validator for Gold AI Engine.
Strictly verifies that every feature and macroeconomic release used for a prediction
was genuinely known and published on or before the prediction cutoff timestamp.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class PointInTimeViolationError(Exception):
    """Raised when a feature violates strict point-in-time publication or observation limits."""

    def __init__(
        self,
        feature_name: str,
        observation_timestamp: str,
        publication_timestamp: Optional[str],
        prediction_timestamp: str,
        reason: str,
    ):
        self.feature_name = feature_name
        self.observation_timestamp = observation_timestamp
        self.publication_timestamp = publication_timestamp
        self.prediction_timestamp = prediction_timestamp
        self.reason = reason
        super().__init__(
            f"[POINT-IN-TIME VIOLATION] Feature '{feature_name}' failed PIT validation at {prediction_timestamp}: "
            f"Observed={observation_timestamp}, Published={publication_timestamp}. Reason: {reason}"
        )


class PointInTimeFeatureValidator:
    """Reusable point-in-time auditor for weekly feature matrices and macro inputs."""

    @staticmethod
    def validate_feature_timestamps(
        feature_metadata: List[Dict[str, Any]],
        prediction_timestamp: Union[str, datetime, pd.Timestamp],
        strict: bool = True,
        as_of_clock: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Validates an array of feature timestamp metadata against the prediction cutoff.

        Each element in feature_metadata should contain:
        - 'name': Feature or dataset name (e.g. 'real_yield_10y')
        - 'observation_timestamp': Timestamp of the market observation
        - 'publication_timestamp': Optional publication release timestamp
        """
        pred_dt = pd.to_datetime(prediction_timestamp, utc=True).to_pydatetime()
        clock_dt = as_of_clock or datetime.now(timezone.utc)
        violations: List[Dict[str, Any]] = []

        for item in feature_metadata:
            feat_name = item.get("name", "unknown_feature")
            obs_raw = item.get("observation_timestamp")
            pub_raw = item.get("publication_timestamp")

            if obs_raw is None:
                viol = {
                    "feature_name": feat_name,
                    "observation_timestamp": "MISSING",
                    "publication_timestamp": str(pub_raw),
                    "prediction_timestamp": pred_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "reason": "Missing observation timestamp.",
                }
                violations.append(viol)
                if strict:
                    raise PointInTimeViolationError(**viol)
                continue

            obs_dt = pd.to_datetime(obs_raw, utc=True).to_pydatetime()

            # Rule 1: Observation time cannot be after prediction cutoff
            if obs_dt > pred_dt:
                viol = {
                    "feature_name": feat_name,
                    "observation_timestamp": obs_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "publication_timestamp": str(pub_raw),
                    "prediction_timestamp": pred_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "reason": "Observation timestamp is in the future relative to prediction cutoff.",
                }
                violations.append(viol)
                if strict:
                    raise PointInTimeViolationError(**viol)
                continue

            # Rule 2: If publication timestamp exists, it must be <= prediction cutoff
            if pub_raw is not None and str(pub_raw).upper() not in {"NONE", "NAN", "N/A", ""}:
                pub_dt = pd.to_datetime(pub_raw, utc=True).to_pydatetime()
                if pub_dt > pred_dt:
                    viol = {
                        "feature_name": feat_name,
                        "observation_timestamp": obs_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "publication_timestamp": pub_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "prediction_timestamp": pred_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "reason": "Publication timestamp occurs after prediction cutoff (look-ahead leakage).",
                    }
                    violations.append(viol)
                    if strict:
                        raise PointInTimeViolationError(**viol)
                    continue

        return {
            "is_valid": len(violations) == 0,
            "prediction_timestamp": pred_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "features_audited": len(feature_metadata),
            "violation_count": len(violations),
            "violations": violations,
        }
