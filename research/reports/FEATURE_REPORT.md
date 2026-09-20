# Feature Engineering & Lineage Report
**Generated:** 2026-09-20 10:54:46 UTC

## Executive Overview
Total engineered features: **57**
All features strictly enforce point-in-time publication cutoffs (Friday 17:00 ET). Expanding-window statistics are utilized for all rolling normalizations, standard deviations, and regime quantiles to eliminate look-ahead bias.

### Feature Distribution by Information Layer
| Information Layer / Category | Feature Count |
| --- | --- |
| RATES_BREAKEVENS | 8 |
| MACRO_SURPRISE | 8 |
| GOLD_TECHNICAL | 7 |
| TARGET | 6 |
| REGIME | 6 |
| RISK_EQUITIES | 5 |
| POSITIONING | 5 |
| INTERACTION | 5 |
| CROSS_ASSET_SHOCK | 4 |
| FX | 3 |


### Point-in-Time & Vintage Classification
| Vintage Status | Count |
| --- | --- |
| EXACT_PIT | 49 |
| POTENTIAL_REVISION_BIAS | 8 |


### Top 20 Features by Correlation with Next-Week Gold Return
| feature | linear_correlation |
| --- | --- |
| next_week_max_favorable_excursion | 0.851 |
| next_week_max_drawdown | 0.8297 |
| next_week_gold_direction | 0.797 |
| real_yield_shock_z | 0.0886 |
| delta_real_yield_1w | 0.0865 |
| yield_transmission | 0.0865 |
| delta_nominal_yield_1w | 0.0865 |
| gold_momentum | -0.0798 |
| gold_return_4w | -0.0798 |
| gold_close | -0.0794 |
| gold_ma_20w | -0.0774 |
| gold_return_12w | -0.0763 |
| gold_ma_50w | -0.0748 |
| gold_distance_20w | -0.0734 |
| is_no_event_week | 0.0705 |
| major_event_this_week | -0.0705 |
| us10y | -0.0679 |
| us2y | -0.0679 |
| real_10y_yield | -0.0679 |
| real_yield_regime | 0.0664 |


### Complete Feature Dictionary
| feature_name | category | vintage_status | publication_lag | transformation_formula | description |
| --- | --- | --- | --- | --- | --- |
| next_week_gold_return | TARGET | EXACT_PIT | Next Friday 17:00 ET | Close(t+1) / Close(t) - 1.0 | Primary research prediction target: Gold return over week t+1. |
| next_week_gold_direction | TARGET | EXACT_PIT | Next Friday 17:00 ET | sign(next_week_gold_return) | Directional return indicator (+1, -1, 0). |
| target_p_up | TARGET | EXACT_PIT | Next Friday 17:00 ET | 1 if return > 0 else 0 | Binary flag: Next week positive return. |
| target_p_plus_1pct | TARGET | EXACT_PIT | Next Friday 17:00 ET | 1 if return > 0.01 else 0 | Binary flag: Next week upside breakout > +1.0%. |
| target_p_minus_1pct | TARGET | EXACT_PIT | Next Friday 17:00 ET | 1 if return < -0.01 else 0 | Binary flag: Next week downside selloff < -1.0%. |
| next_week_gold_volatility | TARGET | EXACT_PIT | Next Friday 17:00 ET | (High(t+1) - Low(t+1)) / Close(t) | Next week realized weekly high-low range volatility. |
| gold_return_1w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | Close(t) / Close(t-1) - 1.0 | Gold return during week t. |
| gold_return_4w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | Close(t) / Close(t-4) - 1.0 | Gold 4-week rolling return. |
| gold_return_12w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | Close(t) / Close(t-12) - 1.0 | Gold quarterly rolling return. |
| gold_distance_20w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | Close(t) / MA_20w(t) - 1.0 | Distance to 20-week moving average. |
| gold_distance_50w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | Close(t) / MA_50w(t) - 1.0 | Distance to 50-week moving average. |
| gold_trend | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | sign(Close - MA20w) if sign(MA20w - MA50w) matches else 0 | Trend alignment (+1 Bullish, -1 Bearish, 0 Sideways). |
| gold_volatility_20w | GOLD_TECHNICAL | EXACT_PIT | 0 hours (Fri 17:00 ET) | std(ret_1w, 20w) * sqrt(52) | 20-week annualized realized volatility. |
| real_10y_yield | RATES_BREAKEVENS | EXACT_PIT | 12 hours (Fri close pub Sat AM) | Level of 10Y TIPS | 10-Year TIPS Real Yield level. |
| delta_real_yield_1w | RATES_BREAKEVENS | EXACT_PIT | 12 hours | TIPS(t) - TIPS(t-1) | 1-week change in 10-Year TIPS real yield. |
| delta_real_yield_4w | RATES_BREAKEVENS | EXACT_PIT | 12 hours | TIPS(t) - TIPS(t-4) | 4-week change in 10-Year TIPS real yield. |
| us10y | RATES_BREAKEVENS | EXACT_PIT | 12 hours | Level of 10Y Treasury | 10-Year US Nominal Treasury Yield. |
| us2y | RATES_BREAKEVENS | EXACT_PIT | 12 hours | Level of 2Y Treasury | 2-Year US Nominal Treasury Yield. |
| breakeven_10y | RATES_BREAKEVENS | EXACT_PIT | 12 hours | us10y - real_10y_yield | 10-Year Breakeven Inflation Rate. |
| delta_breakeven_1w | RATES_BREAKEVENS | EXACT_PIT | 12 hours | breakeven(t) - breakeven(t-1) | 1-week change in 10Y Breakeven Inflation. |
| yield_curve_2s10s | RATES_BREAKEVENS | EXACT_PIT | 12 hours | us10y - us2y | 2s10s Treasury yield curve slope. |
| dxy | FX | EXACT_PIT | 0 hours | Level of US Dollar Index | US Dollar Index level. |
| dxy_return_1w | FX | EXACT_PIT | 0 hours | DXY(t) / DXY(t-1) - 1.0 | 1-week return in US Dollar Index. |
| dxy_return_4w | FX | EXACT_PIT | 0 hours | DXY(t) / DXY(t-4) - 1.0 | 4-week return in US Dollar Index. |
| sp500_return_1w | RISK_EQUITIES | EXACT_PIT | 0 hours | SPX(t) / SPX(t-1) - 1.0 | S&P 500 1-week return. |
| vix | RISK_EQUITIES | EXACT_PIT | 0 hours | Level of VIX | Cboe Volatility Index level. |
| vix_change_1w | RISK_EQUITIES | EXACT_PIT | 0 hours | VIX(t) - VIX(t-1) | 1-week change in VIX level. |
| vix_percentile | RISK_EQUITIES | EXACT_PIT | 0 hours | expanding_quantile(VIX) | Point-in-time expanding percentile of VIX. |
| hy_oas | RISK_EQUITIES | EXACT_PIT | 12 hours | Level of US High Yield Option-Adjusted Spread | US High Yield Credit Spread. |
| cot_net_speculative | POSITIONING | EXACT_PIT | 72 hours (Published Friday 15:30 ET) | NonComm_Long - NonComm_Short | CFTC COMEX Gold net speculative contracts. |
| cot_percentile_3y | POSITIONING | EXACT_PIT | 72 hours | expanding_quantile(cot_net_spec) | Expanding percentile of COT net speculative positioning. |
| cot_change_1w | POSITIONING | EXACT_PIT | 72 hours | cot_net_spec(t) - cot_net_spec(t-1) | 1-week change in COT net speculative contracts. |
| etf_flow | POSITIONING | EXACT_PIT | 0 hours | Sum of GLD + IAU estimated net weekly flows ($M) | Physical Gold ETF weekly fund flows. |
| etf_flow_percentile | POSITIONING | EXACT_PIT | 0 hours | expanding_quantile(etf_flow) | Expanding percentile of weekly ETF flows. |
| cpi_surprise | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published 08:30 ET | Actual - Consensus | CPI headline monthly surprise. |
| cpi_zscore | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published 08:30 ET | surprise / expanding_std(prior_surprises) | CPI standardized surprise Z-score. |
| pce_surprise | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published 08:30 ET | Actual - Consensus | PCE headline monthly surprise. |
| pce_zscore | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published 08:30 ET | surprise / expanding_std(prior_surprises) | PCE standardized surprise Z-score. |
| nfp_surprise | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published First Fri 08:30 ET | Actual - Consensus (k) | Nonfarm Payrolls employment surprise. |
| nfp_zscore | MACRO_SURPRISE | POTENTIAL_REVISION_BIAS | Published First Fri 08:30 ET | surprise / expanding_std(prior_surprises) | Nonfarm Payrolls standardized surprise Z-score. |
| fomc_surprise | MACRO_SURPRISE | EXACT_PIT | Published Wed 14:00 ET | Actual - Consensus Rate | FOMC rate decision surprise. |
| ism_surprise | MACRO_SURPRISE | EXACT_PIT | Published 10:00 ET | Actual - Consensus | ISM Manufacturing PMI surprise. |
| real_yield_regime | REGIME | EXACT_PIT | 12 hours | -1 if d_TIPS_4w <= Q33 else (+1 if >= Q67 else 0) | Real Yield Regime (-1 Falling, 0 Neutral, +1 Rising). |
| dxy_regime | REGIME | EXACT_PIT | 0 hours | -1 if dxy_ret_4w <= Q33 else (+1 if >= Q67 else 0) | DXY Regime (-1 Weakening, 0 Neutral, +1 Strengthening). |
| gold_trend_regime | REGIME | EXACT_PIT | 0 hours | gold_trend | Gold Trend Regime (-1 Bearish, 0 Sideways, +1 Bullish). |
| vix_regime | REGIME | EXACT_PIT | 0 hours | -1 if vix_pct < 25 else (+1 if > 75 else 0) | VIX Volatility Regime (-1 Low, 0 Normal, +1 High). |
| equity_regime | REGIME | EXACT_PIT | 0 hours | -1 if SPX_1w <= Q33 else (+1 if >= Q67 else 0) | Equity Market Regime (-1 Risk Off, 0 Neutral, +1 Risk On). |
| positioning_regime | REGIME | EXACT_PIT | 72 hours | Tiers from -2 (Extreme Short) to +2 (Extreme Long) | CFTC COT Speculative Positioning Regime. |
| sp500_shock_z | CROSS_ASSET_SHOCK | EXACT_PIT | 0 hours | (SPX_ret_1w - exp_mean) / exp_std | Standardized expanding shock score for S&P 500. |
| dxy_shock_z | CROSS_ASSET_SHOCK | EXACT_PIT | 0 hours | (DXY_ret_1w - exp_mean) / exp_std | Standardized expanding shock score for US Dollar Index. |
| real_yield_shock_z | CROSS_ASSET_SHOCK | EXACT_PIT | 12 hours | (d_TIPS_1w - exp_mean) / exp_std | Standardized expanding shock score for 10Y TIPS yield. |
| vix_shock_z | CROSS_ASSET_SHOCK | EXACT_PIT | 0 hours | (d_VIX_1w - exp_mean) / exp_std | Standardized expanding shock score for VIX. |
| cpi_surprise_x_real_yield_regime | INTERACTION | POTENTIAL_REVISION_BIAS | 0 hours | cpi_zscore * real_yield_regime | CPI surprise conditioned on Real Yield regime. |
| cpi_surprise_x_dxy_regime | INTERACTION | POTENTIAL_REVISION_BIAS | 0 hours | cpi_zscore * dxy_regime | CPI surprise conditioned on DXY regime. |
| cot_percentile_x_gold_trend | INTERACTION | EXACT_PIT | 0 hours | (cot_pct / 100) * gold_trend | COT Positioning conditioned on Gold Trend. |
| vix_shock_x_sp500_return | INTERACTION | EXACT_PIT | 0 hours | vix_shock_z * sp500_return_1w | VIX Panic shock interaction with equity selloff. |
| dxy_shock_x_real_yield_change | INTERACTION | EXACT_PIT | 0 hours | dxy_shock_z * delta_real_yield_1w | DXY currency shock interaction with Real Yield move. |
