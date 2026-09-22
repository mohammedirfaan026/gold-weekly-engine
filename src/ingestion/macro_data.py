"""
Macroeconomic series ingestion module.
Fetches real yields (TIPS), nominal yields, credit spreads (HY OAS), and macroeconomic levels from FRED.
Applies point-in-time publication timestamps.
"""

from __future__ import annotations
import os
import io
import datetime as dt
from typing import Optional, Dict, List
import numpy as np
import pandas as pd
import requests

from src.timestamps.calendar_utils import to_utc_time


class MacroDataIngestor:
    """
    Ingests official macroeconomic and rates series from FRED.
    Enforces strict publication availability timestamps.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    SERIES_CONFIG = {
        "real_yield_10y": {"fred_id": "DFII10", "freq": "daily", "lag_days": 1},
        "real_yield_5y": {"fred_id": "DFII5", "freq": "daily", "lag_days": 1},
        "treasury_2y": {"fred_id": "DGS2", "freq": "daily", "lag_days": 1},
        "treasury_5y": {"fred_id": "DGS5", "freq": "daily", "lag_days": 1},
        "treasury_10y": {"fred_id": "DGS10", "freq": "daily", "lag_days": 1},
        "treasury_30y": {"fred_id": "DGS30", "freq": "daily", "lag_days": 1},
        "hy_oas": {"fred_id": "BAMLH0A0HYM2", "freq": "daily", "lag_days": 1},
        "cpi": {"fred_id": "CPIAUCSL", "freq": "monthly", "lag_days": 15},
        "core_cpi": {"fred_id": "CPILFESL", "freq": "monthly", "lag_days": 15},
        "pce": {"fred_id": "PCEPI", "freq": "monthly", "lag_days": 30},
        "core_pce": {"fred_id": "PCEPILFE", "freq": "monthly", "lag_days": 30},
        "nonfarm_payrolls": {"fred_id": "PAYEMS", "freq": "monthly", "lag_days": 7},
        "unemployment_rate": {"fred_id": "UNRATE", "freq": "monthly", "lag_days": 7},
        "jobless_claims": {"fred_id": "ICSA", "freq": "weekly", "lag_days": 5},
    }

    def __init__(self, data_dir: str = "data/macro"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_fred_series(self, fred_id: str) -> Optional[pd.DataFrame]:
        """
        Downloads public CSV series directly from FRED.
        """
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fred_id}"
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=12)
            if resp.status_code != 200:
                return None
            df = pd.read_csv(io.StringIO(resp.text))
            if df.empty or len(df.columns) < 2:
                return None
            df.columns = ["date", "value"]
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"]).reset_index(drop=True)
            df["date"] = pd.to_datetime(df["date"])
            return df
        except Exception:
            return None

    def get_series(
        self,
        series_name: str,
        start_year: int = 2010,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Retrieves macro series with observation and publication timestamps.
        """
        cache_file = os.path.join(self.data_dir, f"{series_name}.parquet")
        if os.path.exists(cache_file) and not force_refresh:
            try:
                df = pd.read_parquet(cache_file)
                if not df.empty:
                    return df
            except Exception:
                pass

        cfg = self.SERIES_CONFIG.get(series_name, {"fred_id": series_name, "freq": "daily", "lag_days": 1})
        fred_id = cfg["fred_id"]
        lag_days = cfg.get("lag_days", 1)

        raw_df = self.fetch_fred_series(fred_id)
        if raw_df is None or raw_df.empty:
            # If network/FRED is unavailable, verify if cache exists; otherwise raise clear error
            if os.path.exists(cache_file):
                return pd.read_parquet(cache_file)
            raise RuntimeError(
                f"FRED macro series '{series_name}' (ID: {fred_id}) could not be retrieved and no cache exists. "
                "Silent synthetic data generation is strictly disabled for research integrity."
            )

        # Build point-in-time observation and publication timestamps
        raw_df["observation_time"] = pd.to_datetime(raw_df["date"]).dt.tz_localize("UTC")
        raw_df["publication_time"] = raw_df["observation_time"] + pd.Timedelta(days=lag_days, hours=13)  # ~08:30-09:00 ET
        raw_df["source"] = "FRED"
        raw_df["source_series_id"] = fred_id
        raw_df["is_imputed"] = False
        raw_df["retrieved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

        # Filter by start_year
        start_ts = pd.Timestamp(f"{start_year}-01-01", tz="UTC")
        result_df = raw_df[raw_df["observation_time"] >= start_ts].copy()
        result_df = result_df.sort_values(by="observation_time").reset_index(drop=True)

        result_df.to_parquet(cache_file, index=False)
        return result_df

