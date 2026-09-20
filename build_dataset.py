"""
Dataset construction pipeline script.
Builds the event-level research dataset and the weekly master research dataset.
Performs pre-event state reconstruction, regime classification, multi-window response analysis,
and relational database persistence.
Usage:
    python build_dataset.py
"""

import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.market_data import MarketDataIngestor
from src.ingestion.macro_data import MacroDataIngestor
from src.ingestion.cot_data import CotDataIngestor
from src.ingestion.etf_data import EtfDataIngestor
from src.ingestion.event_loader import EventLoader
from src.market_state.reconstructor import MarketStateReconstructor
from src.regime_engine.classifier import RegimeClassifier
from src.event_engine.window_analyzer import WindowAnalyzer
from src.weekly_engine.builder import WeeklyDatasetBuilder


def main():
    print("=== Building Gold Weekly Response Datasets ===")
    
    # 1. Load Raw Datasets
    print("\n[1/6] Loading cached market and macroeconomic data...")
    market_ingestor = MarketDataIngestor()
    macro_ingestor = MacroDataIngestor()
    cot_ingestor = CotDataIngestor()
    etf_ingestor = EtfDataIngestor()
    event_loader = EventLoader()

    gold_spot = market_ingestor.get_market_series("gold_spot")
    dxy = market_ingestor.get_market_series("dxy")
    spx = market_ingestor.get_market_series("spx")
    ndx = market_ingestor.get_market_series("ndx")
    vix = market_ingestor.get_market_series("vix")
    wti = market_ingestor.get_market_series("wti")
    silver = market_ingestor.get_market_series("silver")
    copper = market_ingestor.get_market_series("copper")

    ry = macro_ingestor.get_series("real_yield_10y")
    hy = macro_ingestor.get_series("hy_oas")
    cot = cot_ingestor.get_gold_cot_data()
    etf = etf_ingestor.get_etf_flows()
    events = event_loader.load_or_generate_events()

    # 2. Compute Market State Features
    print("\n[2/6] Computing rolling pre-event technical & macro features...")
    gold_feats = MarketStateReconstructor.compute_gold_features(gold_spot)
    macro_feats = MarketStateReconstructor.compute_macro_market_features(
        dxy_df=dxy, real_yield_df=ry, vix_df=vix, spx_df=spx,
        ndx_df=ndx, wti_df=wti, silver_df=silver, copper_df=copper, hy_oas_df=hy
    )

    # 3. Reconstruct Pre-Event State & Classify Regimes
    print("\n[3/6] Reconstructing instantaneous pre-event market state snapshots (point-in-time)...")
    events_reconstructed = MarketStateReconstructor.reconstruct_all_event_states(
        events_df=events,
        gold_features_df=gold_feats,
        macro_features_df=macro_feats,
        cot_df=cot,
        etf_df=etf,
    )
    events_classified = RegimeClassifier.classify_dataset_regimes(events_reconstructed)
    print(f"  [OK] Processed {len(events_classified)} events with full pre-event state & regimes.")

    # 4. Process Multi-Window Response Trajectories
    print("\n[4/6] Measuring multi-window responses (+1m to Next Friday Close, MFE, MAE, Speed, Reversals)...")
    events_master = WindowAnalyzer.process_all_events(events_classified, gold_spot)
    print(f"  [OK] Multi-window response metrics computed across all {len(events_master)} events.")

    # 5. Build Master Weekly Dataset
    print("\n[5/6] Building master Friday-to-Friday weekly research dataset...")
    weekly_master = WeeklyDatasetBuilder.build_weekly_dataset(
        gold_daily_df=gold_spot,
        macro_daily_df=macro_feats,
        events_df=events,
        cot_df=cot,
        etf_df=etf,
    )
    print(f"  [OK] Master weekly dataset built: {len(weekly_master)} discrete trading weeks.")

    # 6. Save Datasets (Parquet & SQLite)
    print("\n[6/6] Persisting analytical datasets to Parquet and SQLite...")
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/weekly", exist_ok=True)
    os.makedirs("database", exist_ok=True)

    events_parquet = "data/processed/events_master.parquet"
    weekly_parquet = "data/weekly/gold_weekly_master.parquet"
    db_path = "database/gold_research.db"

    events_master.to_parquet(events_parquet, index=False)
    weekly_master.to_parquet(weekly_parquet, index=False)
    print(f"  [OK] Saved events dataset: {events_parquet}")
    print(f"  [OK] Saved weekly dataset: {weekly_parquet}")

    # SQLite persistence
    conn = sqlite3.connect(db_path)
    # Convert timestamps to string for clean SQLite storage
    events_sql = events_master.copy()
    for col in events_sql.select_dtypes(include=["datetimetz", "datetime64[ns]"]).columns:
        events_sql[col] = events_sql[col].astype(str)
    events_sql.to_sql("events_master", conn, if_exists="replace", index=False)

    weekly_sql = weekly_master.copy()
    for col in weekly_sql.select_dtypes(include=["datetimetz", "datetime64[ns]"]).columns:
        weekly_sql[col] = weekly_sql[col].astype(str)
    weekly_sql.to_sql("weekly_master", conn, if_exists="replace", index=False)
    conn.close()
    print(f"  [OK] Persisted relational tables to SQLite: {db_path}")

    print("\n=== Dataset Construction Complete! ===")


if __name__ == "__main__":
    main()
