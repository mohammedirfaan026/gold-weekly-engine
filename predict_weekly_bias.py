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

    args = parser.parse_args()

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

    # If recursive self-improvement is requested
    post_mortem_data = None
    recursive_data = None

    if args.recursive or args.post_mortem:
        matrix = engine.matrix
        if target_week is None:
            target_idx = len(matrix) - 1
        else:
            matches = matrix[matrix["week_ending"] == target_week]
            target_idx = matches.index[0]

        # Prior week index
        prior_idx = target_idx - 1
        train_matrix = matrix.iloc[:prior_idx].copy()
        prior_row = matrix.iloc[prior_idx]
        current_row = matrix.iloc[target_idx]

        rec_engine = RecursiveSelfImprovingEngine()
        rec_engine.initialize(train_matrix)

        # Baseline predictions for prior week
        prior_features = {
            "delta_real_yield_1w": float(prior_row.get("delta_real_yield_1w", 0.0)),
            "dxy_return_1w": float(prior_row.get("dxy_return_1w", 0.0)),
            "delta_breakeven_1w": float(prior_row.get("delta_breakeven_1w", 0.0)),
            "gold_distance_20w": float(prior_row.get("gold_distance_20w", 0.0)),
            "vix": float(prior_row.get("vix", 15.0)),
        }

        # Warm up last_prediction with baseline
        prior_price = float(prior_row["gold_close"])
        rec_engine.predict_upcoming_week(
            week=str(prior_row["week_ending"]),
            current_features_dict=prior_features,
            current_gold_price=prior_price,
            baseline_corridor_high=prior_price * 1.025,
            baseline_corridor_low=prior_price * 0.975,
        )

        # Evaluate outcome of prior week
        realized_prior_ret = float(current_row["gold_close"] / prior_row["gold_close"] - 1.0)
        post_mortem_data = rec_engine.process_prior_week_outcome(
            week=str(prior_row["week_ending"]),
            features_dict=prior_features,
            realized_return=realized_prior_ret,
            actual_price=float(current_row["gold_close"]),
        )

        # Generate recursive prediction for current target week
        curr_features = {
            "delta_real_yield_1w": float(current_row.get("delta_real_yield_1w", 0.0)),
            "dxy_return_1w": float(current_row.get("dxy_return_1w", 0.0)),
            "delta_breakeven_1w": float(current_row.get("delta_breakeven_1w", 0.0)),
            "gold_distance_20w": float(current_row.get("gold_distance_20w", 0.0)),
            "vix": float(current_row.get("vix", 15.0)),
        }
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
