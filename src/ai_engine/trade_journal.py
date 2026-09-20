"""
Human-Decision Journal & Trade Logging System for Gold AI Engine.
Provides an immutable audit trail for discretionary trader decisions,
recording model recommendations, human overrides, and realized trade performance.
"""

from __future__ import annotations
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


JOURNAL_DIR = Path("data/journal")
JOURNAL_CSV = JOURNAL_DIR / "trade_journal.csv"
JOURNAL_JSONL = JOURNAL_DIR / "trade_journal.jsonl"


class TradeJournal:
    """Manages discretionary trading audit logs and decision quality metrics."""

    def __init__(self, journal_dir: Optional[Path | str] = None):
        self.dir = Path(journal_dir) if journal_dir else JOURNAL_DIR
        self.csv_path = self.dir / "trade_journal.csv"
        self.jsonl_path = self.dir / "trade_journal.jsonl"
        self.dir.mkdir(parents=True, exist_ok=True)

    def log_decision(
        self,
        week_ending: str,
        gold_price: float,
        model_bias_score: float,
        confidence_tier: str,
        no_trade_triggered: bool,
        trader_decision: str,
        override_rationale: str = "",
        planned_entry: Optional[float] = None,
        planned_stop: Optional[float] = None,
        planned_target: Optional[float] = None,
        no_trade_triggers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Logs a new forward trading decision at observation cutoff."""
        ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry_id = f"JRN-{week_ending.replace('-', '')}-{int(datetime.now().timestamp()) % 10000:04d}"

        record: Dict[str, Any] = {
            "entry_id": entry_id,
            "created_at": ts_now,
            "week_ending": week_ending,
            "gold_price": float(gold_price),
            "model_bias_score": float(model_bias_score),
            "confidence_tier": str(confidence_tier).upper(),
            "no_trade_triggered": bool(no_trade_triggered),
            "no_trade_triggers": "; ".join(no_trade_triggers or []),
            "trader_decision": str(trader_decision).upper(),
            "override_rationale": str(override_rationale),
            "planned_entry": float(planned_entry) if planned_entry is not None else float(gold_price),
            "planned_stop": float(planned_stop) if planned_stop is not None else None,
            "planned_target": float(planned_target) if planned_target is not None else None,
            "actual_entry_price": None,
            "actual_exit_price": None,
            "realized_pnl_pct": None,
            "outcome_status": "PENDING" if trader_decision.upper() in {"FOLLOW", "OVERRIDE", "FADE"} else "SKIPPED",
            "lessons_learned": "",
        }

        # Append to JSONL
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # Sync CSV
        self._sync_csv_from_jsonl()
        return record

    def update_outcome(
        self,
        entry_id: str,
        actual_entry_price: float,
        actual_exit_price: float,
        realized_pnl_pct: float,
        outcome_status: str,
        lessons_learned: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Updates a pending journal entry once the trade week resolves."""
        if not self.jsonl_path.exists():
            return None

        records: List[Dict[str, Any]] = []
        updated_record = None

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("entry_id") == entry_id:
                        r["actual_entry_price"] = float(actual_entry_price)
                        r["actual_exit_price"] = float(actual_exit_price)
                        r["realized_pnl_pct"] = float(realized_pnl_pct)
                        r["outcome_status"] = outcome_status.upper()
                        r["lessons_learned"] = lessons_learned
                        updated_record = r
                    records.append(r)

        if updated_record:
            with open(self.jsonl_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
            self._sync_csv_from_jsonl()

        return updated_record

    def get_history(self) -> pd.DataFrame:
        """Loads complete historical journal records as DataFrame."""
        if not self.csv_path.exists():
            return pd.DataFrame()
        return pd.read_csv(self.csv_path)

    def compute_quality_stats(self) -> Dict[str, Any]:
        """Calculates decision quality metrics comparing Follow vs. Override performance."""
        df = self.get_history()
        if df.empty or "realized_pnl_pct" not in df.columns:
            return {"status": "NO_JOURNAL_DATA", "total_records": 0}

        resolved = df[df["outcome_status"].isin(["WIN", "LOSS", "SCRATCH"]) & df["realized_pnl_pct"].notna()].copy()
        if resolved.empty:
            return {"status": "NO_RESOLVED_TRADES", "total_records": len(df)}

        def calc_group_stats(subset: pd.DataFrame) -> Dict[str, Any]:
            if subset.empty:
                return {"trades": 0, "win_rate": 0.0, "avg_return_pct": 0.0, "total_return_pct": 0.0}
            wins = (subset["realized_pnl_pct"] > 0).sum()
            return {
                "trades": len(subset),
                "win_rate": round(wins / len(subset) * 100, 1),
                "avg_return_pct": round(subset["realized_pnl_pct"].mean() * 100, 2),
                "total_return_pct": round(((1.0 + subset["realized_pnl_pct"]).prod() - 1.0) * 100, 2),
            }

        followed = resolved[resolved["trader_decision"] == "FOLLOW"]
        overridden = resolved[resolved["trader_decision"] == "OVERRIDE"]
        faded = resolved[resolved["trader_decision"] == "FADE"]

        return {
            "total_decisions_logged": len(df),
            "resolved_trades": len(resolved),
            "overall_stats": calc_group_stats(resolved),
            "when_model_followed": calc_group_stats(followed),
            "when_model_overridden": calc_group_stats(overridden),
            "when_model_faded": calc_group_stats(faded),
        }

    def _sync_csv_from_jsonl(self) -> None:
        if not self.jsonl_path.exists():
            return
        records = []
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        if records:
            pd.DataFrame(records).to_csv(self.csv_path, index=False)
