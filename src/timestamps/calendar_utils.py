"""
Calendar utilities for market sessions, trading weeks, and Friday closes.
Ensures rigorous market timing relative to the standard gold weekly session.
"""

from __future__ import annotations
import datetime as dt
from typing import Union
import pandas as pd
import pytz

NY_TZ = pytz.timezone("America/New_York")
UTC_TZ = pytz.UTC


def to_ny_time(ts: Union[str, dt.datetime, pd.Timestamp]) -> pd.Timestamp:
    """Converts any timestamp to America/New_York timezone-aware Timestamp."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        # Assume UTC if naive, or localize to NY
        ts = ts.tz_localize(UTC_TZ).tz_convert(NY_TZ)
    else:
        ts = ts.tz_convert(NY_TZ)
    return ts


def to_utc_time(ts: Union[str, dt.datetime, pd.Timestamp]) -> pd.Timestamp:
    """Converts any timestamp to UTC timezone-aware Timestamp."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize(UTC_TZ)
    else:
        ts = ts.tz_convert(UTC_TZ)
    return ts


def get_next_friday_close(ts: Union[str, dt.datetime, pd.Timestamp], close_hour: int = 17, close_minute: int = 0) -> pd.Timestamp:
    """
    Given an observation or event timestamp, finds the following Friday market close.
    If event occurs on or before Friday 17:00 ET, next Friday close is that same Friday 17:00 ET.
    If event occurs after Friday 17:00 ET or during the weekend, next Friday close is the subsequent Friday.
    """
    ts_ny = to_ny_time(ts)
    weekday = ts_ny.weekday()  # Monday is 0, Friday is 4, Saturday is 5, Sunday is 6
    
    if weekday < 4:  # Mon-Thu
        days_ahead = 4 - weekday
        next_friday = ts_ny + dt.timedelta(days=days_ahead)
    elif weekday == 4:  # Friday
        friday_close_today = ts_ny.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
        if ts_ny <= friday_close_today:
            next_friday = friday_close_today
        else:
            next_friday = ts_ny + dt.timedelta(days=7)
    else:  # Saturday (5) or Sunday (6)
        days_ahead = (4 - weekday) % 7
        next_friday = ts_ny + dt.timedelta(days=days_ahead)
        
    next_friday_close = next_friday.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
    return next_friday_close


def get_previous_friday_close(ts: Union[str, dt.datetime, pd.Timestamp], close_hour: int = 17, close_minute: int = 0) -> pd.Timestamp:
    """
    Given an observation or event timestamp, finds the preceding Friday market close.
    If event occurs on Friday before 17:00 ET, previous Friday close is the Friday of the previous week (7 days ago).
    If event occurs on Friday after 17:00 ET, previous Friday close is that day's 17:00 ET.
    """
    ts_ny = to_ny_time(ts)
    weekday = ts_ny.weekday()
    
    if weekday < 4:  # Mon-Thu
        days_behind = weekday + 3  # Mon (0) -> 3 days back to Fri; Tue (1) -> 4 days back, etc.
        prev_friday = ts_ny - dt.timedelta(days=days_behind)
    elif weekday == 4:  # Friday
        friday_close_today = ts_ny.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
        if ts_ny <= friday_close_today:
            prev_friday = ts_ny - dt.timedelta(days=7)
        else:
            prev_friday = friday_close_today
    else:  # Saturday (5) or Sunday (6)
        days_behind = weekday - 4  # Sat (5) -> 1 day back; Sun (6) -> 2 days back
        prev_friday = ts_ny - dt.timedelta(days=days_behind)
        
    prev_friday_close = prev_friday.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
    return prev_friday_close


def get_trading_week_id(ts: Union[str, dt.datetime, pd.Timestamp]) -> str:
    """
    Returns the ISO date string (YYYY-MM-DD) of the Friday that closes this trading week.
    All events and market data within the same trading week map to the identical week ID.
    """
    next_fri = get_next_friday_close(ts)
    return next_fri.strftime("%Y-%m-%d")


def is_market_open(ts: Union[str, dt.datetime, pd.Timestamp], asset: str = "gold") -> bool:
    """
    Checks if the global gold / financial market is generally open at timestamp ts.
    Gold futures & spot trade 23 hours/day from Sunday 18:00 ET to Friday 17:00 ET.
    Daily maintenance halt is Mon-Thu 17:00-18:00 ET.
    """
    ts_ny = to_ny_time(ts)
    weekday = ts_ny.weekday()
    hour = ts_ny.hour
    
    # Weekend close: Friday 17:00 ET to Sunday 18:00 ET
    if weekday == 4 and hour >= 17:
        return False
    if weekday == 5:  # Saturday all day
        return False
    if weekday == 6 and hour < 18:  # Sunday before 18:00 ET
        return False
    # Daily maintenance halt 17:00 - 18:00 ET Monday through Thursday
    if weekday in (0, 1, 2, 3) and hour == 17:
        return False
    return True
