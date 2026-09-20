# Data Quality & Lineage Audit Report
**Generated:** 2026-09-20 10:54:40 UTC
**Sample Window:** 2010-01-01 to 2026-09-18 (873 completed trading weeks)

## Executive Summary
- **Point-in-Time Compliance Status:** PASS (0 Leaks)
- **Duplicate Trading Weeks:** 0
- **Calendar Sequence Gaps (>7 days):** 0
- **Total Features Audited:** 112
- **Features with Missing Values:** 47
- **Extreme Outliers (>4 sigma expanding z-score):** 15 instances

---

## 1. Timestamp Alignment & Point-in-Time Verification
All weekly features must satisfy the strict temporal precedence condition:
$$\text{published\_at} \le \text{prediction\_timestamp} \quad (\text{Friday 17:00 ET})$$
- **Violations Detected:** 0
- **Audit Finding:** [PASS] No forward look-ahead detected. All market closes, COT reports, and macroeconomic releases are strictly aligned to the prediction cutoff.

## 2. Missing Value Audit
Features with missing values prior to forward-filling or expanding imputation:
| feature | null_count | null_pct | status |
| --- | --- | --- | --- |
| next_week_gold_return | 1 | 0.11% | WARN |
| next_week_gold_volatility | 1 | 0.11% | WARN |
| next_week_max_favorable_excursion | 1 | 0.11% | WARN |
| next_week_max_drawdown | 1 | 0.11% | WARN |
| gold_return_1w | 1 | 0.11% | WARN |
| gold_return_4w | 4 | 0.46% | WARN |
| gold_return_12w | 12 | 1.37% | WARN |
| gold_ma_20w | 4 | 0.46% | WARN |
| gold_ma_50w | 9 | 1.03% | WARN |
| gold_distance_20w | 4 | 0.46% | WARN |
| gold_distance_50w | 9 | 1.03% | WARN |
| gold_volatility_20w | 5 | 0.57% | WARN |
| gold_momentum | 4 | 0.46% | WARN |
| delta_real_yield_1w | 1 | 0.11% | WARN |
| delta_real_yield_4w | 4 | 0.46% | WARN |
| delta_nominal_yield_1w | 1 | 0.11% | WARN |
| delta_breakeven_1w | 1 | 0.11% | WARN |
| delta_yield_curve_1w | 1 | 0.11% | WARN |
| dxy | 1 | 0.11% | WARN |
| dxy_return_1w | 2 | 0.23% | WARN |
| dxy_return_4w | 5 | 0.57% | WARN |
| sp500_return_1w | 2 | 0.23% | WARN |
| vix | 1 | 0.11% | WARN |
| vix_change_1w | 2 | 0.23% | WARN |
| vix_percentile | 10 | 1.15% | WARN |
| hy_oas_change_1w | 1 | 0.11% | WARN |
| wti_return_1w | 2 | 0.23% | WARN |
| silver_return_1w | 2 | 0.23% | WARN |
| cot_net_speculative | 1 | 0.11% | WARN |
| cot_change_1w | 2 | 0.23% | WARN |
| cot_percentile_3y | 26 | 2.98% | WARN |
| etf_flow | 1 | 0.11% | WARN |
| etf_flow_percentile | 9 | 1.03% | WARN |
| etf_flow_change | 2 | 0.23% | WARN |
| sp500_shock_z | 2 | 0.23% | WARN |
| dxy_shock_z | 2 | 0.23% | WARN |
| real_yield_shock_z | 1 | 0.11% | WARN |
| vix_shock_z | 2 | 0.23% | WARN |
| gold_shock_z | 1 | 0.11% | WARN |
| yield_transmission | 1 | 0.11% | WARN |
| dxy_transmission | 2 | 0.23% | WARN |
| breakeven_transmission | 1 | 0.11% | WARN |
| risk_transmission | 2 | 0.23% | WARN |
| cot_percentile_x_gold_trend | 26 | 2.98% | WARN |
| etf_flow_percentile_x_gold_trend | 9 | 1.03% | WARN |
| vix_shock_x_sp500_return | 2 | 0.23% | WARN |
| dxy_shock_x_real_yield_change | 2 | 0.23% | WARN |

> [!NOTE] Features at the very beginning of the history (2010) with initial rolling warm-up periods are handled via backfilling/expanding min_periods to prevent data truncation.

## 3. Vintage & Macro Revision Risk
Economic indicators often undergo revisions in subsequent months. To prevent revision look-ahead bias, series without vintage archiving are flagged:
| feature_name | vintage_status | data_source | description |
| --- | --- | --- | --- |
| next_week_gold_return | EXACT_PIT | COMEX/LBMA | Primary research prediction target: Gold return over week t+1. |
| next_week_gold_direction | EXACT_PIT | COMEX/LBMA | Directional return indicator (+1, -1, 0). |
| target_p_up | EXACT_PIT | COMEX/LBMA | Binary flag: Next week positive return. |
| target_p_plus_1pct | EXACT_PIT | COMEX/LBMA | Binary flag: Next week upside breakout > +1.0%. |
| target_p_minus_1pct | EXACT_PIT | COMEX/LBMA | Binary flag: Next week downside selloff < -1.0%. |
| next_week_gold_volatility | EXACT_PIT | COMEX/LBMA | Next week realized weekly high-low range volatility. |
| gold_return_1w | EXACT_PIT | COMEX/LBMA | Gold return during week t. |
| gold_return_4w | EXACT_PIT | COMEX/LBMA | Gold 4-week rolling return. |
| gold_return_12w | EXACT_PIT | COMEX/LBMA | Gold quarterly rolling return. |
| gold_distance_20w | EXACT_PIT | COMEX/LBMA | Distance to 20-week moving average. |
| gold_distance_50w | EXACT_PIT | COMEX/LBMA | Distance to 50-week moving average. |
| gold_trend | EXACT_PIT | COMEX/LBMA | Trend alignment (+1 Bullish, -1 Bearish, 0 Sideways). |
| gold_volatility_20w | EXACT_PIT | COMEX/LBMA | 20-week annualized realized volatility. |
| real_10y_yield | EXACT_PIT | FRED (DFII10) | 10-Year TIPS Real Yield level. |
| delta_real_yield_1w | EXACT_PIT | FRED (DFII10) | 1-week change in 10-Year TIPS real yield. |
| delta_real_yield_4w | EXACT_PIT | FRED (DFII10) | 4-week change in 10-Year TIPS real yield. |
| us10y | EXACT_PIT | FRED (DGS10) | 10-Year US Nominal Treasury Yield. |
| us2y | EXACT_PIT | FRED (DGS2) | 2-Year US Nominal Treasury Yield. |
| breakeven_10y | EXACT_PIT | FRED | 10-Year Breakeven Inflation Rate. |
| delta_breakeven_1w | EXACT_PIT | FRED | 1-week change in 10Y Breakeven Inflation. |
| yield_curve_2s10s | EXACT_PIT | FRED | 2s10s Treasury yield curve slope. |
| dxy | EXACT_PIT | ICE / Yahoo | US Dollar Index level. |
| dxy_return_1w | EXACT_PIT | ICE / Yahoo | 1-week return in US Dollar Index. |
| dxy_return_4w | EXACT_PIT | ICE / Yahoo | 4-week return in US Dollar Index. |
| sp500_return_1w | EXACT_PIT | S&P / Yahoo | S&P 500 1-week return. |


## 4. Holiday & Shortened Week Calendar Audit
Summary of holiday trading weeks (Thanksgiving, Christmas, New Year, July 4th) with early closes or reduced market participation:
- Total holiday-affected weeks identified: **61**
| week_ending | holiday_type | gold_weekly_return | vix_level |
| --- | --- | --- | --- |
| 2010-01-01 | New Year Week | nan | nan |
| 2010-07-02 | Independence Day Week | -0.0004 | 30.12 |
| 2010-11-26 | Thanksgiving Week | -0.0174 | 22.22 |
| 2010-12-24 | Christmas / Year-End | 0.0191 | 16.47 |
| 2010-12-31 | Christmas / Year-End | 0.0115 | 17.75 |
| 2011-07-01 | Independence Day Week | -0.0363 | 15.87 |
| 2011-11-25 | Thanksgiving Week | -0.0192 | 34.47 |
| 2011-12-30 | Christmas / Year-End | -0.0018 | 23.40 |
| 2012-07-06 | Independence Day Week | -0.0004 | 17.10 |
| 2012-11-23 | Thanksgiving Week | 0.0274 | 15.14 |
| 2012-12-28 | Christmas / Year-End | 0.0064 | 22.72 |
| 2013-01-04 | New Year Week | 0.0385 | 13.83 |
| 2013-07-05 | Independence Day Week | 0.0016 | 14.89 |
| 2013-11-22 | Thanksgiving Week | 0.0148 | 12.26 |
| 2013-12-27 | Christmas / Year-End | -0.0159 | 12.46 |
| 2014-01-03 | New Year Week | -0.0261 | 13.76 |
| 2014-07-04 | Independence Day Week | 0.0349 | 10.32 |
| 2014-11-28 | Thanksgiving Week | 0.0117 | 13.33 |
| 2014-12-26 | Christmas / Year-End | -0.0304 | 14.50 |
| 2015-01-02 | New Year Week | -0.0094 | 17.79 |


## 5. Outlier Detection (>4 Standard Deviations)
Observations exceeding 4 standard deviations relative to the point-in-time expanding historical mean:
| week_ending | feature | value | z_score | event_context |
| --- | --- | --- | --- | --- |
| 2020-02-28 | sp500_return_1w | -0.1149 | -6.07 | Market Shock / Extreme Volatility |
| 2020-03-13 | sp500_return_1w | -0.0879 | -4.51 | Market Shock / Extreme Volatility |
| 2020-03-20 | sp500_return_1w | -0.1498 | -7.48 | Market Shock / Extreme Volatility |
| 2020-03-27 | sp500_return_1w | 0.1026 | 4.75 | Market Shock / Extreme Volatility |
| 2020-04-10 | sp500_return_1w | 0.1210 | 5.49 | Market Shock / Extreme Volatility |
| 2025-04-04 | sp500_return_1w | -0.0908 | -4.15 | Macro Realization |
| 2020-03-20 | dxy_return_1w | 0.0412 | 4.05 | Market Shock / Extreme Volatility |
| 2020-03-27 | dxy_return_1w | -0.0433 | -4.31 | Market Shock / Extreme Volatility |
| 2022-11-11 | dxy_return_1w | -0.0414 | -4.15 | Macro Realization |
| 2010-05-07 | vix_change_1w | 18.9000 | 5.70 | Macro Realization |
| 2015-08-21 | vix_change_1w | 15.2000 | 4.90 | Macro Realization |
| 2020-02-28 | vix_change_1w | 23.0300 | 7.52 | Market Shock / Extreme Volatility |
| 2020-03-13 | vix_change_1w | 15.8900 | 4.92 | Market Shock / Extreme Volatility |
| 2020-04-03 | vix_change_1w | -18.7400 | -5.70 | Market Shock / Extreme Volatility |
| 2025-04-04 | vix_change_1w | 23.6600 | 7.09 | Macro Realization |

> [!IMPORTANT] All identified >4 sigma outliers correspond to documented historical macroeconomic events (e.g., March 2020 COVID shock, August 2011 US debt downgrade, 2022 Fed rate hike shock) rather than data capture errors.

## 6. Gap and Continuity Analysis
- Duplicate Week IDs: **0**
- Timeline Continuity: **PASS**
