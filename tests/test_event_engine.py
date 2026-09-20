"""Unit tests for event response engine and reference prices."""
import pytest
import numpy as np
import pandas as pd
from src.event_engine.reference_prices import ReferencePriceCalculator
from src.event_engine.window_analyzer import WindowAnalyzer
from src.weekly_engine.aggregator import WeeklyEventAggregator


def test_reference_prices_extraction():
    # Build 2 weeks of dummy hourly bars
    dates = pd.date_range("2024-01-01 00:00:00", "2024-01-15 00:00:00", freq="1h", tz="UTC")
    prices = np.linspace(2000.0, 2100.0, len(dates))
    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 2,
        "low": prices - 2,
        "close": prices,
        "volume": 1000,
    })

    event_time = pd.Timestamp("2024-01-10 13:30:00", tz="UTC")
    refs = ReferencePriceCalculator.extract_reference_prices(event_time, df)

    assert refs["ref_a"] is not None
    assert refs["ref_b"] is not None
    assert refs["ref_c"] is not None
    assert refs["target_next_friday"] is not None
    assert refs["event_to_next_fri_return"] is not None


def test_window_analyzer_metrics():
    dates = pd.date_range("2024-01-08 00:00:00", "2024-01-15 00:00:00", freq="5min", tz="UTC")
    base_price = 2050.0
    prices = base_price + np.sin(np.linspace(0, 10, len(dates))) * 20.0
    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 1.0,
        "low": prices - 1.0,
        "close": prices,
    })

    event_time = pd.Timestamp("2024-01-10 13:30:00", tz="UTC")
    metrics = WindowAnalyzer.analyze_event_response(event_time, df)

    assert "return_5m" in metrics
    assert "return_1h" in metrics
    assert "mfe_next_friday" in metrics
    assert "mae_next_friday" in metrics
    assert "reversal_classification" in metrics


def test_weekly_event_aggregation():
    week_events = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2024-01-10 13:30:00", tz="UTC"),
            pd.Timestamp("2024-01-11 13:30:00", tz="UTC"),
        ],
        "event_type": ["CPI", "Jobless Claims"],
        "importance": ["high", "medium"],
        "surprise_zscore": [1.8, -0.4],
    })

    agg = WeeklyEventAggregator.aggregate_week_events(week_events)
    assert agg["event_count"] == 2
    assert agg["high_impact_count"] == 1
    assert agg["cpi_present"] == 1
    assert agg["largest_positive_macro_surprise"] == 1.8
    assert agg["largest_negative_macro_surprise"] == -0.4
    assert "CPI" in agg["event_sequence"]
