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

        # 2. Window Responses - Strictly Independent Horizon Timestamp Resolution
        window_specs = {
            "1m": (t + pd.Timedelta(minutes=1), t, t + pd.Timedelta(minutes=3)),
            "5m": (t + pd.Timedelta(minutes=5), t + pd.Timedelta(minutes=2), t + pd.Timedelta(minutes=10)),
            "15m": (t + pd.Timedelta(minutes=15), t + pd.Timedelta(minutes=10), t + pd.Timedelta(minutes=25)),
            "30m": (t + pd.Timedelta(minutes=30), t + pd.Timedelta(minutes=20), t + pd.Timedelta(minutes=45)),
            "1h": (t + pd.Timedelta(hours=1), t + pd.Timedelta(minutes=45), t + pd.Timedelta(minutes=90)),
            "2h": (t + pd.Timedelta(hours=2), t + pd.Timedelta(minutes=90), t + pd.Timedelta(minutes=160)),
            "4h": (t + pd.Timedelta(hours=4), t + pd.Timedelta(minutes=180), t + pd.Timedelta(minutes=300)),
            "1d": (t + pd.Timedelta(days=1), t + pd.Timedelta(hours=16), t + pd.Timedelta(hours=36)),
            "3d": (t + pd.Timedelta(days=3), t + pd.Timedelta(hours=60), t + pd.Timedelta(hours=84)),
            "5d": (t + pd.Timedelta(days=5), t + pd.Timedelta(hours=108), t + pd.Timedelta(hours=132)),
            "next_friday": (next_fri_ts, t + pd.Timedelta(hours=1), next_fri_ts + pd.Timedelta(hours=12)),
        }

        checkpoints: Dict[str, float] = {}

        for win_name, (target_ts, w_start, w_end) in window_specs.items():
            mask_window = (times >= w_start) & (times <= w_end)
            win_slice = df[mask_window]

            if win_slice.empty:
                # If no bar exists inside the strict horizon window, record MISSING
                # Never silently substitute an unrelated observation or reuse the same price
                results[f"timestamp_{win_name}"] = None
                results[f"return_{win_name}"] = np.nan
                results[f"abs_return_{win_name}"] = np.nan
                results[f"mfe_{win_name}"] = np.nan
                results[f"mae_{win_name}"] = np.nan
                results[f"max_dd_{win_name}"] = np.nan
                results[f"max_runup_{win_name}"] = np.nan
            else:
                # Select the bar closest to target_ts within the valid window
                time_diffs = (times[mask_window] - target_ts).abs()
                best_idx = time_diffs.idxmin()
                best_row = df.loc[best_idx]
                ts_win = best_row[time_col]
                p_win = float(best_row[price_col])

                # MFE / MAE computed from event time t to the resolved horizon bar
                sub_slice = df[(times >= t) & (times <= ts_win)]
                if not sub_slice.empty:
                    high_win = float(sub_slice[high_col].max()) if high_col in df.columns else p_win
                    low_win = float(sub_slice[low_col].min()) if low_col in df.columns else p_win
                else:
                    high_win = p_win
                    low_win = p_win

                ret = (p_win / p0) - 1.0
                mfe = (high_win / p0) - 1.0
                mae = (low_win / p0) - 1.0

                results[f"timestamp_{win_name}"] = ts_win
                results[f"return_{win_name}"] = ret
                results[f"abs_return_{win_name}"] = abs(ret)
                results[f"mfe_{win_name}"] = mfe
                results[f"mae_{win_name}"] = mae
                results[f"max_dd_{win_name}"] = min(0.0, mae)
                results[f"max_runup_{win_name}"] = max(0.0, mfe)
                checkpoints[win_name] = ret

        # 3. Pre-event vs Post-event Volatility
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

        # 4. Response Speed Analysis
        r_week = results.get("event_to_next_fri_return") or checkpoints.get("next_friday")
        if r_week is not None and pd.notna(r_week) and abs(r_week) > 0.0005:
            results["speed_pct_5m"] = (checkpoints["5m"] / r_week * 100.0) if "5m" in checkpoints else np.nan
            results["speed_pct_1h"] = (checkpoints["1h"] / r_week * 100.0) if "1h" in checkpoints else np.nan
            results["speed_pct_4h"] = (checkpoints["4h"] / r_week * 100.0) if "4h" in checkpoints else np.nan
            results["speed_pct_1d"] = (checkpoints["1d"] / r_week * 100.0) if "1d" in checkpoints else np.nan
            results["speed_pct_remaining"] = (100.0 - results["speed_pct_1d"]) if pd.notna(results.get("speed_pct_1d")) else np.nan
        else:
            results["speed_pct_5m"] = np.nan
            results["speed_pct_1h"] = np.nan
            results["speed_pct_4h"] = np.nan
            results["speed_pct_1d"] = np.nan
            results["speed_pct_remaining"] = np.nan

        # 5. Reversal Classification
        r_init = checkpoints.get("1h")
        if r_init is None or pd.isna(r_init) or r_week is None or pd.isna(r_week):
            reversal_type = "unresolved"
        elif abs(r_init) < 0.001:
            reversal_type = "muted_initial"
        elif np.sign(r_init) == np.sign(r_week):
            if abs(r_week) >= abs(r_init):
                reversal_type = "initial_continuation"
            else:
                reversal_type = "partial_reversal"
        else:
            reversal_type = "full_reversal"

        results["reversal_classification"] = reversal_type
        results["initial_reaction_1h"] = r_init if r_init is not None else np.nan
        results["weekly_final_reaction"] = r_week if r_week is not None else np.nan

        return results

    @classmethod
    def validate_horizon_ordering(cls, metrics: Dict[str, Any]) -> bool:
        """
        Validates that resolved horizons satisfy strict monotonicity:
        timestamp_5m < timestamp_1h < timestamp_4h < timestamp_1d < timestamp_next_friday
        """
        keys = ["timestamp_5m", "timestamp_1h", "timestamp_4h", "timestamp_1d", "timestamp_next_friday"]
        valid_ts = [metrics[k] for k in keys if metrics.get(k) is not None]
        if len(valid_ts) < 2:
            return True
        for i in range(1, len(valid_ts)):
            if valid_ts[i] <= valid_ts[i - 1]:
                return False
        return True


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
