"""
Multi-window event response analyzer.
Measures gold price trajectory across horizons:
+1m, +5m, +15m, +30m, +1h, +2h, +4h, +1d, +3d, +5d, and next Friday close.
Calculates returns, absolute returns, MFE, MAE, drawdowns, run-ups, speed, and reversals.
"""

from __future__ import annotations
import datetime as dt
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from src.timestamps.calendar_utils import get_next_friday_close, to_utc_time
from src.event_engine.reference_prices import ReferencePriceCalculator


class WindowAnalyzer:
    """
    Computes rigorous path metrics, excursions, speed, and reversals across all response windows.
    """

    WINDOWS_INTRA_MIN = [1, 5, 15, 30, 60, 120, 240]
    WINDOWS_DAYS = [1, 3, 5]

    @classmethod
    def analyze_event_response(
        cls,
        event_time: pd.Timestamp,
        gold_df: pd.DataFrame,
        time_col: str = "timestamp",
        price_col: str = "close",
        high_col: str = "high",
        low_col: str = "low",
    ) -> Dict[str, Any]:
        """
        Calculates all response window returns, MFE, MAE, drawdowns, speed of response,
        and reversal classifications for a single event.
        """
        t = to_utc_time(event_time)
        df = gold_df.sort_values(by=time_col).reset_index(drop=True)
        times = pd.to_datetime(df[time_col], utc=True)

        # 1. Reference prices and targets
        ref_dict = ReferencePriceCalculator.extract_reference_prices(
            t, df, time_col=time_col, price_col=price_col
        )
        p0 = ref_dict["ref_a"]
        if p0 is None or p0 <= 0:
            return {}

        results = dict(ref_dict)
        next_fri_ts = get_next_friday_close(t)

        # 2. Window Responses
        # Define window offsets
        window_targets = {
            "1m": t + pd.Timedelta(minutes=1),
            "5m": t + pd.Timedelta(minutes=5),
            "15m": t + pd.Timedelta(minutes=15),
            "30m": t + pd.Timedelta(minutes=30),
            "1h": t + pd.Timedelta(hours=1),
            "2h": t + pd.Timedelta(hours=2),
            "4h": t + pd.Timedelta(hours=4),
            "1d": t + pd.Timedelta(days=1),
            "3d": t + pd.Timedelta(days=3),
            "5d": t + pd.Timedelta(days=5),
            "next_friday": next_fri_ts,
        }

        # Track returns at key checkpoints for speed calculation
        checkpoints: Dict[str, float] = {}

        for win_name, target_ts in window_targets.items():
            # Window slice from T to target_ts
            mask_window = (times >= t) & (times <= target_ts)
            win_slice = df[mask_window]

            if win_slice.empty:
                # Find the closest subsequent price
                subsequent = df[times >= t]
                if not subsequent.empty:
                    p_win = float(subsequent[price_col].iloc[0])
                    high_win = float(subsequent[high_col].iloc[0]) if high_col in df.columns else p_win
                    low_win = float(subsequent[low_col].iloc[0]) if low_col in df.columns else p_win
                else:
                    p_win = p0
                    high_win = p0
                    low_win = p0
            else:
                p_win = float(win_slice[price_col].iloc[-1])
                high_win = float(win_slice[high_col].max()) if high_col in df.columns else win_slice[price_col].max()
                low_win = float(win_slice[low_col].min()) if low_col in df.columns else win_slice[price_col].min()

            ret = (p_win / p0) - 1.0
            abs_ret = abs(ret)
            mfe = (high_win / p0) - 1.0
            mae = (low_win / p0) - 1.0
            max_drawdown = min(0.0, mae)
            max_runup = max(0.0, mfe)

            results[f"return_{win_name}"] = ret
            results[f"abs_return_{win_name}"] = abs_ret
            results[f"mfe_{win_name}"] = mfe
            results[f"mae_{win_name}"] = mae
            results[f"max_dd_{win_name}"] = max_drawdown
            results[f"max_runup_{win_name}"] = max_runup

            checkpoints[win_name] = ret

        # 3. Pre-event vs Post-event Volatility (annualized realized vol over 5 days prior vs 5 days post)
        t_pre = t - pd.Timedelta(days=5)
        t_post = t + pd.Timedelta(days=5)
        pre_slice = df[(times >= t_pre) & (times <= t)]
        post_slice = df[(times >= t) & (times <= t_post)]

        pre_vol = (
            pre_slice[price_col].pct_change().std() * np.sqrt(252 * 24 * 12)
            if len(pre_slice) > 3
            else np.nan
        )
        post_vol = (
            post_slice[price_col].pct_change().std() * np.sqrt(252 * 24 * 12)
            if len(post_slice) > 3
            else np.nan
        )
        results["volatility_pre_event"] = pre_vol
        results["volatility_post_event"] = post_vol
        results["volatility_ratio"] = (post_vol / pre_vol) if (pd.notna(pre_vol) and pre_vol > 0) else np.nan

        # 4. Response Speed Analysis (% of weekly response realized over time)
        r_week = results.get("event_to_next_fri_return", checkpoints.get("next_friday", 0.0))
        if r_week and abs(r_week) > 0.0005:
            results["speed_pct_5m"] = (checkpoints.get("5m", 0.0) / r_week) * 100.0
            results["speed_pct_1h"] = (checkpoints.get("1h", 0.0) / r_week) * 100.0
            results["speed_pct_4h"] = (checkpoints.get("4h", 0.0) / r_week) * 100.0
            results["speed_pct_1d"] = (checkpoints.get("1d", 0.0) / r_week) * 100.0
            results["speed_pct_remaining"] = 100.0 - results["speed_pct_1d"]
        else:
            results["speed_pct_5m"] = np.nan
            results["speed_pct_1h"] = np.nan
            results["speed_pct_4h"] = np.nan
            results["speed_pct_1d"] = np.nan
            results["speed_pct_remaining"] = np.nan

        # 5. Reversal Classification
        # Compare initial 1h reaction to final weekly reaction
        r_init = checkpoints.get("1h", 0.0)
        if abs(r_init) < 0.001:
            reversal_type = "muted_initial"
        elif np.sign(r_init) == np.sign(r_week):
            if abs(r_week) >= abs(r_init):
                reversal_type = "initial_continuation"
            else:
                reversal_type = "partial_reversal"
        else:
            reversal_type = "full_reversal"

        results["reversal_classification"] = reversal_type
        results["initial_reaction_1h"] = r_init
        results["weekly_final_reaction"] = r_week

        return results

    @classmethod
    def process_all_events(
        cls,
        events_df: pd.DataFrame,
        gold_df: pd.DataFrame,
        time_col: str = "timestamp",
    ) -> pd.DataFrame:
        """
        Processes multi-window response metrics for an entire table of events.
        """
        all_metrics = []
        for idx, row in events_df.iterrows():
            event_t = row["timestamp"]
            metrics = cls.analyze_event_response(event_t, gold_df, time_col=time_col)
            metrics["event_id"] = row.get("event_id", f"evt_{idx}")
            all_metrics.append(metrics)

        metrics_df = pd.DataFrame(all_metrics)
        merged = pd.merge(events_df, metrics_df, on="event_id", how="left")
        return merged
