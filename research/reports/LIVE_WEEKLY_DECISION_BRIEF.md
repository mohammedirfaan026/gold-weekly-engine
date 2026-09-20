================================================================================
                GOLD WEEKLY AI -- INSTITUTIONAL DECISION BRIEF
================================================================================

--------------------------------------------------------------------------------
A. SYSTEM & RUN IDENTIFICATION
--------------------------------------------------------------------------------
  Observation Week      : 2026-09-18
  Prediction Cutoff     : 2026-09-18 21:00:00+00:00
  Data Cutoff Timestamp : 2026-09-18 21:00:00+00:00
  Model Version         : v1.2.0-decision-support
  Specification Version : v1.2.0-corridor-hedged (Schema: v2.0-pit)
  Git Commit Hash       : a6b4a903
  Configuration Hash    : 19eb8e11fbd738e3
  Reproducibility Note  : CLEAN -- FULLY REPRODUCIBLE

--------------------------------------------------------------------------------
B. CURRENT MARKET STATE & MACRO VINTAGES
--------------------------------------------------------------------------------
  Spot Gold Reference   : $6,256.05
  Gold Technical Trend  : CONSOLIDATION (Distance to 20w MA: -4.86%)
  10Y Real Yield (TIPS) : FALLING (Bullish tailwind) (1w change: -6.8 bps)
  US Dollar Index (DXY) : STRENGTHENING (Headwind) (1w return: +1.11%)
  Market Volatility(VIX): NORMAL VOLATILITY (Level: 14.8)
  Macro-Event Risk      : None scheduled within primary window
  Feature Availability  : All Core Features Available

--------------------------------------------------------------------------------
C. MODEL OUTPUT & CALIBRATED CONFIDENCE
--------------------------------------------------------------------------------
  Tactical Stance       : **Neutral / no directional edge**
  Bias Category         : NEUTRAL
  Recursive Bias Score  : -0.031 (Magnitude: 0.031)
  Raw Baseline Score    : +0.011
  Expected Return       : -0.14% (Raw Static Return: +0.25%)
  Confidence Tier       : **LOW CONFIDENCE** (|bias| < 0.15)
  Sample Size Audit     : 12 trades [LOW SAMPLE (<20 trades) -- Interpret metrics with caution]
  Empirical Win Rate    : 41.7% (Historical Walk-Forward)
  Empirical Sharpe      : -0.78
  Calibration Disclaimer: Exploratory historical calibration -- not a probability forecast.
  Trader Guidance       : Weak directional edge; negative historical expectancy. Stand aside or use strict confirmation.

--------------------------------------------------------------------------------
D. SCENARIO MAP & PRICE VOLATILITY CORRIDOR (10th - 90th PERCENTILE)
--------------------------------------------------------------------------------
  Upper Resistance (90%): $6,496.13 (+3.84%)
  Expected Center       : $6,247.49
  Lower Support (10%)   : $5,998.85 (-4.11%)
  Expected Corridor Band: $497.28 (7.95% wide)
  Historical Containment: 58.3% of weekly ranges remained inside bounds

  * [BASE CASE]         : Gold trades within $5,998.85 - $6,496.13 with an expected center of $6,247.49 (-0.14% expected weekly change).
  * [BULL BREAKOUT]     : A sustained breach above $6,496.13 (+3.84%) indicates sovereign safe-haven accumulation overriding model macro constraints.
  * [BEAR BREAKDOWN]    : A breakdown below $5,998.85 (-4.11%) signals aggressive real-yield steepening or dollar short-squeeze liquidation.
  * [INVALIDATION]      : No directional thesis active. Both corridor boundaries serve as range bounds.
  * [CONDITIONS TO SHIFT]: Decisive breakout with macro factor alignment across yields and dollar.

--------------------------------------------------------------------------------
E. RISK CONTROLS & FAIL-CLOSED CIRCUIT BREAKERS
--------------------------------------------------------------------------------
  Circuit Breaker Status: **NEUTRAL / NO DIRECTIONAL EDGE**
  Active Risk Triggers  : 2
    - [HIGH] SUB_THRESHOLD_EDGE: Weekly bias score (-0.031) is below minimum statistical significance threshold (0.05). No directional edge exists. (Condition: |bias| = 0.031 < 0.05)
    - [HIGH] MACRO_DIVERGENCE_CONFLICT: Conflicting macro forces: Real Yields plunged (-0.07%) while US Dollar surged (+1.11%). Disagreement between rates and FX undermines reliability. (Condition: Yield delta=-0.07%, DXY return=+1.11%)
  Action Recommendation : STAND ASIDE: Bias magnitude is statistically indistinguishable from noise.
  Reflexive Trap Memory : Nearest=NONE, Sim=0.0%, Warning=INACTIVE
  PIT Audit Status      : PASS (0 violations)
  DATA FRESHNESS AUDIT  : OPERATIONAL
  Data Pipeline Health  : OPERATIONAL

--------------------------------------------------------------------------------
F. HUMAN DISCRETIONARY DECISION WORKSHEET
--------------------------------------------------------------------------------
  * Trader Decision     : [  ] FOLLOW   [  ] FADE   [  ] PASS   [  ] OVERRIDE
  * Override Rationale  : ________________________________________________
  * Planned Entry Price : $6,256.05
  * Planned Stop Loss   : $6,256.05
  * Planned Take Profit : $5,998.85
  * Position Sizing     : Fixed 1.0x / Reduced Risk / Standing Aside
  * Execution Timestamp : ____________________
  * Actual Entry Price  : ____________________
  * Actual Exit Price   : ____________________
  * Realized Return (%) : ____________________
  * Post-Trade Review   : ________________________________________________

================================================================================
LEGAL & SCIENTIFIC DISCLAIMER:
- For institutional research and discretionary decision-support only.
- NEVER execute trades solely on algorithmic outputs. Discretionary verification required.
- AUTONOMOUS TRADING NOT SUPPORTED. No automatic order routing capability exists.
- Historical backtests reflect past exploratory evaluations and are NOT future forecasts.
================================================================================