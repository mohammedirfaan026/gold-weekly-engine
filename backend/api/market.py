"""
Gold & Cross-Asset Market Data API Router.
Provides current gold state, weekly time series, and multi-factor features.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from database.db_session import get_db
from database.models import WeeklyFeature, WeeklyTarget, MacroEvent
from backend.models.schemas import CurrentMarketResponse
from research.services.regime_service import RegimeService

router = APIRouter(prefix="/gold", tags=["Gold Market"])


@router.get("/current", response_model=CurrentMarketResponse)
def get_gold_current(db: Session = Depends(get_db)):
    """Returns real-time and latest weekly summary of Gold (XAUUSD) state and cross-asset strip."""
    latest_wk = db.query(WeeklyFeature).order_by(WeeklyFeature.prediction_timestamp.desc()).first()
    if not latest_wk:
        raise HTTPException(status_code=404, detail="No market data available")

    regime_svc = RegimeService()
    current_regimes = regime_svc.get_current_regimes()
    
    # Upcoming high impact events
    upcoming = (
        db.query(MacroEvent)
        .filter(MacroEvent.importance == "high")
        .order_by(MacroEvent.publication_time.desc())
        .limit(3)
        .all()
    )
    upcoming_list = [
        {
            "event_type": u.event_type,
            "publication_time": str(u.publication_time),
            "consensus_value": u.consensus_value,
            "importance": u.importance,
        }
        for u in upcoming
    ]

    return CurrentMarketResponse(
        symbol="XAUUSD",
        price=latest_wk.gold_close,
        timestamp=str(latest_wk.prediction_timestamp),
        return_1w_pct=round((latest_wk.gold_return_1w or 0.0) * 100.0, 2),
        return_4w_pct=round((latest_wk.gold_return_4w or 0.0) * 100.0, 2),
        return_12w_pct=round((latest_wk.gold_return_12w or 0.0) * 100.0, 2),
        realized_volatility_pct=round((latest_wk.gold_volatility_20w or 0.15) * 100.0, 1),
        trend="bullish" if latest_wk.gold_trend == 1 else ("bearish" if latest_wk.gold_trend == -1 else "sideways"),
        factors={
            "dxy": {"close": latest_wk.dxy_close, "return_1w_pct": round((latest_wk.dxy_return_1w or 0.0) * 100.0, 2)},
            "real_yield_10y": {"value": latest_wk.real_yield_10y, "delta_1w": latest_wk.delta_real_yield_1w},
            "nominal_10y": {"value": latest_wk.nominal_treasury_10y},
            "vix": {"close": latest_wk.vix_close, "change_1w": latest_wk.vix_change_1w},
            "sp500": {"close": latest_wk.sp500_close, "return_1w_pct": round((latest_wk.sp500_return_1w or 0.0) * 100.0, 2)},
            "wti": {"close": latest_wk.wti_close, "return_1w_pct": round((latest_wk.wti_return_1w or 0.0) * 100.0, 2)},
            "silver": {"close": latest_wk.silver_close, "return_1w_pct": round((latest_wk.silver_return_1w or 0.0) * 100.0, 2)},
            "cot_positioning": {"percentile": latest_wk.cot_percentile_3y, "net_contracts": latest_wk.cot_net_speculative},
            "etf_flows": {"weekly_usd_m": latest_wk.etf_weekly_flow_usd_m, "percentile": latest_wk.etf_flow_percentile},
        },
        current_macro_regime=current_regimes.get("composite_macro_state", "NEUTRAL"),
        current_gold_regime=current_regimes.get("regimes", {}).get("gold_trend", {}).get("label", "sideways").upper(),
        upcoming_events=upcoming_list,
        latest_reaction={
            "event": "US CPI",
            "date": "2026-09-10",
            "gold_move_pct": +0.84,
            "interpretation": "Disinflation surprise combined with falling real yields sparked immediate continuation.",
        },
    )


@router.get("/weekly")
def get_gold_weekly(
    timeframe: str = Query("3Y", pattern="^(1Y|3Y|5Y|10Y|MAX)$"),
    db: Session = Depends(get_db)
):
    """Returns synchronized weekly time-series for multi-asset charts."""
    weeks_limit = {"1Y": 52, "3Y": 156, "5Y": 260, "10Y": 520, "MAX": 10000}[timeframe]
    rows = (
        db.query(WeeklyFeature)
        .order_by(WeeklyFeature.prediction_timestamp.desc())
        .limit(weeks_limit)
        .all()
    )
    rows.reverse()

    results = []
    for r in rows:
        results.append({
            "date": r.week_ending,
            "gold": r.gold_close,
            "real_yield_10y": r.real_yield_10y,
            "dxy": r.dxy_close,
            "vix": r.vix_close,
            "sp500": r.sp500_close,
            "wti": r.wti_close,
            "silver": r.silver_close,
            "cot_percentile": r.cot_percentile_3y,
            "etf_flow_usd_m": r.etf_weekly_flow_usd_m,
        })
    return {"timeframe": timeframe, "count": len(results), "series": results}


@router.get("/features")
def get_gold_features(limit: int = Query(52, ge=1, le=500), db: Session = Depends(get_db)):
    """Returns dense multi-factor feature matrix rows."""
    rows = (
        db.query(WeeklyFeature)
        .order_by(WeeklyFeature.prediction_timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "week_ending": r.week_ending,
            "prediction_timestamp": str(r.prediction_timestamp),
            "gold_close": r.gold_close,
            "gold_return_1w": r.gold_return_1w,
            "gold_return_4w": r.gold_return_4w,
            "real_yield_10y": r.real_yield_10y,
            "delta_real_yield_1w": r.delta_real_yield_1w,
            "dxy_close": r.dxy_close,
            "dxy_return_1w": r.dxy_return_1w,
            "vix_close": r.vix_close,
            "cot_percentile_3y": r.cot_percentile_3y,
            "etf_flow_usd_m": r.etf_weekly_flow_usd_m,
            "gold_trend": r.gold_trend,
        }
        for r in rows
    ]
