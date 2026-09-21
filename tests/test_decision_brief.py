"""
Unit and Integration Tests for Institutional Decision Support and Live Decision Brief System.
Validates:
- Conservative taxonomy adherence (no BUY/SELL commands)
- Empirical confidence calibration tiers
- Strict No-Trade circuit breaker conditions
- Data freshness auditing and stale triggers
- Trade journal logging and decision quality metrics
- Discretionary execution scenario simulations (Tuesday confirmation & Gap skip)
"""

import os
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.ai_engine.confidence_calibrator import ConfidenceCalibrator
from src.ai_engine.no_trade_filter import NoTradeFilter
from src.ai_engine.data_freshness import DataFreshnessChecker
from src.ai_engine.trade_journal import TradeJournal
from src.ai_engine.decision_brief import WeeklyDecisionBrief
from research.trading.weekly_trade_backtest import WeeklyTradeBacktest


def test_confidence_calibrator_tiers():
    cal = ConfidenceCalibrator()

    # Low tier
    low = cal.calibrate(0.04)
    assert low["tier"] == "LOW"
    assert low["empirical_win_rate_pct"] < 50.0
    assert low["empirical_sharpe"] < 0

    # Moderate tier
    mod = cal.calibrate(0.22)
    assert mod["tier"] == "MODERATE"
    assert mod["empirical_win_rate_pct"] > 60.0
    assert mod["empirical_sharpe"] > 2.0

    # High tier
    high = cal.calibrate(-0.35)
    assert high["tier"] == "HIGH"
    assert high["empirical_win_rate_pct"] >= 75.0
    assert high["empirical_sharpe"] > 5.0


def test_no_trade_filter_sub_threshold():
    nt = NoTradeFilter(bias_threshold=0.05)
    res = nt.evaluate(bias_score=0.02, features_dict={"vix": 14.0})
    assert res["is_no_trade"] is True
    assert any(t["code"] == "SUB_THRESHOLD_EDGE" for t in res["triggers"])
    assert "NEUTRAL" in res["status_label"] or "DO NOT TRADE" in res["status_label"]


def test_no_trade_filter_macro_divergence():
    nt = NoTradeFilter(bias_threshold=0.05)
    # Yields up > 5 bps (bearish for gold) but DXY down < -0.8% (bullish for gold)
    features = {
        "delta_real_yield_1w": 0.08,
        "dxy_return_1w": -0.012,
        "vix": 15.0,
    }
    res = nt.evaluate(bias_score=0.18, features_dict=features)
    assert res["is_no_trade"] is True
    assert any(t["code"] == "MACRO_DIVERGENCE_CONFLICT" for t in res["triggers"])


def test_no_trade_filter_vix_spike():
    nt = NoTradeFilter(vix_hard_limit=25.0)
    res = nt.evaluate(bias_score=0.25, features_dict={"vix": 28.5})
    assert res["is_no_trade"] is True
    assert any(t["code"] == "HIGH_VOLATILITY_REGIME" for t in res["triggers"])


def test_no_trade_filter_failure_trap():
    nt = NoTradeFilter(trap_similarity_limit=0.70)
    memory_data = {
        "failure_similarity_score": 0.82,
        "reflexive_warning_active": True,
        "matching_failure_archetype": "COUNTER_TREND_EXHAUSTION",
    }
    res = nt.evaluate(bias_score=0.20, features_dict={"vix": 15.0}, failure_memory_data=memory_data)
    assert res["is_no_trade"] is True
    assert any(t["code"] == "FAILURE_MEMORY_TRAP" for t in res["triggers"])


def test_data_freshness_checker_operational():
    fc = DataFreshnessChecker()
    report = fc.check_freshness(as_of_date="2026-09-20 00:00:00+00:00")
    assert "series" in report
    assert "is_usable" in report
    assert len(report["series"]) >= 5
    formatted = fc.format_freshness_table(report)
    assert "Observation Reference" in formatted
    assert "Pipeline Status" in formatted


def test_trade_journal_lifecycle(tmp_path):
    journal = TradeJournal(journal_dir=tmp_path)
    entry = journal.log_decision(
        week_ending="2026-09-18",
        gold_price=6250.0,
        model_bias_score=0.25,
        confidence_tier="MODERATE",
        no_trade_triggered=False,
        trader_decision="FOLLOW",
        planned_entry=6250.0,
        planned_stop=6100.0,
        planned_target=6375.0,
    )
    assert entry["entry_id"].startswith("JRN-20260918-")
    assert entry["outcome_status"] == "PENDING"

    # Verify history
    df = journal.get_history()
    assert len(df) == 1
    assert df.iloc[0]["trader_decision"] == "FOLLOW"

    # Update outcome
    updated = journal.update_outcome(
        entry_id=entry["entry_id"],
        actual_entry_price=6250.0,
        actual_exit_price=6350.0,
        realized_pnl_pct=0.016,
        outcome_status="WIN",
        lessons_learned="Corridor target was hit cleanly.",
    )
    assert updated is not None
    assert updated["outcome_status"] == "WIN"
    assert updated["realized_pnl_pct"] == 0.016

    # Verify stats
    stats = journal.compute_quality_stats()
    assert stats["total_decisions_logged"] == 1
    assert stats["resolved_trades"] == 1
    assert stats["when_model_followed"]["win_rate"] == 100.0


def test_decision_brief_taxonomy_and_content():
    brief_gen = WeeklyDecisionBrief()
    prediction = {
        "observation_week": "2026-09-18",
        "prediction_timestamp": "2026-09-18 21:00:00+00:00",
        "current_gold_price": 6250.0,
        "ai_weekly_bias": {
            "bias_score": 0.22,
            "bias_category": "MODERATE_BULLISH",
            "expected_weekly_return_pct": 0.85,
        },
        "expected_price_corridor": {
            "expected_high_90pct": 6375.0,
            "expected_center": 6250.0,
            "expected_low_10pct": 6125.0,
        },
    }
    features = {
        "delta_real_yield_1w": -0.04,
        "dxy_return_1w": -0.002,
        "vix": 16.0,
        "gold_distance_20w": 0.03,
    }

    brief = brief_gen.generate_brief(prediction=prediction, features_dict=features, fetch_news=False)
    assert "taxonomy_stance" in brief
    assert "Bullish bias -- confirmation required" in brief["taxonomy_stance"]

    rendered = brief_gen.render_markdown(brief)
    # Ensure strict non-prescriptive taxonomy (No BUY/SELL commands)
    assert "BUY " not in rendered.upper()
    assert "SELL " not in rendered.upper()
    assert "STRONG BUY" not in rendered.upper()
    assert "STRONG SELL" not in rendered.upper()
    assert "PRICE VOLATILITY CORRIDOR" in rendered
    assert "SCENARIO MAP" in rendered
    assert "DATA FRESHNESS" in rendered
    assert "LIVE NEWS" in rendered
    assert "AUTO-FETCHED" in rendered


def test_backtest_execution_models():
    n = 30
    close = np.linspace(2000, 2200, n)
    df = pd.DataFrame({
        "week_ending": pd.date_range("2025-01-03", periods=n, freq="7D"),
        "open": close, "high": close * 1.02, "low": close * 0.98, "close": close,
        "next_week_gold_return": pd.Series(close).shift(-1) / close - 1,
        "delta_real_yield_1w": np.linspace(-0.01, 0.01, n),
        "dxy_return_1w": np.zeros(n), "delta_breakeven_1w": np.zeros(n),
        "gold_distance_20w": np.zeros(n), "vix": np.full(n, 15.0),
    })

    bt = WeeklyTradeBacktest(data=df)
    res_fc = bt.run(period=10, execution="friday_close")
    res_gap = bt.run(period=10, execution="gap_skip")

    assert len(res_fc["trades"]) == 10
    assert len(res_gap["trades"]) == 10
    assert "corridor_containment_rate" in res_fc["decision_quality"]
    assert "confidence_tiers" in res_fc["decision_quality"]
    assert res_fc["config"]["execution"] == "friday_close"
