"""
Reference price extractor for macroeconomic event studies.
Calculates Reference Prices A, B, C, D, E and decomposes weekly returns into:
- pre-event movement (previous Friday -> event)
- post-event response (event -> next Friday)
- total weekly movement (previous Friday -> next Friday)
"""

from __future__ import annotations
import datetime as dt
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import (
    get_next_friday_close,
    get_previous_friday_close,
    to_utc_time,
)


class ReferencePriceCalculator:
    """
    Computes multiple benchmark reference prices before event timestamp T:
    - Reference A: Price immediately before event (closest prior tick/bar close)
    - Reference B: Close 5 minutes before event
    - Reference C: Close 1 hour before event
    - Reference D: Same-day official close
    - Reference E: Previous Friday close
    And the target price:
    - Next Friday close
    """

    @staticmethod
    def extract_reference_prices(
        event_time: pd.Timestamp,
        gold_df: pd.DataFrame,
        time_col: str = "timestamp",
        price_col: str = "close",
    ) -> Dict[str, Optional[float]]:
        """
        Extracts reference prices A, B, C, D, E and next Friday close from the price history.
        Works seamlessly with multi-resolution (intraday and daily) bar history.
        """
        t = to_utc_time(event_time)
        df = gold_df.sort_values(by=time_col).reset_index(drop=True)
        times = pd.to_datetime(df[time_col], utc=True)

        # 1. Target: Next Friday Close
        next_fri = get_next_friday_close(t)
        prev_fri = get_previous_friday_close(t)

        # Subset before event
        prior_mask = times <= t
        prior_bars = df[prior_mask]
        
        if prior_bars.empty:
            return {
                "ref_a": None, "ref_b": None, "ref_c": None,
                "ref_d": None, "ref_e": None, "target_next_friday": None,
                "event_to_next_fri_return": None,
                "prev_fri_to_event_return": None,
                "prev_fri_to_next_fri_return": None,
            }

        # Reference A: Closest price immediately before event
        ref_a = float(prior_bars[price_col].iloc[-1])

        # Reference B: 5 minutes prior
        t_5m = t - pd.Timedelta(minutes=5)
        bars_5m = df[times <= t_5m]
        ref_b = float(bars_5m[price_col].iloc[-1]) if not bars_5m.empty else ref_a

        # Reference C: 1 hour prior
        t_1h = t - pd.Timedelta(hours=1)
        bars_1h = df[times <= t_1h]
        ref_c = float(bars_1h[price_col].iloc[-1]) if not bars_1h.empty else ref_a

        # Reference D: Same day close (or latest bar of the event day)
        same_day_end = t.replace(hour=23, minute=59, second=59)
        bars_same_day = df[times <= same_day_end]
        ref_d = float(bars_same_day[price_col].iloc[-1]) if not bars_same_day.empty else ref_a

        # Reference E: Previous Friday close
        bars_prev_fri = df[times <= prev_fri]
        ref_e = float(bars_prev_fri[price_col].iloc[-1]) if not bars_prev_fri.empty else ref_a

        # Target Next Friday Close
        bars_next_fri = df[times <= next_fri]
        target_next_friday = float(bars_next_fri[price_col].iloc[-1]) if not bars_next_fri.empty else ref_a

        # Calculate primary returns
        post_event_return = (target_next_friday / ref_a) - 1.0 if ref_a else None
        pre_event_return = (ref_a / ref_e) - 1.0 if ref_e else None
        total_week_return = (target_next_friday / ref_e) - 1.0 if ref_e else None

        return {
            "ref_a": ref_a,
            "ref_b": ref_b,
            "ref_c": ref_c,
            "ref_d": ref_d,
            "ref_e": ref_e,
            "target_next_friday": target_next_friday,
            "event_to_next_fri_return": post_event_return,
            "prev_fri_to_event_return": pre_event_return,
            "prev_fri_to_next_fri_return": total_week_return,
            "weekly_response_ref_b": (target_next_friday / ref_b) - 1.0 if ref_b else None,
            "weekly_response_ref_c": (target_next_friday / ref_c) - 1.0 if ref_c else None,
            "weekly_response_ref_d": (target_next_friday / ref_d) - 1.0 if ref_d else None,
        }
