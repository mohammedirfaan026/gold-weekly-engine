"""
Production CLI Driver for the Gold AI Weekly Bias & Range Engine.
Generates institutional macroeconomic directional bias, expected high-low corridors,
and tail risk assessments for COMEX Gold / XAUUSD.
Supports static baseline inference and recursive self-improving adaptive learning.

Usage:
    # Predict for the latest completed trading week:
    python predict_weekly_bias.py --latest

    # Predict with recursive self-improving adaptation & post-mortem:
    python predict_weekly_bias.py --latest --recursive

    # Predict for a specific historical trading week:
    python predict_weekly_bias.py --week 2026-09-11 --recursive

    # Output machine-readable JSON:
    python predict_weekly_bias.py --latest --recursive --json

    # Run out-of-sample walk-forward validation (2018-2026):
    python predict_weekly_bias.py --evaluate-oos
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import warnings
import pandas as pd

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
warnings.filterwarnings("ignore")

from src.ai_engine.engine import GoldWeeklyBiasEngine
from src.ai_engine.recursive_learner import (
    RecursiveSelfImprovingEngine,
    FailureArchetype,
)
from src.ai_engine.data_freshness import DataFreshnessChecker
from src.ai_engine.trade_journal import TradeJournal
from src.ai_engine.decision_brief import WeeklyDecisionBrief
from src.ai_engine.no_trade_filter import NoTradeFilter
from src.ai_engine.shadow_logger import ShadowLogger
from src.ai_engine.pit_validator import PointInTimeFeatureValidator, PointInTimeViolationError


def main():
    parser = argparse.ArgumentParser(
        description="Gold AI Weekly Bias & Range Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Generate prediction for the most recent completed trading week (default)",
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Target trading week ending date in YYYY-MM-DD format (e.g. 2026-09-11)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Enable recursive self-improving learning loop, post-mortem attribution, and failure memory bank",
    )
    parser.add_argument(
        "--post-mortem",
        action="store_true",
        help="Display dedicated root-cause error forensic on the prior week's forecast",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw structured JSON instead of formatted text briefing",
    )
    parser.add_argument(
        "--evaluate-oos",
        action="store_true",
        help="Execute 8-fold purged walk-forward validation (2018-2026) and report metrics",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Generate institutional live weekly Decision Brief (with scenario map, confidence tiers, and no-trade circuit breakers)",
    )
    parser.add_argument(
        "--freshness",
        action="store_true",
        help="Display data pipeline freshness, observation cutoffs, and publication lag audit",
    )
    parser.add_argument(
        "--no-trade-check",
        action="store_true",
        help="Run standalone evaluation of Do-Not-Trade circuit breakers",
    )
    parser.add_argument(
        "--journal-history",
        action="store_true",
        help="Display complete history of logged discretionary trader decisions",
    )
    parser.add_argument(
        "--journal-stats",
        action="store_true",
        help="Display decision quality metrics comparing Follow vs Override performance",
    )
    parser.add_argument(
        "--journal-log",
        action="store_true",
        help="Log a discretionary decision for the current week into the trade journal",
    )
    parser.add_argument(
        "--decision",
        type=str,
        default="FOLLOW",
        choices=["FOLLOW", "FADE", "PASS", "OVERRIDE"],
        help="Trader decision for journal logging (FOLLOW, FADE, PASS, OVERRIDE)",
    )
    parser.add_argument(
        "--rationale",
        type=str,
        default="",
        help="Rationale or notes for discretionary override",
    )
    parser.add_argument(
        "--shadow-save",
        action="store_true",
        help="Log current prediction into immutable forward shadow-testing record (data/shadow/shadow_log.jsonl)",
    )
    parser.add_argument(
        "--shadow-report",
        action="store_true",
        help="Display forward shadow-testing performance audit report",
    )
    parser.add_argument(
        "--no-strict-pit",
        action="store_true",
        help="Disable strict point-in-time and data freshness fail-closed exceptions (warning only)",
    )
    parser.add_argument(
        "--news",
        action="store_true",
        help="Fetch live news only and print gold/macro intelligence (no full brief)",
    )
    parser.add_argument(
        "--no-news",
        action="store_true",
        help="Skip auto news fetch when generating --brief (model/macro only)",
    )

    args = parser.parse_args()

    if args.news:
        from src.ingestion.news_feed import NewsFeedIngestor
        intel = NewsFeedIngestor().build_intelligence(force_refresh=True)
        print("\n" + "=" * 80)
        print("          GOLD AI ENGINE: LIVE NEWS / GEOPOLITICS / FED FEED")
        print("=" * 80)
        print(f"Fetched at UTC       : {intel.get('fetched_at_utc')}")
        print(f"Headlines            : {intel.get('item_count')}")
        print(f"Risk flags           : {', '.join(intel.get('risk_flags') or [])}")
        size = intel.get("suggested_position_size") or {}
        print(f"Suggested size       : {size.get('label')} -- {size.get('rationale')}")
        print(f"Narrative            : {intel.get('narrative_summary')}")
        print("Top headlines:")
        for h in (intel.get("top_headlines") or [])[:12]:
            print(f"  - [{h.get('category')}|{h.get('tone')}] {h.get('title')} ({h.get('source')})")
        print("Feed health:")
        for name, status in (intel.get("source_status") or {}).items():
            print(f"  - {name}: {status}")
        print("=" * 80 + "\n")
        return

    if args.shadow_report:
        sl = ShadowLogger()
        print("\n" + sl.generate_shadow_report() + "\n")
        return

    if args.freshness:
        fc = DataFreshnessChecker()
        rep = fc.check_freshness()
        print("\n" + "=" * 80)
        print("          GOLD AI ENGINE: DATA PIPELINE FRESHNESS & VINTAGE AUDIT")
        print("=" * 80)
        print(fc.format_freshness_table(rep))
        print("=" * 80 + "\n")
        return

    if args.journal_history:
        tj = TradeJournal()
        df = tj.get_history()
        print("\n" + "=" * 80)
        print("          DISCRETIONARY TRADER DECISION JOURNAL: AUDIT LOG")
        print("=" * 80)
        if df.empty:
            print("No decisions logged yet. Use --journal-log with --brief to log a trade.")
        else:
            print(df.to_string(index=False))
        print("=" * 80 + "\n")
        return

    if args.journal_stats:
        tj = TradeJournal()
        stats = tj.compute_quality_stats()
        print("\n" + "=" * 80)
        print("          DECISION QUALITY: TRADER VS. MODEL AUDIT METRICS")
        print("=" * 80)
        print(json.dumps(stats, indent=2))
        print("=" * 80 + "\n")
        return

    engine = GoldWeeklyBiasEngine()
    engine.load_data()
    engine.fit()

    if args.evaluate_oos:
        print("\nExecuting Out-of-Sample Walk-Forward Validation (2018-2026)...")
        eval_df = engine.evaluate_oos_walk_forward()
        print("\n" + "=" * 80)
        print("          AI WEEKLY BIAS ENGINE: OUT-OF-SAMPLE PERFORMANCE (2018-2026)")
        print("=" * 80)
        print(eval_df.to_string(index=False))
        print("=" * 80 + "\n")
        return

    target_week = args.week if args.week else None
    prediction = engine.predict_week(week_ending=target_week)

    # If recursive self-improvement, brief, or no-trade check is requested
    post_mortem_data = None
    recursive_data = None
    matrix = engine.matrix
    if target_week is None:
        target_idx = len(matrix) - 1
    else:
        matches = matrix[matrix["week_ending"] == target_week]
        target_idx = matches.index[0]

    prior_idx = max(0, target_idx - 1)
    train_matrix = matrix.iloc[:prior_idx].copy()
    prior_row = matrix.iloc[prior_idx]
    current_row = matrix.iloc[target_idx]

    # Point-in-Time & Freshness verification
    strict_pit = not args.no_strict_pit
    fc = DataFreshnessChecker()
    fresh_rep = fc.check_freshness(as_of_date=target_week)

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
            print(f"\n[FAIL-CLOSED POINT-IN-TIME VIOLATION]: {e}")
            print("System halted in fail-closed mode. Stance: Data quality failure -- do not use.\n")
            sys.exit(1)
        pit_rep = {"is_valid": False, "violation_count": 1, "violations": [str(e)]}

    if strict_pit and not fresh_rep.get("is_usable", True):
        print("\n[FAIL-CLOSED DATA QUALITY VIOLATION]: Critical market/macro series failed freshness audit.")
        print(fc.format_freshness_table(fresh_rep))
        print("System halted in fail-closed mode. Stance: Data quality failure -- do not use.\n")
        sys.exit(1)

    curr_features = {
        "delta_real_yield_1w": float(current_row.get("delta_real_yield_1w", 0.0)),
        "dxy_return_1w": float(current_row.get("dxy_return_1w", 0.0)),
        "delta_breakeven_1w": float(current_row.get("delta_breakeven_1w", 0.0)),
        "gold_distance_20w": float(current_row.get("gold_distance_20w", 0.0)),
        "vix": float(current_row.get("vix", 15.0)),
    }

    if args.recursive or args.post_mortem or args.brief or args.no_trade_check:
        rec_engine = RecursiveSelfImprovingEngine()
        rec_engine.initialize(train_matrix)

        prior_features = {
            "delta_real_yield_1w": float(prior_row.get("delta_real_yield_1w", 0.0)),
            "dxy_return_1w": float(prior_row.get("dxy_return_1w", 0.0)),
            "delta_breakeven_1w": float(prior_row.get("delta_breakeven_1w", 0.0)),
            "gold_distance_20w": float(prior_row.get("gold_distance_20w", 0.0)),
            "vix": float(prior_row.get("vix", 15.0)),
        }

        prior_price = float(prior_row["gold_close"])
        rec_engine.predict_upcoming_week(
            week=str(prior_row["week_ending"]),
            current_features_dict=prior_features,
            current_gold_price=prior_price,
            baseline_corridor_high=prior_price * 1.025,
            baseline_corridor_low=prior_price * 0.975,
        )

        realized_prior_ret = float(current_row["gold_close"] / prior_row["gold_close"] - 1.0)
        post_mortem_data = rec_engine.process_prior_week_outcome(
            week=str(prior_row["week_ending"]),
            features_dict=prior_features,
            realized_return=realized_prior_ret,
            actual_price=float(current_row["gold_close"]),
        )

        recursive_data = rec_engine.predict_upcoming_week(
            week=str(current_row["week_ending"]),
            current_features_dict=curr_features,
            current_gold_price=float(current_row["gold_close"]),
            baseline_corridor_high=prediction["expected_price_corridor"]["expected_high_90pct"],
            baseline_corridor_low=prediction["expected_price_corridor"]["expected_low_10pct"],
        )

        prediction["recursive_self_improvement"] = {
            "prior_week_post_mortem": post_mortem_data,
            "adaptive_forecast": recursive_data,
        }

    # Handle --no-trade-check
    if args.no_trade_check:
        nt_filter = NoTradeFilter()
        fail_summary = {
            "failure_similarity_score": recursive_data.get("failure_similarity_score", 0.0) if recursive_data else 0.0,
            "reflexive_warning_active": recursive_data.get("reflexive_warning_active", False) if recursive_data else False,
            "matching_failure_archetype": recursive_data.get("matching_failure_archetype", "NONE") if recursive_data else "NONE",
        }
        bias_to_check = recursive_data["recursive_bias_score"] if recursive_data else prediction["ai_weekly_bias"]["bias_score"]
        eval_res = nt_filter.evaluate(
            bias_score=bias_to_check,
            features_dict=curr_features,
            failure_memory_data=fail_summary,
            freshness_data=fresh_rep,
            pit_validation_data=pit_rep,
        )
        print("\n" + "=" * 80)
        print("          GOLD AI ENGINE: DO-NOT-TRADE CIRCUIT BREAKER STATUS")
        print("=" * 80)
        print(f"Status              : {eval_res['status_label']}")
        print(f"Action Guidance     : {eval_res['action_guidance']}")
        print(f"Active Triggers     : {eval_res['trigger_count']}")
        for t in eval_res["triggers"]:
            print(f"  - [{t['severity']}] {t['code']}: {t['reason']}")
        print("=" * 80 + "\n")
        return

    # Handle --brief or --shadow-save
    brief_dict = None
    if args.brief or args.shadow_save:
        brief_gen = WeeklyDecisionBrief()
        brief_dict = brief_gen.generate_brief(
            prediction=prediction,
            recursive_data=recursive_data,
            features_dict=curr_features,
            freshness_report=fresh_rep,
            pit_validation_report=pit_rep,
            save_file=args.brief,
            fetch_news=not args.no_news,
        )

    if args.shadow_save and brief_dict:
        sl = ShadowLogger()
        try:
            shadow_rec = sl.save_prediction(
                brief=brief_dict,
                features_snapshot=curr_features,
            )
            print(f"\n[SHADOW-TEST RECORDED]: Week {shadow_rec['prediction_week']} logged to data/shadow/shadow_log.jsonl")
            print(f"  Feature Vintage Hash : {shadow_rec['feature_vintage_hash']}")
            print(f"  Tactical Stance      : {shadow_rec['stance']}")
            print(f"  Confidence Tier      : {shadow_rec['confidence_tier']}")
            print(f"  Logged Timestamp     : {shadow_rec['logged_at_utc']}\n")
        except ValueError as e:
            print(f"\n[SHADOW-LOGGER IMMUTABILITY WARNING]: {e}\n")

    if args.brief:
        if args.journal_log:
            tj = TradeJournal()
            cal = brief_dict["confidence_calibration"]
            nt = brief_dict["no_trade_circuit_breaker"]
            entry = tj.log_decision(
                week_ending=str(brief_dict["observation_week"]),
                gold_price=brief_dict["current_gold_price"],
                model_bias_score=brief_dict["bias_score"],
                confidence_tier=cal["tier"],
                no_trade_triggered=nt["is_no_trade"],
                trader_decision=args.decision,
                override_rationale=args.rationale,
                planned_entry=brief_dict["current_gold_price"],
                planned_stop=brief_dict["invalidation"]["level"],
                planned_target=brief_dict["expected_corridor"]["expected_center"],
                no_trade_triggers=[t["code"] for t in nt["triggers"]],
            )
            print(f"\n[JOURNAL LOGGED]: Entry {entry['entry_id']} recorded to data/journal/trade_journal.csv")

        if args.json:
            print(json.dumps(brief_dict, indent=2))
        else:
            print(WeeklyDecisionBrief().render_markdown(brief_dict))
        return

    if args.json:
        print(json.dumps(prediction, indent=2))
    else:
        briefing = engine.format_briefing(prediction)
        if args.recursive and recursive_data and post_mortem_data:
            rec_lines = [
                "",
                "--- 6. RECURSIVE SELF-IMPROVEMENT & ADAPTIVE STATE ---",
                f"  Prior Week Evaluated   : Week {post_mortem_data['week_evaluated']}",
                f"  Prior Forecast Error   : {post_mortem_data['error']:+.2f}% (Predicted: {post_mortem_data['predicted_return']:+.2f}%, Realized: {post_mortem_data['realized_return']:+.2f}%)",
                f"  Failure Archetype      : {post_mortem_data['archetype']}",
                f"  Root Cause Diagnostic  : {post_mortem_data['primary_cause']}",
                "  Adaptive Kalman Betas  :",
                f"    * Intercept (alpha)  : {recursive_data['current_weights']['intercept']:+.4f}",
                f"    * Yield Sensitivity  : {recursive_data['current_weights']['beta_real_yield']:+.4f}",
                f"    * DXY Sensitivity    : {recursive_data['current_weights']['beta_dxy']:+.4f}",
                f"    * Trend Sensitivity  : {recursive_data['current_weights']['beta_trend_20w']:+.4f}",
                "  Failure Memory Bank    :",
                f"    * Max Sim to Failures: {recursive_data['failure_similarity_score'] * 100:.1f}% (Archetype: {recursive_data['matching_failure_archetype']})",
                f"    * Reflexive Warning  : {'ACTIVE (Hedge Applied)' if recursive_data['reflexive_warning_active'] else 'INACTIVE (Setup in Normal Distribution)'}",
                f"  Adaptive Bias Score    : {recursive_data['recursive_bias_score']:+.3f} ({recursive_data['recursive_bias_category']})",
                f"  Adaptive Range Bounds  : ${recursive_data['corridor_low']:,.2f} to ${recursive_data['corridor_high']:,.2f} (Width: ${recursive_data['corridor_width_dollar']:,.2f})",
                "================================================================================",
            ]
            briefing = briefing[:-80] + "\n".join(rec_lines)
        print(briefing)


if __name__ == "__main__":
    main()
