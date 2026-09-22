"""
Database migration & initialization utility.
Initializes schema tables in PostgreSQL or SQLite, and migrates existing Parquet datasets.
"""

from __future__ import annotations

import os
import sys
import datetime as dt
from pathlib import Path
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.db_session import engine, SessionLocal, Base
from database.models import (
    DataSource,
    MarketBar,
    MacroEvent,
    MacroObservation,
    WeeklyFeature,
    WeeklyTarget,
    Regime,
    ResearchRun,
    ModelResult,
    BacktestRun,
    BacktestMetric,
    DataQualityCheck,
)


def init_schema():
    """Initializes all tables defined in models."""
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("Schema initialized successfully.")


def seed_data_sources(db):
    """Registers official data source provenance records."""
    sources = [
        {
            "source_id": "FRED_RATES",
            "name": "Federal Reserve Economic Data (St. Louis Fed)",
            "source_url": "https://fred.stlouisfed.org",
            "frequency": "daily/monthly",
            "timezone": "America/New_York",
            "dataset_version": "v1.0",
        },
        {
            "source_id": "YAHOO_MARKET",
            "name": "Yahoo Finance (COMEX, FX, Equities, Energy)",
            "source_url": "https://finance.yahoo.com",
            "frequency": "1m/5m/1h/1d",
            "timezone": "UTC",
            "dataset_version": "v1.0",
        },
        {
            "source_id": "CFTC_COT",
            "name": "CFTC Commitments of Traders (Disaggregated & Legacy)",
            "source_url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
            "frequency": "weekly (Tuesday obs, Friday pub)",
            "timezone": "America/New_York",
            "dataset_version": "v1.0",
        },
        {
            "source_id": "BLS_BEA_EVENTS",
            "name": "BLS / BEA / Federal Reserve Official Macro Releases",
            "source_url": "https://www.bls.gov / https://www.bea.gov",
            "frequency": "monthly/FOMC schedule",
            "timezone": "America/New_York",
            "dataset_version": "v1.0",
        },
    ]

    for s in sources:
        existing = db.query(DataSource).filter_by(source_id=s["source_id"]).first()
        if not existing:
            db.add(DataSource(
                source_id=s["source_id"],
                name=s["name"],
                source_url=s["source_url"],
                frequency=s["frequency"],
                timezone=s["timezone"],
                dataset_version=s["dataset_version"],
                retrieved_at=dt.datetime.now(dt.timezone.utc),
            ))
    db.commit()
    print("Data source metadata registered.")


def migrate_existing_data():
    """Migrates cached parquet datasets to database tables."""
    db = SessionLocal()
    try:
        seed_data_sources(db)

        # 1. Macro Events
        events_pq = ROOT / "data" / "processed" / "events_master.parquet"
        if events_pq.exists():
            print(f"Migrating macro events from {events_pq}...")
            df_ev = pd.read_parquet(events_pq)
            count = 0
            for _, r in df_ev.iterrows():
                eid = str(r.get("event_id"))
                if not db.query(MacroEvent).filter_by(event_id=eid).first():
                    pub_time = pd.to_datetime(r.get("publication_timestamp") or r.get("timestamp"), utc=True)
                    db.add(MacroEvent(
                        event_id=eid,
                        event_type=str(r.get("event_type")),
                        country=str(r.get("country", "US")),
                        publication_time=pub_time,
                        observation_period=str(r.get("observation_period", "")),
                        previous_value=float(r["previous_value"]) if pd.notna(r.get("previous_value")) else None,
                        consensus_value=float(r["consensus_value"]) if pd.notna(r.get("consensus_value")) else None,
                        actual_value=float(r["actual_value"]) if pd.notna(r.get("actual_value")) else None,
                        surprise_absolute=float(r["surprise_absolute"]) if pd.notna(r.get("surprise_absolute")) else None,
                        surprise_percentage=float(r["surprise_percentage"]) if pd.notna(r.get("surprise_percentage")) else None,
                        surprise_zscore=float(r["surprise_zscore"]) if pd.notna(r.get("surprise_zscore")) else None,
                        surprise_bucket=str(r.get("surprise_bucket", "")),
                        importance=str(r.get("importance", "high")),
                        source=str(r.get("source", "BLS")),
                        vintage_mode=str(r.get("vintage_mode", "REAL_TIME_VINTAGE")),
                        initial_release=float(r["initial_release"]) if pd.notna(r.get("initial_release")) else None,
                        revision=float(r.get("revision", 0.0)) if pd.notna(r.get("revision")) else 0.0,
                        is_synthetic=bool(r.get("is_synthetic", False)),
                    ))
                    count += 1
            db.commit()
            print(f"Migrated {count} macro events.")

        # 2. Weekly Features & Targets
        weekly_pq = ROOT / "data" / "weekly" / "gold_weekly_master.parquet"
        if weekly_pq.exists():
            print(f"Migrating weekly master from {weekly_pq}...")
            df_wk = pd.read_parquet(weekly_pq)
            wcount = 0
            for _, r in df_wk.iterrows():
                week_id = str(r["week_ending"])
                if not db.query(WeeklyFeature).filter_by(week_ending=week_id).first():
                    pred_ts = pd.to_datetime(r.get("prediction_timestamp", week_id + " 21:00:00"), utc=True)
                    close_val = float(r.get("close", 0.0))
                    
                    feat = WeeklyFeature(
                        week_ending=week_id,
                        prediction_timestamp=pred_ts,
                        gold_close=close_val,
                        gold_return_1w=float(r["weekly_return"]) if pd.notna(r.get("weekly_return")) else None,
                        gold_return_4w=float(r["gold_return_4w"]) if pd.notna(r.get("gold_return_4w")) else None,
                        dxy_close=float(r["dxy_close"]) if pd.notna(r.get("dxy_close")) else None,
                        dxy_return_1w=float(r["dxy_weekly_return"]) if pd.notna(r.get("dxy_weekly_return")) else None,
                        real_yield_10y=float(r["real_yield_10y"]) if pd.notna(r.get("real_yield_10y")) else None,
                        delta_real_yield_1w=float(r["real_yield_weekly_change"]) if pd.notna(r.get("real_yield_weekly_change")) else None,
                        vix_close=float(r["vix"]) if pd.notna(r.get("vix")) else None,
                        vix_change_1w=float(r["vix_weekly_change"]) if pd.notna(r.get("vix_weekly_change")) else None,
                        sp500_close=float(r["spx_close"]) if pd.notna(r.get("spx_close")) else None,
                        sp500_return_1w=float(r["spx_weekly_return"]) if pd.notna(r.get("spx_weekly_return")) else None,
                        wti_close=float(r["wti_close"]) if pd.notna(r.get("wti_close")) else None,
                        wti_return_1w=float(r["wti_weekly_return"]) if pd.notna(r.get("wti_weekly_return")) else None,
                        silver_close=float(r["silver_close"]) if pd.notna(r.get("silver_close")) else None,
                        cot_net_speculative=float(r["net_spec_position"]) if pd.notna(r.get("net_spec_position")) else None,
                        cot_percentile_3y=float(r["net_spec_percentile"]) if pd.notna(r.get("net_spec_percentile")) else None,
                        etf_weekly_flow_usd_m=float(r["etf_weekly_flow_usd_m"]) if pd.notna(r.get("etf_weekly_flow_usd_m")) else None,
                    )
                    db.add(feat)

                    # Target
                    fwd_ret = float(r["fwd_weekly_gold_return"]) if pd.notna(r.get("fwd_weekly_gold_return")) else None
                    tgt = WeeklyTarget(
                        week_ending=week_id,
                        next_week_gold_return=fwd_ret,
                        next_week_direction=1 if fwd_ret and fwd_ret > 0 else (-1 if fwd_ret and fwd_ret < 0 else 0),
                        target_p_up=1 if fwd_ret and fwd_ret > 0 else 0,
                        target_p_plus_1pct=1 if fwd_ret and fwd_ret > 0.01 else 0,
                        target_p_minus_1pct=1 if fwd_ret and fwd_ret < -0.01 else 0,
                        next_week_gold_volatility=float(r["weekly_volatility"]) if pd.notna(r.get("weekly_volatility")) else None,
                    )
                    db.add(tgt)
                    wcount += 1
            db.commit()
            print(f"Migrated {wcount} weekly records.")

    finally:
        db.close()


if __name__ == "__main__":
    init_schema()
    migrate_existing_data()
