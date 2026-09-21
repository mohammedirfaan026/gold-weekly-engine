"""
Data ingestion pipeline script.
Fetches, normalizes, and caches all market, macro, COT, ETF, and event data (2010-present).
Usage:
    python ingest_data.py [--start-year 2010] [--force-refresh]
"""

import argparse
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.market_data import MarketDataIngestor
from src.ingestion.macro_data import MacroDataIngestor
from src.ingestion.cot_data import CotDataIngestor
from src.ingestion.etf_data import EtfDataIngestor
from src.ingestion.event_loader import EventLoader
from src.ingestion.news_feed import NewsFeedIngestor


def main():
    parser = argparse.ArgumentParser(description="Ingest all market, macro, COT, ETF, event, and news data.")
    parser.add_argument("--start-year", type=int, default=2010, help="Starting historical year (default: 2010)")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh data from remote sources")
    args = parser.parse_args()

    print(f"=== Starting Gold Weekly Response Engine Ingestion (Start Year: {args.start_year}) ===")

    # 1. Market Data
    print("\n[1/6] Ingesting multi-asset market data (Gold, DXY, Equities, VIX, Commodities)...")
    market_ingestor = MarketDataIngestor()
    assets = [
        "gold_spot", "gold_futures", "dxy", "eurusd", "usdjpy",
        "spx", "ndx", "rut", "vix", "treasury_10y",
        "silver", "copper", "wti", "brent", "gld", "iau", "hyg"
    ]
    for asset in assets:
        df = market_ingestor.get_market_series(asset, interval="1d", start_year=args.start_year, force_refresh=args.force_refresh)
        print(f"  [OK] {asset:<16}: {len(df):>5} rows ({df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')})")

    # 2. Macro Rates & Spreads
    print("\n[2/6] Ingesting FRED macroeconomic series (Real Yields, Treasuries, HY OAS)...")
    macro_ingestor = MacroDataIngestor()
    macro_series = ["real_yield_10y", "real_yield_5y", "treasury_2y", "treasury_10y", "hy_oas"]
    for s in macro_series:
        df = macro_ingestor.get_series(s, start_year=args.start_year, force_refresh=args.force_refresh)
        print(f"  [OK] {s:<16}: {len(df):>5} rows (latest pub: {df['publication_time'].max().strftime('%Y-%m-%d')})")

    # 3. CFTC Commitments of Traders
    print("\n[3/6] Ingesting CFTC Commitments of Traders (COT) Gold Positioning...")
    cot_ingestor = CotDataIngestor()
    cot_df = cot_ingestor.get_gold_cot_data(start_year=args.start_year, force_refresh=args.force_refresh)
    print(f"  [OK] Gold COT       : {len(cot_df):>5} weekly records (Tuesday obs -> Friday 15:30 ET pub)")

    # 4. ETF Flows
    print("\n[4/6] Ingesting Gold ETF Flows (GLD, IAU)...")
    etf_ingestor = EtfDataIngestor()
    etf_df = etf_ingestor.get_etf_flows(start_year=args.start_year, force_refresh=args.force_refresh)
    print(f"  [OK] Gold ETF Flows : {len(etf_df):>5} daily records")

    # 5. Macroeconomic Events
    print("\n[5/6] Ingesting & normalizing macroeconomic event calendar...")
    event_loader = EventLoader()
    events_df = event_loader.load_or_generate_events(start_year=args.start_year, force_refresh=args.force_refresh)
    print(f"  [OK] Macro Events   : {len(events_df):>5} total historical events with expanding Z-scores")

    # 6. Live news / geopolitics / Fed speak
    print("\n[6/6] Fetching live news feeds (RSS + optional API keys)...")
    news = NewsFeedIngestor()
    intel = news.build_intelligence(force_refresh=True)
    print(f"  [OK] Live headlines : {intel['item_count']:>5} relevant items")
    print(f"  [OK] Risk flags     : {', '.join(intel.get('risk_flags') or [])}")
    for name, status in list((intel.get('source_status') or {}).items())[:6]:
        print(f"       feed {name}: {status}")

    print("\n=== Ingestion Completed Successfully! ===")


if __name__ == "__main__":
    main()
