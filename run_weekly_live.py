"""
Friday live pipeline for VPS / local automation.

1) Refresh market + macro + news
2) Rebuild weekly prediction + recursive brief
3) Persist JSON for the private dashboard
4) Push Telegram summary (if configured)

Usage:
    python run_weekly_live.py
    python run_weekly_live.py --skip-ingest
    python run_weekly_live.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.ai_engine.decision_brief import WeeklyDecisionBrief
from src.ai_engine.data_freshness import DataFreshnessChecker
from src.ai_engine.engine import GoldWeeklyBiasEngine
from src.ai_engine.pit_validator import PointInTimeFeatureValidator, PointInTimeViolationError
from src.ai_engine.recursive_learner import RecursiveSelfImprovingEngine
from src.ai_engine.shadow_logger import ShadowLogger
from src.notify.telegram import TelegramNotifier


LIVE_DIR = ROOT / "data" / "live"
BRIEF_JSON = LIVE_DIR / "latest_brief.json"
BRIEF_MD = ROOT / "research" / "reports" / "LIVE_WEEKLY_DECISION_BRIEF.md"
RUN_LOG = LIVE_DIR / "last_run.json"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))


def generate_live_brief(strict_pit: bool = True) -> Dict[str, Any]:
    engine = GoldWeeklyBiasEngine()
    engine.load_data()
    engine.fit()
    prediction = engine.predict_week(week_ending=None)

    matrix = engine.matrix
    target_idx = len(matrix) - 1
    prior_idx = max(0, target_idx - 1)
    train_matrix = matrix.iloc[:prior_idx].copy()
    prior_row = matrix.iloc[prior_idx]
    current_row = matrix.iloc[target_idx]

    fc = DataFreshnessChecker()
    fresh_rep = fc.check_freshness(as_of_date=str(current_row["week_ending"]))
    cutoff_ts = str(current_row["week_ending"]) + " 21:00:00 UTC"
    pit_meta = [
        {"name": "gold_close", "observation_timestamp": cutoff_ts, "publication_timestamp": cutoff_ts},
        {"name": "real_yield_10y", "observation_timestamp": cutoff_ts, "publication_timestamp": cutoff_ts},
        {"name": "dxy_close", "observation_timestamp": cutoff_ts, "publication_timestamp": cutoff_ts},
        {"name": "vix_close", "observation_timestamp": cutoff_ts, "publication_timestamp": cutoff_ts},
    ]
    pit_val = PointInTimeFeatureValidator()
    try:
        pit_rep = pit_val.validate_feature_timestamps(pit_meta, prediction_timestamp=cutoff_ts, strict=strict_pit)
    except PointInTimeViolationError as e:
        if strict_pit:
            raise
        pit_rep = {"is_valid": False, "violation_count": 1, "violations": [str(e)]}

    if strict_pit and not fresh_rep.get("is_usable", True):
        raise RuntimeError("Data freshness fail-closed: critical series stale")

    def feats(row):
        return {
            "delta_real_yield_1w": float(row.get("delta_real_yield_1w", 0.0)),
            "dxy_return_1w": float(row.get("dxy_return_1w", 0.0)),
            "delta_breakeven_1w": float(row.get("delta_breakeven_1w", 0.0)),
            "gold_distance_20w": float(row.get("gold_distance_20w", 0.0)),
            "vix": float(row.get("vix", 15.0)),
        }

    curr_features = feats(current_row)
    prior_features = feats(prior_row)

    rec = RecursiveSelfImprovingEngine()
    rec.initialize(train_matrix)
    prior_price = float(prior_row["gold_close"])
    rec.predict_upcoming_week(
        week=str(prior_row["week_ending"]),
        current_features_dict=prior_features,
        current_gold_price=prior_price,
        baseline_corridor_high=prior_price * 1.025,
        baseline_corridor_low=prior_price * 0.975,
    )
    realized_prior = float(current_row["gold_close"] / prior_row["gold_close"] - 1.0)
    rec.process_prior_week_outcome(
        week=str(prior_row["week_ending"]),
        features_dict=prior_features,
        realized_return=realized_prior,
        actual_price=float(current_row["gold_close"]),
    )
    recursive_data = rec.predict_upcoming_week(
        week=str(current_row["week_ending"]),
        current_features_dict=curr_features,
        current_gold_price=float(current_row["gold_close"]),
        baseline_corridor_high=prediction["expected_price_corridor"]["expected_high_90pct"],
        baseline_corridor_low=prediction["expected_price_corridor"]["expected_low_10pct"],
    )

    brief = WeeklyDecisionBrief().generate_brief(
        prediction=prediction,
        recursive_data=recursive_data,
        features_dict=curr_features,
        freshness_report=fresh_rep,
        pit_validation_report=pit_rep,
        save_file=True,
        output_path=BRIEF_MD,
        fetch_news=True,
    )
    brief["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return brief


def persist_brief(brief: Dict[str, Any]) -> Path:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    BRIEF_JSON.write_text(json.dumps(brief, indent=2, default=str), encoding="utf-8")
    return BRIEF_JSON


def main() -> int:
    parser = argparse.ArgumentParser(description="Gold weekly live VPS pipeline")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip ingest_data.py refresh")
    parser.add_argument("--skip-telegram", action="store_true", help="Do not send Telegram message")
    parser.add_argument("--skip-shadow", action="store_true", help="Do not append shadow log")
    parser.add_argument("--dry-run", action="store_true", help="Build brief only; no Telegram/shadow")
    parser.add_argument("--no-strict-pit", action="store_true", help="Warn-only PIT/freshness")
    args = parser.parse_args()

    started = datetime.now(timezone.utc).isoformat()
    status: Dict[str, Any] = {"started_at_utc": started, "ok": False}

    try:
        if not args.skip_ingest:
            _run([sys.executable, "ingest_data.py", "--force-refresh"])
            # Rebuild weekly master if builders exist; tolerate missing optional steps
            for script in ("build_dataset.py", "run_weekly_analysis.py"):
                if (ROOT / script).exists():
                    try:
                        _run([sys.executable, script])
                    except subprocess.CalledProcessError as exc:
                        print(f"[warn] {script} failed ({exc.returncode}); continuing with existing weekly matrix")

        brief = generate_live_brief(strict_pit=not args.no_strict_pit)
        path = persist_brief(brief)
        print(f"[ok] brief saved -> {path}")
        print(f"[ok] markdown   -> {BRIEF_MD}")

        dashboard_url = os.getenv("DASHBOARD_PUBLIC_URL", "").strip()

        if not args.dry_run and not args.skip_shadow:
            try:
                ShadowLogger().save_prediction(
                    brief=brief,
                    features_snapshot={
                        "delta_real_yield_1w": (brief.get("current_market_state") or {})
                        .get("factor_states", {})
                        .get("real_yield_10y", {})
                        .get("weekly_delta_bps", 0)
                        / 100.0,
                    },
                )
                print("[ok] shadow log appended")
            except Exception as exc:
                print(f"[warn] shadow log skipped: {exc}")

        telegram_result = {"skipped": True}
        if not args.dry_run and not args.skip_telegram:
            notifier = TelegramNotifier()
            telegram_result = notifier.send_brief(brief, dashboard_url=dashboard_url)
            if telegram_result.get("ok"):
                print("[ok] Telegram brief sent")
            elif telegram_result.get("skipped"):
                print(f"[warn] Telegram skipped: {telegram_result.get('reason')}")
            else:
                print(f"[warn] Telegram failed: {telegram_result}")

        status.update({
            "ok": True,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "brief_path": str(path),
            "observation_week": brief.get("observation_week"),
            "stance": brief.get("taxonomy_stance"),
            "telegram": telegram_result,
            "dashboard_url": dashboard_url or None,
        })
    except Exception as exc:
        status.update({
            "ok": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": f"{type(exc).__name__}: {exc}",
        })
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        RUN_LOG.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(f"[FAIL] {status['error']}")
        return 1

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
