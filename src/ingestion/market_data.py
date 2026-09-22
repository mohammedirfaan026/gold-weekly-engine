"""
Market data ingestion module.
Fetches, caches, and prepares multi-asset price and volume history (2010-present).
Covers Gold (Spot & Futures), DXY, Treasuries, TIPS Real Yields, Equities, Commodities, VIX, and Credit.
"""

from __future__ import annotations
import os
import json
import time
import datetime as dt
from typing import Optional, Dict, List, Union
import numpy as np
import pandas as pd
import requests

from src.timestamps.calendar_utils import to_utc_time
from src.normalization.cleaner import DataCleaner


class MarketDataIngestor:
    """
    Ingests and normalizes high-resolution and daily/weekly financial market data.
    Uses institutional-grade Yahoo Finance API with direct query headers, caching, and fallback simulation.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    TICKER_MAP = {
        "gold_spot": "XAUUSD=X",
        "gold_futures": "GC=F",
        "silver": "SI=F",
        "copper": "HG=F",
        "wti": "CL=F",
        "brent": "BZ=F",
        "dxy": "DX-Y.NYB",
        "dxy_proxy": "UUP",
        "eurusd": "EURUSD=X",
        "usdjpy": "USDJPY=X",
        "spx": "^GSPC",
        "ndx": "^IXIC",
        "rut": "^RUT",
        "vix": "^VIX",
        "treasury_10y": "^TNX",
        "treasury_5y": "^FVX",
        "treasury_30y": "^TYX",
        "gld": "GLD",
        "iau": "IAU",
        "hyg": "HYG",
        "lqd": "LQD",
    }

    def __init__(self, data_dir: str = "data/market"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_yahoo_chart(
        self,
        ticker: str,
        interval: str = "1d",
        range_str: str = "max",
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Directly queries Yahoo Finance Chart API v8.
        Supports intervals: '1m', '5m', '15m', '1h', '1d', '1wk'.
        """
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }
        if start_ts and end_ts:
            params["period1"] = int(start_ts)
            params["period2"] = int(end_ts)
        else:
            params["range"] = range_str

        try:
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=15)
            if resp.status_code != 200:
                return None
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if not result:
                return None
            res = result[0]
            timestamps = res.get("timestamp", [])
            indicators = res.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps:
                return None

            df = pd.DataFrame({
                "timestamp": pd.to_datetime(timestamps, unit="s", utc=True),
                "open": indicators.get("open", []),
                "high": indicators.get("high", []),
                "low": indicators.get("low", []),
                "close": indicators.get("close", []),
                "volume": indicators.get("volume", [0] * len(timestamps)),
            })
            df = df.dropna(subset=["close"]).reset_index(drop=True)
            df = DataCleaner.validate_ohlc(df)
            return df
        except Exception:
            return None

    def get_market_series(
        self,
        symbol_key: str,
        interval: str = "1d",
        start_year: int = 2010,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Fetches or loads from cache a market asset's OHLCV series.
        """
        ticker = self.TICKER_MAP.get(symbol_key, symbol_key)
        clean_name = symbol_key.replace("^", "").replace("=", "_").replace("-", "_")
        cache_file = os.path.join(self.data_dir, f"{clean_name}_{interval}.parquet")

        if os.path.exists(cache_file) and not force_refresh:
            try:
                df = pd.read_parquet(cache_file)
                if not df.empty:
                    return df
            except Exception:
                pass

        # Fetch from Yahoo Finance
        start_dt = dt.datetime(start_year, 1, 1, tzinfo=dt.timezone.utc)
        end_dt = dt.datetime.now(dt.timezone.utc)
        df = self.fetch_yahoo_chart(
            ticker,
            interval=interval,
            start_ts=int(start_dt.timestamp()),
            end_ts=int(end_dt.timestamp()),
        )

        if df is None or df.empty:
            if os.path.exists(cache_file):
                return pd.read_parquet(cache_file)
            raise RuntimeError(
                f"Market series '{symbol_key}' (ticker: {ticker}) could not be fetched from Yahoo Finance and no cache exists. "
                "Silent synthetic data generation is strictly disabled for research integrity."
            )

        df["source"] = "YahooFinance"
        df["symbol_key"] = symbol_key
        df["ticker"] = ticker
        df["is_imputed"] = False
        df["retrieved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

        df.to_parquet(cache_file, index=False)
        return df


    def resample_bars(self, df: pd.DataFrame, target_freq: str) -> pd.DataFrame:
        """
        Resamples OHLCV bars to higher timeframes (e.g. '15min', '1h', '4h', '1D', '1W-FRI').
        """
        df_copy = df.copy()
        df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"], utc=True)
        df_copy = df_copy.sort_values(by="timestamp").set_index("timestamp")

        resampled = df_copy.resample(target_freq).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna(subset=["close"]).reset_index()

        return DataCleaner.validate_ohlc(resampled)
