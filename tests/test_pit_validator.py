"""
Unit Tests for Point-in-Time Feature Validator, Shadow Logger, and Zero-Autonomous Invariant.
Ensures fail-closed timestamp verification, immutable forward testing, and strict absence of order execution.
"""

from __future__ import annotations
import os
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.ai_engine.pit_validator import (
    PointInTimeFeatureValidator,
    PointInTimeViolationError,
)
from src.ai_engine.shadow_logger import ShadowLogger


def test_pit_validator_valid_timestamps():
    meta = [
        {
            "name": "gold_spot",
            "observation_timestamp": "2026-09-18 21:00:00 UTC",
            "publication_timestamp": "2026-09-18 21:00:00 UTC",
        },
        {
            "name": "real_yield_10y",
            "observation_timestamp": "2026-09-18 20:00:00 UTC",
            "publication_timestamp": "2026-09-18 20:30:00 UTC",
        },
    ]
    cutoff = "2026-09-18 21:00:00 UTC"
    report = PointInTimeFeatureValidator.validate_feature_timestamps(meta, prediction_timestamp=cutoff, strict=True)
    assert report["is_valid"] is True
    assert report["violation_count"] == 0
    assert len(report["violations"]) == 0


def test_pit_validator_future_observation_strict():
    meta = [
        {
            "name": "real_yield_10y",
            "observation_timestamp": "2026-09-19 12:00:00 UTC",  # 1 day after cutoff
            "publication_timestamp": "2026-09-19 13:00:00 UTC",
        }
    ]
    cutoff = "2026-09-18 21:00:00 UTC"
    with pytest.raises(PointInTimeViolationError) as exc_info:
        PointInTimeFeatureValidator.validate_feature_timestamps(meta, prediction_timestamp=cutoff, strict=True)
    assert "real_yield_10y" in str(exc_info.value)
    assert "future relative to prediction cutoff" in str(exc_info.value)


def test_pit_validator_future_observation_non_strict():
    meta = [
        {
            "name": "dxy_index",
            "observation_timestamp": "2026-09-20 00:00:00 UTC",
            "publication_timestamp": None,
        }
    ]
    cutoff = "2026-09-18 21:00:00 UTC"
    report = PointInTimeFeatureValidator.validate_feature_timestamps(meta, prediction_timestamp=cutoff, strict=False)
    assert report["is_valid"] is False
    assert report["violation_count"] == 1
    assert report["violations"][0]["feature_name"] == "dxy_index"


def test_pit_validator_future_publication_strict():
    meta = [
        {
            "name": "hy_oas",
            "observation_timestamp": "2026-09-18 20:00:00 UTC",
            "publication_timestamp": "2026-09-19 09:00:00 UTC",  # Published Saturday morning after Friday cutoff
        }
    ]
    cutoff = "2026-09-18 21:00:00 UTC"
    with pytest.raises(PointInTimeViolationError) as exc_info:
        PointInTimeFeatureValidator.validate_feature_timestamps(meta, prediction_timestamp=cutoff, strict=True)
    assert "look-ahead leakage" in str(exc_info.value)


def test_pit_validator_missing_observation():
    meta = [
        {
            "name": "vix_index",
            "observation_timestamp": None,
            "publication_timestamp": None,
        }
    ]
    cutoff = "2026-09-18 21:00:00 UTC"
    with pytest.raises(PointInTimeViolationError) as exc_info:
        PointInTimeFeatureValidator.validate_feature_timestamps(meta, prediction_timestamp=cutoff, strict=True)
    assert "Missing observation timestamp" in str(exc_info.value)


def test_shadow_logger_immutability(tmp_path):
    sl = ShadowLogger(shadow_dir=tmp_path)
    sample_brief = {
        "observation_week": "2026-09-18",
        "prediction_timestamp": "2026-09-18 21:00:00 UTC",
        "bias_score": 0.15,
        "expected_return_pct": 0.65,
        "taxonomy_stance": "Bullish bias -- confirmation required",
        "expected_corridor": {
            "lower_support_10pct": 6150.0,
            "upper_resistance_90pct": 6350.0,
        },
        "confidence_calibration": {"tier": "MODERATE"},
        "no_trade_circuit_breaker": {"status_label": "TRADE PERMITTED"},
    }
    features = {"delta_real_yield_1w": -0.05, "dxy_return_1w": -0.01}

    # First save succeeds
    rec = sl.save_prediction(brief=sample_brief, features_snapshot=features)
    assert rec["prediction_week"] == "2026-09-18"
    assert rec["realized_next_week_return"] is None

    # Second save for identical week without force_update must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        sl.save_prediction(brief=sample_brief, features_snapshot=features)
    assert "IMMUTABILITY INVARIANT VIOLATION" in str(exc_info.value)


def test_shadow_logger_outcome_resolution(tmp_path):
    sl = ShadowLogger(shadow_dir=tmp_path)
    sample_brief = {
        "observation_week": "2026-09-18",
        "prediction_timestamp": "2026-09-18 21:00:00 UTC",
        "bias_score": 0.20,
        "expected_return_pct": 0.80,
        "taxonomy_stance": "Bullish bias -- confirmation required",
        "expected_corridor": {
            "lower_support_10pct": 6150.0,
            "upper_resistance_90pct": 6350.0,
        },
        "confidence_calibration": {"tier": "MODERATE"},
        "no_trade_circuit_breaker": {"status_label": "TRADE PERMITTED"},
    }
    features = {"delta_real_yield_1w": -0.05}

    sl.save_prediction(brief=sample_brief, features_snapshot=features)

    # Resolve outcome post-market close: Bullish forecast and positive realized return -> WIN
    resolved = sl.resolve_outcome(
        prediction_week="2026-09-18",
        realized_return=0.015,
        weekly_high=6320.0,
        weekly_low=6200.0,
        archetype="IN_LINE_ACCURATE",
    )
    assert resolved is not None
    assert resolved["directional_correctness"] is True
    assert resolved["corridor_containment"] is True
    assert resolved["realized_next_week_return"] == 0.015
    assert resolved["outcome_resolved_at"] is not None

    # Report verification
    report = sl.generate_shadow_report()
    assert "IMMUTABLE SHADOW-TEST AUDIT" in report
    assert "Directional Win Rate       : 100.0%" in report
    assert "Corridor Containment Rate  : 100.0%" in report
    assert "AUTONOMOUS TRADING NOT SUPPORTED" not in report  # Shadow report has immutability notice


def test_zero_autonomous_trading_invariant():
    """Verifies that no autonomous trade execution or broker order routing code exists."""
    src_dir = Path("src/ai_engine")
    prohibited_terms = [
        "place_order",
        "submit_order",
        "send_order",
        "execute_order",
        "interactive_brokers",
        "binance",
        "alpaca",
        "fix_protocol",
        "buy_order",
        "sell_order",
    ]

    for py_file in src_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8").lower()
        for term in prohibited_terms:
            assert term not in content, (
                f"Prohibited autonomous trading term '{term}' found in {py_file.name}. "
                "The engine must remain purely decision-support with no broker execution."
            )
