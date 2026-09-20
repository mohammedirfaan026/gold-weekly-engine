"""Unit tests for timestamp and calendar utilities."""
import pytest
import pandas as pd
import pytz
from src.timestamps.calendar_utils import (
    get_next_friday_close,
    get_previous_friday_close,
    get_trading_week_id,
    is_market_open,
    to_ny_time,
)

NY_TZ = pytz.timezone("America/New_York")


def test_next_friday_close_wednesday():
    # Wednesday 2024-01-10 14:00 ET -> Next Friday is 2024-01-12 17:00 ET
    dt_wed = NY_TZ.localize(pd.Timestamp("2024-01-10 14:00:00"))
    next_fri = get_next_friday_close(dt_wed)
    assert next_fri == NY_TZ.localize(pd.Timestamp("2024-01-12 17:00:00"))


def test_next_friday_close_friday_morning():
    # Friday 2024-01-12 08:30 ET (NFP release) -> Next Friday close is that same day 2024-01-12 17:00 ET
    dt_fri_morning = NY_TZ.localize(pd.Timestamp("2024-01-12 08:30:00"))
    next_fri = get_next_friday_close(dt_fri_morning)
    assert next_fri == NY_TZ.localize(pd.Timestamp("2024-01-12 17:00:00"))


def test_next_friday_close_friday_after_close():
    # Friday 2024-01-12 18:00 ET -> Next Friday close is next week 2024-01-19 17:00 ET
    dt_fri_evening = NY_TZ.localize(pd.Timestamp("2024-01-12 18:00:00"))
    next_fri = get_next_friday_close(dt_fri_evening)
    assert next_fri == NY_TZ.localize(pd.Timestamp("2024-01-19 17:00:00"))


def test_previous_friday_close_tuesday():
    # Tuesday 2024-01-16 10:00 ET -> Previous Friday close is 2024-01-12 17:00 ET
    dt_tue = NY_TZ.localize(pd.Timestamp("2024-01-16 10:00:00"))
    prev_fri = get_previous_friday_close(dt_tue)
    assert prev_fri == NY_TZ.localize(pd.Timestamp("2024-01-12 17:00:00"))


def test_previous_friday_close_friday_morning():
    # Friday 2024-01-12 08:30 ET -> Previous Friday close is prior week 2024-01-05 17:00 ET
    dt_fri = NY_TZ.localize(pd.Timestamp("2024-01-12 08:30:00"))
    prev_fri = get_previous_friday_close(dt_fri)
    assert prev_fri == NY_TZ.localize(pd.Timestamp("2024-01-05 17:00:00"))


def test_trading_week_id():
    dt_wed = NY_TZ.localize(pd.Timestamp("2024-01-10 14:00:00"))
    assert get_trading_week_id(dt_wed) == "2024-01-12"


def test_is_market_open():
    # Regular trading hours: Tuesday 10:00 ET -> Open
    assert is_market_open(NY_TZ.localize(pd.Timestamp("2024-01-16 10:00:00"))) is True
    # Saturday 12:00 ET -> Closed
    assert is_market_open(NY_TZ.localize(pd.Timestamp("2024-01-13 12:00:00"))) is False
    # Daily halt: Tuesday 17:30 ET -> Closed
    assert is_market_open(NY_TZ.localize(pd.Timestamp("2024-01-16 17:30:00"))) is False


def test_winter_summer_dst_transitions():
    """Verifies that 17:00 America/New_York correctly maps to 22:00 UTC in winter (EST) and 21:00 UTC in summer (EDT)."""
    # 1. Winter Friday (EST = UTC-5)
    winter_date = "2026-01-16"
    winter_close_ny = NY_TZ.localize(pd.Timestamp(f"{winter_date} 17:00:00"))
    winter_close_utc = winter_close_ny.astimezone(pytz.UTC)
    assert winter_close_utc.hour == 22, f"Winter close should be 22:00 UTC, got {winter_close_utc.hour}:00"

    # 2. Summer Friday (EDT = UTC-4)
    summer_date = "2026-07-17"
    summer_close_ny = NY_TZ.localize(pd.Timestamp(f"{summer_date} 17:00:00"))
    summer_close_utc = summer_close_ny.astimezone(pytz.UTC)
    assert summer_close_utc.hour == 21, f"Summer close should be 21:00 UTC, got {summer_close_utc.hour}:00"

    # 3. DST Spring Forward (March 2026 transition: March 8)
    pre_dst_fri = NY_TZ.localize(pd.Timestamp("2026-03-06 17:00:00")).astimezone(pytz.UTC)
    post_dst_fri = NY_TZ.localize(pd.Timestamp("2026-03-13 17:00:00")).astimezone(pytz.UTC)
    assert pre_dst_fri.hour == 22, "Pre-DST March Friday close must be 22:00 UTC"
    assert post_dst_fri.hour == 21, "Post-DST March Friday close must be 21:00 UTC"

    # 4. DST Fall Back (November 2026 transition: November 1)
    pre_fall_fri = NY_TZ.localize(pd.Timestamp("2026-10-30 17:00:00")).astimezone(pytz.UTC)
    post_fall_fri = NY_TZ.localize(pd.Timestamp("2026-11-06 17:00:00")).astimezone(pytz.UTC)
    assert pre_fall_fri.hour == 21, "Pre-fall-back October Friday close must be 21:00 UTC"
    assert post_fall_fri.hour == 22, "Post-fall-back November Friday close must be 22:00 UTC"

