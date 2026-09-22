"""
Macroeconomic Events & Reaction Engine API Router.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database.db_session import get_db
from database.models import MacroEvent
from backend.models.schemas import EventItem, EventReactionResponse
from research.services.event_study_service import EventStudyService

router = APIRouter(prefix="/events", tags=["Events & Reactions"])


@router.get("", response_model=List[EventItem])
def list_events(
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lists historical economic releases with publication timestamps and surprises."""
    svc = EventStudyService()
    return svc.get_events_list(event_type=event_type, start_date=start_date, end_date=end_date, limit=limit)


@router.get("/types", response_model=List[str])
def list_event_types():
    """Returns all distinct macroeconomic event types."""
    svc = EventStudyService()
    return svc.get_event_types()


@router.get("/reaction/summary", response_model=EventReactionResponse)
def get_event_reaction_summary(event_type: str = Query("CPI")):
    """
    Returns empirical multi-window reaction metrics (+5m to Next Friday),
    sample size N, medians, and reversal dynamics for an event type.
    """
    svc = EventStudyService()
    return svc.get_reaction_summary(event_type=event_type)


@router.get("/{event_id}")
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """Fetches full point-in-time record for a specific event."""
    evt = db.query(MacroEvent).filter(MacroEvent.event_id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "event_id": evt.event_id,
        "event_type": evt.event_type,
        "country": evt.country,
        "publication_time": str(evt.publication_time),
        "actual_value": evt.actual_value,
        "consensus_value": evt.consensus_value,
        "previous_value": evt.previous_value,
        "surprise_absolute": evt.surprise_absolute,
        "surprise_zscore": evt.surprise_zscore,
        "surprise_bucket": evt.surprise_bucket,
        "importance": evt.importance,
        "source": evt.source,
        "vintage_mode": evt.vintage_mode,
        "initial_release": evt.initial_release,
        "revision": evt.revision,
    }


@router.get("/{event_id}/reaction")
def get_single_event_reaction(event_id: str, db: Session = Depends(get_db)):
    """Returns the multi-horizon price response trajectory for a single event."""
    import os
    import pandas as pd
    pq_path = "data/processed/events_master.parquet"
    if os.path.exists(pq_path):
        df = pd.read_parquet(pq_path)
        sub = df[df["event_id"] == event_id]
        if not sub.empty:
            row = sub.iloc[0]
            horizons = {}
            for h in ["5m", "1h", "4h", "1d", "next_friday"]:
                ret_k = f"return_{h}"
                ts_k = f"timestamp_{h}"
                horizons[h] = {
                    "return_pct": round(float(row[ret_k] * 100.0), 2) if ret_k in row and pd.notna(row[ret_k]) else None,
                    "timestamp": str(row[ts_k]) if ts_k in row and pd.notna(row[ts_k]) else None,
                }
            return {
                "event_id": event_id,
                "event_type": row.get("event_type"),
                "publication_time": str(row.get("publication_time") or row.get("timestamp")),
                "ref_a_price": float(row.get("ref_a", 0.0)),
                "horizons": horizons,
                "reversal_classification": row.get("reversal_classification", "unresolved"),
            }

    # Fallback to DB
    evt = db.query(MacroEvent).filter(MacroEvent.event_id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "event_id": event_id,
        "event_type": evt.event_type,
        "publication_time": str(evt.publication_time),
        "horizons": {"5m": None, "1h": None, "4h": None, "1d": None, "next_friday": None},
        "reversal_classification": "unresolved",
    }


@router.get("/{event_id}/comparables")
def get_event_comparables(event_id: str, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """Finds historical events matching surprise magnitude and direction."""
    evt = db.query(MacroEvent).filter(MacroEvent.event_id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")

    target_z = evt.surprise_zscore or 0.0
    all_events = (
        db.query(MacroEvent)
        .filter(MacroEvent.event_type == evt.event_type, MacroEvent.event_id != event_id)
        .all()
    )

    scored = []
    for o in all_events:
        oz = o.surprise_zscore or 0.0
        dist = abs(oz - target_z)
        scored.append((dist, o))

    scored.sort(key=lambda x: x[0])
    results = []
    for _, comp in scored[:limit]:
        results.append({
            "event_id": comp.event_id,
            "publication_time": str(comp.publication_time),
            "surprise_zscore": comp.surprise_zscore,
            "actual_value": comp.actual_value,
            "consensus_value": comp.consensus_value,
            "surprise_bucket": comp.surprise_bucket,
        })
    return {"target_event_id": event_id, "comparables": results}
