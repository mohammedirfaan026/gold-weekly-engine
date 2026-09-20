"""Unit tests for surprise calculation and point-in-time rules."""
import pytest
import numpy as np
import pandas as pd
from src.normalization.surprise_calculator import SurpriseCalculator
from src.timestamps.point_in_time import PointInTimeManager


def test_surprise_calculation_absolute_and_percentage():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC"),
        "event_type": ["CPI", "CPI", "CPI"],
        "actual_value": [3.2, 3.5, 3.0],
        "consensus_value": [3.0, 3.5, 3.2],
        "previous_value": [3.1, 3.2, 3.5],
    })
    res = SurpriseCalculator.calculate_surprises(df)
    
    # Event 0: 3.2 - 3.0 = +0.2
    assert pytest.approx(res["surprise_absolute"].iloc[0], 0.001) == 0.2
    assert pytest.approx(res["surprise_percentage"].iloc[0], 0.01) == (0.2 / 3.0) * 100.0

    # Event 1: 3.5 - 3.5 = 0.0
    assert pytest.approx(res["surprise_absolute"].iloc[1], 0.001) == 0.0


def test_surprise_bucketing():
    assert SurpriseCalculator.bucket_surprise(-2.5) == "extreme_negative"
    assert SurpriseCalculator.bucket_surprise(-1.5) == "large_negative"
    assert SurpriseCalculator.bucket_surprise(0.2) == "neutral"
    assert SurpriseCalculator.bucket_surprise(1.8) == "large_positive"
    assert SurpriseCalculator.bucket_surprise(2.5) == "extreme_positive"


def test_point_in_time_filtering():
    macro_df = pd.DataFrame({
        "observation_time": pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC"),
        "publication_time": [
            pd.Timestamp("2024-01-02 12:00:00", tz="UTC"),
            pd.Timestamp("2024-01-05 12:00:00", tz="UTC"),
            pd.Timestamp("2024-01-10 12:00:00", tz="UTC"),
        ],
        "value": [10.0, 20.0, 30.0],
    })

    # As of Jan 3, only the first record (pub Jan 2) is known
    filtered = PointInTimeManager.enforce_pit_filter(macro_df, "2024-01-03 00:00:00")
    assert len(filtered) == 1
    assert filtered["value"].iloc[0] == 10.0

    latest_val = PointInTimeManager.get_latest_pit_value(macro_df, "2024-01-06 00:00:00", value_col="value")
    assert latest_val == 20.0


def test_cot_pit_rules():
    cot_raw = pd.DataFrame({
        "date": ["2024-01-09"],  # Tuesday
        "noncomm_long": [200000],
        "noncomm_short": [50000],
    })
    pit_cot = PointInTimeManager.apply_cot_pit_rules(cot_raw)
    
    # Publication time should be the following Friday (2024-01-12) at 15:30 ET (20:30 UTC)
    pub_time = pit_cot["publication_time"].iloc[0]
    assert pub_time.weekday() == 4  # Friday
    assert pub_time.strftime("%Y-%m-%d") == "2024-01-12"
