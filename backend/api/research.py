"""
Research Runs, Performance Benchmarks, and Conditional Analysis Router.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.db_session import get_db
from database.models import ResearchRun, ModelResult
from backend.models.schemas import ConditionalQueryRequest
from research.services.model_service import ModelEvaluationService
from research.services.conditional_service import ConditionalReactionService

router = APIRouter(prefix="/research", tags=["Research Engine"])


@router.get("/runs")
def list_research_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Returns historical reproducible research runs with metadata and parameters."""
    runs = db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit).all()
    results = []
    for r in runs:
        results.append({
            "run_id": r.run_id,
            "git_commit": r.git_commit,
            "dataset_version": r.dataset_version,
            "feature_version": r.feature_version,
            "model_version": r.model_version,
            "status": r.status,
            "created_at": str(r.created_at),
            "completed_at": str(r.completed_at) if r.completed_at else None,
            "summary": r.results_summary,
        })
    return results


@router.get("/performance")
def get_model_performance():
    """
    Returns candidate model performance evaluated against mandatory baselines
    (Historical Mean, Trend, AR1, Real Yield, DXY, Macro).
    """
    svc = ModelEvaluationService()
    return svc.get_benchmark_comparison_table()


@router.post("/conditional")
def query_conditional_distribution(query: ConditionalQueryRequest):
    """
    Evaluates historical conditional distributions of gold returns matching multi-factor filters:
    e.g. CPI > +1σ AND Real Yield rising AND DXY strengthening AND Gold Trend bullish.
    """
    svc = ConditionalReactionService()
    return svc.query_conditional_distribution(
        event_filter=query.event_filter,
        min_surprise_z=query.min_surprise_z,
        max_surprise_z=query.max_surprise_z,
        real_yield_regime=query.real_yield_regime,
        dxy_regime=query.dxy_regime,
        gold_trend=query.gold_trend,
        vix_regime=query.vix_regime,
        positioning_regime=query.positioning_regime,
    )
