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
  Git Commit Hash       : 7037c0f4
  Configuration Hash    : 19eb8e11fbd738e3
  Reproducibility Note  : UNCOMMITTED CHANGES -- OUTPUT IS NOT REPRODUCIBLE FROM COMMITTED SOURCE

--------------------------------------------------------------------------------
B. CURRENT MARKET STATE & MACRO VINTAGES
--------------------------------------------------------------------------------
  Spot Gold Reference   : $6,256.05
  Gold Technical Trend  : CONSOLIDATION (Distance to 20w MA: -4.86%)
  10Y Real Yield (TIPS) : FALLING (Bullish tailwind) (1w change: -6.8 bps)
  US Dollar Index (DXY) : STRENGTHENING (Headwind) (1w return: +1.11%)
  Market Volatility(VIX): NORMAL VOLATILITY (Level: 14.8)
  Macro-Event Risk      : None scheduled within primary window
  Feature Availability  : DEGRADED

--------------------------------------------------------------------------------
C. MODEL OUTPUT & CALIBRATED CONFIDENCE
--------------------------------------------------------------------------------
  Tactical Stance       : **Data quality failure -- do not use**
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
  Circuit Breaker Status: **DATA QUALITY FAILURE -- DO NOT USE**
  Active Risk Triggers  : 3
    - [CRITICAL] DATA_QUALITY_FAILURE: Input data pipeline degraded, missing, or stale: real_yield_10y: Publication timestamp after prediction cutoff; dxy_index: Future-dated observation; vix_index: Future-dated observation; hy_oas: Publication timestamp after prediction cutoff. (Condition: Stale series: None)
    - [HIGH] SUB_THRESHOLD_EDGE: Weekly bias score (-0.031) is below minimum statistical significance threshold (0.05). No directional edge exists. (Condition: |bias| = 0.031 < 0.05)
    - [HIGH] MACRO_DIVERGENCE_CONFLICT: Conflicting macro forces: Real Yields plunged (-0.07%) while US Dollar surged (+1.11%). Disagreement between rates and FX undermines reliability. (Condition: Yield delta=-0.07%, DXY return=+1.11%)
  Action Recommendation : STAND ASIDE: Data pipeline or point-in-time failure. All models invalid.
  Reflexive Trap Memory : Nearest=NONE, Sim=0.0%, Warning=INACTIVE
  PIT Audit Status      : PASS (0 violations)
  DATA FRESHNESS AUDIT  : DEGRADED
  Data Pipeline Health  : DEGRADED

--------------------------------------------------------------------------------
F. LIVE NEWS / GEOPOLITICS / CENTRAL-BANK FEED (AUTO-FETCHED)
--------------------------------------------------------------------------------
  Fetch Timestamp UTC   : 2026-09-21T16:07:09.381863+00:00
  Headlines Captured    : 40
  Risk Flags            : GEOPOLITICAL_ESCALATION, TRADE_POLICY_SHOCK, HEADLINE_TONE_SKEWED_BULLISH
  Suggested Size        : STAND ASIDE -- Circuit breaker / no-trade status active.
  Narrative Summary     : Central-bank wire: Trump demands 1% rates because the US has the ‘Best Credit in the World’ — the Fed hiked rates anyway. So who’s right? | Geopolitics: Paramount and state AGs will settle lawsuit, allowing Warner Bros. merger to proceed, reports say | Macro: Williams-Sonoma's stock has soared in a sluggish housing market. Here's how it won over Wall Street || Flags: GEOPOLITICAL_ESCALATION, TRADE_POLICY_SHOCK, HEADLINE_TONE_SKEWED_BULLISH
  Top Headlines         :
    - [dollar_yields|bullish_for_gold|2026-09-21T16:06] S&P 500 rises 1% as AI-related stocks surge, oil and yields slide: Live updates (CNBC Top News)
    - [macro|bullish_for_gold|2026-09-21T16:03] Williams-Sonoma's stock has soared in a sluggish housing market. Here's how it won over Wall Street (CNBC Top News)
    - [macro|neutral|2026-09-21T16:03] What is the White House press pool and why does it matter? (CNBC Top News)
    - [macro|neutral|2026-09-21T15:46] Trump sued by MS NOW, CNN, Politico over White House media ban (CNBC Top News)
    - [macro|neutral|2026-09-21T15:43] Cybersecurity stocks are back with a bang. These four are on Josh Brown's list (CNBC Top News)
    - [macro|bullish_for_gold|2026-09-21T15:34] U.S.-listed Greenland stocks surge after Trump announces security deal with Denmark (CNBC Top News)
    - [central_bank|neutral|2026-09-21T15:30] Trump demands 1% rates because the US has the ‘Best Credit in the World’ — the Fed hiked rates anyway. So who’s right? (Yahoo Finance Markets)
    - [dollar_yields|neutral|2026-09-21T15:20] Treasury yields ease as global borrowing costs tumble (CNBC Top News)
  Feed Health            :
    - Reuters Business: ERROR:ConnectionError
    - Reuters World: ERROR:ConnectionError
    - CNBC Top News: OK:30
    - CNBC Economy: OK:30
    - Federal Reserve Press: OK:20
    - Yahoo Finance Markets: OK:47
    - Kitco Gold News: ERROR:ParseError
    - Finnhub: OK:50

--------------------------------------------------------------------------------
G. HUMAN DISCRETIONARY DECISION WORKSHEET
--------------------------------------------------------------------------------
  * Trader Decision     : [  ] FOLLOW   [  ] FADE   [  ] PASS   [  ] OVERRIDE
  * Override Rationale  : ________________________________________________
  * Planned Entry Price : $6,256.05
  * Planned Stop Loss   : $6,256.05
  * Planned Take Profit : $5,998.85
  * Position Sizing     : AUTO-SUGGESTED: STAND ASIDE
  * Execution Timestamp : ____________________
  * Actual Entry Price  : ____________________
  * Actual Exit Price   : ____________________
  * Realized Return (%) : ____________________
  * Post-Trade Review   : ________________________________________________

================================================================================
LEGAL & SCIENTIFIC DISCLAIMER:
- For institutional research and discretionary decision-support only.
- News headlines are auto-fetched from public feeds; verify critical items before risking capital.
- NEVER execute trades solely on algorithmic outputs. Discretionary verification required.
- AUTONOMOUS TRADING NOT SUPPORTED. No automatic order routing capability exists.
- Historical backtests reflect past exploratory evaluations and are NOT future forecasts.
================================================================================