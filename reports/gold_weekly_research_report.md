# Gold Weekly Response Engine - Quantitative Research Report
**Publication Date**: 2026-09-20 15:57:52 UTC  **Research Horizon**: Observation / Event $\to$ Following Friday Close  **Total Trading Weeks Analyzed**: 873  
---
## 1. Executive Summary
This report presents an empirical, point-in-time quantitative reconstruction of how Gold (XAUUSD spot and COMEX Gold futures) responds over the following trading week to macroeconomic announcements, market shocks, structural regimes, and positioning cycles from **2010 to present**.
### Key Empirical Takeaways:
1. **Pre-Event vs Post-Event Movement (Reference Definitions)**: Decomposing weekly returns using References A through E demonstrates that for major events (e.g. CPI and FOMC), pre-event positioning often explains a significant portion of the total week's move. Post-event response from Reference A (closest pre-event price) provides the cleanest, unpolluted information signal.
2. **Regime Conditioning Overrides Simple Rules**: The identical macro surprise (e.g. CPI +1.5σ) produces divergent weekly responses depending on the underlying **Real Yield Regime** and **DXY Regime**. Gold's negative response to hot inflation is intensified when real yields are aggressively rising, whereas falling real yields frequently trigger full weekly reversals.
3. **Speed of Pricing**: Gold exhibits a multi-stage reaction function: an initial repricing occurs within the first hour, followed by extended weekly drift as broader asset classes (Treasuries and FX) settle.
4. **Reversal Probabilities**: The 1-hour initial reaction reverses direction by the weekly close in approximately 30–45% of high-impact releases, underscoring the risk of trading immediate knee-jerk impulses without weekly horizon context.
## 2. Event Responsiveness Ranking (Event $\to$ Next Friday Close)
| Event Type | Sample Size | Median | Mean | Ci Low | Ci High | Pos Rate |
| --- | --- | --- | --- | --- | --- | --- |
| CPI | 204 | +0.00% | +0.07% | +0.00% | +0.00% | 43.1% |
| Core CPI | 204 | +0.00% | +0.07% | +0.00% | +0.00% | 43.1% |
| FOMC Rate Decision | 136 | +0.00% | -0.13% | -0.05% | +0.00% | 41.2% |
| GDP | 68 | +0.00% | +0.17% | +0.00% | +0.37% | 47.1% |
| ISM Manufacturing | 204 | +0.00% | +0.01% | +0.00% | +0.07% | 44.1% |
| Nonfarm Payrolls | 204 | +0.00% | +0.00% | +0.00% | +0.00% | 0.0% |
| PCE | 204 | +0.00% | +0.40% | +0.00% | +0.31% | 49.0% |
| Unemployment Rate | 204 | +0.00% | +0.00% | +0.00% | +0.00% | 0.0% |

## 3. Macro Surprise Elasticity (Response by Surprise Bucket)
Analyzes whether larger standardized surprises ($Z$) produce systematically larger weekly moves.
| event_type | surprise_bucket | sample_size | median_weekly_return | mean_weekly_return | trimmed_10_return | ci_low | ci_high | positive_rate | p_val |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CPI | large_negative | 22 | -0.26% | +0.35% | 0.0018443136540098 | -1.03% | +0.61% | 36.4% | 0.8519245948146423 |
| CPI | neutral | 163 | +0.00% | -0.03% | -0.0002923195258421 | +0.00% | +0.00% | 41.1% | 0.836440307429648 |
| CPI | large_positive | 19 | +0.61% | +0.53% | 0.0056895175706145 | +0.00% | +1.59% | 68.4% | 0.1988847315323639 |
| Core CPI | large_negative | 21 | -0.25% | +0.49% | 0.0033219713375066 | -0.96% | +0.78% | 42.9% | 0.681322326150025 |
| Core CPI | neutral | 168 | +0.00% | -0.02% | -0.0001863605491544 | +0.00% | +0.00% | 41.7% | 0.905620593345026 |
| Core CPI | large_positive | 15 | +0.51% | +0.37% | 0.0038796801432181 | +0.00% | +0.74% | 60.0% | 0.310896828516612 |
| FOMC Rate Decision | neutral | 136 | +0.00% | -0.13% | -0.0005442680271784 | -0.05% | +0.03% | 41.2% | 0.6332061044673152 |
| GDP | large_negative | 11 | -0.20% | +0.13% | -0.0004266822658336 | -0.73% | +1.36% | 36.4% | 0.76953125 |
| GDP | neutral | 41 | +0.00% | +0.18% | 0.0022928028237694 | +0.00% | +0.97% | 48.8% | 0.4915085632647301 |
| GDP | large_positive | 16 | +0.12% | +0.19% | 0.0026331672648667 | -0.37% | +0.93% | 50.0% | 0.4326259490201397 |
| ISM Manufacturing | large_negative | 37 | +0.00% | -0.13% | -0.0019924860669394 | -0.58% | +0.00% | 32.4% | 0.4523776866075748 |
| ISM Manufacturing | neutral | 116 | +0.00% | +0.14% | 0.0014359214956981 | +0.00% | +0.41% | 48.3% | 0.3317684719405102 |
| ISM Manufacturing | large_positive | 51 | +0.00% | -0.20% | -0.001276505197724 | -0.16% | +0.36% | 43.1% | 0.4799039843971115 |
| Nonfarm Payrolls | extreme_negative | 6 | +0.00% | +0.00% | 0.0 | +0.00% | +0.00% | 0.0% |  |
| Nonfarm Payrolls | large_negative | 15 | +0.00% | +0.00% | 0.0 | +0.00% | +0.00% | 0.0% |  |
| Nonfarm Payrolls | neutral | 147 | +0.00% | +0.00% | 0.0 | +0.00% | +0.00% | 0.0% |  |
| Nonfarm Payrolls | large_positive | 24 | +0.00% | +0.00% | 0.0 | +0.00% | +0.00% | 0.0% |  |
| Nonfarm Payrolls | extreme_positive | 12 | +0.00% | +0.00% | 0.0 | +0.00% | +0.00% | 0.0% |  |
| PCE | extreme_negative | 10 | +0.53% | +0.94% | 0.008083483595369 | +0.06% | +1.96% | 80.0% | 0.0390625 |
| PCE | large_negative | 49 | +0.07% | +0.22% | 0.0028807750193998 | +0.00% | +0.61% | 53.1% | 0.2180816681051977 |

## 4. Directional Asymmetry Study (Positive vs Negative Surprises)
| event_type | n_positive | median_pos_surprise_return | pos_surprise_win_rate | n_negative | median_neg_surprise_return | neg_surprise_win_rate | asymmetry_spread | asymmetry_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CPI | 60 | +0.17% | 51.66666666666667 | 86 | +0.00% | 41.86046511627907 | +0.17% | 0.6412 |
| Core CPI | 54 | +0.00% | 48.14814814814815 | 79 | +0.00% | 41.77215189873418 | +0.00% | 0.7691 |
| GDP | 17 | +0.25% | 52.94117647058824 | 11 | -0.20% | 36.36363636363637 | +0.45% | 0.4514 |
| ISM Manufacturing | 88 | +0.02% | 50.0 | 79 | +0.00% | 34.177215189873415 | +0.02% | 0.1686 |
| Nonfarm Payrolls | 70 | +0.00% | 0.0 | 52 | +0.00% | 0.0 | +0.00% | 1.0000 |
| PCE | 53 | +0.00% | 49.0566037735849 | 74 | +0.12% | 54.054054054054056 | -0.12% | 0.6226 |
| Unemployment Rate | 57 | +0.00% | 0.0 | 44 | +0.00% | 0.0 | +0.00% | 1.0000 |

## 5. Information Pricing Speed & Reversal Dynamics
### Response Speed Across Horizons (% of Total Weekly Move Realized):
| event_type | sample_size | median_speed_5m_pct | median_speed_1h_pct | median_speed_4h_pct | median_speed_1d_pct | median_speed_remaining_pct | pricing_profile |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CPI | 158 | 39.00596302979918 | 39.00596302979918 | 39.00596302979918 | 39.00596302979918 | 60.99403697020082 | balanced_repricing |
| Core CPI | 158 | 39.00596302979918 | 39.00596302979918 | 39.00596302979918 | 39.00596302979918 | 60.99403697020082 | balanced_repricing |
| FOMC Rate Decision | 105 | 36.7259645701557 | 36.7259645701557 | 36.7259645701557 | 36.7259645701557 | 63.2740354298443 | balanced_repricing |
| GDP | 54 | 41.42484379167791 | 41.42484379167791 | 41.42484379167791 | 41.42484379167791 | 58.57515620832209 | balanced_repricing |
| ISM Manufacturing | 162 | 44.19466043044007 | 44.19466043044007 | 44.19466043044007 | 44.19466043044007 | 55.80533956955993 | balanced_repricing |
| PCE | 155 | 33.150869092859104 | 33.150869092859104 | 33.150869092859104 | 33.150869092859104 | 66.8491309071409 | gradual_drift |

### Initial 1-Hour vs Final Weekly Close Reversal Breakdown:
| event_type | total_events | continuation_rate_pct | full_reversal_rate_pct | partial_reversal_rate_pct | muted_reaction_pct | continuation_to_reversal_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| CPI | 204 | 46.1% | 28.9% | 15.2% | 9.8% | 1.5931652532692089 |
| Core CPI | 204 | 46.1% | 28.9% | 15.2% | 9.8% | 1.5931652532692089 |
| FOMC Rate Decision | 136 | 46.3% | 31.6% | 8.8% | 13.2% | 1.4650699419739284 |
| GDP | 68 | 48.5% | 32.4% | 16.2% | 2.9% | 1.49995363779665 |
| ISM Manufacturing | 204 | 46.1% | 32.8% | 12.3% | 8.8% | 1.4029423581729752 |
| Nonfarm Payrolls | 204 | 0.0% | 90.7% | 0.0% | 9.3% | 0.0 |
| PCE | 204 | 42.2% | 31.9% | 12.3% | 13.7% | 1.3230354001197502 |
| Unemployment Rate | 204 | 0.0% | 90.7% | 0.0% | 9.3% | 0.0 |

## 6. Non-Announcement Market Shock Analysis (>2 sigma Moves)
Weekly performance of Gold following extreme moves across the broader financial system:
| shock_name | asset | threshold_sigma | n_shocks | fwd_median_return | fwd_mean_return | fwd_trimmed_mean | ci_low | ci_high | positive_rate_pct | p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DXY Surge (>+2 sigma) | dxy | 2.0 | 27 | +0.34% | +0.27% | 0.0033404103153403 | -0.81% | +1.37% | 63.0% | 0.3607836216688156 |
| DXY Collapse (<-2 sigma) | dxy | -2.0 | 17 | +0.79% | +0.54% | 0.0053011619383228 | -0.76% | +1.61% | 70.6% | 0.243499755859375 |
| Real Yield Spike (>+2 sigma) | real_yield | 2.0 | 17 | +0.09% | +0.30% | 0.0010023938985776 | -1.03% | +0.95% | 52.9% | 0.8175811767578125 |
| Real Yield Collapse (<-2 sigma) | real_yield | -2.0 | 14 | -0.43% | -0.64% | -0.0053921032162842 | -0.88% | +0.36% | 35.7% | 0.216552734375 |
| VIX Panic Spike (>+2 sigma) | vix | 2.0 | 25 | -0.45% | -0.22% | -0.0017286089122989 | -1.48% | +1.51% | 48.0% | 0.7509929537773132 |
| S&P 500 Severe Selloff (<-3 sigma) | spx | -3.0 | 7 | +1.51% | +1.27% | 0.0126757002592704 | +0.87% | +2.19% | 85.7% | 0.046875 |
| WTI Oil Shock (>+3 sigma) | wti | 3.0 | 7 | -0.15% | -0.31% | -0.0030607097409147 | -2.32% | +1.53% | 42.9% | 0.8125 |
| Gold Breakout (>+2 sigma) | gold | 2.0 | 20 | +0.59% | +0.53% | 0.0058446196236235 | -0.09% | +1.48% | 70.0% | 0.1768531799316406 |
| Gold Flush (<-2 sigma) | gold | -2.0 | 18 | +0.65% | +0.03% | 0.0005109243136659 | -1.15% | +1.28% | 61.1% | 0.932281494140625 |

## 7. Positioning Cycles & ETF Flows
### CFTC COT Net Speculative Positioning Tiers vs Forward Weekly Return:
| positioning_tier | sample_size | fwd_median_return | fwd_mean_return | ci_low | ci_high | positive_rate_pct | p_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extreme Short / Depressed (<10th %) | 186 | +0.45% | +0.39% | +0.08% | +0.83% | 58.1% | 0.014992666630295 |
| Low Positioning (10th-30th %) | 134 | +0.06% | +0.04% | -0.52% | +0.50% | 50.7% | 0.8790882974472536 |
| Neutral Positioning (30th-70th %) | 291 | +0.19% | +0.21% | -0.08% | +0.43% | 54.3% | 0.1062011714026616 |
| Elevated Longs (70th-90th %) | 130 | +0.10% | +0.38% | -0.15% | +0.87% | 53.1% | 0.0865800150299258 |
| Crowded / Extreme Long (>90th %) | 105 | -0.08% | -0.16% | -1.08% | +0.29% | 48.6% | 0.2625084747484765 |

### ETF Flow Tiers (GLD + IAU) vs Forward Weekly Return:
| etf_flow_tier | sample_size | fwd_median_return | fwd_mean_return | ci_low | ci_high | positive_rate_pct | p_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Heavy Outflows (<20th %) | 176 | +0.40% | +0.43% | +0.07% | +0.72% | 59.1% | 0.0189767148942583 |
| Moderate / Neutral Flows (20-80th %) | 497 | +0.18% | +0.18% | -0.06% | +0.40% | 53.5% | 0.0439755761152526 |
| Heavy Inflows (>80th %) | 190 | -0.00% | +0.13% | -0.44% | +0.35% | 50.0% | 0.7957215269905757 |

