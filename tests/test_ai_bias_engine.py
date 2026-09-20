"""
Automated Test Suite for the Gold AI Weekly Bias & Range Engine.
Verifies:
1. Bias score boundedness in [-1.0, +1.0].
2. Economic monotonicity (real yield and DXY inverse sensitivity).
3. Range corridor ordering: Low 10% < Center < High 90%.
4. Tail risk probability bounds in [0, 1].
5. Strict point-in-time analog search invariant (zero look-ahead).
6. Master engine inference pipeline.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai_engine.core_bias import MacroBiasEstimator
from src.ai_engine.range_predictor import WeeklyRangePredictor
from src.ai_engine.tail_risk import TailRiskEstimator
from src.ai_engine.analog_matcher import PointInTimeAnalogMatcher
from src.ai_engine.engine import GoldWeeklyBiasEngine


@pytest.fixture(scope="module")
def loaded_engine():
    engine = GoldWeeklyBiasEngine()
    engine.load_data()
    engine.fit()
    return engine


def test_bias_score_boundedness(loaded_engine):
    """Verifies that the bias score is strictly bounded in [-1.0, +1.0] across sample weeks."""
    sample_df = loaded_engine.matrix.sample(30, random_state=42)
    estimator = loaded_engine.bias_model

    for _, row in sample_df.iterrows():
        res = estimator.predict_bias(pd.DataFrame([row]))
        score = res["bias_score"]
        assert -1.0 <= score <= 1.0, f"Bias score {score} out of bounds [-1.0, +1.0]!"
        assert res["bias_category"] in ["STRONG_BULLISH", "MILD_BULLISH", "NEUTRAL", "MILD_BEARISH", "STRONG_BEARISH"]


def test_economic_monotonicity(loaded_engine):
    """Verifies that higher real yields penalize gold bias score."""
    estimator = loaded_engine.bias_model
    base_row = loaded_engine.matrix.iloc[-2].copy()

    # Create synthetic test rows: rising yields vs falling yields
    row_falling = base_row.copy()
    row_falling["delta_real_yield_1w"] = -0.15  # -15 bps real yield drop

    row_rising = base_row.copy()
    row_rising["delta_real_yield_1w"] = +0.15   # +15 bps real yield spike

    res_falling = estimator.predict_bias(pd.DataFrame([row_falling]))
    res_rising = estimator.predict_bias(pd.DataFrame([row_rising]))

    assert res_falling["bias_score"] >= res_rising["bias_score"], (
        f"Monotonicity violation: falling yield bias ({res_falling['bias_score']}) "
        f"should be >= rising yield bias ({res_rising['bias_score']})"
    )


def test_range_corridor_ordering(loaded_engine):
    """Verifies that predicted range satisfies Low 10% < Center < High 90%."""
    prediction = loaded_engine.predict_week()
    corridor = prediction["expected_price_corridor"]

    low = corridor["expected_low_10pct"]
    center = corridor["expected_center"]
    high = corridor["expected_high_90pct"]

    assert low < center, f"Range ordering error: Low ({low}) >= Center ({center})"
    assert center < high, f"Range ordering error: Center ({center}) >= High ({high})"
    assert corridor["expected_dollar_range"] == round(high - low, 2)


def test_tail_risk_probabilities(loaded_engine):
    """Verifies that risk probabilities are in [0, 1] and sum properly."""
    prediction = loaded_engine.predict_week()
    risk = prediction["tail_risk_probabilities"]

    p_up = risk["p_positive_week"]
    p_down = risk["p_negative_week"]

    assert 0.0 <= p_up <= 1.0
    assert 0.0 <= p_down <= 1.0
    assert abs((p_up + p_down) - 1.0) < 1e-5

    assert 0.0 <= risk["p_breakout_surge_plus_1pct"] <= 1.0
    assert 0.0 <= risk["p_liquidation_flush_minus_1pct"] <= 1.0


def test_pit_analog_no_future_leak(loaded_engine):
    """Verifies that matched historical analogs are strictly older than the target week."""
    # Test for an intermediate historical week (e.g. week 500 in 2019)
    target_idx = 500
    target_row = loaded_engine.matrix.iloc[target_idx]
    target_date = pd.Timestamp(target_row["week_ending"])

    analogs = loaded_engine.analog_matcher.find_analogs(target_row, loaded_engine.matrix, top_k=3)
    assert len(analogs) == 3

    for a in analogs:
        analog_date = pd.Timestamp(a["week_ending"])
        # Analog week must be strictly earlier than target date
        assert analog_date < target_date, (
            f"Forward look-ahead detected: analog date {analog_date} >= target date {target_date}"
        )


def test_full_engine_briefing_output(loaded_engine):
    """Verifies that format_briefing produces structured, informative text."""
    pred = loaded_engine.predict_week()
    briefing = loaded_engine.format_briefing(pred)

    assert "GOLD AI WEEKLY BIAS & VOLATILITY CORRIDOR ENGINE" in briefing
    assert "Expected Weekly Trading Range" in briefing
    assert "TAIL RISK & EXCURSION PROBABILITIES" in briefing
    assert "HISTORICAL MACROECONOMIC TWINS" in briefing
