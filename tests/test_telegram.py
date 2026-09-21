"""Tests for Telegram brief formatting (no network)."""

from src.notify.telegram import TelegramNotifier


def test_format_brief_message_contains_stance():
    brief = {
        "identification": {"observation_week": "2026-09-18"},
        "current_market_state": {"gold_reference_price": 6250.0},
        "model_output": {
            "directional_stance": "Bullish bias -- confirmation required",
            "recursive_bias_score": 0.22,
            "recursive_expected_return_pct": 0.85,
            "confidence_calibration": {"tier": "MODERATE"},
        },
        "scenario_map": {
            "expected_corridor": {
                "lower_support_10pct": 6125.0,
                "upper_resistance_90pct": 6375.0,
            }
        },
        "no_trade_circuit_breaker": {"status_label": "TRADE PERMITTED"},
        "live_news_intelligence": {
            "risk_flags": ["CENTRAL_BANK_SPEAK_ACTIVE"],
            "suggested_position_size": {"label": "STANDARD (1.0x)"},
            "top_headlines": [{"category": "gold", "title": "Gold holds near highs"}],
        },
    }
    text = TelegramNotifier.format_brief_message(brief, dashboard_url="http://127.0.0.1:8787")
    assert "GOLD WEEKLY BRIEF" in text
    assert "Bullish bias" in text
    assert "FOLLOW / FADE / PASS" in text
    assert "Dashboard: http://127.0.0.1:8787" in text


def test_chunk_long_message():
    long = "\n".join([f"line {i}" for i in range(500)])
    parts = TelegramNotifier._chunk(long, 200)
    assert len(parts) > 1
    assert "".join(parts) == long
