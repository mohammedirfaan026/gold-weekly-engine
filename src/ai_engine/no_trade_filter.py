"""
Strict Do-Not-Trade (No-Trade) Circuit Breaker Filter for Gold AI Engine.
Enforces conservative fail-closed risk management across macro divergence,
volatility regimes, failure traps, model disagreements, and data vintage integrity.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np


class NoTradeFilter:
    """Evaluates systematic risk circuit breakers before permitting swing trading."""

    def __init__(
        self,
        bias_threshold: float = 0.05,
        vix_hard_limit: float = 25.0,
        vix_spike_pct_limit: float = 0.25,
        trap_similarity_limit: float = 0.70,
        trend_extension_limit: float = 0.12,
    ):
        self.bias_threshold = bias_threshold
        self.vix_hard_limit = vix_hard_limit
        self.vix_spike_pct_limit = vix_spike_pct_limit
        self.trap_similarity_limit = trap_similarity_limit
        self.trend_extension_limit = trend_extension_limit

    def evaluate(
        self,
        bias_score: float,
        features_dict: Dict[str, float],
        failure_memory_data: Optional[Dict[str, Any]] = None,
        freshness_data: Optional[Dict[str, Any]] = None,
        pit_validation_data: Optional[Dict[str, Any]] = None,
        raw_expected_return: Optional[float] = None,
        event_risk_active: bool = False,
        event_risk_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-factor safety checks.
        Fails closed on any critical data failure, macro conflict, or trap setup.
        """
        triggers: List[Dict[str, str]] = []
        is_data_failure = False

        # 1. Stale or Missing Data Check (Data Freshness)
        if freshness_data and not freshness_data.get("is_usable", True):
            stale = ", ".join(freshness_data.get("stale_series", []))
            crit_errors = "; ".join(freshness_data.get("critical_errors", []))
            triggers.append({
                "code": "DATA_QUALITY_FAILURE",
                "severity": "CRITICAL",
                "condition": f"Stale series: {stale or 'None'}",
                "explanation": f"Input data pipeline degraded, missing, or stale: {crit_errors or stale}.",
                "recommended_action": "REJECT SETUP: Repair data pipeline before taking any positioning.",
            })
            is_data_failure = True

        # 2. Strict Point-in-Time Vintage Check
        if pit_validation_data and not pit_validation_data.get("is_valid", True):
            viols = pit_validation_data.get("violations", [])
            summary_v = "; ".join([f"{v['feature_name']}: {v['reason']}" for v in viols[:3]])
            triggers.append({
                "code": "PIT_VINTAGE_VIOLATION",
                "severity": "CRITICAL",
                "condition": f"{len(viols)} features violated cutoff timestamp",
                "explanation": f"Point-in-Time leakage detected: {summary_v}",
                "recommended_action": "REJECT SETUP: Forecast is tainted with look-ahead information.",
            })
            is_data_failure = True

        # 3. Sub-threshold / Pure Noise Check
        abs_bias = abs(float(bias_score)) if np.isfinite(bias_score) else 0.0
        if abs_bias < self.bias_threshold:
            triggers.append({
                "code": "SUB_THRESHOLD_EDGE",
                "severity": "HIGH",
                "condition": f"|bias| = {abs_bias:.3f} < {self.bias_threshold:.2f}",
                "explanation": f"Weekly bias score ({bias_score:+.3f}) is below minimum statistical significance threshold ({self.bias_threshold:.2f}). No directional edge exists.",
                "recommended_action": "STAND ASIDE: Insufficient edge to overcome trading friction.",
            })

        # 4. Macro Cross-Asset Divergence (Conflicting Forces)
        d_yield = float(features_dict.get("delta_real_yield_1w", 0.0))
        dxy_ret = float(features_dict.get("dxy_return_1w", 0.0))
        # Yields up > 5 bps (bearish) but DXY down < -0.8% (bullish)
        if d_yield >= 0.05 and dxy_ret <= -0.008:
            triggers.append({
                "code": "MACRO_DIVERGENCE_CONFLICT",
                "severity": "HIGH",
                "condition": f"Yield delta={d_yield:+.2f}%, DXY return={dxy_ret:+.2%}",
                "explanation": f"Conflicting macro forces: Real Yields surged ({d_yield:+.2f}%) while US Dollar plunged ({dxy_ret:+.2%}). Cross-asset divergence produces high whipsaw risk.",
                "recommended_action": "STAND ASIDE: Opposing macro factors cancel directional momentum.",
            })
        # Yields down < -5 bps (bullish) but DXY rallied > +0.8% (bearish)
        elif d_yield <= -0.05 and dxy_ret >= 0.008:
            triggers.append({
                "code": "MACRO_DIVERGENCE_CONFLICT",
                "severity": "HIGH",
                "condition": f"Yield delta={d_yield:+.2f}%, DXY return={dxy_ret:+.2%}",
                "explanation": f"Conflicting macro forces: Real Yields plunged ({d_yield:+.2f}%) while US Dollar surged ({dxy_ret:+.2%}). Disagreement between rates and FX undermines reliability.",
                "recommended_action": "STAND ASIDE: Wait for rates and dollar to re-align.",
            })

        # 5. Extreme Volatility / Market De-Risking Shock
        vix = float(features_dict.get("vix", 15.0))
        if vix > self.vix_hard_limit:
            triggers.append({
                "code": "HIGH_VOLATILITY_REGIME",
                "severity": "HIGH",
                "condition": f"VIX = {vix:.1f} > ceiling {self.vix_hard_limit:.1f}",
                "explanation": f"VIX elevated at {vix:.1f}. Broad equity or liquidity de-risking threatens non-linear gold flushes via margin liquidations.",
                "recommended_action": "REDUCE CONFIDENCE / STAND ASIDE: Tail risk dwarfs weekly expected return.",
            })

        # 6. Active Failure Memory Trap
        if failure_memory_data:
            sim = float(failure_memory_data.get("failure_similarity_score", 0.0))
            warning_active = bool(failure_memory_data.get("reflexive_warning_active", False))
            archetype = failure_memory_data.get("matching_failure_archetype", "UNKNOWN")
            if warning_active and sim >= self.trap_similarity_limit:
                triggers.append({
                    "code": "FAILURE_MEMORY_TRAP",
                    "severity": "HIGH",
                    "condition": f"Similarity = {sim * 100:.1f}% >= limit {self.trap_similarity_limit * 100:.0f}%",
                    "explanation": f"Context vector matches historical failure archetype '{archetype}' with {sim * 100:.1f}% cosine similarity. High probability of repeating past forecast error.",
                    "recommended_action": "STAND ASIDE / WIDEN CORRIDOR: Setup is in a recognized failure trap regime.",
                })

        # 7. Overbought / Oversold Price Exhaustion
        trend_dist = float(features_dict.get("gold_distance_20w", 0.0))
        if abs(trend_dist) > self.trend_extension_limit:
            ext_type = "overbought" if trend_dist > 0 else "oversold"
            triggers.append({
                "code": "PRICE_EXHAUSTION_STRETCH",
                "severity": "MEDIUM",
                "condition": f"Distance to 20w MA = {trend_dist:+.1%}",
                "explanation": f"Gold is technically extreme {ext_type} ({trend_dist:+.1%} away from 20-week moving average). Severe mean-reversion risk.",
                "recommended_action": "REDUCE SIZING: Require pullback to moving average before positioning.",
            })

        # 8. Model Disagreement (Raw return sign vs Recursive bias sign)
        if raw_expected_return is not None and abs_bias >= self.bias_threshold:
            if (raw_expected_return > 0.003 and bias_score < -0.05) or (raw_expected_return < -0.003 and bias_score > 0.05):
                triggers.append({
                    "code": "MODEL_DISAGREEMENT",
                    "severity": "HIGH",
                    "condition": f"Raw return = {raw_expected_return:+.2%}, Recursive bias = {bias_score:+.3f}",
                    "explanation": f"Material contradiction between Static Macro Return ({raw_expected_return:+.2%}) and Adaptive Recursive Bias ({bias_score:+.3f}).",
                    "recommended_action": "STAND ASIDE: Resolving internal model tension takes precedence over trading.",
                })

        # 9. Imminent Tier-1 Macro Event Risk
        if event_risk_active:
            triggers.append({
                "code": "IMMINENT_MACRO_EVENT_RISK",
                "severity": "HIGH",
                "condition": f"Event: {event_risk_name or 'FOMC / NFP / CPI'}",
                "explanation": f"Binary event risk scheduled within trading window: {event_risk_name or 'Tier-1 Macro Release'}.",
                "recommended_action": "STAND ASIDE: Binary release can invalidate macro relationships instantaneously.",
            })

        is_no_trade = len(triggers) > 0

        if is_data_failure:
            status_label = "DATA QUALITY FAILURE -- DO NOT USE"
            action = "STAND ASIDE: Data pipeline or point-in-time failure. All models invalid."
        elif is_no_trade:
            if any(t["code"] == "HIGH_VOLATILITY_REGIME" for t in triggers):
                status_label = "HIGH-RISK REGIME -- REDUCE CONFIDENCE / STAND ASIDE"
                action = "REDUCE CONFIDENCE: Extreme market volatility warrants de-risking."
            elif any(t["code"] == "SUB_THRESHOLD_EDGE" for t in triggers):
                status_label = "NEUTRAL / NO DIRECTIONAL EDGE"
                action = "STAND ASIDE: Bias magnitude is statistically indistinguishable from noise."
            else:
                status_label = "DO NOT TRADE -- UNFAVORABLE CONDITIONS"
                action = "STAND ASIDE: Risk circuit breaker active. Capital preservation prioritized."
        else:
            status_label = "TRADE PERMITTED -- CONDITIONS FAVORABLE"
            action = "PROCEED: Setup satisfies all multi-factor alignment and safety checks."

        return {
            "is_no_trade": is_no_trade,
            "status_label": status_label,
            "action_guidance": action,
            "trigger_count": len(triggers),
            "triggers": triggers,
        }
