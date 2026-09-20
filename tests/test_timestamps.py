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
