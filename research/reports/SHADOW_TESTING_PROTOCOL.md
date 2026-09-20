# Institutional Shadow-Testing Protocol: Gold Weekly AI Engine

**Engine Version:** `v1.2.0-frozen`  
**Effective Freeze Date:** 2026-09-18 (Friday 17:00 ET close)  
**Governance Standard:** Non-interventional forward walk-forward shadow evaluation  

---

## 1. Executive Protocol Summary

To establish an honest, unpolluted track record and eliminate all forms of post-hoc selection bias, this protocol mandates that **all algorithmic hyperparameters, feature sets, Kalman filter gains, failure memory states, and trade execution rules are strictly frozen as of 2026-09-18**.

No changes to the model codebase, feature engineering, or threshold parameters are permitted during the forward shadow-testing window.

---

## 2. Frozen Engine Specification

| Parameter / Module | Frozen Specification | Rationale |
|---|---|---|
| **Core Architecture** | Multi-factor Ridge + Recursive Kalman State Estimator | Dynamic macro adaptation with Bayesian shrinkage |
| **Active Features** | `delta_real_yield_1w`, `dxy_return_1w`, `delta_breakeven_1w`, `gold_distance_20w`, `vix_percentile`, `hy_oas_change_1w` | Standardized macro and risk transmission channels |
| **Bias Threshold** | `0.05` | Filters low-conviction noise while capturing directional swings |
| **Position Sizing** | Fixed 1.0x notional exposure | Pure unscaled baseline performance tracking |
| **Corridor Stop-Loss** | `2.50%` (or Lower Corridor Support for Longs, Upper for Shorts) | Caps tail drawdown from unexpected geopolitical shocks |
| **Corridor Take-Profit**| `2.00%` (or Upper Corridor Resistance for Longs, Lower for Shorts) | Locks in mean-reverting weekly target gains |
| **Ambiguity Assumption** | `conservative` | Stop hit assumed first if both levels touched in weekly OHLC |
| **Transaction Costs** | `10.0 bps` round-trip deduction | Realistic institutional institutional broker/EBS execution |
| **Slippage Assumption** | `0.05%` (5 bps) round-trip deduction | Accounts for spread widening at Sunday open / Friday close |

---

## 3. Forward Operational Workflow & Audit Trail

1. **Friday Observation Cutoff (17:00 ET / 21:00 UTC)**:
   - Weekly market data ingests the final COMEX gold settle, 10Y real yield publication, DXY close, and VIX settle.
   - Run data freshness verification:
     ```bash
     python predict_weekly_bias.py --freshness
     ```
   - All series must report `FRESH` (age $\le 3.5$ days). If degraded, trigger `DATA_QUALITY_FAILURE` (No Trade).

2. **Automated Prediction Logging**:
   - Every Friday before Monday Asian open (22:00 UTC), execute forward prediction:
     ```bash
     python predict_weekly_bias.py --latest --recursive --brief --journal-log --decision FOLLOW
     ```
   - The forecast is appended to `data/shadow_predictions.csv` and `data/journal/trade_journal.csv` with an immutable UTC timestamp.

3. **Weekend Discretionary Review**:
   - The human trader reviews the **Live Decision Brief**:
     - Check **Circuit Breaker Status**: If `DO NOT TRADE`, trader stands aside.
     - Check **Confidence Tier**: Low (<0.15), Moderate (0.15-0.30), High ($\ge$0.30).
     - Check **Scenario Map**: Invalidation thresholds and support/resistance boundaries.
   - If the trader overrides or modifies the setup, the override rationale is recorded in the trade journal before Monday open.

4. **Friday Close Resolution & Post-Mortem**:
   - At the following Friday 17:00 ET close, the realized weekly return and OHLC levels are observed.
   - The recursive engine evaluates the error, classifies the failure archetype, and updates Kalman state vectors.
   - The trade journal is updated with `actual_entry_price`, `actual_exit_price`, and `realized_pnl_pct`.

---

## 4. Evaluation Milestones & Checkpoints

The shadow test will evaluate out-of-sample forward performance across three formal checkpoints:

| Checkpoint | Target Weeks | Expected Resolution Date | Primary Success Criteria |
|---|---:|:---:|---|
| **Phase 1** | 13 Weeks | 2026-12-18 | Win Rate $\ge 60\%$, Sharpe $\ge 1.50$, MaxDD $\le 5.0\%$ |
| **Phase 2** | 26 Weeks | 2027-03-19 | Win Rate $\ge 60\%$, Sharpe $\ge 1.80$, MaxDD $\le 6.0\%$ |
| **Phase 3** | 52 Weeks | 2027-09-17 | Net Return $\ge 30\%$, Sharpe $\ge 2.00$, MaxDD $\le 7.5\%$ |

---

## 5. Non-Intervention & Integrity Rules

1. **Zero Mid-Flight Tuning**: No parameters (thresholds, stop levels, Kalman gains, or features) may be altered during a phase.
2. **Pre-Trade Timestamping**: Any trade logged after Sunday 22:00 UTC (market open) is classified as invalid and excluded from official performance audits.
3. **Double Logging**: Model raw signals and discretionary human overrides are tracked in separate parallel ledgers to measure human alpha vs algorithmic edge.
