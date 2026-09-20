import numpy as np
import pandas as pd

from src.ai_engine.trade_executor import (
    apply_costs, signal_from_bias, simulate_corridor_trade, size_position,
)
from research.trading.weekly_trade_backtest import WeeklyTradeBacktest, _metrics


def test_signal_thresholds_are_symmetric():
    assert signal_from_bias(.15, .15) == 1
    assert signal_from_bias(-.15, .15) == -1
    assert signal_from_bias(.149, .15) == 0
    assert signal_from_bias(np.nan, .15) == 0


def test_round_trip_costs_and_slippage():
    assert apply_costs(.02, 1, 10, .001) == .018
    assert apply_costs(.02, 0, 10, .001) == 0


def test_ambiguous_stop_target_modes():
    conservative = simulate_corridor_trade(1, 100, 101, 105, 95, 104, 96, "conservative")
    optimistic = simulate_corridor_trade(1, 100, 101, 105, 95, 104, 96, "optimistic")
    assert conservative.exit == 96
    assert optimistic.exit == 104


def test_sizing_and_drawdown_metrics():
    assert size_position(.04, "fixed") == 1
    assert size_position(.04, "volatility_scaled") == 2.0
    metrics = _metrics([.1, -.05, -.2, .1])
    assert metrics["max_drawdown"] < -.2
    assert metrics["weeks"] == 4


def test_weekly_loop_uses_realized_rows_and_timing():
    n = 40
    close = np.linspace(100, 120, n)
    df = pd.DataFrame({
        "week_ending": pd.date_range("2025-01-03", periods=n, freq="7D"),
        "open": close, "high": close * 1.03, "low": close * .97, "close": close,
        "next_week_gold_return": pd.Series(close).shift(-1) / close - 1,
        "delta_real_yield_1w": np.linspace(-.02, .02, n),
        "dxy_return_1w": np.zeros(n), "delta_breakeven_1w": np.zeros(n),
        "gold_distance_20w": np.zeros(n), "vix": np.full(n, 15.),
    })
    result = WeeklyTradeBacktest(data=df).run(period=13, execution="monday_open")
    assert len(result["trades"]) == 13
    assert result["leakage_audit"]["training_rows_end_before_eval"]
    assert result["leakage_audit"]["outcome_observed_after_prediction"]
