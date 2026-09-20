"""
Empirical Confidence Calibrator for Gold AI Engine.
Maps continuous model bias scores into empirical historical confidence tiers
calibrated against walk-forward out-of-sample containment and hit rates.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np


@dataclass
class CalibratedTierInfo:
    tier: str
    bias_range: str
    empirical_win_rate: float
    empirical_sharpe: float
    historical_trades: int
    corridor_containment: float
    guidance: str


# Empirically measured over 52-week walk-forward evaluation
EMPIRICAL_TIER_BENCHMARKS: Dict[str, CalibratedTierInfo] = {
    "LOW": CalibratedTierInfo(
        tier="LOW",
        bias_range="|bias| < 0.15",
        empirical_win_rate=0.4167,
        empirical_sharpe=-0.78,
        historical_trades=12,
        corridor_containment=0.583,
        guidance="Weak directional edge; negative historical expectancy. Stand aside or use strict confirmation.",
    ),
    "MODERATE": CalibratedTierInfo(
        tier="MODERATE",
        bias_range="0.15 <= |bias| < 0.30",
        empirical_win_rate=0.7647,
        empirical_sharpe=4.02,
        historical_trades=17,
        corridor_containment=0.529,
        guidance="Solid directional conviction; high historical win rate. Standard swing risk allocation permitted.",
    ),
    "HIGH": CalibratedTierInfo(
        tier="HIGH",
        bias_range="|bias| >= 0.30",
        empirical_win_rate=0.8000,
        empirical_sharpe=8.59,
        historical_trades=15,
        corridor_containment=0.533,
        guidance="Exceptional macro & trend alignment; robust historical payoff. High conviction setup.",
    ),
}


class ConfidenceCalibrator:
    """Classifies raw AI bias scores into empirical confidence tiers."""

    def __init__(self, custom_benchmarks: Optional[Dict[str, CalibratedTierInfo]] = None):
        self.benchmarks = custom_benchmarks or EMPIRICAL_TIER_BENCHMARKS

    def calibrate(self, bias_score: float) -> Dict[str, Any]:
        """Maps a bias score to an empirical confidence tier."""
        abs_bias = abs(float(bias_score)) if np.isfinite(bias_score) else 0.0

        if abs_bias < 0.15:
            tier_name = "LOW"
        elif abs_bias < 0.30:
            tier_name = "MODERATE"
        else:
            tier_name = "HIGH"

        info = self.benchmarks[tier_name]

        return {
            "tier": info.tier,
            "bias_magnitude": round(abs_bias, 3),
            "bias_range": info.bias_range,
            "empirical_win_rate_pct": round(info.empirical_win_rate * 100, 1),
            "empirical_sharpe": round(info.empirical_sharpe, 2),
            "historical_sample_trades": info.historical_trades,
            "corridor_containment_pct": round(info.corridor_containment * 100, 1),
            "trader_guidance": info.guidance,
        }
