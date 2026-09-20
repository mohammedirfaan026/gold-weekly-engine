# Point-in-Time & Vintage Lineage Audit

**Audit Date:** 2026-09-20  
**Scope:** Rigorous examination of observation dates, publication timestamps, availability lags, and historical vintage revision risks across all 112 variables in the research feature matrix.

---

## 1. Executive Summary & Audit Mandate

A feature matrix cannot be described as "leakage-free" solely because `available_timestamp <= prediction_timestamp`. If an economic time series incorporates data revisions released months or years after the observation date, using the currently published series introduces severe **look-ahead revision bias**.

### Classification Taxonomy
Every feature in the Gold Research Engine is categorized under one of four strict standards:
1. **`TRUE_POINT_IN_TIME`**: The historical series represents immutable market prices or initial releases that are never revised. Permitted in strict production models.
2. **`VINTAGE_AVAILABLE`**: The underlying data source provides a real-time historical vintage archive (e.g., ALFRED point-in-time snapshots). Permitted only if verified against the initial release vintage.
3. **`POTENTIAL_REVISION_BIAS`**: The series reflects revised or benchmarked historical values from statistical agencies (BLS, BEA) without full real-time vintage isolation. **Disallowed in strict models unless vintaged**.
4. **`UNKNOWN`**: Data lineage cannot be independently verified from primary exchange logs. Disallowed in strict models.

---

## 2. Lineage & Vintage Audit by Information Layer

### A. Market Prices, Rates, and Technical Features
- **Data Sources**: COMEX, NYMEX, LBMA, US Treasury, FRED (H.15).
- **Revision Risk**: **NONE**.
- **Audit Finding**: [PASS] Traded market prices, moving averages, Treasury nominal yields, and TIPS real yields are settled daily. Historical closes are final and never revised retroactively.
- **Classification**: `TRUE_POINT_IN_TIME`.

### B. CFTC Commitments of Traders (COT) Positioning
- **Data Source**: Commodity Futures Trading Commission (CFTC).
- **Observation Time**: Tuesday 17:00 ET.
- **Publication Time**: Friday 15:30 ET.
- **Revision Risk**: **LOW**. Minor annual corrections occur, but the historical weekly releases reflect the exact numbers disseminated to the market on Friday afternoons.
- **Classification**: `TRUE_POINT_IN_TIME`.

### C. Physical Gold ETF Flows
- **Data Sources**: SPDR Gold Shares (GLD), iShares Gold Trust (IAU), Bloomberg / World Gold Council.
- **Revision Risk**: **MEDIUM**. Share creation and redemption operates on a T+2 clearing cycle; historical flow data can undergo minor share reconciliation adjustments.
- **Classification**: `VINTAGE_AVAILABLE`.

### D. Macroeconomic Release Surprises
- **Headline CPI & Core CPI**: `TRUE_POINT_IN_TIME`. Headline non-seasonally adjusted CPI is legally final and never revised. Seasonal factors are updated annually, but nominal monthly inflation prints stand.
- **FOMC Rate Decisions**: `TRUE_POINT_IN_TIME`. Fed target rates are policy actions and never revised.
- **ISM Manufacturing**: `TRUE_POINT_IN_TIME`. Survey diffusion indices are final on release day.
- **Nonfarm Payrolls (NFP)**: `POTENTIAL_REVISION_BIAS`. The BLS revises previous monthly payroll figures in each of the subsequent two months, followed by annual comprehensive benchmark revisions every February (often adjusting payrolls by hundreds of thousands of jobs).
- **GDP (Gross Domestic Product)**: `POTENTIAL_REVISION_BIAS`. The BEA issues "Advance", "Second", and "Third" releases over three consecutive months, followed by annual updates every July and comprehensive benchmark updates every five years.
- **PCE & Core PCE Deflator**: `POTENTIAL_REVISION_BIAS`. The Fed's preferred inflation gauge is revised frequently in conjunction with personal income and GDP updates.

---

## 3. Comprehensive Feature-by-Feature Vintage Classification

| Feature Name | Source | Vintage Status | Revision Risk | Allowed in Strict Model? | Audit Justification |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `gold_return_1w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Traded market close; immutable. |
| `gold_return_4w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Traded market close; immutable. |
| `gold_return_12w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Traded market close; immutable. |
| `gold_ma_20w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Rolling mean of immutable historical closes. |
| `gold_ma_50w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Rolling mean of immutable historical closes. |
| `gold_distance_20w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Price relative to moving average; immutable. |
| `gold_distance_50w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Price relative to moving average; immutable. |
| `gold_trend` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Categorical trend state based on immutable closes. |
| `gold_volatility_20w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Realized volatility of immutable historical closes. |
| `gold_momentum` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | 4-week price momentum; immutable. |
| `real_10y_yield` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Daily 10Y TIPS real yield; official daily series. |
| `delta_real_yield_1w` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Weekly difference of official daily TIPS yields. |
| `delta_real_yield_4w` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Monthly difference of official daily TIPS yields. |
| `us10y` | US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 10Y nominal Treasury yield; final daily close. |
| `us2y` | US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 2Y nominal Treasury yield; final daily close. |
| `delta_nominal_yield_1w`| US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in 10Y Treasury yield; immutable. |
| `breakeven_10y` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Nominal 10Y minus 10Y TIPS; immutable market spread. |
| `delta_breakeven_1w` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in breakeven inflation rate. |
| `yield_curve_2s10s` | US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 10Y minus 2Y slope; immutable market spread. |
| `delta_yield_curve_1w` | US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in 2s10s slope. |
| `dxy` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | US Dollar Index closing value; immutable. |
| `dxy_return_1w` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week DXY return; immutable. |
| `dxy_return_4w` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | 4-week DXY return; immutable. |
| `sp500_return_1w` | S&P Dow Jones | `TRUE_POINT_IN_TIME` | None | **Yes** | S&P 500 weekly return; immutable. |
| `vix` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | Cboe Volatility Index closing level; immutable. |
| `vix_change_1w` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in VIX level. |
| `vix_percentile` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante percentile of immutable VIX closes. |
| `hy_oas` | ICE BofA | `TRUE_POINT_IN_TIME` | Low | **Yes** | High yield credit spread; T+1 official publication. |
| `hy_oas_change_1w` | ICE BofA | `TRUE_POINT_IN_TIME` | Low | **Yes** | 1-week change in credit spread. |
| `wti_return_1w` | NYMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | WTI crude oil futures return; immutable. |
| `silver_return_1w` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | COMEX silver futures return; immutable. |
| `cot_net_speculative` | CFTC | `TRUE_POINT_IN_TIME` | Low | **Yes** | Published Friday 15:30 ET for prior Tuesday. |
| `cot_change_1w` | CFTC | `TRUE_POINT_IN_TIME` | Low | **Yes** | 1-week change in net speculative contracts. |
| `cot_percentile_3y` | CFTC | `TRUE_POINT_IN_TIME` | Low | **Yes** | Expanding 3-year ex-ante percentile of COT. |
| `etf_flow` | Bloomberg / WGC | `VINTAGE_AVAILABLE` | Medium | **Yes** | ETF share flows; minor T+2 settlement revisions. |
| `etf_flow_percentile` | Bloomberg / WGC | `VINTAGE_AVAILABLE` | Medium | **Yes** | Expanding percentile of ETF flows. |
| `etf_flow_change` | Bloomberg / WGC | `VINTAGE_AVAILABLE` | Medium | **Yes** | 1-week change in ETF flow. |
| `cpi_surprise` | BLS | `TRUE_POINT_IN_TIME` | Low | **Yes** | Headline CPI print is legally unrevised. |
| `cpi_zscore` | BLS | `TRUE_POINT_IN_TIME` | Low | **Yes** | Expanding standard deviation z-score; ex-ante. |
| `core_cpi_surprise` | BLS | `TRUE_POINT_IN_TIME` | Low | **Yes** | Core CPI release surprise; unrevised. |
| `core_cpi_zscore` | BLS | `TRUE_POINT_IN_TIME` | Low | **Yes** | Expanding standard deviation z-score; ex-ante. |
| `pce_surprise` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Subject to subsequent benchmark updates. |
| `pce_zscore` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Subject to subsequent benchmark updates. |
| `core_pce_surprise` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Subject to subsequent benchmark updates. |
| `core_pce_zscore` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Subject to subsequent benchmark updates. |
| `gdp_surprise` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Advance/Second/Third/Benchmark revision cycle. |
| `gdp_zscore` | BEA | `POTENTIAL_REVISION_BIAS`| High | **No** | Advance/Second/Third/Benchmark revision cycle. |
| `nfp_surprise` | BLS | `POTENTIAL_REVISION_BIAS`| High | **No** | Revised in T+1, T+2 months, and annual benchmarks. |
| `nfp_zscore` | BLS | `POTENTIAL_REVISION_BIAS`| High | **No** | Revised in T+1, T+2 months, and annual benchmarks. |
| `ism_surprise` | ISM | `TRUE_POINT_IN_TIME` | Low | **Yes** | Monthly survey diffusion index; stable on release. |
| `ism_zscore` | ISM | `TRUE_POINT_IN_TIME` | Low | **Yes** | Expanding standard deviation z-score; ex-ante. |
| `fomc_surprise` | Federal Reserve | `TRUE_POINT_IN_TIME` | None | **Yes** | Rate decision is an immutable policy action. |
| `fomc_zscore` | Federal Reserve | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding standard deviation z-score; ex-ante. |
| `event_count` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Known ex-ante from annual statistical calendars. |
| `high_impact_event_count`| Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Known ex-ante from annual statistical calendars. |
| `major_event_this_week`| Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Known ex-ante from annual statistical calendars. |
| `major_event_next_week`| Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Known ex-ante from annual statistical calendars. |
| `is_cpi_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled release date. |
| `is_pce_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled release date. |
| `is_fomc_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled FOMC meeting date. |
| `is_nfp_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled release date. |
| `is_gdp_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled release date. |
| `is_ism_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled release date. |
| `is_multiple_event_week`| Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled calendar overlap. |
| `is_no_event_week` | Calendar Schedule | `TRUE_POINT_IN_TIME` | None | **Yes** | Pre-scheduled quiet calendar week. |
| `sp500_shock_z` | S&P Dow Jones | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante z-score on immutable returns. |
| `dxy_shock_z` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante z-score on immutable returns. |
| `real_yield_shock_z` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante z-score on immutable yields. |
| `vix_shock_z` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante z-score on immutable VIX closes. |
| `gold_shock_z` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante z-score on immutable gold closes. |
| `sp500_shock_neg2s` | S&P Dow Jones | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `sp500_shock_neg3s` | S&P Dow Jones | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `dxy_shock_pos2s` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `dxy_shock_neg2s` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `real_yield_shock_pos2s`| FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `real_yield_shock_neg2s`| FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `vix_shock_pos2s` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | Binary threshold on ex-ante shock score. |
| `real_yield_regime` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante tercile on immutable yields. |
| `dxy_regime` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante tercile on immutable returns. |
| `gold_trend_regime` | COMEX | `TRUE_POINT_IN_TIME` | None | **Yes** | Immutable moving average sign. |
| `vix_regime` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante percentile threshold. |
| `equity_regime` | S&P Dow Jones | `TRUE_POINT_IN_TIME` | None | **Yes** | Expanding ex-ante tercile on immutable returns. |
| `positioning_regime` | CFTC | `TRUE_POINT_IN_TIME` | Low | **Yes** | Expanding ex-ante percentile of CFTC COT. |
| `yield_transmission` | FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in TIPS real yield. |
| `dxy_transmission` | ICE | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week return in DXY. |
| `breakeven_transmission`| FRED / US Treasury | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in breakeven rate. |
| `risk_transmission` | Cboe | `TRUE_POINT_IN_TIME` | None | **Yes** | 1-week change in VIX level. |
| `cpi_surprise_x_real_yield_regime` | Engineered | `TRUE_POINT_IN_TIME` | Low | **Yes** | Product of unrevised CPI and ex-ante yield regime. |
| `cpi_surprise_x_dxy_regime` | Engineered | `TRUE_POINT_IN_TIME` | Low | **Yes** | Product of unrevised CPI and ex-ante DXY regime. |
| `cpi_surprise_x_gold_trend` | Engineered | `TRUE_POINT_IN_TIME` | Low | **Yes** | Product of unrevised CPI and immutable trend. |
| `pce_surprise_x_real_yield_regime` | Engineered | `POTENTIAL_REVISION_BIAS`| High | **No** | Inherits PCE revision bias. |
| `cot_percentile_x_gold_trend` | Engineered | `TRUE_POINT_IN_TIME` | Low | **Yes** | Product of ex-ante COT and immutable trend. |
| `etf_flow_percentile_x_gold_trend`| Engineered | `VINTAGE_AVAILABLE` | Medium | **Yes** | Product of ETF flows and immutable trend. |
| `vix_shock_x_sp500_return` | Engineered | `TRUE_POINT_IN_TIME` | None | **Yes** | Interaction of immutable market series. |
| `dxy_shock_x_real_yield_change` | Engineered | `TRUE_POINT_IN_TIME` | None | **Yes** | Interaction of immutable market series. |

---

## 4. Policy Recommendations for Production Inference

1. **Strict Core Model**: Must exclude all features marked as `POTENTIAL_REVISION_BIAS` (`pce_*`, `gdp_*`, `nfp_*`, and their interaction terms) unless paired with an ALFRED first-release vintage pipeline.
2. **Robustness Benchmark**: In our walk-forward tests, the top-performing model (**Baseline 4: Real Yield Only**) uses `delta_real_yield_1w`, which is classified as `TRUE_POINT_IN_TIME` with **zero revision risk**. Its empirical performance is completely immune to macro revision bias.
