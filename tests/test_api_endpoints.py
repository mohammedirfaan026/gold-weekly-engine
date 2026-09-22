"""
Integration tests for FastAPI endpoints.
Verifies all routes return valid status codes and Pydantic-compliant responses.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "healthy"
    assert data["database"] == "healthy"
    assert "latest_market_data" in data


def test_gold_current_endpoint():
    response = client.get("/api/gold/current")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "XAUUSD"
    assert "price" in data
    assert "factors" in data
    assert "current_macro_regime" in data


def test_gold_weekly_endpoint():
    response = client.get("/api/gold/weekly?timeframe=1Y")
    assert response.status_code == 200
    data = response.json()
    assert data["timeframe"] == "1Y"
    assert "series" in data
    assert len(data["series"]) > 0


def test_events_endpoint():
    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "event_type" in data[0]
    assert "surprise_zscore" in data[0]


def test_event_types_endpoint():
    response = client.get("/api/events/types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_regimes_current_endpoint():
    response = client.get("/api/regimes/current")
    assert response.status_code == 200
    data = response.json()
    assert "regimes" in data
    assert "composite_macro_state" in data


def test_research_performance_endpoint():
    response = client.get("/api/research/performance")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "model" in data[0]
    assert "directional_accuracy_pct" in data[0]


def test_conditional_query_endpoint():
    payload = {
        "event_filter": "cpi",
        "real_yield_regime": "falling",
        "gold_trend": "bullish",
    }
    response = client.post("/api/research/conditional", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "matched_count" in data
    assert "conditions" in data


def test_data_health_endpoint():
    response = client.get("/api/data-health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["PASS", "WARNING", "FAIL"]
    assert "checks" in data
    assert len(data["checks"]) > 0


def test_backtest_lifecycle():
    payload = {
        "strategy_name": "TestMacroTrend",
        "start_date": "2020-01-01",
        "end_date": "2024-01-01",
        "signal_type": "macro_regime",
        "threshold_entry": 0.0,
        "slippage_bps": 2.0,
        "commission_bps": 1.5,
        "initial_capital": 100000.0,
    }
    response = client.post("/api/backtests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    run_id = data["run_id"]

    # Check status
    st_res = client.get(f"/api/backtests/{run_id}/status")
    assert st_res.status_code == 200
    st_data = st_res.json()
    assert st_data["status"] in ["QUEUED", "RUNNING", "COMPLETED"]
