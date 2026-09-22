# 100-Trade Point-in-Time Backtest Executive Report

**Execution Date:** 2026-09-21 17:26 UTC  
**Evaluation Window:** 2024-07-05 to 2026-09-11 (115 weeks)  
**Total Executed Trades:** 100  
**Execution Timing:** Causal prediction at Friday 17:00 ET -> Trade execution at Friday close / Monday open -> Exit next Friday 17:00 ET  
**Cost Assumptions:** 5 bps commission + 5 bps execution slippage per trade (10 bps round-trip)

---

## 1. Key Performance Summary

| Metric | Recursive AI Engine | Static Macro Model | Buy & Hold Gold | Outperformance |
| :--- | :--- | :--- | :--- | :--- |
| **Total Net Return** | **+199.71%** | +0.45% | +18.86% | **+180.85%** |
| **CAGR (Annualized)** | **+64.27%** | +0.20% | +8.13% | — |
| **Sharpe Ratio** | **4.49** | 0.07 | 0.56 | **+3.93** |
| **Max Drawdown** | **-3.98%** | -12.93% | -20.25% | **Lower risk by 16.3 pts** |
| **Trade Win Rate** | **72.0%** | 44.1% | 53.0% | — |
| **Profit Factor** | **5.98** | 1.03 | 1.45 | — |
| **Expectancy / Trade** | **+0.97%** | +0.01% | +0.28% | — |

---

## 2. Trade Execution Diagnostics

- **Total Active Trades:** 100
  - **Long Positions:** 58 trades
  - **Short Positions:** 42 trades
  - **Flat / Cash Preservation:** 15 weeks
- **Win / Loss Dispersion:**
  - Average Winner: `+1.86%`
  - Average Loser: `-0.80%`
  - Win/Loss Ratio: `2.33`
  - Best Trade: `+4.97%`
  - Worst Trade: `-1.98%`
  - Longest Winning Streak: `8 consecutive wins`
  - Longest Losing Streak: `6 consecutive losses`

---

## 3. Statistical Significance & Baseline Gate

- **Bootstrap Difference Test vs Static Model:**
  - Mean Weekly Alpha: `+0.957%`
  - 95% Confidence Interval: `[0.599%, 1.315%]`
  - Bootstrap p-value: `p = 0.0000`
  - Permutation p-value: `p = 0.0000`
- **Conclusion:** The Recursive Self-Improving Engine demonstrates statistically significant alpha against static macro models and passive buy-and-hold benchmarks with strict transaction costs.
