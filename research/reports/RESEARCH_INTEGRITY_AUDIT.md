# Research Integrity Audit: Gold Predictive Research System

**Audit Date:** 2026-09-20  
**Audit Objective:** Independent, objective evaluation of all empirical claims, econometric methodology, point-in-time guarantees, and statistical conclusions in the Gold Weekly Predictive Research System.

---

## 1. Executive Summary & Core Principle

In quantitative research, passing unit tests establishes **code correctness**, but does not prove **statistical validity** or **economic truth**. 

This integrity audit treats every conclusion previously reported as a hypothesis that must survive rigorous independent scrutiny. Models were evaluated under strict out-of-sample walk-forward isolation (454 trading weeks from 2018 to 2026), exact binomial confidence intervals, block bootstrapping, permutation tests, Chow structural break tests, and multiple-testing False Discovery Rate (FDR) corrections.

### The Bottom Line
Evidence does **not** establish genuine, statistically significant out-of-sample return predictability for next-week gold returns ($R(t+1)$). 
- The highest-performing model (**Baseline 4: Real Yield Only**) produced an out-of-sample Information Coefficient of **+0.0316**, which is **statistically indistinguishable from zero ($p = 0.5014$)**.
- Its simulated Sharpe ratio of **0.65** is an artifact of an **87.2% long position posture** during a secular bull market in gold (2018–2026), evaluated under zero-cost, zero-slippage assumptions.
- Out of 12 foundational quantitative hypotheses, **zero (0) survive Benjamini-Hochberg FDR correction at the 5% level**.
- The previously asserted "structural break in 2022" is an unconfirmed economic hypothesis ($p = 0.5965$ on a formal Chow test).

---

## 2. Answers to the Nine Mandatory Audit Questions

### Question 1: What findings are genuinely supported?
1. **L2 Regularization and Shallow Trees Prevent Explosive Overfitting**: Ridge regression and shallow Random Forests maintained stable out-of-sample loss metrics, whereas unconstrained non-linear models and unregularized high-dimensional feature sets degraded rapidly out-of-sample.
2. **Weekly Gold Returns Exhibit Near-Zero Linear Serial Autocorrelation**: Lag-1 weekly autocorrelation is $\rho_1 = -0.0008$, and lag-2 is $\rho_2 = -0.0492$. Weekly COMEX gold returns behave as an efficient sub-martingale with a persistent positive drift (+0.076% per week).
3. **Timestamp Lineage Is Correctly Standardized**: Session boundaries, Friday 17:00 New York electronic market halts, and Sunday 18:00 New York session opens are accurately converted to UTC across all winter (EST, 22:00 UTC), summer (EDT, 21:00 UTC), and Daylight Saving Time transition boundaries.

---

### Question 2: What findings are merely suggestive?
1. **Directional Asymmetry of Real Yield Changes**: Baseline 4 achieved a Directional Accuracy of **55.95%** (Wilson 95% CI: `[51.35%, 60.44%]`). While statistically distinguishable from a 50/50 coin toss ($p = 0.0064$), it is **barely distinguishable from the market's unconditional up-week rate of 51.98% ($p = 0.0499$)**.
2. **Incremental Information Content of Rates and Dollar Index**: Sequential ablation demonstrated that combining 10Y TIPS real yields with the DXY Index (Layer C) maximized the out-of-sample Information Coefficient at +0.0420 (Sharpe = 0.65). While economically coherent, its statistical significance remains unproven ($p = 0.3722$).

---

### Question 3: What findings are unsupported?
1. **"Genuine Out-of-Sample Predictive Power"**: The primary predictive metric (Spearman IC) across all 11 models yielded $p$-values between 0.37 and 0.97. No model achieved statistically significant predictive rank correlation ($p < 0.05$).
2. **"Layer B and C Contribute Over 80% of Signal"**: Unsupported by any formal variance decomposition or Shapley attribution. It was an informal narrative characterization and is retracted.
3. **"A Structural Break Occurred in 2022"**: A formal Chow test for parameter stability yields $F = 0.5171$ ($p = 0.5965$). The change in regression slope is completely within expected random sampling noise.
4. **"Technical Momentum and Trend Following Predict Next-Week Returns"**: Both the 1-week lag return baseline and the 20w/50w moving average trend baseline produced **negative out-of-sample ICs** (-0.0615 and -0.0809, respectively).
5. **"Positioning (COT and ETF Flows) Provide Predictive Signal"**: Neither CFTC net speculative positioning ($r = +0.0205, p = 0.5451$) nor physical ETF flows ($r = +0.0244, p = 0.4728$) exhibited statistically significant predictive power. Adding Layer E degraded out-of-sample IC.
6. **"Calibrated Probabilities P(R > 0) Confirm Reliable Extreme Probabilities"**: The calibrated probability model produced a **negative Brier Skill Score (-0.1606)** and a calibration slope of -0.0026. The probability head carries zero discriminative power beyond the baseline sample average.
7. **"Rapid 24–48 Hour Macro Absorption"**: Intraday event returns in the processed dataset were filled from daily closing prices when minute bars were unavailable. The claim cannot be tested from this dataset.

---

### Question 4: Where does possible leakage remain?
1. **Macroeconomic Revision Bias (Unvintaged BLS/BEA Data)**:
   - Nonfarm Payrolls (NFP), Gross Domestic Product (GDP), and PCE Price Indices are subject to significant multi-month benchmark revisions.
   - Using contemporary published series from FRED rather than point-in-time ALFRED real-time first releases introduces potential look-ahead bias into these specific macro features.
   - *Mitigation*: The top-performing benchmark (**Baseline 4: Real Yield Only**) uses 10Y TIPS real yields, which are finalized daily by the US Treasury and carry **zero revision risk**.
2. **ETF Share Settlement Reconciliation**:
   - Physical ETF flow estimates can experience minor share reconciliation adjustments within T+2 settlement windows.
3. **Intraday Resolution Gap**:
   - Minute-level event horizons ($T+5\text{m}$ to $T+1\text{d}$) in `events_master.parquet` were approximated from daily bars and must not be used for high-frequency latency claims.

---

### Question 5: What is the effective sample size?
- **Full History (2010–2026)**: $N = 872$ weekly returns. With lag-1 autocorrelation $\rho_1 = +0.0051$, the effective sample size is:
  $$N_{\text{eff}} = N \cdot \frac{1 - \rho_1}{1 + \rho_1} = 872 \cdot \frac{0.9949}{1.0051} \approx \mathbf{863.2}$$
- **Out-of-Sample Window (2018–2026)**: $N = 454$ weekly returns. With $\rho_1 = -0.0008$:
  $$N_{\text{eff}} \approx \mathbf{454.7}$$
- **Finding**: Because weekly gold returns exhibit negligible linear serial autocorrelation, the effective sample size is virtually identical to the nominal sample size. However, macro announcements are temporally clustered (occurring predominantly on Wednesdays and Fridays).

---

### Question 6: Which relationships survive out-of-sample validation?
- **None survive at standard econometric significance ($p < 0.05$) on a continuous rank-correlation (IC) basis.**
- Only **Baseline 4 (Real Yield Only)** achieved an economically interesting Directional Accuracy of **55.95%**, but its 95% confidence interval spans `[51.24%, 60.57%]`, and its linear predictive power is statistically uncertain ($p = 0.5014$).

---

### Question 7: Which survive multiple-testing correction?
- In the 12-hypothesis ledger:
  - Significant before multiple-testing correction: **2** (Real Yield at unadjusted $p = 0.0234$ and DXY at unadjusted $p = 0.0469$).
  - **Significant after Benjamini-Hochberg False Discovery Rate (FDR) correction: ZERO (0)** (minimum $q = 0.1404$).
  - **Significant after Bonferroni correction: ZERO (0)** (minimum adjusted $p = 0.2808$).
- Every tested relationship must be categorized as **`EXPLORATORY`** rather than confirmatory.

---

### Question 8: Which survive across different historical regimes?
- **None demonstrate stationary, regime-invariant stability.**
- The correlation between 1-week real yield changes and forward gold returns fluctuates radically across sub-periods:
  - 2010–2014: $+0.1632$ ($p = 0.008$)
  - 2015–2019: $+0.0439$ ($p = 0.480$)
  - 2020–2021: $+0.0402$ ($p = 0.684$)
  - 2022–2023: $-0.0324$ ($p = 0.744$)
  - 2024–2026: $+0.0943$ ($p = 0.266$)
- In four out of five market regimes, the correlation is statistically indistinguishable from zero ($p > 0.25$).

---

### Question 9: What should be investigated next?
1. **Reframe from Directional Forecasting to Conditional Volatility & Tail Risk**:
   - Forecasting weekly directional sign ($R(t+1) > 0$) on an efficient asset like gold is notoriously close to a random walk.
   - Research should pivot toward modeling **conditional volatility**, **tail risk bounds (VaR / Expected Shortfall)**, and **realized trading range (MFE/MAE)**, where econometric predictability is historically much higher.
2. **Ingest Point-in-Time First-Release Vintage Macro Data**:
   - Replace FRED headline series with ALFRED first-release archives for NFP, GDP, and PCE to eliminate all lingering revision bias.
3. **Ingest Authentic 1-Minute Tick Data for Event Study Validation**:
   - Reconstruct true high-frequency response paths around CPI and FOMC announcements to test whether intraday absorption is complete within minutes.
4. **Explicitly Model Sovereign Central Bank Accumulation and Geopolitical Risk**:
   - Replace narrative explanations with observable time series: IMF International Financial Statistics (IFS) central bank gold reserve filings and the Caldara-Iacoviello Geopolitical Risk (GPR) Index.
5. **Enforce Transaction Cost and Turnover Penalties**:
   - All future model comparisons must evaluate net-of-cost performance with realistic execution friction (5–15 bps per turnover).

---

## 3. Summary Audit Table of Generated Reports

| Report Name | Status | Location | Key Content |
| :--- | :---: | :--- | :--- |
| **`RESEARCH_INTEGRITY_AUDIT.md`** | **COMPLETE** | [`research/reports/RESEARCH_INTEGRITY_AUDIT.md`](file:///d:/Gold/research/reports/RESEARCH_INTEGRITY_AUDIT.md) | High-level executive synthesis answering the 9 mandatory questions. |
| **`CLAIM_AUDIT.md`** | **COMPLETE** | [`research/reports/CLAIM_AUDIT.md`](file:///d:/Gold/research/reports/CLAIM_AUDIT.md) | Line-by-line audit and classification of all 12 claims in the final report. |
| **`TIMESTAMP_AUDIT.md`** | **COMPLETE** | [`research/reports/TIMESTAMP_AUDIT.md`](file:///d:/Gold/research/reports/TIMESTAMP_AUDIT.md) | Audit of timezone conversions, DST transitions, winter/summer cutoffs, and holidays. |
| **`POINT_IN_TIME_AUDIT.md`** | **COMPLETE** | [`research/reports/POINT_IN_TIME_AUDIT.md`](file:///d:/Gold/research/reports/POINT_IN_TIME_AUDIT.md) | Feature-by-feature classification of all 112 features by source, vintage, and revision risk. |
| **`STATISTICAL_SIGNIFICANCE_AUDIT.md`** | **COMPLETE** | [`research/reports/STATISTICAL_SIGNIFICANCE_AUDIT.md`](file:///d:/Gold/research/reports/STATISTICAL_SIGNIFICANCE_AUDIT.md) | Mathematical audit of IC, Sharpe, Chow test, Brier decomposition, and multiple testing. |

---

## 4. Final Scientific Conclusion

The Gold Weekly Response Engine is a **well-constructed, leak-proof historical measurement and reconstruction tool**. Its data engineering, timestamp isolation, and expanding-window statistics adhere to institutional standards.

However, from an **econometric perspective**, the evidence does **not** support the claim that macroeconomic announcements, technical momentum, positioning data, or machine learning models possess genuine, statistically significant out-of-sample predictive power for gold's next-week return. 

The strategy should be operated strictly as a **regime-aware risk conditioning and scenario simulation tool**, rather than a directional predictive engine.
