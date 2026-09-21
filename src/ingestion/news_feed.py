"""
Live news / macro-event intelligence feed for Gold weekly decision support.

Pulls automatically from:
  1) Free RSS wires (no API key) -- primary path
  2) Optional Finnhub / NewsAPI / Alpha Vantage NEWS_SENTIMENT when keys exist

Does NOT place trades. Enriches the discretionary decision brief with
geopolitics, Fed speak, gold/macro headlines, and a risk-size suggestion.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GoldWeeklyAI/1.2; "
        "+https://github.com/local/gold-weekly-response-engine)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*",
}

# Free RSS sources -- no API key required
RSS_FEEDS = [
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "category": "macro",
    },
    {
        "name": "Reuters World",
        "url": "https://feeds.reuters.com/Reuters/worldNews",
        "category": "geopolitics",
    },
    {
        "name": "CNBC Top News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "category": "macro",
    },
    {
        "name": "CNBC Economy",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
        "category": "macro",
    },
    {
        "name": "Federal Reserve Press",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "category": "central_bank",
    },
    {
        "name": "Yahoo Finance Markets",
        "url": "https://finance.yahoo.com/news/rssindex",
        "category": "markets",
    },
    {
        "name": "Kitco Gold News",
        "url": "https://www.kitco.com/news/rss/",
        "category": "gold",
    },
]

GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "precious metal", "comex", "gld",
    "fed", "fomc", "powell", "rate cut", "rate hike", "interest rate",
    "treasury", "yield", "tips", "real yield", "dollar", "dxy",
    "inflation", "cpi", "pce", "payroll", "nfp", "jobs",
    "geopolit", "war", "sanction", "tariff", "china", "middle east",
    "safe haven", "risk-off", "risk off", "vix", "recession",
    "ecb", "boj", "central bank", "hawkish", "dovish",
]

CATEGORY_RULES = [
    ("central_bank", ["fed", "fomc", "powell", "ecb", "boj", "central bank", "rate cut", "rate hike", "hawkish", "dovish"]),
    ("geopolitics", ["war", "sanction", "tariff", "geopolit", "middle east", "israel", "ukraine", "china", "taiwan"]),
    ("macro", ["cpi", "pce", "payroll", "nfp", "inflation", "gdp", "jobs", "unemployment", "recession"]),
    ("positioning", ["cot", "positioning", "speculative", "etf flow", "gld", "iau", "bullion bank"]),
    ("gold", ["gold", "xau", "bullion", "precious metal", "comex"]),
    ("dollar_yields", ["dollar", "dxy", "yield", "treasury", "tips", "real yield"]),
]


class NewsFeedIngestor:
    """Fetches, filters, caches, and summarizes gold-relevant live news."""

    def __init__(self, data_dir: str = "data/news", lookback_hours: int = 168):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lookback_hours = lookback_hours
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "").strip()
        self.newsapi_key = os.getenv("NEWS_API_KEY", "").strip()
        self.alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

    def fetch_all(self, force_refresh: bool = True, max_items: int = 40) -> pd.DataFrame:
        """Pull RSS + optional APIs, dedupe, filter to gold/macro relevance."""
        cache = self.data_dir / "latest_news.parquet"
        if not force_refresh and cache.exists():
            try:
                cached = pd.read_parquet(cache)
                if not cached.empty:
                    return cached.head(max_items)
            except Exception:
                pass

        rows: List[Dict[str, Any]] = []
        source_status: Dict[str, str] = {}

        for feed in RSS_FEEDS:
            items, status = self._fetch_rss(feed["url"], feed["name"], feed["category"])
            source_status[feed["name"]] = status
            rows.extend(items)

        if self.finnhub_key:
            items, status = self._fetch_finnhub()
            source_status["Finnhub"] = status
            rows.extend(items)

        if self.newsapi_key:
            items, status = self._fetch_newsapi()
            source_status["NewsAPI"] = status
            rows.extend(items)

        if self.alpha_key:
            items, status = self._fetch_alpha_vantage()
            source_status["AlphaVantage"] = status
            rows.extend(items)

        df = self._normalize(rows)
        df = self._filter_relevant(df)
        df = self._dedupe(df)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        if "published_utc" in df.columns and not df.empty:
            df = df[df["published_utc"] >= cutoff].copy()
        df = df.sort_values("published_utc", ascending=False).head(max_items).reset_index(drop=True)

        meta = {
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "item_count": int(len(df)),
            "source_status": source_status,
            "lookback_hours": self.lookback_hours,
            "optional_apis": {
                "finnhub": bool(self.finnhub_key),
                "newsapi": bool(self.newsapi_key),
                "alpha_vantage": bool(self.alpha_key),
            },
        }
        (self.data_dir / "latest_news_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if not df.empty:
            df.to_parquet(cache, index=False)
            df.to_csv(self.data_dir / "latest_news.csv", index=False)
        else:
            # Persist empty schema for downstream consumers
            empty = pd.DataFrame(
                columns=["id", "title", "summary", "url", "source", "category",
                         "published_utc", "relevance_score", "tone"]
            )
            empty.to_parquet(cache, index=False)
            empty.to_csv(self.data_dir / "latest_news.csv", index=False)

        return df

    def build_intelligence(
        self,
        force_refresh: bool = True,
        max_items: int = 40,
        confidence_tier: str = "MODERATE",
        no_trade: bool = False,
    ) -> Dict[str, Any]:
        """Structured news package for the weekly decision brief."""
        df = self.fetch_all(force_refresh=force_refresh, max_items=max_items)
        meta_path = self.data_dir / "latest_news_meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        headlines: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            item = {
                "title": str(row["title"]),
                "source": str(row["source"]),
                "category": str(row["category"]),
                "published_utc": row["published_utc"].isoformat() if pd.notna(row["published_utc"]) else "",
                "url": str(row.get("url", "")),
                "tone": str(row.get("tone", "neutral")),
                "relevance_score": float(row.get("relevance_score", 0)),
            }
            headlines.append(item)
            by_cat.setdefault(item["category"], []).append(item)

        risk_flags = self._risk_flags(df)
        suggested_size = self._suggest_size(confidence_tier, no_trade, risk_flags)
        narrative = self._narrative(by_cat, risk_flags)

        return {
            "fetched_at_utc": meta.get("fetched_at_utc", datetime.now(timezone.utc).isoformat()),
            "item_count": int(len(df)),
            "source_status": meta.get("source_status", {}),
            "optional_apis_enabled": meta.get("optional_apis", {}),
            "categories": {k: len(v) for k, v in by_cat.items()},
            "risk_flags": risk_flags,
            "suggested_position_size": suggested_size,
            "narrative_summary": narrative,
            "top_headlines": headlines[:15],
            "by_category": {k: v[:5] for k, v in by_cat.items()},
            "manual_input_required": False,
            "note": (
                "News auto-fetched from live feeds. You still confirm FOLLOW/FADE/PASS; "
                "position size below is a model suggestion only."
            ),
        }

    # ------------------------------------------------------------------ #
    # Fetchers
    # ------------------------------------------------------------------ #
    def _fetch_rss(self, url: str, source: str, default_cat: str) -> tuple[List[Dict[str, Any]], str]:
        try:
            resp = self.session.get(url, timeout=12)
            if resp.status_code != 200:
                return [], f"HTTP_{resp.status_code}"
            root = ET.fromstring(resp.content)
            items: List[Dict[str, Any]] = []
            # RSS 2.0
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                if not title:
                    continue
                desc = (item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = item.findtext("pubDate") or item.findtext("published") or ""
                items.append(self._row(title, desc, link, source, default_cat, pub))
            # Atom
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//a:entry", ns):
                title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
                if not title:
                    continue
                summary = (entry.findtext("a:summary", default="", namespaces=ns)
                           or entry.findtext("a:content", default="", namespaces=ns) or "").strip()
                link_el = entry.find("a:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                pub = entry.findtext("a:updated", default="", namespaces=ns) or entry.findtext("a:published", default="", namespaces=ns) or ""
                items.append(self._row(title, summary, link, source, default_cat, pub))
            return items, f"OK:{len(items)}"
        except Exception as exc:
            return [], f"ERROR:{type(exc).__name__}"

    def _fetch_finnhub(self) -> tuple[List[Dict[str, Any]], str]:
        try:
            url = "https://finnhub.io/api/v1/news"
            params = {"category": "general", "token": self.finnhub_key}
            resp = self.session.get(url, params=params, timeout=12)
            if resp.status_code != 200:
                return [], f"HTTP_{resp.status_code}"
            data = resp.json()
            items = []
            for art in data[:50]:
                title = str(art.get("headline") or "")
                if not title:
                    continue
                pub = datetime.fromtimestamp(int(art.get("datetime", 0)), tz=timezone.utc).isoformat()
                items.append(self._row(
                    title,
                    str(art.get("summary") or ""),
                    str(art.get("url") or ""),
                    f"Finnhub/{art.get('source', 'wire')}",
                    "markets",
                    pub,
                ))
            return items, f"OK:{len(items)}"
        except Exception as exc:
            return [], f"ERROR:{type(exc).__name__}"

    def _fetch_newsapi(self) -> tuple[List[Dict[str, Any]], str]:
        try:
            q = "(gold OR Fed OR FOMC OR inflation OR CPI OR yields OR geopolitics OR dollar)"
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": q,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 40,
                "apiKey": self.newsapi_key,
            }
            resp = self.session.get(url, params=params, timeout=12)
            if resp.status_code != 200:
                return [], f"HTTP_{resp.status_code}"
            arts = resp.json().get("articles", [])
            items = []
            for art in arts:
                title = str(art.get("title") or "")
                if not title or title == "[Removed]":
                    continue
                items.append(self._row(
                    title,
                    str(art.get("description") or ""),
                    str(art.get("url") or ""),
                    f"NewsAPI/{(art.get('source') or {}).get('name', 'wire')}",
                    "macro",
                    str(art.get("publishedAt") or ""),
                ))
            return items, f"OK:{len(items)}"
        except Exception as exc:
            return [], f"ERROR:{type(exc).__name__}"

    def _fetch_alpha_vantage(self) -> tuple[List[Dict[str, Any]], str]:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": "GLD,IAU",
                "topics": "economy_monetary,financial_markets",
                "limit": 40,
                "apikey": self.alpha_key,
            }
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                return [], f"HTTP_{resp.status_code}"
            feed = resp.json().get("feed", [])
            items = []
            for art in feed:
                title = str(art.get("title") or "")
                if not title:
                    continue
                # Alpha timestamps: 20240918T143000
                raw_ts = str(art.get("time_published") or "")
                pub = raw_ts
                try:
                    pub = datetime.strptime(raw_ts, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    pass
                tone = "neutral"
                try:
                    score = float(art.get("overall_sentiment_score", 0) or 0)
                    tone = "bullish" if score > 0.15 else "bearish" if score < -0.15 else "neutral"
                except (TypeError, ValueError):
                    pass
                row = self._row(
                    title,
                    str(art.get("summary") or ""),
                    str(art.get("url") or ""),
                    f"AlphaVantage/{art.get('source', 'wire')}",
                    "gold",
                    pub,
                )
                row["tone"] = tone
                items.append(row)
            return items, f"OK:{len(items)}"
        except Exception as exc:
            return [], f"ERROR:{type(exc).__name__}"

    # ------------------------------------------------------------------ #
    # Normalize / filter
    # ------------------------------------------------------------------ #
    def _row(self, title: str, summary: str, url: str, source: str, category: str, published: str) -> Dict[str, Any]:
        clean_summary = re.sub(r"<[^>]+>", " ", summary or "")
        clean_summary = re.sub(r"\s+", " ", clean_summary).strip()[:500]
        pub_dt = self._parse_time(published)
        text = f"{title} {clean_summary}".lower()
        cat = self._classify(text, category)
        score = self._relevance(text)
        tone = self._tone(text)
        uid = hashlib.sha1(f"{title}|{source}".encode("utf-8")).hexdigest()[:16]
        return {
            "id": uid,
            "title": title.strip(),
            "summary": clean_summary,
            "url": url,
            "source": source,
            "category": cat,
            "published_utc": pub_dt,
            "relevance_score": score,
            "tone": tone,
        }

    def _parse_time(self, value: str) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
        try:
            dt = pd.to_datetime(value, utc=True).to_pydatetime()
            return dt
        except Exception:
            return datetime.now(timezone.utc)

    def _classify(self, text: str, default: str) -> str:
        for cat, keys in CATEGORY_RULES:
            if any(k in text for k in keys):
                return cat
        return default

    def _relevance(self, text: str) -> float:
        hits = sum(1 for k in GOLD_KEYWORDS if k in text)
        return float(min(1.0, hits / 4.0))

    def _tone(self, text: str) -> str:
        bull = ["rally", "surge", "soar", "bullish", "safe haven", "rate cut", "dovish", "weak dollar"]
        bear = ["plunge", "selloff", "bearish", "rate hike", "hawkish", "strong dollar", "yields rise"]
        b = sum(1 for w in bull if w in text)
        s = sum(1 for w in bear if w in text)
        if b > s:
            return "bullish_for_gold"
        if s > b:
            return "bearish_for_gold"
        return "neutral"

    def _normalize(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(
                columns=["id", "title", "summary", "url", "source", "category",
                         "published_utc", "relevance_score", "tone"]
            )
        return pd.DataFrame(rows)

    def _filter_relevant(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        # Keep gold/macro-relevant items; allow central bank / geopolitics even if score low
        mask = (
            (df["relevance_score"] >= 0.25)
            | (df["category"].isin(["gold", "central_bank", "geopolitics", "dollar_yields", "macro", "positioning"]))
        )
        return df.loc[mask].copy()

    def _dedupe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        df["title_key"] = df["title"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str[:80]
        return df.drop_duplicates(subset=["title_key"], keep="first").drop(columns=["title_key"])

    def _risk_flags(self, df: pd.DataFrame) -> List[str]:
        flags: List[str] = []
        if df.empty:
            flags.append("NO_RELEVANT_HEADLINES -- news feed empty or offline")
            return flags
        text = " ".join((df["title"] + " " + df["summary"]).astype(str).tolist()).lower()
        if any(k in text for k in ["war", "missile", "invasion", "escalation"]):
            flags.append("GEOPOLITICAL_ESCALATION")
        if any(k in text for k in ["fomc", "powell", "rate decision", "fed chair"]):
            flags.append("CENTRAL_BANK_SPEAK_ACTIVE")
        if any(k in text for k in ["cpi", "pce", "payroll", "nfp", "jobs report"]):
            flags.append("HIGH_IMPACT_MACRO_PRINT")
        if any(k in text for k in ["sanction", "tariff", "trade war"]):
            flags.append("TRADE_POLICY_SHOCK")
        if (df["tone"] == "bearish_for_gold").sum() >= 5 and (df["tone"] == "bullish_for_gold").sum() <= 1:
            flags.append("HEADLINE_TONE_SKEWED_BEARISH")
        if (df["tone"] == "bullish_for_gold").sum() >= 5 and (df["tone"] == "bearish_for_gold").sum() <= 1:
            flags.append("HEADLINE_TONE_SKEWED_BULLISH")
        if not flags:
            flags.append("NO_EXTREME_NEWS_FLAGS")
        return flags

    def _suggest_size(self, confidence_tier: str, no_trade: bool, risk_flags: List[str]) -> Dict[str, Any]:
        if no_trade:
            return {
                "label": "STAND ASIDE",
                "multiplier": 0.0,
                "rationale": "Circuit breaker / no-trade status active.",
            }
        severe = {"GEOPOLITICAL_ESCALATION", "TRADE_POLICY_SHOCK", "HIGH_IMPACT_MACRO_PRINT"}
        if severe.intersection(risk_flags):
            return {
                "label": "REDUCED RISK (0.5x)",
                "multiplier": 0.5,
                "rationale": "Elevated news-event risk flags present -- halve notional.",
            }
        tier = (confidence_tier or "MODERATE").upper()
        if tier == "HIGH":
            return {"label": "STANDARD (1.0x)", "multiplier": 1.0, "rationale": "High confidence, no extreme news flags."}
        if tier == "LOW":
            return {"label": "REDUCED RISK (0.5x)", "multiplier": 0.5, "rationale": "Low confidence -- reduced size."}
        return {"label": "STANDARD (1.0x)", "multiplier": 1.0, "rationale": "Moderate confidence default."}

    def _narrative(self, by_cat: Dict[str, List[Dict[str, Any]]], risk_flags: List[str]) -> str:
        parts = []
        if by_cat.get("central_bank"):
            parts.append(f"Central-bank wire: {by_cat['central_bank'][0]['title']}")
        if by_cat.get("geopolitics"):
            parts.append(f"Geopolitics: {by_cat['geopolitics'][0]['title']}")
        if by_cat.get("gold"):
            parts.append(f"Gold tape: {by_cat['gold'][0]['title']}")
        if by_cat.get("macro"):
            parts.append(f"Macro: {by_cat['macro'][0]['title']}")
        if by_cat.get("positioning"):
            parts.append(f"Positioning: {by_cat['positioning'][0]['title']}")
        if not parts:
            return "No high-relevance gold/macro headlines in the lookback window."
        flag_txt = ", ".join(risk_flags)
        return " | ".join(parts) + f" || Flags: {flag_txt}"


def fetch_live_news_intelligence(**kwargs: Any) -> Dict[str, Any]:
    """Convenience entry point used by the decision brief CLI."""
    return NewsFeedIngestor().build_intelligence(**kwargs)
