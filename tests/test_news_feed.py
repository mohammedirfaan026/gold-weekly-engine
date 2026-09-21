"""Tests for live news feed ingestion and risk-size suggestions."""

from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from src.ingestion.news_feed import NewsFeedIngestor


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test</title>
    <item>
      <title>Fed Chair Powell signals possible rate cut as inflation cools</title>
      <description>FOMC commentary moves Treasury yields and gold.</description>
      <link>https://example.com/fed</link>
      <pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Geopolitical tensions rise in Middle East after escalation</title>
      <description>Safe-haven demand for gold increases.</description>
      <link>https://example.com/geo</link>
      <pubDate>Mon, 21 Sep 2026 11:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Celebrity opens new restaurant in Miami</title>
      <description>Unrelated lifestyle story.</description>
      <link>https://example.com/food</link>
      <pubDate>Mon, 21 Sep 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


class _FakeResp:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status


def test_rss_relevance_and_flags(tmp_path):
    ing = NewsFeedIngestor(data_dir=str(tmp_path), lookback_hours=720)

    def fake_get(url, timeout=12, params=None):
        return _FakeResp(SAMPLE_RSS)

    with patch.object(ing.session, "get", side_effect=fake_get):
        # Force only one feed path by patching RSS_FEEDS usage via fetch_all internals
        items, status = ing._fetch_rss("https://example.com/rss", "TestWire", "macro")
        assert status.startswith("OK")
        assert len(items) == 3

    df = ing._normalize(items)
    df = ing._filter_relevant(df)
    # Celebrity item should drop; Fed + geopolitics remain
    assert len(df) >= 2
    titles = " ".join(df["title"].tolist()).lower()
    assert "powell" in titles or "fed" in titles
    assert "middle east" in titles or "geopolit" in titles

    flags = ing._risk_flags(df)
    assert "CENTRAL_BANK_SPEAK_ACTIVE" in flags or "GEOPOLITICAL_ESCALATION" in flags


def test_suggest_size_reduces_on_risk():
    ing = NewsFeedIngestor(data_dir="data/news")
    size = ing._suggest_size("HIGH", no_trade=False, risk_flags=["GEOPOLITICAL_ESCALATION"])
    assert size["multiplier"] == 0.5
    aside = ing._suggest_size("HIGH", no_trade=True, risk_flags=[])
    assert aside["multiplier"] == 0.0


def test_classify_central_bank():
    ing = NewsFeedIngestor()
    assert ing._classify("powell speaks at fomc press conference", "markets") == "central_bank"
    assert ing._classify("gold bullion etf inflows rise", "markets") in {"gold", "positioning"}
