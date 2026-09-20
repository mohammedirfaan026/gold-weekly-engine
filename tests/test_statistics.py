"""Unit tests for statistical analysis, market state, and regime classification."""
import pytest
import numpy as np
import pandas as pd
from src.statistics.event_study import EventStudyEngine
from src.statistics.shock_analysis import MarketShockAnalyzer
from src.regime_engine.classifier import RegimeClassifier
from src.market_state.reconstructor import MarketStateReconstructor


def test_bootstrap_ci_and_summary():
    data = pd.Series(np.random.normal(0.01, 0.02, 100))
    summary = EventStudyEngine.compute_summary_statistics(data, n_boot=500)
    
    assert summary["n"] == 100
    assert summary["ci_low"] < summary["ci_high"]
    assert 0.0 <= summary["positive_rate"] <= 100.0


def test_market_shock_identification():
    dates = pd.date_range("2020-01-01", periods=100, freq="W-FRI", tz="UTC")
    ret = np.random.normal(0.0, 0.01, 100)
    # Inject a 4-sigma shock at index 50
    ret[50] = 0.08
    
    df = pd.DataFrame({
        "week_ending": dates,
        "weekly_return": ret,
        "fwd_weekly_gold_return": pd.Series(ret).shift(-1),
    })

    shocks_df = MarketShockAnalyzer.analyze_shocks(df)
    assert not shocks_df.empty
    gold_shock = shocks_df[shocks_df["asset"] == "gold"]
    assert not gold_shock.empty


def test_regime_classification():
    series = pd.Series(np.linspace(-0.10, 0.10, 100))
    regimes = RegimeClassifier.classify_by_percentile(series, labels=("falling", "neutral", "rising"))
    
    assert (regimes == "falling").any()
    assert (regimes == "rising").any()
    assert (regimes == "neutral").any()


def test_gold_technical_features():
    dates = pd.date_range("2020-01-01", periods=120, freq="B", tz="UTC")
    prices = 1800.0 + np.cumsum(np.random.normal(0.5, 5.0, 120))
    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 3.0,
        "low": prices - 3.0,
        "close": prices,
    })

    features = MarketStateReconstructor.compute_gold_features(df)
    assert "gold_return_1d" in features.columns
    assert "gold_distance_20w_ma" in features.columns
    assert "gold_volatility" in features.columns
    assert "gold_ATR" in features.columns
    assert "gold_drawdown" in features.columns
    assert "gold_trend" in features.columns
