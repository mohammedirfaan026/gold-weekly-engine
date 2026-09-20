"""
Unit tests for the Recursive Self-Improving Gold AI Engine.
"""

import pytest
import numpy as np
import pandas as pd

from src.ai_engine.recursive_learner import (
    FailureArchetype,
    ErrorAttributionEngine,
    FailureMemoryBank,
    RecursiveKalmanEstimator,
    RecursiveSelfImprovingEngine,
)


def test_error_attribution_archetypes():
    engine = ErrorAttributionEngine()

    # 1. Counter-trend exhaustion: yields plunged, but gold dropped
    res1 = engine.evaluate_miss(
        predicted_ret=0.002,
        actual_ret=-0.025,
        predicted_bias=0.05,
        delta_real_yield=-0.09,
        dxy_ret=0.001,
        vix=14.0,
        gold_distance_20w=0.01,
    )
    assert res1["archetype"] == FailureArchetype.COUNTER_TREND_EXHAUSTION
    assert res1["is_error"] is True

    # 2. Volatility liquidation: VIX > 22 spike
    res2 = engine.evaluate_miss(
        predicted_ret=0.003,
        actual_ret=-0.040,
        predicted_bias=0.10,
        delta_real_yield=0.01,
        dxy_ret=0.002,
        vix=26.5,
        gold_distance_20w=0.02,
    )
    assert res2["archetype"] == FailureArchetype.VOLATILITY_LIQUIDATION
    assert res2["is_transient_noise"] is True

    # 3. Macro decoupling: USD & yields surged, but gold rallied
    res3 = engine.evaluate_miss(
        predicted_ret=-0.002,
        actual_ret=+0.035,
        predicted_bias=-0.05,
        delta_real_yield=+0.06,
        dxy_ret=+0.015,
        vix=15.0,
        gold_distance_20w=0.02,
    )
    assert res3["archetype"] == FailureArchetype.MACRO_DECOUPLING
    assert res3["is_structural_shift"] is True

    # 4. In-line accurate prediction
    res4 = engine.evaluate_miss(
        predicted_ret=0.005,
        actual_ret=0.007,
        predicted_bias=0.04,
        delta_real_yield=-0.01,
        dxy_ret=-0.002,
        vix=13.5,
        gold_distance_20w=0.01,
    )
    assert res4["archetype"] == FailureArchetype.IN_LINE
    assert res4["is_error"] is False


def test_failure_memory_bank_query():
    bank = FailureMemoryBank()

    # Record a counter-trend failure
    failed_features = {
        "delta_real_yield_1w": -0.10,
        "dxy_return_1w": 0.001,
        "gold_distance_20w": 0.01,
        "vix": 14.0,
    }
    bank.record_failure(
        week="2025-01-17",
        features=failed_features,
        archetype=FailureArchetype.COUNTER_TREND_EXHAUSTION,
        error=0.05,
        actual_ret=-0.052,
    )

    # Query with an identical / very similar setup
    similar_features = {
        "delta_real_yield_1w": -0.095,
        "dxy_return_1w": 0.001,
        "gold_distance_20w": 0.01,
        "vix": 14.2,
    }
    risk = bank.query_reflexive_risk(similar_features)
    assert risk["reflexive_warning"] is True
    assert risk["max_similarity"] > 0.85
    assert risk["matching_archetype"] == FailureArchetype.COUNTER_TREND_EXHAUSTION.value
    assert risk["corridor_widening_factor"] > 1.0


def test_recursive_kalman_updating():
    kalman = RecursiveKalmanEstimator()
    dummy_df = pd.DataFrame({
        "delta_real_yield_1w": np.random.normal(0, 0.03, 100),
        "dxy_return_1w": np.random.normal(0, 0.01, 100),
        "delta_breakeven_1w": np.random.normal(0, 0.02, 100),
        "gold_distance_20w": np.random.normal(0.01, 0.02, 100),
        "next_week_gold_return": np.random.normal(0.002, 0.02, 100),
    })
    kalman.warm_start(dummy_df, dummy_df["next_week_gold_return"])
    assert not np.isnan(kalman.w).any()

    w_before = kalman.w.copy()
    past_row = {
        "delta_real_yield_1w": -0.08,
        "dxy_return_1w": -0.005,
        "delta_breakeven_1w": 0.01,
        "gold_distance_20w": 0.02,
    }
    attribution = {
        "archetype": FailureArchetype.MACRO_DECOUPLING,
        "is_transient_noise": False,
        "is_structural_shift": True,
    }
    kalman.update_with_post_mortem(past_row, realized_return=0.03, attribution=attribution)
    w_after = kalman.w.copy()
    assert not np.allclose(w_before, w_after)


def test_full_recursive_engine_loop():
    engine = RecursiveSelfImprovingEngine()
    dummy_df = pd.DataFrame({
        "delta_real_yield_1w": np.random.normal(0, 0.03, 100),
        "dxy_return_1w": np.random.normal(0, 0.01, 100),
        "delta_breakeven_1w": np.random.normal(0, 0.02, 100),
        "gold_distance_20w": np.random.normal(0.01, 0.02, 100),
        "next_week_gold_return": np.random.normal(0.002, 0.02, 100),
    })
    engine.initialize(dummy_df)

    curr_features = {
        "delta_real_yield_1w": -0.05,
        "dxy_return_1w": 0.002,
        "delta_breakeven_1w": 0.001,
        "gold_distance_20w": 0.02,
        "vix": 16.0,
    }
    pred_res = engine.predict_upcoming_week(
        week="2026-09-18",
        current_features_dict=curr_features,
        current_gold_price=2600.0,
        baseline_corridor_high=2650.0,
        baseline_corridor_low=2550.0,
    )
    assert "recursive_bias_score" in pred_res
    assert -1.0 <= pred_res["recursive_bias_score"] <= 1.0
    assert pred_res["corridor_high"] > pred_res["corridor_low"]

    # Process realized outcome
    post_res = engine.process_prior_week_outcome(
        week="2026-09-18",
        features_dict=curr_features,
        realized_return=-0.01,
        actual_price=2580.0,
    )
    assert "archetype" in post_res
    assert "updated_weights" in post_res
