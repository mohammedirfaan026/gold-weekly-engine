"""
Immutable Shadow-Mode Workflow for Gold AI Engine.
Records pre-trade weekly forecasts with feature snapshots, configuration hashes,
and immutable timestamps before future outcomes are known.
Resolves realized returns strictly after weekly market close.
"""

from __future__ import annotations
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from .versioning import MODEL_VERSION, get_system_version_info


SHADOW_DIR = Path("data/shadow")
SHADOW_JSONL = SHADOW_DIR / "shadow_log.jsonl"
SHADOW_CSV = SHADOW_DIR / "shadow_log.csv"


class ShadowLogger:
    """Manages forward shadow-testing forecasts and immutable pre-trade records."""

    def __init__(self, shadow_dir: Optional[Path | str] = None):
        self.dir = Path(shadow_dir) if shadow_dir else SHADOW_DIR
        self.jsonl_path = self.dir / "shadow_log.jsonl"
        self.csv_path = self.dir / "shadow_log.csv"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save_prediction(
        self,
        brief: Dict[str, Any],
        features_snapshot: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        force_update: bool = False,
    ) -> Dict[str, Any]:
        """
        Saves an immutable pre-trade forecast before next week's outcome is known.
        Raises ValueError if a prediction for this week has already been recorded.
        """
        week = str(brief.get("observation_week") or brief.get("identification", {}).get("observation_week", ""))
        existing = self.get_records()

        # Check for immutability violation
        for rec in existing:
            if str(rec.get("prediction_week")) == week and not force_update:
                raise ValueError(
                    f"[IMMUTABILITY INVARIANT VIOLATION] Shadow forecast for week '{week}' "
                    f"already exists recorded at {rec.get('prediction_timestamp')}. "
                    f"Overwriting historical shadow signals is strictly prohibited."
                )

        # Compute feature vintage hash
        serialized_features = json.dumps(features_snapshot, sort_keys=True, default=str)
        feature_hash = hashlib.sha256(serialized_features.encode("utf-8")).hexdigest()[:16]

        ver_info = get_system_version_info(config=config)
        corr = brief.get("expected_corridor") or brief.get("scenario_map", {}).get("expected_corridor", {})
        cal = brief.get("confidence_calibration") or brief.get("model_output", {}).get("confidence_calibration", {})
        nt = brief.get("no_trade_circuit_breaker") or brief.get("risk_controls", {}).get("no_trade_circuit_breaker", {})
        bias_val = float(brief.get("bias_score") or brief.get("model_output", {}).get("recursive_bias_score", 0.0))
        ret_val = float(brief.get("expected_return_pct") or brief.get("model_output", {}).get("recursive_expected_return_pct", 0.0)) / 100.0
        stance_val = str(brief.get("taxonomy_stance") or brief.get("model_output", {}).get("directional_stance", "NEUTRAL"))
        pred_ts = str(brief.get("prediction_timestamp") or brief.get("identification", {}).get("prediction_timestamp", ""))

        record: Dict[str, Any] = {
            "prediction_week": week,
            "prediction_timestamp": pred_ts,
            "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "model_version": ver_info["model_version"],
            "git_commit": ver_info["git_commit"],
            "configuration": config or {},
            "bias_score": bias_val,
            "expected_return": ret_val,
            "corridor_low": float(corr.get("lower_support_10pct", 0.0)),
            "corridor_high": float(corr.get("upper_resistance_90pct", 0.0)),
            "stance": stance_val,
            "confidence_tier": str(cal.get("tier", "LOW")),
            "no_trade_status": str(nt.get("status_label", "DO NOT TRADE")),
            "feature_vintage_hash": feature_hash,
            "features_snapshot": features_snapshot,
            "realized_next_week_return": None,
            "directional_correctness": None,
            "corridor_containment": None,
            "post_mortem_result": None,
            "outcome_resolved_at": None,
        }

        # Append to JSONL
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        self._sync_csv_from_jsonl()
        return record

    def resolve_outcome(
        self,
        prediction_week: str,
        realized_return: float,
        weekly_high: float,
        weekly_low: float,
        archetype: str = "NORMAL",
    ) -> Optional[Dict[str, Any]]:
        """Updates realized performance fields once t+1 close is observed."""
        if not self.jsonl_path.exists():
            return None

        records: List[Dict[str, Any]] = []
        updated = None

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if str(r.get("prediction_week")) == str(prediction_week):
                        bias = float(r.get("bias_score", 0.0))
                        c_low = float(r.get("corridor_low", 0.0))
                        c_high = float(r.get("corridor_high", 0.0))

                        # Evaluate correctness:
                        if abs(bias) >= 0.05:
                            correct = bool((bias > 0 and realized_return > 0) or (bias < 0 and realized_return < 0))
                        else:
                            correct = None  # Neutral bias

                        contained = bool(weekly_low >= c_low and weekly_high <= c_high)

                        r["realized_next_week_return"] = round(realized_return, 4)
                        r["directional_correctness"] = correct
                        r["corridor_containment"] = contained
                        r["post_mortem_result"] = archetype
                        r["outcome_resolved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                        updated = r

                    records.append(r)

        if updated:
            with open(self.jsonl_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")
            self._sync_csv_from_jsonl()

        return updated

    def get_records(self) -> List[Dict[str, Any]]:
        """Reads all recorded shadow forecasts."""
        if not self.jsonl_path.exists():
            return []
        records = []
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def generate_shadow_report(self) -> str:
        """Renders comprehensive shadow-testing performance audit report."""
        records = self.get_records()
        total = len(records)
        resolved = [r for r in records if r.get("realized_next_week_return") is not None]
        pending = [r for r in records if r.get("realized_next_week_return") is None]

        lines = [
            "================================================================================",
            "                 GOLD AI ENGINE: IMMUTABLE SHADOW-TEST AUDIT",
            "================================================================================",
            f"Audit Timestamp        : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Forecasts Logged : {total}",
            f"Resolved Forecasts     : {len(resolved)}",
            f"Pending Realizations   : {len(pending)}",
            "",
        ]

        if not resolved:
            lines.append("Status: All shadow records are currently pending future market resolution.")
        else:
            active_signals = [r for r in resolved if r.get("directional_correctness") is not None]
            wins = sum(1 for r in active_signals if r.get("directional_correctness") is True)
            win_rate = (wins / len(active_signals) * 100.0) if active_signals else 0.0

            contained = sum(1 for r in resolved if r.get("corridor_containment") is True)
            containment_rate = (contained / len(resolved) * 100.0) if resolved else 0.0

            lines.extend([
                "--------------------------------------------------------------------------------",
                "FORWARD PERFORMANCE SUMMARY (REALIZED UNSEEN MARKET DATA)",
                "--------------------------------------------------------------------------------",
                f"Active Directional Signals : {len(active_signals)}",
                f"Directional Win Rate       : {win_rate:.1f}% ({wins} / {len(active_signals)})",
                f"Corridor Containment Rate  : {containment_rate:.1f}% ({contained} / {len(resolved)})",
                "",
                "| Week | Logged Cutoff | Stance | Conf | Bias | Expected | Realized | Won? | Contained? |",
                "|---|---|---|:---:|---:|---:|---:|:---:|:---:|",
            ])

            for r in resolved:
                w = r.get("prediction_week")
                cut = (r.get("prediction_timestamp") or "")[:10]
                st = (r.get("stance") or "").split(" -- ")[0]
                tier = r.get("confidence_tier")
                b = f"{r.get('bias_score', 0.0):+.3f}"
                exp = f"{r.get('expected_return', 0.0)*100:+.2f}%"
                real = f"{r.get('realized_next_week_return', 0.0)*100:+.2f}%"
                won = "YES" if r.get("directional_correctness") is True else "NO" if r.get("directional_correctness") is False else "FLAT"
                cont = "YES" if r.get("corridor_containment") is True else "NO"
                lines.append(f"| {w} | {cut} | {st} | {tier} | {b} | {exp} | {real} | {won} | {cont} |")

        if pending:
            lines.extend([
                "",
                "--------------------------------------------------------------------------------",
                "PENDING FORWARD SHADOW PREDICTIONS",
                "--------------------------------------------------------------------------------",
            ])
            for p in pending:
                lines.append(
                    f"- Week {p.get('prediction_week')}: Stance='{p.get('stance')}', "
                    f"Bias={p.get('bias_score'):+.3f}, Corridor=[${p.get('corridor_low'):,.2f} - ${p.get('corridor_high'):,.2f}], "
                    f"Hash={p.get('feature_vintage_hash')}"
                )

        lines.extend([
            "",
            "================================================================================",
            "IMMUTABILITY NOTE: Shadow predictions are timestamped prior to session open.",
            "Historical forecast records cannot be overwritten after real-world outcomes occur.",
            "================================================================================",
        ])
        return "\n".join(lines)

    def _sync_csv_from_jsonl(self) -> None:
        records = self.get_records()
        if records:
            clean_records = []
            for r in records:
                flat = {k: v for k, v in r.items() if k not in {"configuration", "features_snapshot"}}
                clean_records.append(flat)
            pd.DataFrame(clean_records).to_csv(self.csv_path, index=False)
