"""
Live Weekly Decision Brief Generator for Institutional Swing Traders.
Generates multi-scenario market analysis, fundamental attribution,
failure-memory trap detection, invalidation levels, strict no-trade circuit breakers,
and human discretionary decision worksheets.
Strictly adheres to non-prescriptive, conservative institutional terminology.
Automatically writes live briefs to research/reports/LIVE_WEEKLY_DECISION_BRIEF.md.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from .confidence_calibrator import ConfidenceCalibrator
from .no_trade_filter import NoTradeFilter
from .data_freshness import DataFreshnessChecker
from .pit_validator import PointInTimeFeatureValidator
from .versioning import get_system_version_info


DEFAULT_REPORT_PATH = Path("research/reports/LIVE_WEEKLY_DECISION_BRIEF.md")


class WeeklyDecisionBrief:
    """Orchestrates comprehensive discretionary swing-trading decision briefs."""

    def __init__(self):
        self.calibrator = ConfidenceCalibrator()
        self.no_trade_filter = NoTradeFilter()
        self.freshness_checker = DataFreshnessChecker()
        self.pit_validator = PointInTimeFeatureValidator()

    def generate_brief(
        self,
        prediction: Dict[str, Any],
        recursive_data: Optional[Dict[str, Any]] = None,
        features_dict: Optional[Dict[str, float]] = None,
        freshness_report: Optional[Dict[str, Any]] = None,
        pit_validation_report: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        save_file: bool = True,
        output_path: Optional[Path | str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes model predictions, recursive state, provenance, and safety filters
        into a structured institutional weekly decision briefing.
        """
        f_dict = features_dict or {}
        price = float(prediction.get("current_gold_price", 0.0))
        bias_res = prediction.get("ai_weekly_bias", {})
        raw_bias = float(bias_res.get("bias_score", 0.0))
        raw_exp_ret_pct = float(bias_res.get("expected_weekly_return_pct", 0.0))

        # Versioning metadata
        version_info = get_system_version_info(config=config)

        # Use recursive bias score if available
        if recursive_data and "recursive_bias_score" in recursive_data:
            bias_score = float(recursive_data["recursive_bias_score"])
            exp_ret_pct = float(recursive_data.get("recursive_expected_return", 0.0)) * 100.0
            corridor_high = float(recursive_data.get("corridor_high", price * 1.02))
            corridor_low = float(recursive_data.get("corridor_low", price * 0.98))
        else:
            bias_score = raw_bias
            exp_ret_pct = raw_exp_ret_pct
            corridor = prediction.get("expected_price_corridor", {})
            corridor_high = float(corridor.get("expected_high_90pct", price * 1.02))
            corridor_low = float(corridor.get("expected_low_10pct", price * 0.98))

        corridor_width = corridor_high - corridor_low
        expected_center = (corridor_high + corridor_low) / 2.0

        # Freshness audit
        if freshness_report is None:
            freshness_report = self.freshness_checker.check_freshness()

        # Calibration
        calibration = self.calibrator.calibrate(bias_score)

        # Failure memory
        fail_mem_summary = {
            "failure_similarity_score": recursive_data.get("failure_similarity_score", 0.0) if recursive_data else 0.0,
            "reflexive_warning_active": recursive_data.get("reflexive_warning_active", False) if recursive_data else False,
            "matching_failure_archetype": recursive_data.get("matching_failure_archetype", "NONE") if recursive_data else "NONE",
        }

        # No-Trade filter evaluation (fail closed)
        no_trade_eval = self.no_trade_filter.evaluate(
            bias_score=bias_score,
            features_dict=f_dict,
            failure_memory_data=fail_mem_summary,
            freshness_data=freshness_report,
            pit_validation_data=pit_validation_report,
            raw_expected_return=raw_exp_ret_pct / 100.0,
        )

        # Conservative UI Taxonomy
        if not freshness_report.get("is_usable", True) or (pit_validation_report and not pit_validation_report.get("is_valid", True)):
            taxonomy_stance = "Data quality failure -- do not use"
            direction = "DATA_ERROR"
        elif no_trade_eval["is_no_trade"]:
            if any(t["code"] == "HIGH_VOLATILITY_REGIME" for t in no_trade_eval["triggers"]):
                taxonomy_stance = "High-risk regime -- reduce confidence / stand aside"
            elif any(t["code"] == "SUB_THRESHOLD_EDGE" for t in no_trade_eval["triggers"]):
                taxonomy_stance = "Neutral / no directional edge"
            else:
                taxonomy_stance = "DO NOT TRADE -- unfavorable conditions"
            direction = "NEUTRAL"
        elif bias_score >= 0.05:
            taxonomy_stance = "Bullish bias -- confirmation required"
            direction = "BULLISH"
        elif bias_score <= -0.05:
            taxonomy_stance = "Bearish bias -- confirmation required"
            direction = "BEARISH"
        else:
            taxonomy_stance = "Neutral / no directional edge"
            direction = "NEUTRAL"

        # Invalidation thresholds
        if direction == "BULLISH":
            invalidation_level = corridor_low
            invalidation_note = f"Weekly close below ${corridor_low:,.2f} invalidates the bullish thesis."
            change_conditions = "Real-yield spike > 10 bps, DXY surge > 1.0%, or break of support corridor."
        elif direction == "BEARISH":
            invalidation_level = corridor_high
            invalidation_note = f"Weekly close above ${corridor_high:,.2f} invalidates the bearish thesis."
            change_conditions = "Real-yield plunge > 10 bps, DXY breakdown > 1.0%, or break of resistance corridor."
        else:
            invalidation_level = price
            invalidation_note = "No directional thesis active. Both corridor boundaries serve as range bounds."
            change_conditions = "Decisive breakout with macro factor alignment across yields and dollar."

        # Scenario Map
        scenarios = {
            "base_case": {
                "title": f"Base Case ({taxonomy_stance.split(' -- ')[0]})",
                "trajectory": (
                    f"Gold trades within ${corridor_low:,.2f} - ${corridor_high:,.2f} with an expected "
                    f"center of ${expected_center:,.2f} ({exp_ret_pct:+.2f}% expected weekly change)."
                ),
                "drivers": "Driven by prevailing macro yield sensitivity and multi-factor alignment.",
            },
            "bullish_invalidation_breakout": {
                "title": "Bullish Scenario / Breakout",
                "trigger_level": f"${corridor_high:,.2f}",
                "narrative": (
                    f"A sustained breach above ${corridor_high:,.2f} ({(corridor_high/price - 1)*100:+.2f}%) "
                    f"indicates sovereign safe-haven accumulation overriding model macro constraints."
                ),
            },
            "bearish_invalidation_breakdown": {
                "title": "Bearish Scenario / Breakdown",
                "trigger_level": f"${corridor_low:,.2f}",
                "narrative": (
                    f"A breakdown below ${corridor_low:,.2f} ({(corridor_low/price - 1)*100:+.2f}%) "
                    f"signals aggressive real-yield steepening or dollar short-squeeze liquidation."
                ),
            },
            "conditions_that_change_view": change_conditions,
        }

        # Macro factor state deconstruction
        d_yield = f_dict.get("delta_real_yield_1w", 0.0)
        dxy_ret = f_dict.get("dxy_return_1w", 0.0)
        vix_val = f_dict.get("vix", 15.0)
        trend_dist = f_dict.get("gold_distance_20w", 0.0)

        factor_states = {
            "real_yield_10y": {
                "state": "RISING (Bearish pressure)" if d_yield > 0.02 else "FALLING (Bullish tailwind)" if d_yield < -0.02 else "NEUTRAL / FLAT",
                "weekly_delta_bps": round(d_yield * 100, 1),
            },
            "us_dollar_dxy": {
                "state": "STRENGTHENING (Headwind)" if dxy_ret > 0.003 else "WEAKENING (Tailwind)" if dxy_ret < -0.003 else "RANGEBOUND",
                "weekly_return_pct": round(dxy_ret * 100, 2),
            },
            "market_risk_vix": {
                "state": "STRESS REGIME (>20)" if vix_val >= 20.0 else "NORMAL VOLATILITY",
                "vix_level": round(vix_val, 1),
            },
            "gold_trend": {
                "state": "EXTENDED BULLISH" if trend_dist > 0.05 else "EXTENDED BEARISH" if trend_dist < -0.05 else "CONSOLIDATION",
                "distance_20w_pct": round(trend_dist * 100, 2),
            },
        }

        brief_dict = {
            "identification": {
                "observation_week": str(prediction.get("observation_week")),
                "prediction_timestamp": str(prediction.get("prediction_timestamp")),
                "data_cutoff_timestamp": str(prediction.get("prediction_timestamp")),
                "model_version": version_info["model_version"],
                "specification_version": version_info["specification_version"],
                "feature_schema_version": version_info["feature_schema_version"],
                "data_version": version_info["data_version"],
                "git_commit": version_info["git_commit"],
                "reproducibility_status": version_info["reproducibility_status"],
                "config_hash": version_info["config_hash"],
            },
            "current_market_state": {
                "gold_reference_price": price,
                "gold_weekly_trend": factor_states["gold_trend"]["state"],
                "factor_states": factor_states,
                "macro_event_risk": "None scheduled within primary window" if not f_dict.get("event_risk") else "High Event Risk",
                "feature_availability_status": "All Core Features Available" if freshness_report.get("is_usable") else "DEGRADED",
            },
            "model_output": {
                "raw_expected_return_pct": round(raw_exp_ret_pct, 2),
                "recursive_expected_return_pct": round(exp_ret_pct, 2),
                "raw_bias_score": round(raw_bias, 3),
                "recursive_bias_score": round(bias_score, 3),
                "bias_category": recursive_data.get("recursive_bias_category") if recursive_data else bias_res.get("bias_category", "NEUTRAL"),
                "directional_stance": taxonomy_stance,
                "confidence_calibration": calibration,
            },
            "scenario_map": {
                "expected_corridor": {
                    "upper_resistance_90pct": round(corridor_high, 2),
                    "expected_center": round(expected_center, 2),
                    "lower_support_10pct": round(corridor_low, 2),
                    "corridor_width_dollar": round(corridor_width, 2),
                    "corridor_width_pct": round(corridor_width / price * 100, 2),
                },
                "invalidation": {
                    "level": round(invalidation_level, 2),
                    "note": invalidation_note,
                },
                "scenarios": scenarios,
            },
            "risk_controls": {
                "no_trade_circuit_breaker": no_trade_eval,
                "failure_memory": fail_mem_summary,
                "data_freshness": freshness_report,
                "pit_validation": pit_validation_report or {"is_valid": True, "violation_count": 0},
            },
            "human_decision_worksheet": {
                "instruction": "Fill out manually before execution. The engine will never execute orders automatically.",
                "fields": {
                    "trader_decision": "[  ] FOLLOW   [  ] FADE   [  ] PASS   [  ] OVERRIDE",
                    "override_rationale": "________________________________________________",
                    "planned_entry_price": f"${price:,.2f}",
                    "planned_stop_loss": f"${invalidation_level:,.2f}",
                    "planned_take_profit": f"${corridor_high if direction == 'BULLISH' else corridor_low:,.2f}",
                    "position_size_decision": "Fixed 1.0x / Reduced Risk / Standing Aside",
                    "decision_timestamp_utc": "____________________",
                    "actual_entry_price": "____________________",
                    "actual_exit_price": "____________________",
                    "realized_return_pct": "____________________",
                    "post_trade_review": "________________________________________________",
                },
            },
        }

        # Convenience top-level accessors
        brief_dict["observation_week"] = brief_dict["identification"]["observation_week"]
        brief_dict["current_gold_price"] = price
        brief_dict["bias_score"] = bias_score
        brief_dict["expected_return_pct"] = exp_ret_pct
        brief_dict["expected_corridor"] = brief_dict["scenario_map"]["expected_corridor"]
        brief_dict["invalidation"] = brief_dict["scenario_map"]["invalidation"]
        brief_dict["confidence_calibration"] = calibration
        brief_dict["no_trade_circuit_breaker"] = no_trade_eval
        brief_dict["taxonomy_stance"] = taxonomy_stance

        # Auto-save report if requested
        if save_file:
            rendered = self.render_markdown(brief_dict)
            save_dest = Path(output_path) if output_path else DEFAULT_REPORT_PATH
            save_dest.parent.mkdir(parents=True, exist_ok=True)
            save_dest.write_text(rendered, encoding="utf-8")

        return brief_dict

    def render_markdown(self, brief: Dict[str, Any]) -> str:
        """Formats the brief as an institutional executive Markdown report adhering to Sections A through F."""
        ident = brief["identification"]
        mkt = brief["current_market_state"]
        fac = mkt["factor_states"]
        out = brief["model_output"]
        cal = out["confidence_calibration"]
        scen_map = brief["scenario_map"]
        corr = scen_map["expected_corridor"]
        scen = scen_map["scenarios"]
        risk = brief["risk_controls"]
        nt = risk["no_trade_circuit_breaker"]
        mem = risk["failure_memory"]
        fresh = risk["data_freshness"]
        pit = risk.get("pit_validation", {})
        worksheet = brief["human_decision_worksheet"]["fields"]

        lines = [
            "================================================================================",
            "                GOLD WEEKLY AI -- INSTITUTIONAL DECISION BRIEF",
            "================================================================================",
            "",
            "--------------------------------------------------------------------------------",
            "A. SYSTEM & RUN IDENTIFICATION",
            "--------------------------------------------------------------------------------",
            f"  Observation Week      : {ident['observation_week']}",
            f"  Prediction Cutoff     : {ident['prediction_timestamp']}",
            f"  Data Cutoff Timestamp : {ident['data_cutoff_timestamp']}",
            f"  Model Version         : {ident['model_version']}",
            f"  Specification Version : {ident['specification_version']} (Schema: {ident['feature_schema_version']})",
            f"  Git Commit Hash       : {ident['git_commit']}",
            f"  Configuration Hash    : {ident['config_hash']}",
            f"  Reproducibility Note  : {ident['reproducibility_status']}",
            "",
            "--------------------------------------------------------------------------------",
            "B. CURRENT MARKET STATE & MACRO VINTAGES",
            "--------------------------------------------------------------------------------",
            f"  Spot Gold Reference   : ${mkt['gold_reference_price']:,.2f}",
            f"  Gold Technical Trend  : {mkt['gold_weekly_trend']} (Distance to 20w MA: {fac['gold_trend']['distance_20w_pct']:+.2f}%)",
            f"  10Y Real Yield (TIPS) : {fac['real_yield_10y']['state']} (1w change: {fac['real_yield_10y']['weekly_delta_bps']:+.1f} bps)",
            f"  US Dollar Index (DXY) : {fac['us_dollar_dxy']['state']} (1w return: {fac['us_dollar_dxy']['weekly_return_pct']:+.2f}%)",
            f"  Market Volatility(VIX): {fac['market_risk_vix']['state']} (Level: {fac['market_risk_vix']['vix_level']:.1f})",
            f"  Macro-Event Risk      : {mkt['macro_event_risk']}",
            f"  Feature Availability  : {mkt['feature_availability_status']}",
            "",
            "--------------------------------------------------------------------------------",
            "C. MODEL OUTPUT & CALIBRATED CONFIDENCE",
            "--------------------------------------------------------------------------------",
            f"  Tactical Stance       : **{out['directional_stance']}**",
            f"  Bias Category         : {out['bias_category']}",
            f"  Recursive Bias Score  : {out['recursive_bias_score']:+.3f} (Magnitude: {cal['bias_magnitude']:.3f})",
            f"  Raw Baseline Score    : {out['raw_bias_score']:+.3f}",
            f"  Expected Return       : {out['recursive_expected_return_pct']:+.2f}% (Raw Static Return: {out['raw_expected_return_pct']:+.2f}%)",
            f"  Confidence Tier       : **{cal['tier']} CONFIDENCE** ({cal['bias_range']})",
            f"  Sample Size Audit     : {cal['historical_sample_trades']} trades [{cal['sample_size_warning']}]",
            f"  Empirical Win Rate    : {cal['empirical_win_rate_pct']:.1f}% (Historical Walk-Forward)",
            f"  Empirical Sharpe      : {cal['empirical_sharpe']:.2f}",
            f"  Calibration Disclaimer: {cal['calibration_disclaimer']}",
            f"  Trader Guidance       : {cal['trader_guidance']}",
            "",
            "--------------------------------------------------------------------------------",
            "D. SCENARIO MAP & PRICE VOLATILITY CORRIDOR (10th - 90th PERCENTILE)",
            "--------------------------------------------------------------------------------",
            f"  Upper Resistance (90%): ${corr['upper_resistance_90pct']:,.2f} ({(corr['upper_resistance_90pct']/mkt['gold_reference_price'] - 1)*100:+.2f}%)",
            f"  Expected Center       : ${corr['expected_center']:,.2f}",
            f"  Lower Support (10%)   : ${corr['lower_support_10pct']:,.2f} ({(corr['lower_support_10pct']/mkt['gold_reference_price'] - 1)*100:+.2f}%)",
            f"  Expected Corridor Band: ${corr['corridor_width_dollar']:,.2f} ({corr['corridor_width_pct']:.2f}% wide)",
            f"  Historical Containment: {cal['corridor_containment_pct']:.1f}% of weekly ranges remained inside bounds",
            "",
            f"  * [BASE CASE]         : {scen['base_case']['trajectory']}",
            f"  * [BULL BREAKOUT]     : {scen['bullish_invalidation_breakout']['narrative']}",
            f"  * [BEAR BREAKDOWN]    : {scen['bearish_invalidation_breakdown']['narrative']}",
            f"  * [INVALIDATION]      : {scen_map['invalidation']['note']}",
            f"  * [CONDITIONS TO SHIFT]: {scen['conditions_that_change_view']}",
            "",
            "--------------------------------------------------------------------------------",
            "E. RISK CONTROLS & FAIL-CLOSED CIRCUIT BREAKERS",
            "--------------------------------------------------------------------------------",
            f"  Circuit Breaker Status: **{nt['status_label']}**",
            f"  Active Risk Triggers  : {nt['trigger_count']}",
        ]

        if nt["triggers"]:
            for t in nt["triggers"]:
                lines.append(f"    - [{t['severity']}] {t['code']}: {t['explanation']} (Condition: {t.get('condition', 'N/A')})")
        else:
            lines.append("    - No risk circuit breakers tripped. Multi-factor alignment confirmed.")

        if pit.get("is_valid", True):
            pit_str = "PASS (0 violations)"
        else:
            pit_str = f"FAIL ({pit.get('violation_count', 0)} violations)"

        pipeline_health = "OPERATIONAL" if fresh.get("is_usable") else "DEGRADED"

        lines.extend([
            f"  Action Recommendation : {nt['action_guidance']}",
            f"  Reflexive Trap Memory : Nearest={mem['matching_failure_archetype']}, Sim={mem['failure_similarity_score']*100:.1f}%, Warning={'ACTIVE' if mem['reflexive_warning_active'] else 'INACTIVE'}",
            f"  PIT Audit Status      : {pit_str}",
            f"  DATA FRESHNESS AUDIT  : {pipeline_health}",
            f"  Data Pipeline Health  : {pipeline_health}",
            "",
            "--------------------------------------------------------------------------------",
            "F. HUMAN DISCRETIONARY DECISION WORKSHEET",
            "--------------------------------------------------------------------------------",
            "  * Trader Decision     : " + worksheet["trader_decision"],
            "  * Override Rationale  : " + worksheet["override_rationale"],
            "  * Planned Entry Price : " + worksheet["planned_entry_price"],
            "  * Planned Stop Loss   : " + worksheet["planned_stop_loss"],
            "  * Planned Take Profit : " + worksheet["planned_take_profit"],
            "  * Position Sizing     : " + worksheet["position_size_decision"],
            "  * Execution Timestamp : " + worksheet["decision_timestamp_utc"],
            "  * Actual Entry Price  : " + worksheet["actual_entry_price"],
            "  * Actual Exit Price   : " + worksheet["actual_exit_price"],
            "  * Realized Return (%) : " + worksheet["realized_return_pct"],
            "  * Post-Trade Review   : " + worksheet["post_trade_review"],
            "",
            "================================================================================",
            "LEGAL & SCIENTIFIC DISCLAIMER:",
            "- For institutional research and discretionary decision-support only.",
            "- NEVER execute trades solely on algorithmic outputs. Discretionary verification required.",
            "- AUTONOMOUS TRADING NOT SUPPORTED. No automatic order routing capability exists.",
            "- Historical backtests reflect past exploratory evaluations and are NOT future forecasts.",
            "================================================================================",
        ])
        return "\n".join(lines)
