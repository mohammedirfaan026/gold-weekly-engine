"""Data ingestion package."""
from src.ingestion.market_data import MarketDataIngestor
from src.ingestion.macro_data import MacroDataIngestor
from src.ingestion.cot_data import CotDataIngestor
from src.ingestion.etf_data import EtfDataIngestor
from src.ingestion.event_loader import EventLoader
from src.ingestion.news_feed import NewsFeedIngestor

__all__ = [
    "MarketDataIngestor",
    "MacroDataIngestor",
    "CotDataIngestor",
    "EtfDataIngestor",
    "EventLoader",
    "NewsFeedIngestor",
]
