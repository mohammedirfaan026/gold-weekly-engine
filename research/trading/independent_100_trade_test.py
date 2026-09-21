"""Independent 100-trade portfolio evaluation of Gold Weekly AI predictions.

This script does NOT tune parameters. It freezes two published specs and walks
forward from the most recent realized weeks until 100 filled trades are taken.

Specs evaluated:
  1) Locked baseline: threshold 0.10, no corridor stops, 10 bps + 0.05% slip
  2) Shadow-frozen exploratory: threshold 0.05, corridor stops, 10 bps + 0.05% slip
  3) Same exploratory at 0 cost (optimistic research case)

Outputs portfolio equity, trade log, and a go-live readiness verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.trading.weekly_trade_backtest import WeeklyTradeBacktest, _trade_metrics


STARTING_CAPITAL = 10_000.0
TARGET_TRADES = 100


def _trim_to_n_trades(result: Dict[str, Any], n: int = TARGET_TRADES) -> Dict[str, Any]:
    trades = result["trades"].copy()
    active = trades[trades["signal"] != 0].copy()
    if len(active) < n:
        raise RuntimeError(
            f"Only {len(active)} filled trades available in window; need {n}. "
            "Increase lookback period."
        )
    # Keep the most recent n filled trades, plus intervening flat weeks for equity continuity.
    keep_ids = set(active.tail(n).index)
    first_keep = min(keep_ids)
    window = trades.loc[first_keep:].copy()
    # Drop leading flats before the first of the n trades already handled by first_keep.
    # Recompute equity only on this window.
    window["equity"] = (1.0 + window["net_return"]).cumprod()
    window["drawdown"] = window["equity"] / window["equity"].cummax() - 1.0
    window["capital"] = STARTING_CAPITAL * window["equity"]
    filled = window[window["signal"] != 0]
    assert len(filled) == n, f"expected {n} trades, got {len(filled)}"

    metrics = _trade_metrics(window["net_return"].tolist(), window["signal"].tolist())
    buy_hold = window["realized_return"].astype(float).tolist()
    static = _trade_metrics(window["static_return"].tolist(), window["static_signal"].tolist())
    out = dict(result)
    out["trades"] = window
    out["metrics"] = metrics
    out["static_ai"] = static
    out["baselines"] = {
        "buy_hold": _trade_metrics(buy_hold, [1] * len(buy_hold)),
    }
    out["filled_trades"] = int(n)
    out["weeks_in_window"] = int(len(window))
    out["start_week"] = str(window["week_ending"].iloc[0])
    out["end_week"] = str(window["trade_week"].iloc[-1])
    out["ending_capital"] = float(window["capital"].iloc[-1])
    out["peak_capital"] = float(window["capital"].max())
    out["trough_capital"] = float(window["capital"].min())
    return out


def _run_until_trades(
    bt: WeeklyTradeBacktest,
    *,
    threshold: float,
    use_stops: bool,
    cost_bps: float,
    slippage: float,
    label: str,
    lookback_weeks: int = 180,
) -> Dict[str, Any]:
    raw = bt.run(
        period=lookback_weeks,
        execution="friday_close",
        threshold=threshold,
        cost_bps=cost_bps,
        slippage=slippage,
        sizing="fixed",
        use_stops=use_stops,
        ambiguous="conservative",
        stop_pct=0.025,
        target_pct=0.020,
    )
    trimmed = _trim_to_n_trades(raw, TARGET_TRADES)
    trimmed["label"] = label
    return trimmed


def _portfolio_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    m = result["metrics"]
    trades = result["trades"]
    filled = trades[trades["signal"] != 0]
    longs = int((filled["signal"] > 0).sum())
    shorts = int((filled["signal"] < 0).sum())
    return {
        "label": result["label"],
        "start_week": result["start_week"],
        "end_week": result["end_week"],
        "weeks_in_window": result["weeks_in_window"],
        "filled_trades": result["filled_trades"],
        "long_trades": longs,
        "short_trades": shorts,
        "flat_weeks": int(m.get("flat_weeks", 0)),
        "starting_capital": STARTING_CAPITAL,
        "ending_capital": round(result["ending_capital"], 2),
        "peak_capital": round(result["peak_capital"], 2),
        "trough_capital": round(result["trough_capital"], 2),
        "total_return_pct": round(100 * m["total_return"], 2),
        "annualized_return_pct": round(100 * m["annualized_return"], 2),
        "sharpe": round(m["sharpe"], 2),
        "max_drawdown_pct": round(100 * m["max_drawdown"], 2),
        "trade_win_rate_pct": round(100 * m["trade_win_rate"], 2),
        "profit_factor": round(float(m["profit_factor"]), 2) if np.isfinite(m["profit_factor"]) else None,
        "expectancy_pct": round(100 * m["expectancy"], 3),
        "avg_winner_pct": round(100 * m["average_winner"], 3),
        "avg_loser_pct": round(100 * m["average_loser"], 3),
        "best_trade_pct": round(100 * m["best_trade"], 2),
        "worst_trade_pct": round(100 * m["worst_trade"], 2),
        "buy_hold_return_pct": round(100 * result["baselines"]["buy_hold"]["total_return"], 2),
        "static_ai_return_pct": round(100 * result["static_ai"]["total_return"], 2),
        "config": result["config"],
    }


def _readiness_verdict(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    locked = next(s for s in summaries if "Locked" in s["label"])
    shadow = next(s for s in summaries if "Shadow-frozen" in s["label"])

    blockers = []
    warnings = []

    if locked["total_return_pct"] <= 0:
        blockers.append(
            "Locked baseline (threshold 0.10, no stops) is not profitable after realistic costs over the last 100 trades."
        )
    if shadow["max_drawdown_pct"] < -15:
        blockers.append("Shadow-frozen max drawdown exceeds -15% on the 100-trade sample.")
    if shadow["trade_win_rate_pct"] < 50:
        warnings.append("Shadow-frozen win rate below 50% after costs.")
    if abs(shadow["total_return_pct"] - locked["total_return_pct"]) > 20:
        warnings.append(
            "Large gap between locked baseline and exploratory corridor spec — corridor result is post-hoc and not unbiased OOS proof."
        )

    blockers.extend([
        "No live broker/order-routing integration exists (research CLI + decision brief only).",
        "Weekly OHLC cannot resolve same-bar stop vs target order; live fills will differ.",
        "No completed forward shadow period yet under the frozen 2026-09-18 protocol.",
        "Transaction costs/slippage are assumptions, not measured XAUUSD execution records.",
    ])

    production_ready = False
    live_market_use = (
        "Decision-support / discretionary shadow only. "
        "Do NOT auto-route or size live capital solely on model output."
    )

    return {
        "production_ready": production_ready,
        "live_market_use": live_market_use,
        "recommended_mode": "SHADOW / PAPER with human discretionary confirmation",
        "blockers": blockers,
        "warnings": warnings,
        "why_not_production": [
            "Historical backtest edge != live edge; sample selection and corridor params were explored after seeing results.",
            "Recursive incremental value was not consistently detectable on the locked 52w baseline.",
            "No autonomous execution, kill-switch ops, or broker reconciliation stack.",
            "Shadow protocol Phase 1 (13 weeks) has not completed from the freeze date.",
        ],
    }


def main() -> int:
    out_dir = ROOT / "research" / "trading" / "output" / "independent_100"
    out_dir.mkdir(parents=True, exist_ok=True)
    bt = WeeklyTradeBacktest()

    specs = [
        {
            "label": "Locked baseline (th=0.10, no stops, 10bps+5bps slip)",
            "threshold": 0.10,
            "use_stops": False,
            "cost_bps": 10.0,
            "slippage": 0.0005,
        },
        {
            "label": "Shadow-frozen exploratory (th=0.05, corridor, 10bps+5bps slip)",
            "threshold": 0.05,
            "use_stops": True,
            "cost_bps": 10.0,
            "slippage": 0.0005,
        },
        {
            "label": "Exploratory zero-cost (th=0.05, corridor, 0 cost)",
            "threshold": 0.05,
            "use_stops": True,
            "cost_bps": 0.0,
            "slippage": 0.0,
        },
    ]

    results: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []
    for spec in specs:
        print(f"Running: {spec['label']} ...", flush=True)
        r = _run_until_trades(bt, **spec)
        results.append(r)
        summaries.append(_portfolio_summary(r))
        # Persist trade log + equity for this spec
        safe = spec["label"].split("(")[0].strip().lower().replace(" ", "_")
        r["trades"].to_csv(out_dir / f"{safe}_trades.csv", index=False)
        equity = r["trades"][["week_ending", "trade_week", "signal", "net_return", "equity", "capital", "drawdown"]].copy()
        equity.to_csv(out_dir / f"{safe}_equity.csv", index=False)

    verdict = _readiness_verdict(summaries)

    payload = {
        "target_trades": TARGET_TRADES,
        "starting_capital": STARTING_CAPITAL,
        "portfolios": summaries,
        "readiness": verdict,
    }
    (out_dir / "independent_100_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    # Human-readable report
    lines = [
        "# Independent 100-Trade Portfolio Test",
        "",
        f"**Target:** {TARGET_TRADES} filled trades on model predictions",
        f"**Starting capital:** ${STARTING_CAPITAL:,.0f}",
        f"**Execution:** Friday close → 1-week hold (point-in-time recursive prediction)",
        "",
        "## Portfolio results",
        "",
        "| Spec | Window | Trades (L/S) | Ending $ | Return | Sharpe | MaxDD | Win% | vs Buy&Hold |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['label']} | {s['start_week']} -> {s['end_week']} | "
            f"{s['filled_trades']} ({s['long_trades']}/{s['short_trades']}) | "
            f"${s['ending_capital']:,.2f} | {s['total_return_pct']:.2f}% | "
            f"{s['sharpe']:.2f} | {s['max_drawdown_pct']:.2f}% | "
            f"{s['trade_win_rate_pct']:.1f}% | {s['buy_hold_return_pct']:.2f}% |"
        )

    lines += [
        "",
        "## Primary portfolio (Shadow-frozen, after costs)",
        "",
    ]
    primary = next(s for s in summaries if "Shadow-frozen" in s["label"])
    lines += [
        f"- Start: **${STARTING_CAPITAL:,.0f}** → End: **${primary['ending_capital']:,.2f}**",
        f"- Peak / trough capital: ${primary['peak_capital']:,.2f} / ${primary['trough_capital']:,.2f}",
        f"- Expectancy / trade: {primary['expectancy_pct']:.3f}%",
        f"- Avg winner / loser: {primary['avg_winner_pct']:.3f}% / {primary['avg_loser_pct']:.3f}%",
        f"- Best / worst trade: {primary['best_trade_pct']:.2f}% / {primary['worst_trade_pct']:.2f}%",
        "",
        "## Is it production ready?",
        "",
        f"**No.** `production_ready = {verdict['production_ready']}`",
        "",
        f"**Live market use:** {verdict['live_market_use']}",
        "",
        f"**Recommended mode:** {verdict['recommended_mode']}",
        "",
        "### Blockers",
        "",
    ]
    for b in verdict["blockers"]:
        lines.append(f"- {b}")
    lines += ["", "### Why not production", ""]
    for w in verdict["why_not_production"]:
        lines.append(f"- {w}")
    if verdict["warnings"]:
        lines += ["", "### Warnings", ""]
        for w in verdict["warnings"]:
            lines.append(f"- {w}")

    lines += [
        "",
        "## Bottom line",
        "",
        "The model can generate a researched weekly bias and a simulated portfolio.",
        "On this independent 100-trade sample after costs, treat it as **research / shadow decision-support**,",
        "not as a production auto-trader for real live capital.",
        "",
        f"Artifacts: `{out_dir}`",
    ]
    report = "\n".join(lines) + "\n"
    (out_dir / "INDEPENDENT_100_TRADE_REPORT.md").write_text(report, encoding="utf-8")
    (ROOT / "research" / "reports" / "INDEPENDENT_100_TRADE_REPORT.md").write_text(
        report, encoding="utf-8"
    )

    print(report)
    print(f"\nWrote: {out_dir / 'independent_100_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
