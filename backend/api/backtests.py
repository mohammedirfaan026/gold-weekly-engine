"""
Asynchronous Backtesting API Router.
Non-blocking execution of systematic backtests with background worker.
"""

from __future__ import annotations

import uuid
import datetime as dt
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from database.db_session import get_db
from database.models import ResearchRun, BacktestRun, BacktestMetric
from backend.models.schemas import BacktestRequest, BacktestResponse
from backend.workers.task_worker import run_backtest_job

router = APIRouter(prefix="/backtests", tags=["Backtesting"])


@router.post("", response_model=BacktestResponse)
def launch_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Asynchronously queues a backtest job and returns run_id immediately.
    Frontend polls /api/backtests/{run_id}/status for progress.
    """
    run_id = f"BT-{request.strategy_name[:8].upper()}-{uuid.uuid4().hex[:6]}"

    # Create research_run
    run_record = ResearchRun(
        run_id=run_id,
        git_commit="HEAD",
        dataset_version="v1.0",
        feature_version="v1.0",
        model_version=request.signal_type,
        parameters=request.model_dump(),
        status="QUEUED",
        created_at=dt.datetime.now(dt.timezone.utc),
    )
    db.add(run_record)

    # Create backtest_run metadata
    bt_record = BacktestRun(
        run_id=run_id,
        strategy_name=request.strategy_name,
        start_date=dt.date.fromisoformat(request.start_date),
        end_date=dt.date.fromisoformat(request.end_date),
        parameters=request.model_dump(),
        slippage_bps=request.slippage_bps,
        commission_bps=request.commission_bps,
        initial_capital=request.initial_capital,
    )
    db.add(bt_record)
    db.commit()

    # Queue background task
    background_tasks.add_task(run_backtest_job, run_id, request.model_dump())

    return BacktestResponse(
        run_id=run_id,
        status="QUEUED",
        strategy_name=request.strategy_name,
        created_at=str(run_record.created_at),
    )


@router.get("/{run_id}/status")
def get_backtest_status(run_id: str, db: Session = Depends(get_db)):
    """Returns the current execution lifecycle state of a backtest."""
    run_record = db.query(ResearchRun).filter_by(run_id=run_id).first()
    if not run_record:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    return {
        "run_id": run_id,
        "status": run_record.status,
        "created_at": str(run_record.created_at),
        "completed_at": str(run_record.completed_at) if run_record.completed_at else None,
        "error_message": run_record.error_message,
    }


@router.get("/{run_id}", response_model=BacktestResponse)
def get_backtest_details(run_id: str, db: Session = Depends(get_db)):
    """Returns complete backtest results, equity curves, and performance metrics."""
    run_record = db.query(ResearchRun).filter_by(run_id=run_id).first()
    if not run_record:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    bt_run = db.query(BacktestRun).filter_by(run_id=run_id).first()
    metrics = db.query(BacktestMetric).filter_by(run_id=run_id).first()

    metrics_dict = None
    equity_curve = []
    recent_trades = []

    if metrics:
        metrics_dict = {
            "total_return_pct": metrics.total_return_pct,
            "cagr_pct": metrics.annualized_return_pct,
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
            "max_drawdown_pct": metrics.max_drawdown_pct,
            "win_rate_pct": metrics.win_rate_pct,
            "profit_factor": metrics.profit_factor,
            "annualized_turnover": metrics.turnover_annualized,
            "total_trading_weeks": metrics.total_trades,
        }
        equity_curve = metrics.equity_curve or []
        recent_trades = metrics.trade_log or []

    return BacktestResponse(
        run_id=run_id,
        status=run_record.status,
        strategy_name=bt_run.strategy_name if bt_run else "Unknown",
        created_at=str(run_record.created_at),
        metrics=metrics_dict,
        equity_curve=equity_curve,
        recent_trades=recent_trades,
    )


@router.get("")
def list_backtests(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Lists historical backtest runs."""
    runs = (
        db.query(BacktestRun)
        .join(ResearchRun, BacktestRun.run_id == ResearchRun.run_id)
        .order_by(BacktestRun.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for b in runs:
        m = db.query(BacktestMetric).filter_by(run_id=b.run_id).first()
        r = db.query(ResearchRun).filter_by(run_id=b.run_id).first()
        results.append({
            "run_id": b.run_id,
            "strategy_name": b.strategy_name,
            "status": r.status if r else "UNKNOWN",
            "period": f"{b.start_date} to {b.end_date}",
            "created_at": str(b.created_at),
            "total_return_pct": m.total_return_pct if m else None,
            "sharpe_ratio": m.sharpe_ratio if m else None,
            "max_drawdown_pct": m.max_drawdown_pct if m else None,
        })
    return results
