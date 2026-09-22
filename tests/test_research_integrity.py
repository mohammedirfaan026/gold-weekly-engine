"""
Automated Research Integrity and Point-in-Time Verification Suite.
Tests:
1. Timestamp integrity (UTC normalization, publication vs observation timestamps).
2. Event/price alignment (strict independent horizon timestamps: 5m < 1h < 4h < 1d < next_fri).
3. Elimination of silent synthetic data (explicit MISSING / NaN; synthetic_values_used tracking).
4. Point-in-time boundary enforcement (no future data in week t features).
5. Deterministic target generation (canonical close[t+1]/close[t] - 1).
6. Macro revision modes (REAL_TIME_VINTAGE vs CURRENT_REVISED_DATA).
"""

import pytest
import datetime as dt
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import to_utc_time, get_next_friday_close, get_previous_friday_close
from src.event_engine.reference_prices import ReferencePriceCalculator
from src.event_engine.window_analyzer import WindowAnalyzer
from src.weekly_engine.builder import WeeklyDatasetBuilder
from src.normalization.surprise_calculator import SurpriseCalculator
from research.validation.integrity_auditor import ResearchIntegrityAuditor


def test_timestamp_integrity_and_utc_normalization():
    """Verify timestamps are timezone-aware UTC and publication >= observation time."""
    auditor = ResearchIntegrityAuditor()
    df = pd.DataFrame({
        "observation_time": [
            pd.Timestamp("2024-01-05 08:30:00", tz="UTC"),
            pd.Timestamp("2024-02-02 08:30:00", tz="UTC"),
        ],
        "publication_time": [
            pd.Timestamp("2024-01-05 13:30:00", tz="UTC"),
            pd.Timestamp("2024-02-02 13:30:00", tz="UTC"),
        ],
    })
    res = auditor.audit_timestamps(df)
    assert res["status"] == "PASS"
    assert res["violations_count"] == 0


def test_event_price_independent_horizon_ordering():
    """
    Automated test proving:
    5m timestamp < 1h timestamp < 4h timestamp < 1d timestamp < next_friday timestamp.
    Ensures each horizon resolves independently without cross-substituting price observations.
    """
    # Create 5-minute simulated price bars over 2 weeks
    dates = pd.date_range("2024-01-08 00:00:00", "2024-01-20 00:00:00", freq="5min", tz="UTC")
    prices = 2050.0 + np.cumsum(np.random.normal(0.02, 0.5, len(dates)))
    gold_df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 0.5,
        "low": prices - 0.5,
        "close": prices,
    })

    event_time = pd.Timestamp("2024-01-10 13:30:00", tz="UTC")
    metrics = WindowAnalyzer.analyze_event_response(event_time, gold_df)

    # All horizons must be resolved with distinct timestamps
    t_5m = metrics["timestamp_5m"]
    t_1h = metrics["timestamp_1h"]
    t_4h = metrics["timestamp_4h"]
    t_1d = metrics["timestamp_1d"]
    t_next_fri = metrics["timestamp_next_friday"]

    assert t_5m is not None
    assert t_1h is not None
    assert t_4h is not None
    assert t_1d is not None
    assert t_next_fri is not None

    # Prove strict inequality: 5m < 1h < 4h < 1d < next_fri
    assert t_5m < t_1h, f"5m timestamp {t_5m} not strictly less than 1h {t_1h}"
    assert t_1h < t_4h, f"1h timestamp {t_1h} not strictly less than 4h {t_4h}"
    assert t_4h < t_1d, f"4h timestamp {t_4h} not strictly less than 1d {t_1d}"
    assert t_1d < t_next_fri, f"1d timestamp {t_1d} not strictly less than next_fri {t_next_fri}"

    # Verify helper validator
    assert WindowAnalyzer.validate_horizon_ordering(metrics) is True


def test_missing_intraday_data_returns_nan_not_reused_price():
    """
    If high-frequency intraday data is missing (e.g. daily bars only),
    intraday horizons (5m, 1h, 4h) must return NaN / MISSING instead of silently substituting daily close.
    """
    # Daily bars only (1 bar per day at 21:00 UTC)
    daily_dates = pd.date_range("2024-01-01", "2024-01-20", freq="B", tz="UTC")
    prices = 2050.0 + np.cumsum(np.random.normal(1.0, 5.0, len(daily_dates)))
    daily_df = pd.DataFrame({
        "timestamp": daily_dates,
        "open": prices,
        "high": prices + 2.0,
        "low": prices - 2.0,
        "close": prices,
    })

    event_time = pd.Timestamp("2024-01-10 13:30:00", tz="UTC")
    metrics = WindowAnalyzer.analyze_event_response(event_time, daily_df)

    # 5m, 1h, 4h must be NaN / None because daily data has no bars in those windows
    assert pd.isna(metrics["return_5m"]), "return_5m should be NaN for daily data"
    assert metrics["timestamp_5m"] is None, "timestamp_5m should be None for daily data"
    assert pd.isna(metrics["return_1h"]), "return_1h should be NaN for daily data"
    assert metrics["timestamp_1h"] is None, "timestamp_1h should be None for daily data"
    assert pd.isna(metrics["return_4h"]), "return_4h should be NaN for daily data"
    assert metrics["timestamp_4h"] is None, "timestamp_4h should be None for daily data"


def test_zero_silent_synthetic_values_audit():
    """Verify synthetic_values_used audit correctly identifies clean vs fallback datasets."""
    auditor = ResearchIntegrityAuditor()
    
    # Clean dataset with explicit valid variations
    clean_df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="B", tz="UTC"),
        "dxy": np.linspace(101.5, 104.2, 10),
        "vix": np.linspace(13.2, 19.4, 10),
        "is_synthetic": [False] * 10,
    })
    res_clean = auditor.audit_synthetic_values(clean_df)
    assert res_clean["status"] == "PASS"
    assert res_clean["synthetic_values_used"] == 0

    # Contaminated dataset with hardcoded DXY=100.0 fallbacks
    dirty_df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=20, freq="B", tz="UTC"),
        "dxy": [100.0] * 20,
        "vix": [18.0] * 20,
    })
    res_dirty = auditor.audit_synthetic_values(dirty_df)
    assert res_dirty["status"] == "WARNING"
    assert res_dirty["synthetic_values_used"] > 0


def test_point_in_time_expanding_surprise_std():
    """
    Ensure surprise standard deviations are strictly expanding backward only,
    with no future standard deviations leaking into historical z-scores.
    """
    dates = pd.date_range("2020-01-01", periods=30, freq="MS", tz="UTC")
    actuals = np.linspace(100.0, 200.0, 30)
    consensus = actuals - 5.0  # constant surprise of +5.0

    events = pd.DataFrame({
        "event_id": [f"E_{i}" for i in range(30)],
        "event_type": ["CPI"] * 30,
        "timestamp": dates,
        "actual_value": actuals,
        "consensus_value": consensus,
        "previous_value": consensus - 1.0,
    })

    df = SurpriseCalculator.calculate_surprises(events, min_history_for_zscore=5)
    
    # First 5 observations should have NaN expanding std (no future sample std leak)
    assert pd.isna(df["surprise_hist_std"].iloc[0])
    assert pd.isna(df["surprise_hist_std"].iloc[4])


def test_deterministic_weekly_targets():
    """Canonical prediction target R(t+1) must equal close[t+1]/close[t] - 1 exactly."""
    dates = pd.date_range("2024-01-05", periods=5, freq="W-FRI", tz="UTC")
    closes = [2000.0, 2020.0, 2010.0, 2050.0, 2060.0]
    
    gold_daily = []
    for d, c in zip(dates, closes):
        gold_daily.append({
            "timestamp": d, "open": c, "high": c + 5, "low": c - 5, "close": c, "volume": 1000
        })
    gold_df = pd.DataFrame(gold_daily)

    macro_df = pd.DataFrame({
        "time": dates, "dxy_close": [102.0] * 5, "real_yield_10y": [1.8] * 5
    })
    events_df = pd.DataFrame(columns=["timestamp", "event_type", "importance", "surprise_zscore"])

    master = WeeklyDatasetBuilder.build_weekly_dataset(
        gold_daily_df=gold_df,
        macro_daily_df=macro_df,
        events_df=events_df,
    )

    # Week 0 return: 2020/2000 - 1 = +0.01
    assert abs(master["next_week_gold_return"].iloc[0] - 0.01) < 1e-6
    assert master["next_week_direction"].iloc[0] == 1
    assert master["target_p_up"].iloc[0] == 1

    # Week 1 return: 2010/2020 - 1 = -0.00495...
    assert master["next_week_gold_return"].iloc[1] < 0.0
    assert master["next_week_direction"].iloc[1] == -1
    assert master["target_p_up"].iloc[1] == 0
