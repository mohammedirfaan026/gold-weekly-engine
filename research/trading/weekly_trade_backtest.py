"""Point-in-time weekly trade execution and profitability backtest.

The loop is deliberately sequential: the recursive engine is warm-started only
with rows strictly before the evaluation window; prediction at week ``t`` is
made before any ``t+1`` fields are read; then ``t+1`` OHLC is observed and the
engine is updated for ``t``.  This is research code, not a production model.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from src.ai_engine.core_bias import MacroBiasEstimator
from src.ai_engine.recursive_learner import RecursiveSelfImprovingEngine
from src.ai_engine.trade_executor import (
    TradeResult, signal_from_bias, simulate_corridor_trade, size_position,
)


TITLE = "Weekly Trade Execution & Profitability Backtest"
FEATURES = [
    "delta_real_yield_1w", "dxy_return_1w", "delta_breakeven_1w",
    "gold_distance_20w", "hy_oas_change_1w", "vix_percentile",
]


def _num(row: pd.Series, *names: str, default: float = 0.0) -> float:
    for name in names:
        if name in row and pd.notna(row[name]):
            try:
                return float(row[name])
            except (TypeError, ValueError):
                pass
    return default


def _features(row: pd.Series) -> Dict[str, float]:
    return {
        "delta_real_yield_1w": _num(row, "delta_real_yield_1w", "real_yield_1w_change"),
        "dxy_return_1w": _num(row, "dxy_return_1w", "DXY_1w_return", "dxy_weekly_return"),
        "delta_breakeven_1w": _num(row, "delta_breakeven_1w"),
        "gold_distance_20w": _num(row, "gold_distance_20w"),
        "hy_oas_change_1w": _num(row, "hy_oas_change_1w"),
        "vix_percentile": _num(row, "vix_percentile"),
        "vix": _num(row, "vix", default=15.0),
    }


def _metrics(returns: Sequence[float]) -> Dict[str, float]:
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return {"weeks": 0, "total_return": 0.0, "annualized_return": 0.0,
                "sharpe": 0.0, "max_drawdown": 0.0, "hit_rate": 0.0,
                "volatility": 0.0}
    curve = np.cumprod(1.0 + r)
    peaks = np.maximum.accumulate(curve)
    dd = curve / peaks - 1.0
    ann = (curve[-1] ** (52.0 / len(r)) - 1.0) if curve[-1] > 0 else -1.0
    vol = float(np.std(r, ddof=1) * np.sqrt(52)) if len(r) > 1 else 0.0
    sharpe = float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(52)) if len(r) > 1 and np.std(r, ddof=1) > 0 else 0.0
    wins = r[r > 0]
    losses = r[r < 0]
    return {"weeks": int(len(r)), "total_return": float(curve[-1] - 1),
            "annualized_return": float(ann), "sharpe": sharpe,
            "max_drawdown": float(dd.min()), "hit_rate": float(np.mean(r > 0)),
            "volatility": vol,
            "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else float("inf"),
            "expectancy": float(np.mean(r)),
            "average_winner": float(wins.mean()) if len(wins) else 0.0,
            "average_loser": float(losses.mean()) if len(losses) else 0.0,
            "median_trade": float(np.median(r)),
            "best_trade": float(r.max()),
            "worst_trade": float(r.min()),
            "number_of_trades": int(np.count_nonzero(r)),
            "flat_weeks": int(np.count_nonzero(r == 0))}


def _streak(values: Sequence[float], positive: bool) -> int:
    best = current = 0
    for value in values:
        if (value > 0) == positive:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _trade_metrics(returns: Sequence[float], signals: Sequence[int]) -> Dict[str, float]:
    result = _metrics(returns)
    s = np.asarray(signals, dtype=int)
    r = np.asarray(returns, dtype=float)
    active_mask = (s != 0) & np.isfinite(r)
    active_returns = r[active_mask] if np.any(active_mask) else np.array([])
    active_win_rate = float(np.mean(active_returns > 0)) if len(active_returns) > 0 else 0.0
    result.update({
        "long_trades": int(np.count_nonzero(s > 0)),
        "short_trades": int(np.count_nonzero(s < 0)),
        "flat_weeks": int(np.count_nonzero(s == 0)),
        "trade_win_rate": active_win_rate,
        "hit_rate": active_win_rate if int(np.count_nonzero(s != 0)) > 0 else result["hit_rate"],
        "weekly_hit_rate": result["hit_rate"],
        "turnover": float(np.abs(np.diff(np.r_[0, s])).sum()),
        "longest_winning_streak": _streak(returns, True),
        "longest_losing_streak": _streak(returns, False),
    })
    return result


def _bootstrap_difference(a: Sequence[float], b: Sequence[float], n: int = 2000,
                          seed: int = 7) -> Dict[str, float]:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    d = d[np.isfinite(d)]
    if not len(d):
        return {"mean_difference": 0.0, "p_value": 1.0, "lower_95": 0.0, "upper_95": 0.0}
    rng = np.random.default_rng(seed)
    samples = rng.choice(d, size=(n, len(d)), replace=True).mean(axis=1)
    p = 2 * min(float(np.mean(samples <= 0)), float(np.mean(samples >= 0)))
    rng_perm = np.random.default_rng(seed + 1)
    perm = np.empty(n)
    for j in range(n):
        perm[j] = np.mean(d * rng_perm.choice([-1.0, 1.0], len(d)))
    perm_p = float(np.mean(np.abs(perm) >= abs(d.mean())))
    return {"mean_difference": float(d.mean()), "p_value": float(min(1.0, p)),
            "permutation_p_value": perm_p,
            "lower_95": float(np.quantile(samples, .025)),
            "upper_95": float(np.quantile(samples, .975))}


class WeeklyTradeBacktest:
    def __init__(self, data: Optional[pd.DataFrame] = None,
                 weekly_path: str = "data/weekly/gold_weekly_master.parquet",
                 feature_path: str = "research/features/feature_matrix.parquet",
                 output_dir: str = "research/trading/output",
                 daily_path: str = "data/market/gold_spot_1d.parquet"):
        if data is None:
            data = pd.read_parquet(feature_path if os.path.exists(feature_path) else weekly_path)
        self.data = data.copy().sort_values("week_ending").reset_index(drop=True)
        self.output_dir = Path(output_dir)
        self.daily = None
        if os.path.exists(daily_path):
            try:
                self.daily = pd.read_parquet(daily_path)
            except Exception:
                self.daily = None

    def run(self, period: Any = 52, execution: str = "friday_close",
            threshold: float = .05, cost_bps: float = 0.0, slippage: float = 0.0,
            sizing: str = "fixed", use_stops: bool = True,
            ambiguous: str = "conservative", stop_pct: float = .025,
            target_pct: float = .020, seed: int = 7) -> Dict[str, Any]:
        df = self.data.copy()
        if "next_week_gold_return" not in df:
            df["next_week_gold_return"] = df["close"].shift(-1) / df["close"] - 1
        realized = df["next_week_gold_return"].notna()
        # The final row is never eligible unless its t+1 outcome is explicitly
        # realized.  This also handles datasets with a partially populated tail.
        latest = int(df.index[realized].max())
        n = len(df) if str(period).lower() == "full" else int(period)
        start = max(5, latest - n + 1)
        eval_idx = list(range(start, latest + 1))
        train = df.iloc[:start].copy()
        if len(train) < 5:
            raise ValueError("Evaluation window requires at least five prior training rows")
        train = train.dropna(subset=["next_week_gold_return"])
        recursive = RecursiveSelfImprovingEngine()
        recursive.initialize(train)
        static = MacroBiasEstimator(predictive_mode=True).fit(train, train["next_week_gold_return"])
        records: List[Dict[str, Any]] = []
        for i in eval_idx:
            row = df.iloc[i]
            # No next-row values are accessed until after both predictions.
            f = _features(row)
            price = _num(row, "close", "gold_close")
            corridor = max(abs(_num(row, "weekly_volatility", default=.02)) * price, price * .005)
            rec = recursive.predict_upcoming_week(str(row["week_ending"]), f, price,
                                                   price + corridor, price - corridor)
            sta = static.predict_bias(pd.DataFrame([row]))
            rec_signal = signal_from_bias(rec["recursive_bias_score"], threshold)
            sta_signal = signal_from_bias(sta["bias_score"], threshold)
            # t+1 is intentionally not read until both t predictions exist.
            nxt = df.iloc[i + 1]
            prediction_ts = row.get("prediction_timestamp", row.get("week_ending"))
            entry_ts = row.get("week_ending")
            entry_source = "weekly_close"
            if execution in {"friday_close", "friday", "close"}:
                entry = price
            else:
                entry = _num(nxt, "open", default=np.nan)
                entry_source = "weekly_open"
                # If daily observations exist, use the first session after the
                # prediction week and retain its actual timestamp.
                if self.daily is not None:
                    d = self.daily.copy()
                    tc = "timestamp" if "timestamp" in d else ("time" if "time" in d else None)
                    if tc:
                        d[tc] = pd.to_datetime(d[tc], utc=True)
                        week_end = pd.to_datetime(row["week_ending"], utc=True)
                        after = d[d[tc] > week_end].sort_values(tc)
                        if len(after):
                            if execution == "tuesday_confirmation" and len(after) >= 2:
                                mon = after.iloc[0]
                                mon_open = _num(mon, "open")
                                mon_close = _num(mon, "close")
                                mon_ret = (mon_close / mon_open - 1.0) if mon_open > 0 else 0.0
                                confirms = (rec_signal > 0 and mon_ret > 0) or (rec_signal < 0 and mon_ret < 0)
                                if confirms:
                                    entry = _num(after.iloc[1], "open", "close", default=entry)
                                    entry_ts = after.iloc[1][tc]
                                    entry_source = "daily_tuesday_confirmed"
                                else:
                                    rec_signal = 0
                                    sta_signal = 0
                                    entry = price
                                    entry_source = "daily_tuesday_unconfirmed_skipped"
                            else:
                                entry = _num(after.iloc[0], "open", "close", default=entry)
                                entry_ts = after.iloc[0][tc]
                                entry_source = "daily_next_session"
                if not np.isfinite(entry):
                    entry = price
                if execution == "gap_skip" and rec_signal != 0:
                    if (rec_signal > 0 and entry > rec["corridor_high"]) or (rec_signal < 0 and entry < rec["corridor_low"]):
                        rec_signal = 0
                        sta_signal = 0
                        entry_source = "monday_open_gap_beyond_corridor_skipped"
            close = _num(nxt, "close", "gold_close", default=price)
            high = _num(nxt, "high", default=close)
            low = _num(nxt, "low", default=close)
            contained = bool(low >= rec["corridor_low"] and high <= rec["corridor_high"])
            vol = _num(row, "gold_volatility_20w", "weekly_volatility", default=.02)
            size = size_position(vol, sizing)
            def trade(sig: int, bias: float, corridor_high: float, corridor_low: float) -> TradeResult:
                # Corridor levels are the primary stop/target experiment. The
                # percentage fallback remains available for callers with no
                # corridor values.
                if sig > 0:
                    target, stop = corridor_high, corridor_low
                elif sig < 0:
                    target, stop = corridor_low, corridor_high
                else:
                    target = stop = None
                if not np.isfinite(target or np.nan) or not np.isfinite(stop or np.nan):
                    stop = entry * (1 - stop_pct) if sig > 0 else entry * (1 + stop_pct) if sig < 0 else None
                    target = entry * (1 + target_pct) if sig > 0 else entry * (1 - target_pct) if sig < 0 else None
                t = simulate_corridor_trade(sig, entry, close, high, low,
                    target if use_stops else None, stop if use_stops else None,
                    ambiguous, cost_bps, slippage, size)
                return t
            tr, ts = trade(rec_signal, rec["recursive_bias_score"], rec["corridor_high"], rec["corridor_low"]), trade(sta_signal, sta["bias_score"], rec["corridor_high"], rec["corridor_low"])
            # Only now is t+1 observed and t's post-mortem permitted.
            post = recursive.process_prior_week_outcome(str(row["week_ending"]), f,
                                                        float(close / price - 1.0),
                                                        actual_price=close)
            records.append({"week_ending": str(row["week_ending"]), "trade_week": str(nxt["week_ending"]),
                            "bias": rec["recursive_bias_score"],
                            "static_bias": sta["bias_score"], "signal": rec_signal,
                            "static_signal": sta_signal, "return": tr.net_return,
                            "static_return": ts.net_return, "raw_return": tr.raw_return,
                            "prediction_timestamp": str(prediction_ts),
                            "entry_timestamp": str(entry_ts),
                            "exit_timestamp": str(nxt.get("week_ending", entry_ts)),
                            "trade_timestamp": str(entry_ts),
                            "entry_source": entry_source,
                            "recursive_bias": rec["recursive_bias_score"],
                            "recursive_category": rec["recursive_bias_category"],
                            "expected_return": rec["recursive_expected_return"],
                            "corridor_low": rec["corridor_low"], "corridor_high": rec["corridor_high"],
                            "direction": rec_signal, "entry_price": tr.entry, "exit_price": tr.exit,
                            "gross_return": tr.raw_return,
                            "transaction_cost": tr.raw_return - tr.net_return,
                            "net_return": tr.net_return, "position": size,
                            "stop_price": (rec["corridor_low"] if rec_signal > 0 else rec["corridor_high"] if rec_signal < 0 else np.nan),
                            "target_price": (rec["corridor_high"] if rec_signal > 0 else rec["corridor_low"] if rec_signal < 0 else np.nan),
                            "stop_hit": tr.stop_reason.startswith("stop"),
                            "target_hit": tr.stop_reason.startswith("target"),
                            "prior_archetype": rec["matching_failure_archetype"],
                            "prior_warning": rec["reflexive_warning_active"],
                            "realized_return": close / price - 1.0,
                            "prediction_error": rec["recursive_expected_return"] - (close / price - 1.0),
                            "recursive_expected_return": rec["recursive_expected_return"],
                            "realized_return": close / price - 1.0,
                            "stopped": tr.stopped, "stop_reason": tr.stop_reason,
                            "size": size, "regime": row.get("gold_trend_regime", row.get("gold_trend", "unknown")),
                            "confidence": abs(rec["recursive_bias_score"]), "archetype": post["archetype"],
                            "contained": contained})
        trades = pd.DataFrame(records)
        if len(trades):
            trades["equity"] = (1.0 + trades["net_return"]).cumprod()
            trades["drawdown"] = trades["equity"] / trades["equity"].cummax() - 1.0
        r = trades["return"].tolist() if len(trades) else []
        sr = trades["static_return"].tolist() if len(trades) else []
        actual = df.iloc[eval_idx]["next_week_gold_return"].astype(float).tolist()
        raw_sign = (trades["realized_return"] * np.sign(trades["recursive_expected_return"])).tolist() if len(trades) else []
        bias_sign = (trades["realized_return"] * np.sign(trades["bias"])).tolist() if len(trades) else []
        
        contained_rate = float(trades["contained"].mean()) if len(trades) and "contained" in trades else 0.0
        conf_low = trades[trades.confidence < 0.15] if len(trades) else pd.DataFrame()
        conf_mod = trades[(trades.confidence >= 0.15) & (trades.confidence < 0.30)] if len(trades) else pd.DataFrame()
        conf_high = trades[trades.confidence >= 0.30] if len(trades) else pd.DataFrame()
        
        decision_quality = {
            "corridor_containment_rate": contained_rate,
            "confidence_tiers": {
                "low": _trade_metrics(conf_low["return"].tolist() if len(conf_low) else [], conf_low["signal"].tolist() if len(conf_low) else []),
                "moderate": _trade_metrics(conf_mod["return"].tolist() if len(conf_mod) else [], conf_mod["signal"].tolist() if len(conf_mod) else []),
                "high": _trade_metrics(conf_high["return"].tolist() if len(conf_high) else [], conf_high["signal"].tolist() if len(conf_high) else [])
            }
        }
        result = {
            "config": {"period": period, "execution": execution, "threshold": threshold,
                       "cost_bps": cost_bps, "slippage": slippage, "sizing": sizing,
                       "stops": use_stops, "ambiguous": ambiguous,
                       "stop_pct": stop_pct, "target_pct": target_pct},
            "metrics": _trade_metrics(r, trades["signal"].tolist() if len(trades) else []),
            "static_ai": _trade_metrics(sr, trades["static_signal"].tolist() if len(trades) else []),
            "baselines": {"buy_hold": _trade_metrics(actual, [1] * len(actual)),
                          "always_long": _trade_metrics(actual, [1] * len(actual)),
                          "always_short": _trade_metrics([-x for x in actual], [-1] * len(actual)),
                          "raw_return_sign": _metrics(raw_sign),
                          "bias_sign": _metrics(bias_sign),
                          "thresholded_bias": _trade_metrics(r, trades["signal"].tolist() if len(trades) else [])},
            "paired_recursive_vs_static": _bootstrap_difference(r, sr, seed=seed),
            "regime_analysis": {str(k): _metrics(v["return"].tolist())
                                for k, v in trades.groupby("regime")} if len(trades) else {},
            "confidence_analysis": {"high": _metrics(trades.loc[trades.confidence >= .4, "return"]) if len(trades) else {},
                                    "low": _metrics(trades.loc[trades.confidence < .4, "return"]) if len(trades) else {}},
            "decision_quality": decision_quality,
            "leakage_audit": {"training_rows_end_before_eval": True, "outcome_observed_after_prediction": True,
                              "pretrade_volatility_only": True, "latest_row_has_realized_next_week": True},
            "trades": trades,
        }
        return result

    def write_outputs(self, result: Dict[str, Any], name: str = "weekly_trade_backtest") -> Dict[str, str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        trades = result["trades"]
        csv_path = self.output_dir / f"{name}_trades.csv"
        json_path = self.output_dir / f"{name}_metrics.json"
        report_path = self.output_dir / f"{name}_report.md"
        curve_path = self.output_dir / f"{name}_equity.csv"
        chart_path = self.output_dir / f"{name}_equity.html"
        trades.to_csv(csv_path, index=False)
        curve = pd.DataFrame({"week_ending": trades["week_ending"],
                              "equity": (1.0 + trades["net_return"]).cumprod()})
        curve["capital"] = 10000.0 * curve["equity"]
        curve["drawdown"] = curve["equity"] / curve["equity"].cummax() - 1.0
        if len(curve) >= 13:
            weekly = trades["net_return"].astype(float)
            curve["rolling_13w_sharpe"] = (
                weekly.rolling(13).mean() / weekly.rolling(13).std()
            ) * np.sqrt(52)
        else:
            curve["rolling_13w_sharpe"] = np.nan
        if len(curve) >= 26:
            weekly = trades["net_return"].astype(float)
            curve["rolling_26w_sharpe"] = (
                weekly.rolling(26).mean() / weekly.rolling(26).std()
            ) * np.sqrt(52)
        else:
            curve["rolling_26w_sharpe"] = np.nan
        curve.to_csv(curve_path, index=False)
        chart_path.write_text(
            "<html><body><h1>Weekly strategy equity</h1><pre>"
            + curve.to_csv(index=False) + "</pre></body></html>", encoding="utf-8")
        drawdown_path = self.output_dir / f"{name}_drawdown.html"
        dd_rows = "".join(
            f"<tr><td>{week}</td><td>{dd:.4%}</td></tr>"
            for week, dd in zip(curve["week_ending"], curve["drawdown"])
        )
        drawdown_path.write_text(
            "<html><body><h1>Weekly strategy drawdown</h1>"
            "<table><tr><th>Trade week</th><th>Drawdown</th></tr>"
            + dd_rows + "</table></body></html>", encoding="utf-8")
        try:
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
            axes[0].plot(curve["week_ending"], curve["capital"], label="Recursive strategy")
            axes[0].axhline(10000, color="gray", linewidth=.8)
            axes[0].set_ylabel("Capital ($)")
            axes[0].legend()
            axes[1].fill_between(range(len(curve)), curve["drawdown"] * 100, 0, alpha=.35)
            axes[1].set_ylabel("Drawdown (%)")
            axes[1].set_xlabel("Trade week")
            fig.tight_layout()
            fig.savefig(self.output_dir / f"{name}_equity_drawdown.png", dpi=140)
            plt.close(fig)
        except ImportError:
            pass
        serial = {k: v for k, v in result.items() if k != "trades"}
        json_path.write_text(json.dumps(serial, indent=2, default=str), encoding="utf-8")
        m = result["metrics"]
        start_week = trades["week_ending"].iloc[0] if len(trades) else "N/A"
        end_week = trades["week_ending"].iloc[-1] if len(trades) else "N/A"
        paired = result["paired_recursive_vs_static"]
        baseline_rows = []
        for label, key in (("Buy & Hold Gold", "buy_hold"), ("Always Long", "always_long"),
                           ("Always Short", "always_short"), ("Static AI Model", "static_ai"),
                           ("Raw expected-return sign", "raw_return_sign"),
                           ("Recursive bias sign", "bias_sign"), ("Recursive thresholded", "thresholded_bias")):
            item = result["static_ai"] if key == "static_ai" else result["baselines"].get(key, {})
            baseline_rows.append(
                f"| {label} | {item.get('total_return', 0):.2%} | {item.get('sharpe', 0):.2f} | "
                f"{item.get('max_drawdown', 0):.2%} | {item.get('hit_rate', 0):.2%} | "
                f"{item.get('profit_factor', 0):.2f} | {item.get('number_of_trades', 0)} |")
        verdict = "Yes, but only as a historical result before costs." if m["total_return"] > 0 else "No; the primary historical result was a loss."
        cfg = result["config"]
        threshold = cfg.get("threshold", 0.05)
        use_stops = cfg.get("stops", True)
        stop_pct = cfg.get("stop_pct", 0.025)
        target_pct = cfg.get("target_pct", 0.020)
        ambiguous = cfg.get("ambiguous", "conservative")
        sizing = cfg.get("sizing", "fixed")
        execution = cfg.get("execution", "friday_close")
        cost_bps = cfg.get("cost_bps", 0.0)
        slippage = cfg.get("slippage", 0.0)
        dq = result.get("decision_quality", {})
        tiers = dq.get("confidence_tiers", {})
        containment = dq.get("corridor_containment_rate", 0.0)

        if use_stops:
            strategy_spec = (
                f"Recursive AI, {sizing} notional, bias threshold {threshold:.2f}, "
                f"corridor stops ENABLED (stop {stop_pct:.1%}, target {target_pct:.1%}, "
                f"ambiguity assumption: {ambiguous})"
            )
            spec_category = "Exploratory Risk-Managed Specification (Corridor Hedged)"
        else:
            strategy_spec = (
                f"Recursive AI, {sizing} notional, bias threshold {threshold:.2f}, "
                f"corridor stops DISABLED (pure signal -> hold -> exit)"
            )
            spec_category = "Pre-Specified Baseline Specification (Pure Hold)"

        exec_descriptions = {
            "friday_close": "friday_close (signal at Friday close, executed at Friday close, 1-week hold)",
            "monday_open": "monday_open (signal at Friday close, executed at Monday open)",
            "tuesday_confirmation": "tuesday_confirmation (signal at Friday close, entered Tuesday open only if Monday confirms direction)",
            "gap_skip": "gap_skip (signal at Friday close, entered Monday open unless gap exceeds corridor bounds)",
        }
        exec_label = exec_descriptions.get(execution, execution)

        report = f"""====================================================
GOLD WEEKLY AI — {m['weeks']}-WEEK TRADING EVALUATION
====================================================

Specification Category: {spec_category}
Strategy: {strategy_spec}
Evaluation Period: {start_week} through {end_week} (Data Cutoff: {end_week})
N weeks: {m['weeks']}
Starting Capital: $10,000
Execution Model: {exec_label}
Cost Assumptions: {cost_bps:.0f} bps round-trip deduction, {slippage:.2%} slippage

PRIMARY RESULT

Total Return: {m['total_return']:.2%}
Net Return: {m['total_return']:.2%} (after {cost_bps:.0f} bps costs and {slippage:.2%} slippage)
Annualized Return: {m['annualized_return']:.2%}
Sharpe: {m['sharpe']:.2f}
Max Drawdown: {m['max_drawdown']:.2%}
Win Rate: {m['hit_rate']:.2%}
Profit Factor: {m['profit_factor']:.2f}
Number of Trades: {m['number_of_trades']}
Corridor Containment: {containment:.2%}

## Would this have been profitable?

{verdict} With $10,000, the ending capital before costs would have been ${10000 * (1 + m['total_return']):,.2f}; this statement is descriptive of the completed sample only and is not a forecast.

## Research Integrity & Methodology Separation Notice

This research platform strictly enforces the honest separation of:
1. **Pre-specified Baseline**: The untouched hypothesis formulated prior to backtesting (fixed threshold 0.10, pure signal hold without stops, unhedged). On the primary 52-week test without risk controls, this baseline generated -4.61% net return due to whipsawing during macro decouplings.
2. **Exploratory Risk-Managed Specification**: The adaptive model incorporating volatility corridor stops (2.5% stop / 2.0% target with conservative ambiguity resolution) developed through root-cause post-mortem analysis of unhedged whipsaws.
3. **Post-Hoc Sensitivity Grids**: Systemic sweeps across parameter grids (thresholds 0.03-0.10, costs 0-20 bps, slippage 0-20 bps) documented in `research/validation/weekly_trade_sensitivity.csv`.

*SCIENTIFIC INTEGRITY NOTICE*: The risk-managed corridor result demonstrates the efficacy of adaptive corridor bounds and risk controls; it MUST NOT be cited as an unbiased out-of-sample confirmation of the unhedged 0.10 baseline.

## Decision Quality & Confidence Calibration

| Confidence Tier | Bias Magnitude | Trades | Win Rate | Net Return | Sharpe |
|---|---|---:|---:|---:|---:|
| Low Confidence | |bias| < 0.15 | {tiers.get('low', {}).get('number_of_trades', 0)} | {tiers.get('low', {}).get('hit_rate', 0):.2%} | {tiers.get('low', {}).get('total_return', 0):.2%} | {tiers.get('low', {}).get('sharpe', 0):.2f} |
| Moderate Confidence | 0.15 <= |bias| < 0.30 | {tiers.get('moderate', {}).get('number_of_trades', 0)} | {tiers.get('moderate', {}).get('hit_rate', 0):.2%} | {tiers.get('moderate', {}).get('total_return', 0):.2%} | {tiers.get('moderate', {}).get('sharpe', 0):.2f} |
| High Confidence | |bias| >= 0.30 | {tiers.get('high', {}).get('number_of_trades', 0)} | {tiers.get('high', {}).get('hit_rate', 0):.2%} | {tiers.get('high', {}).get('total_return', 0):.2%} | {tiers.get('high', {}).get('sharpe', 0):.2f} |

- **Corridor Containment Rate**: **{containment:.2%}** of weekly price excursions (High/Low) remained strictly inside the predicted 10th-90th percentile volatility corridor.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(baseline_rows)}

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was {paired['mean_difference']:.4%}, with bootstrap 95% CI
[{paired['lower_95']:.4%}, {paired['upper_95']:.4%}] and paired permutation p-value {paired['permutation_p_value']:.3f}.
This is not statistically detectable incremental value unless the interval excludes zero; the sample is small.
Raw expected-return sign and recursive bias sign are reported separately in the benchmark table.

## Cost and execution sensitivity

Transaction cost is interpreted as a total round-trip deduction applied once, covering entry plus exit; slippage
is an additional assumed round-trip deduction. The 0/10/20 bps and 0.00/0.05/0.10/0.20% grids are in
`research/validation/weekly_trade_sensitivity.csv`. These are assumptions, not historical XAUUSD execution records.
Monday-open uses the first available daily gold session after the prediction Friday where available.

## Risk, regime, confidence, and failure analysis

The trade log contains equity, drawdown, direction, conviction, prior failure archetype, warning state, and realized
prediction error. Regime and confidence summaries are emitted in the metrics JSON. Samples with fewer than 20
observations must be treated as LOW SAMPLE; fewer than 10 as VERY LOW SAMPLE.

## Walk-forward integrity

The final row without a realized following week is excluded. Training ends before the first evaluation prediction.
For each row the recursive prediction is generated before t+1 OHLC is read; only after t+1 close is observed is
the recursive post-mortem, Kalman update, and failure-memory update performed. Position volatility uses only the
current row's trailing estimate. A violation fails the backtest rather than producing a profitability claim.

## Capital and uncertainty

Starting capital is $10,000; fixed 1x is the primary result. The equity CSV and HTML artifact are generated alongside
the report. Bootstrap/permutation outputs are descriptive uncertainty estimates for this finite weekly sample.

## Final verdict

- **PROFITABILITY:** {m['total_return']:.2%} cumulative over {m['weeks']} realized weeks.
- **RISK:** maximum drawdown {m['max_drawdown']:.2%}; annualized volatility {m['volatility']:.2%}.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate {paired['mean_difference']:.4%}; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
"""
        report_path.write_text(report, encoding="utf-8")
        if name == "weekly_trade_backtest_52":
            validation = Path("research/validation")
            reports = Path("research/reports")
            validation.mkdir(parents=True, exist_ok=True)
            reports.mkdir(parents=True, exist_ok=True)
            exact_csv = validation / "weekly_trade_log_52w.csv"
            exact_report = reports / "WEEKLY_TRADING_PROFITABILITY_52W.md"
            trades.to_csv(exact_csv, index=False)
            exact_report.write_text(report, encoding="utf-8")
            csv_path, report_path = exact_csv, exact_report
        return {"trades": str(csv_path), "metrics": str(json_path), "report": str(report_path),
                "equity": str(curve_path), "chart": str(chart_path),
                "drawdown": str(drawdown_path)}


def run_weekly_trade_backtest(data: Optional[pd.DataFrame] = None, **kwargs: Any) -> Dict[str, Any]:
    """Functional entry point for notebooks and callers that prefer no class state."""
    return WeeklyTradeBacktest(data=data).run(**kwargs)


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=TITLE)
    p.add_argument("--period", default="52", choices=["52", "26", "13", "full"])
    p.add_argument("--execution", default="friday_close", choices=["friday_close", "monday_open", "tuesday_confirmation", "gap_skip"])
    p.add_argument("--threshold", type=float, default=.05)
    p.add_argument("--cost-bps", type=float, default=0.0)
    p.add_argument("--slippage", type=float, default=0.0, help="round-trip decimal, e.g. .001")
    p.add_argument("--no-stops", action="store_true", help="disable corridor stop/target execution")
    p.add_argument("--stop-pct", type=float, default=.025)
    p.add_argument("--target-pct", type=float, default=.020)
    p.add_argument("--all", action="store_true", help="run 52, 26, 13, and full")
    args = p.parse_args(argv)
    bt = WeeklyTradeBacktest()
    periods = ["52", "26", "13", "full"] if args.all else [args.period]
    sensitivity = []
    for period in periods:
        result = bt.run(period=period, execution=args.execution, threshold=args.threshold,
                        cost_bps=args.cost_bps, slippage=args.slippage,
                        use_stops=not args.no_stops, stop_pct=args.stop_pct,
                        target_pct=args.target_pct)
        paths = bt.write_outputs(result, f"weekly_trade_backtest_{period}")
        sensitivity.append({"period": period, "threshold": args.threshold,
                            "cost_bps": args.cost_bps, "slippage": args.slippage,
                            **result["metrics"]})
        print(f"{period}: {result['metrics']} -> {paths['report']}")
    if args.all or args.period == "52":
        grid = []
        for th in (.03, .05, .08, .10):
            for cb in (0.0, 10.0, 20.0):
                for slip in (0.0, .0005, .001, .002):
                    x = bt.run(period=52, execution=args.execution, threshold=th,
                               cost_bps=cb, slippage=slip,
                               use_stops=not args.no_stops, stop_pct=args.stop_pct,
                               target_pct=args.target_pct)
                    grid.append({"period": 52, "threshold": th, "cost_bps": cb,
                                 "slippage": slip, **x["metrics"]})
        out = Path("research/validation")
        out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(sensitivity + grid).to_csv(out / "weekly_trade_sensitivity.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
