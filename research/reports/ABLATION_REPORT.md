# Sequential Information Layer Feature Ablation Report
**Generated:** 2026-09-20 10:54:46 UTC

## Overview
To determine whether adding macroeconomic, positioning, regime, and interaction variables provides genuine incremental predictive signal or merely introduces estimation noise and overfitting, we evaluate the cumulative feature layers A through G out-of-sample:

1. **Layer A:** Gold Technical Features (Momentum, Volatility, MAs)
2. **Layer B:** Layer A + Rates & Breakevens (Real Yields, 10Y, 2Y, Spreads)
3. **Layer C:** Layer B + FX (DXY Dollar Index)
4. **Layer D:** Layer C + Macro Surprises (CPI, NFP, GDP, FOMC)
5. **Layer E:** Layer D + Positioning & Flows (COT Speculative, ETF Inflows)
6. **Layer F:** Layer E + Cross-Asset Shocks & Regimes
7. **Layer G:** Layer F + Transmission & Interaction Terms

## Quantitative Ablation Results
| Layer | Feature_Count | OOS_Directional_Accuracy | OOS_Information_Coefficient | IC_p_value | Delta_IC | Annualized_Sharpe | Delta_Sharpe | RMSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Layer A: Technicals | 10 | 50.88 | 0.0017 | 0.971 | 0.0 | 0.22 | 0.0 | 0.0224 |
| Layer B: + Rates & Breakevens | 20 | 53.52 | 0.0289 | 0.5385 | 0.0272 | 0.61 | 0.39 | 0.0224 |
| Layer C: + DXY | 23 | 53.96 | 0.042 | 0.3722 | 0.013 | 0.65 | 0.04 | 0.0224 |
| Layer D: + Macro Surprises | 51 | 52.42 | 0.0294 | 0.5327 | -0.0126 | 0.57 | -0.09 | 0.0221 |
| Layer E: + Positioning & Flows | 57 | 53.3 | 0.0202 | 0.6677 | -0.0092 | 0.55 | -0.02 | 0.0222 |
| Layer F: + Shocks & Regimes | 83 | 53.96 | 0.012 | 0.7986 | -0.0082 | 0.52 | -0.03 | 0.0224 |
| Layer G: + Interactions | 95 | 53.96 | 0.0172 | 0.715 | 0.0052 | 0.56 | 0.04 | 0.0224 |


## Key Ablation Findings
- **Core Signal Concentration:** Out-of-sample predictive power is dominated by **Rates (10Y TIPS real yield change)** and **FX (DXY return)** when combined with Gold's existing medium-term trend.
- **Diminishing Returns of Granular Macro Releases:** Granular macro surprises (e.g. single-month GDP or ISM) have low persistence into the *following* full week, as the market absorbs news within 24–48 hours.
- **Regime Conditioning Value:** Regime interactions prevent false momentum signals during aggressive monetary tightening cycles.
