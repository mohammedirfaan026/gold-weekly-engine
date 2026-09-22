"""
Helper for extracting and formatting the Gold Weekly directional bias prediction
and human-readable macroeconomic rationale for the minimal web interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = ROOT / "data" / "live"
BRIEF_JSON = LIVE_DIR / "latest_brief.json"


def get_latest_prediction_summary() -> Dict[str, Any]:
    """
    Returns a clean, minimal dictionary containing:
    - bias prediction (direction, score, expected return, spot price, week)
    - concise description of the reason for the bias
    - core macroeconomic drivers breakdown
    """
    brief = _load_brief_json()
    if brief:
        return _format_brief_data(brief)

    # Fallback to direct model inference if latest_brief.json does not exist
    return _generate_fallback_prediction()


def refresh_prediction() -> Dict[str, Any]:
    """
    Recomputes the weekly bias using the engine and refreshes data.
    """
    try:
        from src.ai_engine.engine import GoldWeeklyBiasEngine
        engine = GoldWeeklyBiasEngine()
        pred = engine.predict_week()
        return _format_engine_prediction(pred)
    except Exception as e:
        # If live inference fails, return existing or error state
        existing = get_latest_prediction_summary()
        existing["refresh_error"] = str(e)
        return existing


def _load_brief_json() -> Optional[Dict[str, Any]]:
    if not BRIEF_JSON.exists():
        return None
    try:
        return json.loads(BRIEF_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_brief_data(brief: Dict[str, Any]) -> Dict[str, Any]:
    ident = brief.get("identification") or {}
    mkt = brief.get("current_market_state") or {}
    out = brief.get("model_output") or {}
    cal = out.get("confidence_calibration") or brief.get("confidence_calibration") or {}
    corr = (brief.get("scenario_map") or {}).get("expected_corridor") or brief.get("expected_corridor") or {}
    factors = mkt.get("factor_states") or {}
    rc = brief.get("risk_controls") or {}
    triggers = (rc.get("no_trade_circuit_breaker") or {}).get("triggers") or []

    # Direction and score
    bias_score = float(out.get("recursive_bias_score", brief.get("bias_score", 0.0)))
    expected_ret = float(out.get("recursive_expected_return_pct", brief.get("expected_return_pct", 0.0)))
    raw_cat = str(out.get("bias_category", brief.get("taxonomy_stance", "NEUTRAL"))).upper()

    if bias_score >= 0.15 or "BULLISH" in raw_cat:
        direction = "BULLISH"
        badge_class = "bullish"
    elif bias_score <= -0.15 or "BEARISH" in raw_cat:
        direction = "BEARISH"
        badge_class = "bearish"
    else:
        direction = "NEUTRAL"
        badge_class = "neutral"

    # Price & week
    price = float(mkt.get("gold_reference_price") or brief.get("current_gold_price") or 0.0)
    week = str(ident.get("observation_week") or brief.get("observation_week") or "Current")
    gen_time = str(brief.get("generated_at_utc") or ident.get("prediction_timestamp") or "")

    # Macro factors deconstruction
    ry = factors.get("real_yield_10y", {})
    dx = factors.get("us_dollar_dxy", {})
    vx = factors.get("market_risk_vix", {})
    gt = factors.get("gold_trend", {})

    ry_delta = float(ry.get("weekly_delta_bps", 0.0))
    dx_ret = float(dx.get("weekly_return_pct", 0.0))
    vix_val = vx.get("vix_level", 15.0)
    trend_dist = float(gt.get("distance_20w_pct", 0.0))

    # Build concise reason narrative
    reason_narrative = _compose_reason_narrative(
        direction=direction,
        bias_score=bias_score,
        expected_ret=expected_ret,
        ry_delta=ry_delta,
        dx_ret=dx_ret,
        vix_val=vix_val,
        trend_dist=trend_dist,
        trend_state=gt.get("state", "Consolidation"),
        triggers=triggers,
    )

    # Key factor driver pills
    driver_items = _compose_driver_items(ry_delta, dx_ret, vix_val, trend_dist, gt.get("state", "Consolidation"))

    # Caution note / circuit breaker note
    caution = None
    for t in triggers:
        if t.get("code") == "MACRO_DIVERGENCE_CONFLICT":
            caution = "Macro Divergence: Real yields and the US Dollar moved in opposing directions, moderating high-conviction follow-through."
            break
        elif t.get("code") == "SUB_THRESHOLD_EDGE":
            caution = "Sub-Threshold Edge: The absolute bias score is under 0.05, representing low directional momentum."
            break
        elif t.get("code") == "HIGH_VOLATILITY_REGIME":
            caution = "High Volatility Regime: Heightened market stress calls for tighter risk management."
            break

    return {
        "week": week,
        "generated_at": gen_time,
        "price": price,
        "direction": direction,
        "badge_class": badge_class,
        "bias_score": bias_score,
        "expected_return_pct": expected_ret,
        "confidence_tier": cal.get("tier", "MODERATE"),
        "reason_narrative": reason_narrative,
        "drivers": driver_items,
        "caution_note": caution,
        "corridor_low": float(corr.get("lower_support_10pct") or 0.0),
        "corridor_high": float(corr.get("upper_resistance_90pct") or 0.0),
    }


def _compose_reason_narrative(
    direction: str,
    bias_score: float,
    expected_ret: float,
    ry_delta: float,
    dx_ret: float,
    vix_val: Any,
    trend_dist: float,
    trend_state: str,
    triggers: List[Dict[str, Any]],
) -> str:
    """Composes a tight, clear 2-3 sentence explanation of the bias."""
    parts = []

    if direction == "BULLISH":
        parts.append(
            f"Gold carries a Bullish bias ({bias_score:+.3f} score, {expected_ret:+.2f}% expected weekly change)."
        )
        if ry_delta < 0:
            parts.append(
                f"The primary catalyst is falling 10-year real yields ({ry_delta:+.1f} bps), reducing the holding cost of bullion."
            )
        if dx_ret < 0:
            parts.append(f"A weakening US Dollar ({dx_ret:+.2f}%) provides an additional pricing tailwind.")
        elif dx_ret > 0:
            parts.append(f"US Dollar strength ({dx_ret:+.2f}%) introduces mild counter-resistance.")
    elif direction == "BEARISH":
        parts.append(
            f"Gold carries a Bearish bias ({bias_score:+.3f} score, {expected_ret:+.2f}% expected weekly change)."
        )
        if ry_delta > 0:
            parts.append(
                f"Rising 10-year real yields (+{ry_delta:.1f} bps) increase the attractiveness of yielding cash over gold."
            )
        if dx_ret > 0:
            parts.append(f"A strengthening US Dollar (+{dx_ret:.2f}%) exerts sustained downward pressure on spot prices.")
        elif dx_ret < 0:
            parts.append(f"Even with a softer dollar ({dx_ret:+.2f}%), yield headwinds dominate the outlook.")
    else:
        parts.append(
            f"Gold carries a Neutral bias ({bias_score:+.3f} score, {expected_ret:+.2f}% expected weekly change)."
        )
        if ry_delta < 0 and dx_ret > 0:
            parts.append(
                f"Conflicting macroeconomic forces are offsetting each other: lower 10-year real yields ({ry_delta:+.1f} bps) offer a tailwind, but a surging US Dollar (+{dx_ret:.2f}%) creates an equal headwind."
            )
        elif ry_delta > 0 and dx_ret < 0:
            parts.append(
                f"Mixed signals: rising real yields (+{ry_delta:.1f} bps) negate the benefit of a softer US Dollar ({dx_ret:+.2f}%)."
            )
        else:
            parts.append("Macro interest rates and currencies are broadly balanced, indicating a range-bound environment.")

    clean_trend = str(trend_state).replace("EXTENDED ", "").title()
    parts.append(
        f"Price action is in {clean_trend} ({trend_dist:+.1f}% vs 20-week MA) while volatility remains at {vix_val} VIX."
    )

    return " ".join(parts)


def _compose_driver_items(
    ry_delta: float, dx_ret: float, vix_val: Any, trend_dist: float, trend_state: str
) -> List[Dict[str, str]]:
    """Builds the 4 primary macro driver items."""
    # 1. Real Yields
    if ry_delta <= -2.0:
        ry_impact = "Tailwind (Bullish)"
        ry_badge = "bullish"
    elif ry_delta >= 2.0:
        ry_impact = "Headwind (Bearish)"
        ry_badge = "bearish"
    else:
        ry_impact = "Neutral / Flat"
        ry_badge = "neutral"

    # 2. DXY Dollar
    if dx_ret <= -0.3:
        dx_impact = "Tailwind (Bullish)"
        dx_badge = "bullish"
    elif dx_ret >= 0.3:
        dx_impact = "Headwind (Bearish)"
        dx_badge = "bearish"
    else:
        dx_impact = "Rangebound"
        dx_badge = "neutral"

    # 3. VIX
    try:
        v_num = float(vix_val)
        if v_num >= 20.0:
            vix_impact = "Stress Regime (>20)"
            vix_badge = "bearish"
        else:
            vix_impact = "Normal Volatility"
            vix_badge = "neutral"
    except Exception:
        vix_impact = str(vix_val)
        vix_badge = "neutral"

    # 4. Trend
    if trend_dist > 4.0:
        trend_impact = "Strong Uptrend"
        trend_badge = "bullish"
    elif trend_dist < -4.0:
        trend_impact = "Consolidation / Pullback"
        trend_badge = "neutral"
    else:
        trend_impact = "Consolidation"
        trend_badge = "neutral"

    return [
        {
            "name": "10Y Real Yield",
            "value": f"{ry_delta:+.1f} bps",
            "impact": ry_impact,
            "badge": ry_badge,
            "description": "Yields lower = gold bullish; Yields higher = gold bearish.",
        },
        {
            "name": "US Dollar Index (DXY)",
            "value": f"{dx_ret:+.2f}%",
            "impact": dx_impact,
            "badge": dx_badge,
            "description": "Weaker dollar supports gold; Stronger dollar pressures gold.",
        },
        {
            "name": "Market Risk (VIX)",
            "value": f"{vix_val}",
            "impact": vix_impact,
            "badge": vix_badge,
            "description": "Elevated volatility spikes safe-haven demand.",
        },
        {
            "name": "20-Week Trend",
            "value": f"{trend_dist:+.2f}%",
            "impact": trend_impact,
            "badge": trend_badge,
            "description": "Distance from 20-week moving average.",
        },
    ]


def _format_engine_prediction(pred: Dict[str, Any]) -> Dict[str, Any]:
    """Formats output from direct GoldWeeklyBiasEngine prediction."""
    bias = pred.get("ai_weekly_bias") or {}
    corridor = pred.get("expected_price_corridor") or {}
    price = float(pred.get("current_gold_price", 0.0))
    week = str(pred.get("observation_week", "Current"))
    score = float(bias.get("bias_score", 0.0))
    exp_ret = float(bias.get("expected_weekly_return_pct", 0.0))
    category = str(bias.get("bias_category", "NEUTRAL")).upper()

    if score >= 0.15 or "BULLISH" in category:
        direction = "BULLISH"
        badge_class = "bullish"
    elif score <= -0.15 or "BEARISH" in category:
        direction = "BEARISH"
        badge_class = "bearish"
    else:
        direction = "NEUTRAL"
        badge_class = "neutral"

    drivers = bias.get("dominant_drivers", [])
    driver_text = ", ".join([f"{d.get('feature')}: {d.get('impact'):+.3f}%" for d in drivers[:3]])

    return {
        "week": week,
        "generated_at": str(pred.get("prediction_timestamp", "")),
        "price": price,
        "direction": direction,
        "badge_class": badge_class,
        "bias_score": score,
        "expected_return_pct": exp_ret,
        "confidence_tier": "MODERATE",
        "reason_narrative": f"Model inference indicates a {direction.lower()} stance with a bias score of {score:+.3f} ({exp_ret:+.2f}% expected return). Dominant feature weights: {driver_text}.",
        "drivers": [
            {"name": d.get("feature"), "value": f"{d.get('impact'):+.3f}%", "impact": "Weighted Factor", "badge": "neutral", "description": "Normalized feature contribution"}
            for d in drivers[:4]
        ],
        "caution_note": None,
        "corridor_low": float(corridor.get("expected_low_10pct") or price * 0.98),
        "corridor_high": float(corridor.get("expected_high_90pct") or price * 1.02),
    }


def _generate_fallback_prediction() -> Dict[str, Any]:
    """Generates a safe fallback prediction if no brief exists."""
    try:
        from src.ai_engine.engine import GoldWeeklyBiasEngine
        engine = GoldWeeklyBiasEngine()
        pred = engine.predict_week()
        return _format_engine_prediction(pred)
    except Exception as e:
        return {
            "week": "N/A",
            "generated_at": "N/A",
            "price": 0.0,
            "direction": "NEUTRAL",
            "badge_class": "neutral",
            "bias_score": 0.0,
            "expected_return_pct": 0.0,
            "confidence_tier": "LOW",
            "reason_narrative": f"No cached prediction brief found. Run 'python run_weekly_live.py' or click Refresh to initialize. ({e})",
            "drivers": [],
            "caution_note": "Awaiting initial pipeline run.",
            "corridor_low": 0.0,
            "corridor_high": 0.0,
        }
