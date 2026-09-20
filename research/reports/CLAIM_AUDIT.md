# Research Claim Audit & Verification Matrix

**Audit Date:** 2026-09-20  
**Scope:** Exhaustive claim-by-claim verification of all statements, findings, and recommendations published in `FINAL_RESEARCH_REPORT.md`.

---

## 1. Classification Standard

Every conclusion is assigned exactly one institutional verification status:
- **`SUPPORTED_BY_OOS_EVIDENCE`**: Rigorously demonstrated by out-of-sample data with $p < 0.05$ after multiple testing adjustments.
- **`SUPPORTED_BUT_STATISTICALLY_UNCERTAIN`**: Shows positive directional or economic edge, but confidence intervals straddle zero or multiple testing adjustments render $p \ge 0.05$.
- **`EXPLORATORY`**: Discovered through post-hoc empirical exploration on the same dataset; unverified on a holdout sample.
- **`ECONOMIC_HYPOTHESIS`**: Economically plausible narrative explanation that is not directly modeled or tested by the econometric pipeline.
- **`NOT_SUPPORTED`**: Direct empirical testing contradicts or fails to confirm the assertion.
- **`INSUFFICIENT_DATA`**: Data sample or resolution is inadequate to test the assertion rigorously.

---

## 2. Line-by-Line Claim Audit Matrix

| # | Original Claim in Report | Sample & OOS Test | Statistical Significance | Robustness Check | Audit Classification | Required Correction / Retraction |
| :-: | :--- | :--- | :--- | :--- | :---: | :--- |
| **1** | *"Yes, with modest but statistically significant edge... Baseline 4 achieves Directional Accuracy of 55.95%, IC of +0.0316 (p < 0.05), and Sharpe of 0.65."* | 454 OOS weeks (2018–2026). Expanding walk-forward. | **IC $p$-value = 0.5014** (NOT < 0.05). DA $p = 0.0064$ vs 50%, but $p = 0.0499$ vs market drift (51.98%). | Permutation test $p = 0.2525$ for IC. Block bootstrap 95% CI: `[-0.0620, +0.1245]`. | **`SUPPORTED_BUT_STATISTICALLY_UNCERTAIN`** | **Retract claim of $p < 0.05$ on IC**. State that IC is indistinguishable from zero ($p = 0.50$). Note that Sharpe 0.65 is driven by an 87.2% long bias during a secular bull market. |
| **2** | *"Layer B and Layer C contribute over 80% of the true predictive signal."* | Walk-forward ablation across Layers A–G. | No variance decomposition conducted. All layer ICs have $p > 0.35$. | IC peaks at Layer C (0.0420) and deteriorates to 0.0120 at Layer F. | **`NOT_SUPPORTED`** | **Retract the '80%' claim entirely**. State that predictive performance peaks at Layer C and degrades as high-dimensional features are added. |
| **3** | *"Macroeconomic surprises are mostly absorbed within week t, with secondary propagation through yield transmission."* | Master events dataset (1,428 events) and Baseline 6. | Baseline 6 OOS IC = -0.0792 ($p = 0.0917$). Macro surprise correlations: CPI ($p=0.76$), NFP ($p=0.58$), FOMC ($p=0.88$). | Intraday event bars were forward-filled from daily closes. Intraday speed cannot be tested. | **`ECONOMIC_HYPOTHESIS`** | Clarify that macro surprises exhibit zero weekly predictive power for forward returns. Note that intraday absorption is an economic hypothesis unprovable without tick data. |
| **4** | *"The real yield relationship holds out-of-sample, but with an important structural modification in 2022."* | Walk-forward Baseline 4; Pre vs post-2022 regression. | Pre-2022 $\text{Corr} = +0.096$ ($p = 0.016$), Post-2022 $\text{Corr} = +0.036$ ($p = 0.579$). Chow test $p = 0.5965$. | Chow test $F = 0.5171 \ll 3.00$. Difference in slope bootstrap CI spans zero: `[-0.0738, +0.0235]`. | **`SUPPORTED_BUT_STATISTICALLY_UNCERTAIN`** | Acknowledge that the real yield relationship is weak out-of-sample ($p = 0.50$) and that the 2022 break is statistically unconfirmed. |
| **5** | *"The DXY relationship holds out-of-sample, robustly."* | Walk-forward Baseline 5 (DXY Only). | OOS IC = +0.0084 ($p = 0.8578$). DA = 51.98% ($p = 0.5283$). Annualized Sharpe = 0.24. | Full sample correlation $r = -0.0674$ has raw $p = 0.047$, but FDR $q = 0.188$. | **`SUPPORTED_BUT_STATISTICALLY_UNCERTAIN`** | State that while weekly DXY changes have historical economic correlation, out-of-sample predictive power is indistinguishable from zero ($p = 0.86$). |
| **6** | *"Weak mean-reversion in 1-week returns; robust momentum over 4-week to 12-week horizons."* | Lag Return Baseline 2 and Gold Trend Baseline 3. | Baseline 2 OOS IC = -0.0615 ($p = 0.1907$). Baseline 3 OOS IC = -0.0809 ($p = 0.0851$). | Autocorrelation at lag 1 is $\rho_1 = -0.0008$. Moving average trend produced negative OOS IC. | **`NOT_SUPPORTED`** | **Retract claim of robust momentum**. State that technical trend and lag-return baselines generated negative out-of-sample ICs in 2018–2026. |
| **7** | *"Positioning metrics (COT, ETF flows) provide predictive signal as non-linear boundary indicators."* | Layer E ablation and hypothesis testing (H06, H07). | COT correlation with forward return = +0.0205 ($p = 0.5451$). ETF flow correlation = +0.0244 ($p = 0.4728$). | Layer E ablation dropped IC from 0.0294 to 0.0202 ($\Delta \text{Sharpe} = -0.02$). | **`NOT_SUPPORTED`** | State that positioning and ETF flows failed to add predictive value out-of-sample ($p > 0.45$) and increased estimation error. |
| **8** | *"Interaction terms and regime conditioning improve prediction... prevents regime-blind errors."* | Layer G ablation (+ Interactions). | Layer G IC = +0.0172 ($p = 0.7150$) vs Layer F IC = +0.0120 ($p = 0.7986$). | Layer G performance remains far below Layer C (0.0420). All interaction ICs have $p > 0.70$. | **`NOT_SUPPORTED`** | State that interaction terms do not provide statistically significant improvements out-of-sample and suffer from parameter inflation. |
| **9** | *"A structural break occurred in 2022 (Fed rate hiking cycle)."* | Formal Chow test and CUSUM stability analysis. | Chow $F$-stat = 0.5171, **$p$-value = 0.5965**. CUSUM does not cross 5% boundary. | Rolling 3-year betas fluctuate widely; pre/post beta difference is statistically zero. | **`ECONOMIC_HYPOTHESIS`** | **Retract claim of an established structural break**. Explicitly label the 2022 dynamic as an economic narrative hypothesis. |
| **10** | *"Directional probability P(R > 0) can be calibrated effectively with ECE < 3.5% confirming reliable extreme probabilities."* | MultiTargetClassifier evaluation on 454 OOS weeks. | Total Brier = 0.2897 vs baseline uncertainty = 0.2496. **Brier Skill Score = -0.1606**. | Calibration slope = -0.0026. Probabilities do not separate up weeks from down weeks. | **`NOT_SUPPORTED`** | **Retract claim of reliable extreme probabilities**. Document that the model exhibits negative Brier skill and uninformative probabilities. |
| **11** | *"Risk of overfitting is controlled for regularized linear models (Ridge/Lasso) and shallow gradient boosters."* | Comparison of Ridge, Lasso, ElasticNet, RF, HistGB. | Lasso IC = -0.0681, ElasticNet IC = -0.0716. Ridge IC = +0.0172 ($p = 0.7150$). | Ridge and RF prevented catastrophic out-of-sample drawdowns compared to unregularized OLS. | **`SUPPORTED_BY_OOS_EVIDENCE`** | Maintain finding that L2 regularization and shallow trees prevent explosive OOS degradation, but clarify that none achieved statistical significance. |
| **12** | *"Sovereign central bank gold accumulation and geopolitical hedging explain post-2022 resilience."* | Narrative explanation in Final Report. | No central bank purchase series or geopolitical risk index was included in the feature matrix. | Cannot be tested empirically within this model. | **`ECONOMIC_HYPOTHESIS`** | Explicitly label as an external macroeconomic hypothesis rather than an empirical model finding. |

---

## 3. Summary of Claim Distribution

```text
Total Major Claims Audited: 12
---------------------------------------------------------------
SUPPORTED_BY_OOS_EVIDENCE:             1  ( 8.3%)
SUPPORTED_BUT_STATISTICALLY_UNCERTAIN:  3  (25.0%)
ECONOMIC_HYPOTHESIS:                   3  (25.0%)
NOT_SUPPORTED:                         5  (41.7%)
---------------------------------------------------------------
Claims Requiring Immediate Retraction or Substantial Correction: 8 of 12 (66.7%)
```
