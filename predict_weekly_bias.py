"""
Production CLI Driver for the Gold AI Weekly Bias & Range Engine.
Generates institutional macroeconomic directional bias, expected high-low corridors,
and tail risk assessments for COMEX Gold / XAUUSD.

Usage:
    # Predict for the latest completed trading week:
    python predict_weekly_bias.py --latest

    # Predict for a specific historical trading week:
    python predict_weekly_bias.py --week 2026-09-11

    # Output machine-readable JSON:
    python predict_weekly_bias.py --latest --json

    # Run out-of-sample walk-forward validation (2018-2026):
    python predict_weekly_bias.py --evaluate-oos
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import warnings

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
warnings.filterwarnings("ignore")

from src.ai_engine.engine import GoldWeeklyBiasEngine


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

    if args.json:
        print(json.dumps(prediction, indent=2))
    else:
        briefing = engine.format_briefing(prediction)
        print(briefing)


if __name__ == "__main__":
    main()
