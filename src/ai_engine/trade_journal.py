"""
Human-Decision Journal & Trade Logging System for Gold AI Engine.
Provides an immutable audit trail for discretionary trader decisions,
recording model recommendations, human overrides, MFE/MAE excursions,
and objective post-trade discretionary attribution analytics.
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
        position_size: Optional[float] = 1.0,
        no_trade_triggers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Logs a new forward trading decision at observation cutoff."""
        decision_upper = str(trader_decision).upper().strip()
        if decision_upper not in {"FOLLOW", "FADE", "PASS", "OVERRIDE"}:
            raise ValueError(f"Invalid trader decision '{trader_decision}'. Must be one of: FOLLOW, FADE, PASS, OVERRIDE.")

        ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry_id = f"JRN-{week_ending.replace('-', '')}-{int(datetime.now().timestamp()) % 10000:04d}"

        record: Dict[str, Any] = {
            "entry_id": entry_id,
            "created_at": ts_now,
            "week_ending": str(week_ending),
            "gold_price": float(gold_price),
            "model_bias_score": float(model_bias_score),
            "confidence_tier": str(confidence_tier).upper(),
            "no_trade_triggered": bool(no_trade_triggered),
            "no_trade_triggers": "; ".join(no_trade_triggers or []),
            "trader_decision": decision_upper,
            "model_followed": decision_upper == "FOLLOW",
            "override_rationale": str(override_rationale),
            "planned_entry": float(planned_entry) if planned_entry is not None else float(gold_price),
            "planned_stop": float(planned_stop) if planned_stop is not None else None,
            "planned_target": float(planned_target) if planned_target is not None else None,
            "position_size": float(position_size) if position_size is not None else 1.0,
            "actual_entry_price": None,
            "actual_exit_price": None,
            "exit_reason": None,
            "realized_pnl_pct": None,
            "mfe_pct": None,
            "mae_pct": None,
            "outcome_status": "PENDING" if decision_upper in {"FOLLOW", "OVERRIDE", "FADE"} else "SKIPPED",
            "post_trade_assessment": "",
        }

        # Append to JSONL
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        self._sync_csv_from_jsonl()
        return record

    def update_outcome(
        self,
        entry_id: str,
        actual_entry_price: float,
        actual_exit_price: float,
        realized_pnl_pct: float,
        outcome_status: str,
        exit_reason: str = "WEEKLY_CLOSE",
        mfe_pct: Optional[float] = None,
        mae_pct: Optional[float] = None,
        post_trade_assessment: str = "",
        lessons_learned: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Updates a pending journal entry once the trade resolves."""
        if not self.jsonl_path.exists():
            return None

        assessment_notes = post_trade_assessment or lessons_learned
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
                        r["exit_reason"] = exit_reason
                        r["mfe_pct"] = float(mfe_pct) if mfe_pct is not None else None
                        r["mae_pct"] = float(mae_pct) if mae_pct is not None else None
                        r["post_trade_assessment"] = assessment_notes
                        r["lessons_learned"] = assessment_notes
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
        total_records = len(df)
        if df.empty or "realized_pnl_pct" not in df.columns:
            return {
                "status": "NO_JOURNAL_DATA",
                "total_records": 0,
                "warning": "No discretionary trades recorded yet. Use --journal-log to begin journal.",
            }

        resolved = df[df["outcome_status"].isin(["WIN", "LOSS", "SCRATCH"]) & df["realized_pnl_pct"].notna()].copy()

        def calc_group_stats(subset: pd.DataFrame) -> Dict[str, Any]:
            if subset.empty:
                return {"trades": 0, "win_rate": 0.0, "avg_return_pct": 0.0, "total_return_pct": 0.0}
            wins = (subset["realized_pnl_pct"] > 0).sum()
            return {
                "trades": len(subset),
                "win_rate": round(wins / len(subset) * 100, 1),
                "avg_return_pct": round(subset["realized_pnl_pct"].mean() * 100, 2),
                "total_return_pct": round(((1.0 + subset["realized_pnl_pct"]).prod() - 1.0) * 100, 2),
                "avg_mfe_pct": round(subset["mfe_pct"].mean() * 100, 2) if "mfe_pct" in subset and subset["mfe_pct"].notna().any() else None,
                "avg_mae_pct": round(subset["mae_pct"].mean() * 100, 2) if "mae_pct" in subset and subset["mae_pct"].notna().any() else None,
            }

        followed = resolved[resolved["trader_decision"] == "FOLLOW"]
        overridden = resolved[resolved["trader_decision"] == "OVERRIDE"]
        faded = resolved[resolved["trader_decision"] == "FADE"]
        passed = df[df["trader_decision"] == "PASS"]

        followed_stats = calc_group_stats(followed)
        override_stats = calc_group_stats(overridden)
        fade_stats = calc_group_stats(faded)

        # Discretionary Override Alpha
        if override_stats["trades"] > 0 and followed_stats["trades"] > 0:
            override_alpha = override_stats["avg_return_pct"] - followed_stats["avg_return_pct"]
            if override_alpha > 0.1:
                override_impact = "Overrides IMPROVED results vs model (+{:.2f}% avg diff)".format(override_alpha)
            elif override_alpha < -0.1:
                override_impact = "Overrides HARMED results vs model ({:.2f}% avg diff)".format(override_alpha)
            else:
                override_impact = "Overrides had NEUTRAL impact ({:.2f}% avg diff)".format(override_alpha)
        else:
            override_alpha = 0.0
            override_impact = "INSUFFICIENT DATA to compare Followed vs Override results"

        # Accuracy by Confidence Tier
        tier_accuracy = {}
        for tier in ["LOW", "MODERATE", "HIGH"]:
            sub = resolved[resolved["confidence_tier"] == tier]
            tier_accuracy[tier] = calc_group_stats(sub)

        sample_caution = (
            "INSUFFICIENT OBSERVATIONS (<10 trades) -- Do not draw statistical conclusions about model or discretionary edge."
            if len(resolved) < 10
            else "ADEQUATE TRACK RECORD"
        )

        return {
            "total_decisions_logged": total_records,
            "resolved_trades": len(resolved),
            "pending_or_skipped": total_records - len(resolved),
            "pass_decisions": len(passed),
            "sample_caution": sample_caution,
            "overall_resolved_performance": calc_group_stats(resolved),
            "when_model_followed": followed_stats,
            "when_model_overridden": override_stats,
            "when_model_faded": fade_stats,
            "override_alpha_pct": round(override_alpha, 2),
            "override_impact_assessment": override_impact,
            "performance_by_confidence_tier": tier_accuracy,
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
