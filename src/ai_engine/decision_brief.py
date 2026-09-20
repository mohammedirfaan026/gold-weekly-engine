"""
Live Weekly Decision Brief Generator for Institutional Swing Traders.
Generates multi-scenario market analysis, fundamental attribution,
failure-memory trap detection, invalidation levels, and strict no-trade circuit breakers.
Strictly adheres to non-prescriptive, conservative institutional terminology.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from .confidence_calibrator import ConfidenceCalibrator
from .no_trade_filter import NoTradeFilter
from .data_freshness import DataFreshnessChecker


class WeeklyDecisionBrief:
    """Orchestrates comprehensive discretionary swing-trading decision briefs."""

    def __init__(self):
        self.calibrator = ConfidenceCalibrator()
        self.no_trade_filter = NoTradeFilter()
        self.freshness_checker = DataFreshnessChecker()

    def generate_brief(
        self,
        prediction: Dict[str, Any],
        recursive_data: Optional[Dict[str, Any]] = None,
        features_dict: Optional[Dict[str, float]] = None,
        freshness_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes model predictions, recursive state, and safety filters
        into a structured institutional weekly decision briefing.
        """
        f_dict = features_dict or {}
        price = float(prediction.get("current_gold_price", 0.0))
        bias_res = prediction.get("ai_weekly_bias", {})
        raw_bias = float(bias_res.get("bias_score", 0.0))

        # Use recursive bias score if available
        if recursive_data and "recursive_bias_score" in recursive_data:
            bias_score = float(recursive_data["recursive_bias_score"])
            exp_ret_pct = float(recursive_data.get("recursive_expected_return", 0.0)) * 100.0
            corridor_high = float(recursive_data.get("corridor_high", price * 1.02))
            corridor_low = float(recursive_data.get("corridor_low", price * 0.98))
        else:
            bias_score = raw_bias
            exp_ret_pct = float(bias_res.get("expected_weekly_return_pct", 0.0))
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
        failure_memory_info = recursive_data.get("prior_week_post_mortem") if recursive_data else None
        fail_mem_summary = {
            "failure_similarity_score": recursive_data.get("failure_similarity_score", 0.0) if recursive_data else 0.0,
            "reflexive_warning_active": recursive_data.get("reflexive_warning_active", False) if recursive_data else False,
            "matching_failure_archetype": recursive_data.get("matching_failure_archetype", "NONE") if recursive_data else "NONE",
        }

        # No-Trade filter
        no_trade_eval = self.no_trade_filter.evaluate(
            bias_score=bias_score,
            features_dict=f_dict,
            failure_memory_data=fail_mem_summary,
            freshness_data=freshness_report,
        )

        # Conservative UI Taxonomy
        if not freshness_report.get("is_usable", True):
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
            bull_invalidation = corridor_high
            bear_invalidation = corridor_low  # Dropping below support invalidates bullish thesis
            invalidation_level = corridor_low
            invalidation_note = f"Weekly close below ${corridor_low:,.2f} invalidates the bullish thesis."
        elif direction == "BEARISH":
            bull_invalidation = corridor_high  # Rallying above resistance invalidates bearish thesis
            bear_invalidation = corridor_low
            invalidation_level = corridor_high
            invalidation_note = f"Weekly close above ${corridor_high:,.2f} invalidates the bearish thesis."
        else:
            bull_invalidation = corridor_high
            bear_invalidation = corridor_low
            invalidation_level = price
            invalidation_note = "No directional thesis active. Both corridor boundaries serve as breakout boundaries."

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
                "title": "Bullish Invalidation / Breakout Scenario",
                "trigger_level": f"${corridor_high:,.2f}",
                "narrative": (
                    f"A sustained breach above ${corridor_high:,.2f} (+{(corridor_high/price - 1)*100:.1f}%) "
                    f"indicates sovereign accumulation or unexpected safe-haven escalation, overriding macro model bounds."
                ),
            },
            "bearish_invalidation_breakdown": {
                "title": "Bearish Invalidation / Breakdown Scenario",
                "trigger_level": f"${corridor_low:,.2f}",
                "narrative": (
                    f"A breakdown below ${corridor_low:,.2f} ({(corridor_low/price - 1)*100:.1f}%) "
                    f"signals aggressive real-yield steepening or dollar short-squeeze liquidation."
                ),
            },
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

        return {
            "observation_week": prediction.get("observation_week"),
            "prediction_timestamp": prediction.get("prediction_timestamp"),
            "current_gold_price": price,
            "taxonomy_stance": taxonomy_stance,
            "directional_bias": direction,
            "bias_score": round(bias_score, 3),
            "confidence_calibration": calibration,
            "expected_return_pct": round(exp_ret_pct, 2),
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
            "factor_states": factor_states,
            "failure_memory": fail_mem_summary,
            "no_trade_circuit_breaker": no_trade_eval,
            "data_freshness": freshness_report,
        }

    def render_markdown(self, brief: Dict[str, Any]) -> str:
        """Formats the brief as an institutional executive Markdown report."""
        cal = brief["confidence_calibration"]
        corr = brief["expected_corridor"]
        nt = brief["no_trade_circuit_breaker"]
        mem = brief["failure_memory"]
        fac = brief["factor_states"]
        scen = brief["scenarios"]
        fresh = brief["data_freshness"]

        lines = [
            "================================================================================",
            "                GOLD WEEKLY AI -- INSTITUTIONAL DECISION BRIEF",
            "================================================================================",
            f"Observation Week     : {brief['observation_week']}",
            f"Prediction Cutoff    : {brief['prediction_timestamp']}",
            f"Spot Gold Reference : ${brief['current_gold_price']:,.2f}",
            "",
            "--------------------------------------------------------------------------------",
            "1. EXECUTIVE STANCE & DIRECTIONAL TAXONOMY",
            "--------------------------------------------------------------------------------",
            f"  Tactical Stance       : **{brief['taxonomy_stance']}**",
            f"  Directional Bias      : {brief['directional_bias']}",
            f"  Bias Score            : {brief['bias_score']:+.3f} (Magnitude: {cal['bias_magnitude']:.3f})",
            f"  Calibrated Confidence : **{cal['tier']} CONFIDENCE** ({cal['bias_range']})",
            f"  Empirical Win Rate    : {cal['empirical_win_rate_pct']:.1f}% (Historical Walk-Forward)",
            f"  Empirical Sharpe      : {cal['empirical_sharpe']:.2f} (Sample: {cal['historical_sample_trades']} weeks)",
            f"  Expected Return       : {brief['expected_return_pct']:+.2f}%",
            f"  Trader Guidance       : {cal['trader_guidance']}",
            "",
            "--------------------------------------------------------------------------------",
            "2. PRICE VOLATILITY CORRIDOR (10th - 90th PERCENTILE)",
            "--------------------------------------------------------------------------------",
            f"  Upper Resistance (90%): ${corr['upper_resistance_90pct']:,.2f} ({(corr['upper_resistance_90pct']/brief['current_gold_price'] - 1)*100:+.2f}%)",
            f"  Expected Center       : ${corr['expected_center']:,.2f}",
            f"  Lower Support (10%)   : ${corr['lower_support_10pct']:,.2f} ({(corr['lower_support_10pct']/brief['current_gold_price'] - 1)*100:+.2f}%)",
            f"  Expected Corridor Band: ${corr['corridor_width_dollar']:,.2f} ({corr['corridor_width_pct']:.2f}% wide)",
            f"  Corridor Containment  : {cal['corridor_containment_pct']:.1f}% historical containment probability",
            "",
            "--------------------------------------------------------------------------------",
            "3. MACRO & CROSS-ASSET FACTOR ATTRIBUTION",
            "--------------------------------------------------------------------------------",
            f"  * 10Y Real Yield (TIPS): {fac['real_yield_10y']['state']} (1w change: {fac['real_yield_10y']['weekly_delta_bps']:+.1f} bps)",
            f"  * US Dollar (DXY)      : {fac['us_dollar_dxy']['state']} (1w return: {fac['us_dollar_dxy']['weekly_return_pct']:+.2f}%)",
            f"  * Market Risk (VIX)    : {fac['market_risk_vix']['state']} (Level: {fac['market_risk_vix']['vix_level']:.1f})",
            f"  * Gold Trend (20w MA)  : {fac['gold_trend']['state']} (Distance: {fac['gold_trend']['distance_20w_pct']:+.2f}%)",
            "",
            "--------------------------------------------------------------------------------",
            "4. REFLEXIVE FAILURE-MEMORY TRAP DETECTOR",
            "--------------------------------------------------------------------------------",
            f"  Nearest Failure Archetype: {mem['matching_failure_archetype']}",
            f"  Similarity to Trap       : {mem['failure_similarity_score'] * 100:.1f}%",
            f"  Reflexive Trap Warning   : {'ACTIVE (Corridor widened, confidence reduced)' if mem['reflexive_warning_active'] else 'INACTIVE (Setup within normal distribution)'}",
            "",
            "--------------------------------------------------------------------------------",
            "5. STRICT 'DO NOT TRADE' CIRCUIT BREAKER",
            "--------------------------------------------------------------------------------",
            f"  Circuit Breaker Status   : **{nt['status_label']}**",
            f"  Active Risk Triggers     : {nt['trigger_count']}",
        ]

        if nt["triggers"]:
            for t in nt["triggers"]:
                lines.append(f"    - [{t['severity']}] {t['code']}: {t['reason']}")
        else:
            lines.append("    - No risk circuit breakers tripped. Multi-factor alignment confirmed.")

        lines.extend([
            f"  Action Recommendation    : {nt['action_guidance']}",
            "",
            "--------------------------------------------------------------------------------",
            "6. SCENARIO MAP & INVALIDATION THRESHOLDS",
            "--------------------------------------------------------------------------------",
            f"  * [BASE CASE]: {scen['base_case']['trajectory']}",
            f"  * [BULL BREAKOUT]: {scen['bullish_invalidation_breakout']['narrative']}",
            f"  * [BEAR BREAKDOWN]: {scen['bearish_invalidation_breakdown']['narrative']}",
            f"  * [INVALIDATION]: {brief['invalidation']['note']}",
            "",
            "--------------------------------------------------------------------------------",
            "7. DATA FRESHNESS & VINTAGE AUDIT",
            "--------------------------------------------------------------------------------",
            f"  Pipeline Health : {'OPERATIONAL' if fresh['is_usable'] else 'DEGRADED'}",
            f"  Audit Cutoff    : {fresh['reference_timestamp']}",
        ])
        for s_name, s_info in fresh["series"].items():
            lines.append(f"    - `{s_name}`: age {s_info.get('lag_days', 999.0):.1f} days ({s_info.get('status', 'UNKNOWN')})")

        lines.extend([
            "================================================================================",
            "DISCLAIMER: For institutional research & discretionary decision support only.",
            "Never execute orders solely on algorithmic outputs. Discretionary confirmation required.",
            "================================================================================",
        ])
        return "\n".join(lines)
