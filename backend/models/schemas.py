"""
Pydantic schemas for FastAPI request and response validation.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    api: str = "healthy"
    database: str = "healthy"
    worker: str = "healthy"
    latest_market_data: Optional[str] = None
    latest_macro_data: Optional[str] = None
    latest_feature_build: Optional[str] = None
    last_validation: str = "PASS"
    synthetic_values_used: int = 0
    environment: str = "production"


class CurrentMarketResponse(BaseModel):
    symbol: str = "XAUUSD"
    price: float
    timestamp: str
    return_1w_pct: float
    return_4w_pct: float
    return_12w_pct: float
    realized_volatility_pct: float
    trend: str
    factors: Dict[str, Any]
    current_macro_regime: str
    current_gold_regime: str
    upcoming_events: List[Dict[str, Any]]
    latest_reaction: Optional[Dict[str, Any]] = None


class EventItem(BaseModel):
    event_id: str
    event_type: str
    country: str = "US"
    publication_time: str
    actual_value: Optional[float] = None
    consensus_value: Optional[float] = None
    previous_value: Optional[float] = None
    surprise_absolute: Optional[float] = None
    surprise_zscore: Optional[float] = None
    surprise_bucket: Optional[str] = None
    importance: str = "high"
    source: str = "BLS"
    vintage_mode: str = "REAL_TIME_VINTAGE"


class EventReactionResponse(BaseModel):
    event_type: str
    sample_size: int
    horizons: Dict[str, Any]
    reversal_dynamics: Dict[str, Any]


class RegimeCurrentResponse(BaseModel):
    week_ending: str
    prediction_timestamp: str
    gold_price: float
    regimes: Dict[str, Any]
    composite_macro_state: str


class DataHealthCheckItem(BaseModel):
    name: str
    status: str  # PASS, WARNING, FAIL
    details: str
    violations_count: int = 0


class DataHealthResponse(BaseModel):
    status: str
    last_audit_utc: str
    synthetic_values_used: int
    checks: List[DataHealthCheckItem]
    market_data_coverage: Dict[str, Any]
    macro_data_coverage: Dict[str, Any]


class BacktestRequest(BaseModel):
    strategy_name: str = "MacroRegimeTrend"
    start_date: str = "2018-01-01"
    end_date: str = "2026-09-01"
    signal_type: str = "macro_regime"
    threshold_entry: float = 0.0
    slippage_bps: float = 2.0
    commission_bps: float = 1.5
    initial_capital: float = 100000.0


class BacktestResponse(BaseModel):
    run_id: str
    status: str
    strategy_name: str
    created_at: str
    metrics: Optional[Dict[str, Any]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None
    recent_trades: Optional[List[Dict[str, Any]]] = None


class ConditionalQueryRequest(BaseModel):
    event_filter: Optional[str] = None
    min_surprise_z: Optional[float] = None
    max_surprise_z: Optional[float] = None
    real_yield_regime: Optional[str] = None
    dxy_regime: Optional[str] = None
    gold_trend: Optional[str] = None
    vix_regime: Optional[str] = None
    positioning_regime: Optional[str] = None
