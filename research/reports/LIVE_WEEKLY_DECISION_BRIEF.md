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
  Git Commit Hash       : 23b7013d
  Configuration Hash    : 19eb8e11fbd738e3
  Reproducibility Note  : UNCOMMITTED CHANGES -- OUTPUT IS NOT REPRODUCIBLE FROM COMMITTED SOURCE

--------------------------------------------------------------------------------
B. CURRENT MARKET STATE & MACRO VINTAGES
--------------------------------------------------------------------------------
  Spot Gold Reference   : $6,250.00
  Gold Technical Trend  : CONSOLIDATION (Distance to 20w MA: +3.00%)
  10Y Real Yield (TIPS) : FALLING (Bullish tailwind) (1w change: -4.0 bps)
  US Dollar Index (DXY) : RANGEBOUND (1w return: -0.20%)
  Market Volatility(VIX): NORMAL VOLATILITY (Level: 16.0)
  Macro-Event Risk      : None scheduled within primary window
  Feature Availability  : All Core Features Available

--------------------------------------------------------------------------------
C. MODEL OUTPUT & CALIBRATED CONFIDENCE
--------------------------------------------------------------------------------
  Tactical Stance       : **Bullish bias -- confirmation required**
  Bias Category         : MODERATE_BULLISH
  Recursive Bias Score  : +0.220 (Magnitude: 0.220)
  Raw Baseline Score    : +0.220
  Expected Return       : +0.85% (Raw Static Return: +0.85%)
  Confidence Tier       : **MODERATE CONFIDENCE** (0.15 <= |bias| < 0.30)
  Sample Size Audit     : 17 trades [LOW SAMPLE (<20 trades) -- Interpret metrics with caution]
  Empirical Win Rate    : 76.5% (Historical Walk-Forward)
  Empirical Sharpe      : 4.02
  Calibration Disclaimer: Exploratory historical calibration -- not a probability forecast.
  Trader Guidance       : Solid directional conviction; high historical win rate. Standard swing risk allocation permitted.

--------------------------------------------------------------------------------
D. SCENARIO MAP & PRICE VOLATILITY CORRIDOR (10th - 90th PERCENTILE)
--------------------------------------------------------------------------------
  Upper Resistance (90%): $6,375.00 (+2.00%)
  Expected Center       : $6,250.00
  Lower Support (10%)   : $6,125.00 (-2.00%)
  Expected Corridor Band: $250.00 (4.00% wide)
  Historical Containment: 52.9% of weekly ranges remained inside bounds

  * [BASE CASE]         : Gold trades within $6,125.00 - $6,375.00 with an expected center of $6,250.00 (+0.85% expected weekly change).
  * [BULL BREAKOUT]     : A sustained breach above $6,375.00 (+2.00%) indicates sovereign safe-haven accumulation overriding model macro constraints.
  * [BEAR BREAKDOWN]    : A breakdown below $6,125.00 (-2.00%) signals aggressive real-yield steepening or dollar short-squeeze liquidation.
  * [INVALIDATION]      : Weekly close below $6,125.00 invalidates the bullish thesis.
  * [CONDITIONS TO SHIFT]: Real-yield spike > 10 bps, DXY surge > 1.0%, or break of support corridor.

--------------------------------------------------------------------------------
E. RISK CONTROLS & FAIL-CLOSED CIRCUIT BREAKERS
--------------------------------------------------------------------------------
  Circuit Breaker Status: **TRADE PERMITTED -- CONDITIONS FAVORABLE**
  Active Risk Triggers  : 0
    - No risk circuit breakers tripped. Multi-factor alignment confirmed.
  Action Recommendation : PROCEED: Setup satisfies all multi-factor alignment and safety checks.
  Reflexive Trap Memory : Nearest=NONE, Sim=0.0%, Warning=INACTIVE
  PIT Audit Status      : PASS (0 violations)
  DATA FRESHNESS AUDIT  : OPERATIONAL
  Data Pipeline Health  : OPERATIONAL

--------------------------------------------------------------------------------
F. LIVE NEWS / GEOPOLITICS / CENTRAL-BANK FEED (AUTO-FETCHED)
--------------------------------------------------------------------------------
  Fetch Timestamp UTC   : 
  Headlines Captured    : 0
  Risk Flags            : NEWS_FETCH_DISABLED
  Suggested Size        : STANDARD (1.0x) -- News fetch disabled by caller.
  Narrative Summary     : News fetch disabled.
  Top Headlines         :
    - No relevant headlines returned this run.

--------------------------------------------------------------------------------
G. HUMAN DISCRETIONARY DECISION WORKSHEET
--------------------------------------------------------------------------------
  * Trader Decision     : [  ] FOLLOW   [  ] FADE   [  ] PASS   [  ] OVERRIDE
  * Override Rationale  : ________________________________________________
  * Planned Entry Price : $6,250.00
  * Planned Stop Loss   : $6,125.00
  * Planned Take Profit : $6,375.00
  * Position Sizing     : AUTO-SUGGESTED: STANDARD (1.0x)
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