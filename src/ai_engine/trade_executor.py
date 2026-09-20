"""Execution and portfolio primitives for weekly research backtests.

This module intentionally contains no model fitting.  It is used by the research
backtest so that entry timing, costs, stops, and sizing are explicit and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


def signal_from_bias(bias: float, threshold: float = 0.10) -> int:
    """Return +1 (long), -1 (short), or 0 (flat) using symmetric thresholds."""
    if not np.isfinite(bias):
        return 0
    if bias >= abs(threshold):
        return 1
    if bias <= -abs(threshold):
        return -1
    return 0


def apply_costs(raw_return: float, signal: int, cost_bps: float = 0.0,
                slippage: float = 0.0) -> float:
    """Apply round-trip transaction costs and round-trip slippage."""
    if signal == 0:
        return 0.0
    return float(raw_return - cost_bps / 10000.0 - abs(slippage))


@dataclass
class TradeResult:
    signal: int
    entry: float
    exit: float
    raw_return: float
    net_return: float
    stopped: bool = False
    stop_reason: str = ""
    size: float = 1.0


def simulate_corridor_trade(
    signal: int,
    entry: float,
    close: float,
    high: float,
    low: float,
    target: Optional[float] = None,
    stop: Optional[float] = None,
    ambiguous: str = "conservative",
    cost_bps: float = 0.0,
    slippage: float = 0.0,
    size: float = 1.0,
) -> TradeResult:
    """Simulate one weekly trade using OHLC and an optional stop/target corridor.

    If both levels are touched in the same weekly bar, conservative chooses the
    adverse level and optimistic chooses the favorable level.
    """
    if signal == 0 or not np.isfinite(entry) or entry <= 0:
        return TradeResult(0, entry, entry, 0.0, 0.0, size=size)
    ambiguous = ambiguous.lower()
    if ambiguous not in {"conservative", "optimistic"}:
        raise ValueError("ambiguous must be conservative or optimistic")
    hit_stop = stop is not None and ((signal > 0 and low <= stop) or (signal < 0 and high >= stop))
    hit_target = target is not None and ((signal > 0 and high >= target) or (signal < 0 and low <= target))
    exit_price, reason = close, ""
    if hit_stop and hit_target:
        if ambiguous == "conservative":
            exit_price, reason = stop, "stop_and_target_conservative"
        else:
            exit_price, reason = target, "stop_and_target_optimistic"
    elif hit_stop:
        exit_price, reason = stop, "stop"
    elif hit_target:
        exit_price, reason = target, "target"
    unit_raw = signal * (float(exit_price) / float(entry) - 1.0)
    # cost_bps and slippage are already round-trip assumptions.  Scale both
    # P&L and costs once by notional size.
    raw = unit_raw * float(size)
    net = (unit_raw - cost_bps / 10000.0 - abs(slippage)) * float(size)
    return TradeResult(signal, float(entry), float(exit_price), raw, net,
                       bool(reason), reason, float(size))


def size_position(volatility: float, sizing: str = "fixed", target_vol: float = 0.10,
                  max_size: float = 2.0) -> float:
    """Fixed or trailing-volatility scaled notional, capped for risk control."""
    if sizing == "fixed":
        return 1.0
    if sizing not in {"volatility", "volatility_scaled"}:
        raise ValueError("sizing must be fixed or volatility_scaled")
    if not np.isfinite(volatility) or volatility <= 0:
        return 1.0
    return float(np.clip(target_vol / volatility, 0.0, max_size))


class TradeExecutor:
    """Small state-free facade convenient for notebooks and tests."""

    signal_from_bias = staticmethod(signal_from_bias)
    apply_costs = staticmethod(apply_costs)
    simulate_corridor_trade = staticmethod(simulate_corridor_trade)
    size_position = staticmethod(size_position)
