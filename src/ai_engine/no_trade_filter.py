"""
Strict Do-Not-Trade (No-Trade) Circuit Breaker Filter for Gold AI Engine.
Detects conflicting macro signals, volatility spikes, active failure traps,
extreme price exhaustion, and stale data to prevent low-edge or trap-prone trades.
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
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-factor safety checks.
        Returns whether trading should be prohibited and the specific triggers.
        """
        triggers: List[Dict[str, str]] = []
        is_data_failure = False

        # 1. Stale or Missing Data Check
        if freshness_data and not freshness_data.get("is_usable", True):
            stale = ", ".join(freshness_data.get("stale_series", []))
            triggers.append({
                "code": "DATA_QUALITY_FAILURE",
                "severity": "CRITICAL",
                "reason": f"Input data pipeline degraded or stale: {stale}. Forecast is untrustworthy.",
            })
            is_data_failure = True

        # 2. Sub-threshold / Pure Noise Check
        abs_bias = abs(float(bias_score)) if np.isfinite(bias_score) else 0.0
        if abs_bias < self.bias_threshold:
            triggers.append({
                "code": "SUB_THRESHOLD_EDGE",
                "severity": "HIGH",
                "reason": f"Weekly bias score ({bias_score:+.3f}) is below minimum significance threshold ({self.bias_threshold:.2f}). No directional edge exists.",
            })

        # 3. Macro Cross-Asset Divergence (Conflicting Signals)
        # Yields up is bearish; DXY down is bullish. If both move strongly in opposite directions:
        d_yield = float(features_dict.get("delta_real_yield_1w", 0.0))
        dxy_ret = float(features_dict.get("dxy_return_1w", 0.0))
        # Case A: Yields up > 5 bps (bearish) but DXY down < -0.8% (bullish)
        if d_yield >= 0.05 and dxy_ret <= -0.008:
            triggers.append({
                "code": "MACRO_DIVERGENCE_CONFLICT",
                "severity": "HIGH",
                "reason": f"Conflicting macro forces: Real Yields surged ({d_yield:+.2f}%) but US Dollar weakened ({dxy_ret:+.2%}). Market forces cancel out.",
            })
        # Case B: Yields down < -5 bps (bullish) but DXY surged > +0.8% (bearish)
        elif d_yield <= -0.05 and dxy_ret >= 0.008:
            triggers.append({
                "code": "MACRO_DIVERGENCE_CONFLICT",
                "severity": "HIGH",
                "reason": f"Conflicting macro forces: Real Yields plunged ({d_yield:+.2f}%) but US Dollar rallied ({dxy_ret:+.2%}). Cross-asset divergence creates high whipsaw risk.",
            })

        # 4. Extreme Volatility / Market De-Risking Shock
        vix = float(features_dict.get("vix", 15.0))
        if vix > self.vix_hard_limit:
            triggers.append({
                "code": "HIGH_VOLATILITY_REGIME",
                "severity": "HIGH",
                "reason": f"VIX elevated at {vix:.1f} (above safety ceiling {self.vix_hard_limit:.1f}). Broad equity/liquidity margin calls threaten gold.",
            })

        # 5. Active Failure Memory Trap
        if failure_memory_data:
            sim = float(failure_memory_data.get("failure_similarity_score", 0.0))
            warning_active = bool(failure_memory_data.get("reflexive_warning_active", False))
            archetype = failure_memory_data.get("matching_failure_archetype", "UNKNOWN")
            if warning_active and sim >= self.trap_similarity_limit:
                triggers.append({
                    "code": "FAILURE_MEMORY_TRAP",
                    "severity": "HIGH",
                    "reason": f"Context vector matches historical failure trap with {sim * 100:.1f}% cosine similarity (Archetype: {archetype}). High probability of repeating past forecast error.",
                })

        # 6. Overbought / Oversold Price Exhaustion
        trend_dist = float(features_dict.get("gold_distance_20w", 0.0))
        if abs(trend_dist) > self.trend_extension_limit:
            ext_type = "overbought" if trend_dist > 0 else "oversold"
            triggers.append({
                "code": "PRICE_EXHAUSTION_STRETCH",
                "severity": "MEDIUM",
                "reason": f"Gold is extreme {ext_type} ({trend_dist:+.1%} away from 20-week MA). High mean-reversion risk against continuation trades.",
            })

        is_no_trade = len(triggers) > 0

        if is_data_failure:
            status_label = "DATA QUALITY FAILURE -- Do Not Trade"
            action = "STAND ASIDE: Repair data pipeline before taking any positioning."
        elif is_no_trade:
            status_label = "DO NOT TRADE -- Unfavorable Conditions"
            action = "STAND ASIDE: Circuit breaker active. Preserving capital is prioritized over low-conviction entry."
        else:
            status_label = "TRADE PERMITTED -- Conditions Favorable"
            action = "PROCEED: Setup satisfies all multi-factor alignment and safety checks."

        return {
            "is_no_trade": is_no_trade,
            "status_label": status_label,
            "action_guidance": action,
            "trigger_count": len(triggers),
            "triggers": triggers,
        }
