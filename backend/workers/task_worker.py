"""
Lightweight background task worker for asynchronous research and backtest execution.
Executes non-blocking jobs and updates database state.
"""

from __future__ import annotations

import datetime as dt
import traceback
from typing import Dict, Any

from database.db_session import SessionLocal
from database.models import ResearchRun, BacktestRun, BacktestMetric
from research.services.backtest_service import BacktestService


def run_backtest_job(run_id: str, params: Dict[str, Any]):
    """
    Executes a backtest asynchronously, storing complete metrics and equity curve in the database.
    """
    db = SessionLocal()
    try:
        # Mark as RUNNING
        run_record = db.query(ResearchRun).filter_by(run_id=run_id).first()
        if run_record:
            run_record.status = "RUNNING"
            db.commit()

        # Execute backtest calculation
        service = BacktestService()
        result = service.run_backtest(
            strategy_name=params.get("strategy_name", "MacroRegimeTrend"),
            start_date=params.get("start_date", "2018-01-01"),
            end_date=params.get("end_date", "2026-09-01"),
            signal_type=params.get("signal_type", "macro_regime"),
            threshold_entry=params.get("threshold_entry", 0.0),
            slippage_bps=params.get("slippage_bps", 2.0),
            commission_bps=params.get("commission_bps", 1.5),
            initial_capital=params.get("initial_capital", 100000.0),
        )

        if result.get("status") == "ERROR":
            if run_record:
                run_record.status = "FAILED"
                run_record.error_message = result.get("message", "Execution error")
                db.commit()
            return

        # Store results
        if run_record:
            run_record.status = "COMPLETED"
            run_record.completed_at = dt.datetime.now(dt.timezone.utc)
            run_record.results_summary = result.get("metrics", {})

            # Upsert backtest metrics
            existing_metrics = db.query(BacktestMetric).filter_by(run_id=run_id).first()
            metrics_data = result.get("metrics", {})
            if not existing_metrics:
                b_metrics = BacktestMetric(
                    run_id=run_id,
                    total_return_pct=metrics_data.get("total_return_pct"),
                    annualized_return_pct=metrics_data.get("cagr_pct"),
                    sharpe_ratio=metrics_data.get("sharpe_ratio"),
                    sortino_ratio=metrics_data.get("sortino_ratio"),
                    max_drawdown_pct=metrics_data.get("max_drawdown_pct"),
                    win_rate_pct=metrics_data.get("win_rate_pct"),
                    profit_factor=metrics_data.get("profit_factor"),
                    turnover_annualized=metrics_data.get("annualized_turnover"),
                    total_trades=metrics_data.get("total_trading_weeks", 0),
                    trade_log=result.get("recent_trades", []),
                    equity_curve=result.get("equity_curve", []),
                )
                db.add(b_metrics)
            db.commit()

    except Exception as e:
        traceback.print_exc()
        if run_record:
            run_record.status = "FAILED"
            run_record.error_message = str(e)
            db.commit()
    finally:
        db.close()
