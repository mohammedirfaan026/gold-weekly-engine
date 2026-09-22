"""
Reproducible Backtesting Research Service.
Executes deterministic Friday-to-Friday systematic trading backtests with:
- Transaction costs (commissions in bps)
- Execution slippage (in bps)
- Strict execution timing: Prediction at Friday 17:00 ET -> Trade entered at Friday 18:00 ET / Monday open -> Exited at next Friday 17:00 ET.
- Detailed metrics: CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Turnover, Trade Log, Equity Curve.
"""

from __future__ import annotations

import os
import uuid
import datetime as dt
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class BacktestService:
    """
    Headless research service for reproducible systematic backtesting.
    """

    def __init__(self, weekly_matrix_path: str = "research/features/feature_matrix.parquet"):
        self.weekly_matrix_path = weekly_matrix_path
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        if os.path.exists(self.weekly_matrix_path):
            self._df = pd.read_parquet(self.weekly_matrix_path)
        else:
            alt_path = "data/weekly/gold_weekly_master.parquet"
            if os.path.exists(alt_path):
                self._df = pd.read_parquet(alt_path)
            else:
                self._df = pd.DataFrame()
        return self._df

    def run_backtest(
        self,
        strategy_name: str = "MacroRegimeTrend",
        start_date: str = "2018-01-01",
        end_date: str = "2026-09-01",
        signal_type: str = "macro_regime",  # 'macro_regime', 'trend_following', 'reversal', 'equal_weight'
        threshold_entry: float = 0.0,
        slippage_bps: float = 2.0,          # 2 basis points slippage
        commission_bps: float = 1.5,        # 1.5 basis points broker fee
        initial_capital: float = 100000.0,
    ) -> Dict[str, Any]:
        """
        Executes a point-in-time Friday-to-Friday backtest run.
        """
        run_id = f"BT-{strategy_name.upper()}-{uuid.uuid4().hex[:8]}"
        df = self._load_data().copy()
        if df.empty:
            return {"run_id": run_id, "status": "ERROR", "message": "Dataset unavailable"}

        # Filter date range
        df["week_ending"] = pd.to_datetime(df["week_ending"])
        df = df[(df["week_ending"] >= pd.to_datetime(start_date)) & (df["week_ending"] <= pd.to_datetime(end_date))]
        df = df.sort_values(by="week_ending").reset_index(drop=True)

        if len(df) < 10:
            return {"run_id": run_id, "status": "ERROR", "message": "Insufficient data in specified period"}

        # Determine trading signals strictly using features available at week t
        signals = np.zeros(len(df))

        if signal_type == "macro_regime":
            # Long when Real Yield is falling (-1) OR Gold Trend is bullish (1)
            ry = df["real_yield_regime"] if "real_yield_regime" in df.columns else pd.Series(0, index=df.index)
            gt = df["gold_trend"] if "gold_trend" in df.columns else pd.Series(0, index=df.index)
            dxy = df["dxy_regime"] if "dxy_regime" in df.columns else pd.Series(0, index=df.index)

            score = (-1 * ry) + (1 * gt) + (-0.5 * dxy)
            signals = np.where(score > threshold_entry, 1.0, np.where(score < -threshold_entry, -1.0, 0.0))

        elif signal_type == "trend_following":
            if "gold_trend" in df.columns:
                signals = df["gold_trend"].values.astype(float)
            else:
                signals = np.ones(len(df))

        elif signal_type == "reversal":
            # Contrarian COT or shock reversal
            if "cot_percentile_3y" in df.columns:
                signals = np.where(df["cot_percentile_3y"] < 25.0, 1.0, np.where(df["cot_percentile_3y"] > 75.0, -1.0, 0.0))
            else:
                signals = np.zeros(len(df))
        else:
            signals = np.ones(len(df))  # Long buy & hold

        # Target next week return
        ret_col = "next_week_gold_return" if "next_week_gold_return" in df.columns else "fwd_weekly_gold_return"
        raw_rets = df[ret_col].fillna(0.0).values

        # Apply transaction costs on position turnover
        turnover = np.abs(np.diff(signals, prepend=0.0))
        round_trip_cost = (slippage_bps + commission_bps) * 2.0 / 10000.0  # in decimal

        net_returns = (signals * raw_rets) - (turnover * round_trip_cost)

        # Build equity curve
        equity = [initial_capital]
        for r in net_returns:
            new_eq = equity[-1] * (1.0 + r)
            equity.append(new_eq)
        equity = np.array(equity[1:])  # match length of df

        # Drawdown calculation
        peak = np.maximum.accumulate(equity)
        drawdowns = (equity - peak) / peak
        max_dd = float(np.min(drawdowns) * 100.0)

        # Performance summary metrics
        total_ret = float((equity[-1] / initial_capital - 1.0) * 100.0)
        num_weeks = len(df)
        years = max(0.5, num_weeks / 52.0)
        cagr = float(((equity[-1] / initial_capital) ** (1.0 / years) - 1.0) * 100.0)

        ann_mean = float(np.mean(net_returns) * 52)
        ann_vol = float(np.std(net_returns) * np.sqrt(52)) if np.std(net_returns) > 0 else 1.0
        sharpe = float(ann_mean / ann_vol) if ann_vol > 0 else 0.0

        downside = net_returns[net_returns < 0]
        downside_vol = float(np.std(downside) * np.sqrt(52)) if len(downside) > 1 and np.std(downside) > 0 else 1.0
        sortino = float(ann_mean / downside_vol)

        trade_mask = signals != 0
        win_rate = float((net_returns[trade_mask] > 0).mean() * 100.0) if trade_mask.sum() > 0 else 0.0
        wins = net_returns[trade_mask & (net_returns > 0)]
        losses = net_returns[trade_mask & (net_returns < 0)]
        profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) > 0 and abs(losses.sum()) > 0 else 1.0

        # Build sample trade log (last 20 trades)
        trade_log = []
        for i in range(max(0, len(df) - 20), len(df)):
            trade_log.append({
                "week_ending": str(df["week_ending"].iloc[i].date()),
                "signal": int(signals[i]),
                "stance": "LONG" if signals[i] > 0 else ("SHORT" if signals[i] < 0 else "FLAT"),
                "gross_return_pct": round(float(raw_rets[i] * 100.0), 2),
                "net_return_pct": round(float(net_returns[i] * 100.0), 2),
                "portfolio_equity": round(float(equity[i]), 2),
                "drawdown_pct": round(float(drawdowns[i] * 100.0), 2),
            })

        # Subsample equity curve for plotting
        step = max(1, len(equity) // 100)
        eq_curve_sample = []
        for i in range(0, len(equity), step):
            eq_curve_sample.append({
                "date": str(df["week_ending"].iloc[i].date()),
                "equity": round(float(equity[i]), 2),
                "drawdown_pct": round(float(drawdowns[i] * 100.0), 2),
            })

        return {
            "run_id": run_id,
            "strategy_name": strategy_name,
            "signal_type": signal_type,
            "period": f"{start_date} to {end_date}",
            "assumptions": {
                "slippage_bps": slippage_bps,
                "commission_bps": commission_bps,
                "initial_capital": initial_capital,
                "execution_timing": "Prediction Friday 17:00 ET -> Trade Friday 18:00 ET -> Exit next Friday 17:00 ET",
            },
            "metrics": {
                "total_return_pct": round(total_ret, 2),
                "cagr_pct": round(cagr, 2),
                "sharpe_ratio": round(sharpe, 2),
                "sortino_ratio": round(sortino, 2),
                "max_drawdown_pct": round(max_dd, 2),
                "win_rate_pct": round(win_rate, 1),
                "profit_factor": round(profit_factor, 2),
                "total_trading_weeks": num_weeks,
                "annualized_turnover": round(float(turnover.mean() * 52), 1),
            },
            "equity_curve": eq_curve_sample,
            "recent_trades": trade_log,
        }
