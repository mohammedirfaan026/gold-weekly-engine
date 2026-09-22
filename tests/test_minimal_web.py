"""
Tests for the minimal web interface and prediction summary helper.
"""

import pytest
from web.app import create_app
from web.prediction_helper import get_latest_prediction_summary, refresh_prediction


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_prediction_helper_structure():
    data = get_latest_prediction_summary()
    assert "direction" in data
    assert data["direction"] in ("BULLISH", "BEARISH", "NEUTRAL")
    assert "bias_score" in data
    assert "expected_return_pct" in data
    assert "price" in data
    assert "week" in data
    assert "reason_narrative" in data
    assert len(data["reason_narrative"]) > 20
    assert "drivers" in data
    assert len(data["drivers"]) >= 3


def test_home_page_renders_minimal_interface(client):
    res = client.get("/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "GOLD" in html
    assert "Reason for Bias" in html
    assert "Macro Transmission Drivers" in html
    assert "Refresh" in html


def test_api_prediction_endpoint(client):
    res = client.get("/api/prediction", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert res.status_code == 200
    data = res.get_json()
    assert "direction" in data
    assert "reason_narrative" in data
    assert "drivers" in data


def test_api_refresh_endpoint(client):
    res = client.post("/api/refresh", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert res.status_code == 200
    data = res.get_json()
    assert "direction" in data
