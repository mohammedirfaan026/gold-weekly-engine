# Statistical Significance & Methodology Audit

**Audit Date:** 2026-09-20  
**Scope:** Independent quantitative audit of all statistical claims, out-of-sample predictability metrics, hypothesis testing procedures, probability calibrations, and structural break assertions.

---

## 1. Executive Summary

This audit subjects every statistical conclusion of the Gold Predictive Research System to strict independent verification. 

### Core Audit Verdicts
1. **Real Yield Predictive Power**: The claim of "genuine out-of-sample predictive power" is **OVERSTATED**. 
   - While Directional Accuracy is 55.95% ($p = 0.0064$ vs a 50% coin flip), it is **barely significant against the market's secular positive drift of 51.98% ($p = 0.0499$)**.
   - The linear correlation with forward returns is **indistinguishable from pure noise**: Spearman $\text{IC} = +0.0316$ ($p = 0.5014$) and Pearson $r = +0.0229$ ($p = 0.6270$).
   - **Classification**: **`SUPPORTED_BUT_STATISTICALLY_UNCERTAIN`**.
2. **Reconciliation of IC ($p=0.50$) vs Sharpe ($0.65$)**: 
   - The strategy's Sharpe ratio of 0.65 is **not** a reflection of fine-grained predictive skill.
   - It is driven by a persistent **87.2% Long position bias** during an extraordinary secular bull market in gold (2018–2026), amplified by zero-cost, friction-free rebalancing assumptions.
3. **Structural Break in 2022**: The claim of a structural break in 2022 is **STATISTICALLY UNSUPPORTED**.
   - A formal Chow test yields $F = 0.5171$ ($p = 0.5965$).
   - The bootstrap 95% confidence interval for the pre/post beta difference is `[-0.0738, +0.0235]`, firmly straddling zero.
   - **Classification**: **`ECONOMIC_HYPOTHESIS`** (not an established econometric break).
4. **"80% of Signal" Claim**: **UNJUSTIFIED & RETRACTED**. No mathematical variance decomposition was performed. Adding macro and positioning layers degrades OOS performance due to estimation noise.
5. **Multiple Testing Reality**: Out of 12 tested hypotheses, **zero (0) survive Benjamini-Hochberg False Discovery Rate (FDR) correction at $q < 0.05$**. All historical empirical relationships must be classified as **`EXPLORATORY`**.

---

## 2. In-Depth Audit of the Real-Yield Result

### Empirical Diagnostics ($N = 454$ Out-of-Sample Weeks, 2018–2026)

| Metric | Point Estimate | Exact Test / 95% Confidence Interval | $p$-value | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Directional Accuracy (DA)** | **55.95%** (254/454) | Wilson: `[51.35%, 60.44%]`<br>Clopper-Pearson: `[51.24%, 60.57%]` | $p = 0.0064$ (vs 50%)<br>$p = 0.0499$ (vs 51.98%) | Borderline edge over market drift; lower bound is near 51%. |
| **Information Coefficient (Spearman)** | **+0.0316** | Block Bootstrap (k=8): `[-0.0620, +0.1245]` | $p = 0.5014$ | **Not statistically significant**. Indistinguishable from zero. |
| **Linear Correlation (Pearson $r$)** | **+0.0229** | Exact Student's $t$: `[-0.0691, +0.1147]` | $p = 0.6270$ | **Not statistically significant**. |
| **Permutation Test (10,000 Shuffles)** | — | Fraction of permutations with $\text{IC} \ge 0.0316$ | $p = 0.2525$ | 25.25% of random permutations beat this IC. |
| **Simulated Sharpe (Zero Cost)** | **0.65** | Block Bootstrap (k=8): `[0.08, 1.21]` | $p = 0.0208$ (Permutation) | Positive Sharpe, but confidence interval spans 0.08 to 1.21. |
| **OOS Mean Weekly Return** | **+0.1935%** | Annualized: +10.06% | — | Driven by persistent long posture. |
| **OOS Median Weekly Return** | **+0.2444%** | — | — | Skewed positively by long bull market. |
| **Buy & Hold Gold Sharpe** | **0.24** | Mean Return: +0.076% / week | — | Benchmark comparison. |

### Block Bootstrap Sensitivity Across Block Lengths

To account for potential weekly serial dependence, stationary block bootstrapping (2,000 resamples) was evaluated across block lengths $k \in \{2, 4, 8, 12, 16\}$:

| Block Length ($k$) | Mean DA | 95% CI for DA | Mean IC | 95% CI for IC | Mean Sharpe | 95% CI for Sharpe |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$k = 2$** | 55.94% | `[51.32%, 60.57%]` | +0.0321 | `[-0.0594, +0.1235]` | 0.65 | `[0.10, 1.18]` |
| **$k = 4$** | 55.93% | `[51.10%, 60.79%]` | +0.0318 | `[-0.0601, +0.1241]` | 0.65 | `[0.09, 1.20]` |
| **$k = 8$** | 55.95% | `[50.88%, 61.01%]` | +0.0315 | `[-0.0620, +0.1245]` | 0.65 | `[0.08, 1.21]` |
| **$k = 12$** | 55.92% | `[50.66%, 61.23%]` | +0.0310 | `[-0.0635, +0.1258]` | 0.64 | `[0.06, 1.23]` |
| **$k = 16$** | 55.89% | `[50.22%, 61.45%]` | +0.0304 | `[-0.0662, +0.1274]` | 0.64 | `[0.04, 1.25]` |

**Finding**: At block lengths $k \ge 8$, the lower bound of the 95% confidence interval for Directional Accuracy drops to **50.88%** and at $k=16$ touches **50.22%**, confirming that directional predictability cannot be distinguished from a fair coin at the 95% confidence level under serial dependence.

---

## 3. Reconciling IC ($p=0.50$) vs Sharpe ($0.65$)

Why does a model with an Information Coefficient of +0.0316 ($p = 0.50$) achieve a simulated Sharpe ratio of 0.65?

### Step-by-Step Return Transformation Audit
$$\text{Prediction} \ \hat{R}_{t+1} \longrightarrow \text{Signal} \ \text{sign}(\hat{R}_{t+1}) \longrightarrow \text{Position} \ P_t \in \{-1, +1\} \longrightarrow R_{\text{strat}} = P_t \cdot R_{t+1}$$

1. **Fitted Model Parameters**:
   The expanding OLS model in `RealYieldBaseline` is:
   $$\hat{R}_{t+1} = \hat{\alpha}_t + \hat{\beta}_t \cdot \Delta \text{Real Yield}_{1w, t}$$
   In the training folds (2010–2017 onwards), the fitted intercept $\hat{\alpha}_t$ is positive (+0.002 to +0.003), while $\hat{\beta}_t$ is small ($\approx -0.01$).
2. **Weekly Shift Distribution**:
   Weekly changes in 10Y TIPS real yields ($\Delta \text{Real Yield}_{1w}$) are small, typically spanning $\pm 0.05\%$ ($\pm 5$ bps). Consequently, $\hat{\alpha}_t + \hat{\beta}_t \Delta \text{Yield}$ evaluates to a positive number the vast majority of the time.
3. **Extreme Long Allocation**:
   The model allocated **87.2% of all out-of-sample weeks to LONG (+1)** and only **12.8% of weeks to SHORT (-1)**.
4. **Bull Market Beta**:
   During 2018–2026, gold surged from ~$1,300/oz to over $2,700/oz, experiencing positive returns in 51.98% of all weeks. By staying long 87.2% of the time and occasionally flipping short during sharp upward yield spikes (which happened to coincide with several gold pullbacks), the strategy captured the market's positive drift with lower drawdown.
5. **Zero Frictions Assumption**:
   The 0.65 Sharpe was computed assuming:
   - **0 bps commission**
   - **0 bps bid-ask spread / slippage**
   - **0 borrow fees for shorting COMEX futures**
   - **Execution precisely at the Friday 17:00 ET closing print**

### Impact of Realistic Transaction Costs

With an average turnover of 0.45 position flips per week, imposing realistic frictions reduces the simulated Sharpe:

| Roundtrip Transaction Cost | Net Weekly Mean Return | Annualized Net Sharpe | Sharpe Degradation |
| :---: | :---: | :---: | :---: |
| **0 bps (Reported Baseline)** | **+0.1935%** | **0.65** | 0.0% |
| **5 bps** | +0.1822% | **0.61** | -6.2% |
| **10 bps** | +0.1710% | **0.57** | -12.3% |
| **15 bps** | +0.1597% | **0.53** | -18.5% |
| **20 bps** | +0.1485% | **0.50** | -23.1% |

**Conclusion**: The Sharpe of 0.65 is **measuring the beta of an asymmetric long bias during a secular bull market**, NOT genuine predictive ranking ability. Calling this "proof of predictive power" conflates market beta and position transformation with statistical edge.

---

## 4. Formal Structural Break Audit (The 2022 Claim)

The report claimed: *"A structural break occurred in 2022 where the real yield relationship broke down."*

### Formal Econometric Hypothesis
$$H_0: \beta_{\text{pre-2022}} = \beta_{\text{post-2022}} \quad \text{vs} \quad H_1: \beta_{\text{pre-2022}} \neq \beta_{\text{post-2022}}$$

### Econometric Results

| Diagnostic | Pre-2022 Sample (2010–2021) | Post-2022 Sample (2022–2026) | Test Statistic | $p$-value |
| :--- | :--- | :--- | :--- | :--- |
| **Sample Size ($N$)** | 626 trading weeks | 245 trading weeks | — | — |
| **Regression Slope ($\beta$)** | +0.0360 | +0.0113 | $\Delta \beta = -0.0247$ | — |
| **Spearman Correlation** | +0.0959 ($p = 0.016$) | +0.0357 ($p = 0.579$) | — | — |
| **Chow Test for Structural Stability** | $\text{RSS}_1 = 0.2981$ | $\text{RSS}_2 = 0.1194$ | **$F = 0.5171$** | **$p = 0.5965$** |
| **Bootstrap 95% CI for $\Delta \beta$** | — | — | `[-0.0738, +0.0235]` | $p = 0.4210$ |

### Verdict
The Chow test $p$-value is **0.5965** ($F = 0.52 \ll F_{\text{critical}} = 3.00$). The apparent reduction in sensitivity between 10Y TIPS yields and weekly gold returns post-2022 is **statistically indistinguishable from random sampling variance**. The claim that a structural break occurred in 2022 is an **economic narrative**, not an established empirical fact.

---

## 5. Audit of the "80% of Signal" Claim

The previous report asserted that *Layer B (Rates) and Layer C (DXY) contribute over 80% of the true predictive signal.*

### Re-Evaluation of Out-of-Sample Ablation

| Layer | Feature Count | OOS Directional Accuracy | OOS IC | IC $p$-value | Annualized Sharpe | Marginal $\Delta \text{Sharpe}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Layer A: Technicals** | 10 | 50.88% | +0.0017 | 0.9710 | 0.22 | Baseline |
| **Layer B: + Rates & Breakevens** | 20 | 53.52% | +0.0289 | 0.5385 | 0.61 | +0.39 |
| **Layer C: + DXY** | 23 | 53.96% | **+0.0420** | 0.3722 | **0.65** | +0.04 |
| **Layer D: + Macro Surprises** | 51 | 52.42% | +0.0294 | 0.5327 | 0.57 | -0.08 |
| **Layer E: + Positioning & Flows** | 57 | 53.30% | +0.0202 | 0.6677 | 0.55 | -0.02 |
| **Layer F: + Shocks & Regimes** | 83 | 53.96% | +0.0120 | 0.7986 | 0.52 | -0.03 |
| **Layer G: + Interactions** | 95 | 53.96% | +0.0172 | 0.7150 | 0.56 | +0.04 |

### Audit Findings
1. **No Formal Variance Decomposition**: The figure "80%" was an arbitrary narrative characterization based on observing that Sharpe rose from 0.22 to 0.65 in Layers B/C, rather than a mathematical Shapley value or ANOVA $R^2$ decomposition.
2. **High-Dimensional Degradation**: Out-of-sample IC peaks at Layer C (0.0420) and **steadily deteriorates** as macro surprises, positioning, and shocks are added (dropping to 0.0120 in Layer F). Adding more features adds estimation error.
3. **Statistical Insignificance**: Crucially, **every single layer has an IC $p$-value $> 0.35$**. None of the layers achieve statistically significant prediction.
4. **Correction**: The "80% of signal" statement is retracted and replaced with: *"Predictive performance peaks at Layer C and degrades as additional unconstrained feature layers are introduced, though all layers remain statistically indistinguishable from zero."*

---

## 6. Audit of the Macro Digestion Claim

The previous report claimed: *"Macro release surprises are rapidly digested by COMEX futures within 24–48 hours."*

### Data Investigation
Inspection of `data/processed/events_master.parquet` across all 1,428 historical announcements revealed:
- The mean absolute move from $T+5\text{m}$ through $T+1\text{d}$ is identical across all intraday fields:
  $$\text{Mean } |R_{5\text{m}}| = 0.769\%, \quad \text{Mean } |R_{15\text{m}}| = 0.769\%, \quad \text{Mean } |R_{1\text{h}}| = 0.769\%, \quad \text{Mean } |R_{1\text{d}}| = 0.769\%$$
- **Cause**: In the underlying data collection, intraday minute bars were approximated from daily closing bars when high-frequency tick data was unavailable.
- **Audit Conclusion**: Because intraday resolution was forward-filled from daily bars, **the claim of 24–48 hour market absorption cannot be validated from this dataset**. It represents an institutional intuition rather than an empirically demonstrated finding in this codebase.

---

## 7. Probability Calibration & Brier Score Audit

The calibrated logistic head was reported as having *"ECE < 3.5% confirming reliable extreme probabilities."*

### Murphy Brier Score Decomposition
$$\text{Brier} = \text{Uncertainty} + \text{Reliability} - \text{Resolution}$$

| Component | Value | Optimal Value | Interpretation |
| :--- | :---: | :---: | :--- |
| **Total Brier Score** | **0.2897** | 0.0000 | Overall mean squared error of probabilities. |
| **Uncertainty (Baseline Variance)** | **0.2496** | — | Variance of the unconditional base rate ($0.52 \times 0.48$). |
| **Reliability (Calibration Error)** | **0.0435** | 0.0000 | Weighted distance from perfect calibration. |
| **Resolution (Discriminative Power)** | **0.0034** | $\approx 0.25$ | Ability to separate up weeks from down weeks. |
| **Brier Skill Score ($1 - \text{Brier}/\text{Uncertainty}$)** | **-0.1606** | 1.0000 | **NEGATIVE**: Performs worse than predicting a constant 52%. |
| **Calibration Slope** | **-0.0026** | 1.0000 | Near zero: Model probabilities carry almost no discriminatory slope. |
| **Calibration Intercept** | **0.5204** | 0.0000 | Matches the unconditional positive rate (52.0%). |

### Audit Finding
The Brier Skill Score is **negative (-0.16)**. This proves that the multi-target probability model does not possess genuine discriminatory resolution. Extreme probabilities (>65% or <35%) are rare artifacts of sample noise and **cannot be trusted as reliable high-conviction signals**.

---

## 8. Multiple Testing & Hypothesis Ledger Audit

### Ledger Analysis (12 Hypotheses)

| ID | Hypothesis Name | Expected Sign | Observed Correlation | Raw $p$-value | FDR Adjusted $q$-value | Bonferroni $p$-value | Audit Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **H01** | Real Yield Inverse Effect | -1 | +0.0768 | 0.0234 | 0.1404 | 0.2808 | `SUPPORTED_BUT_STATISTICALLY_UNCERTAIN` |
| **H02** | DXY Dollar Inverse Effect | -1 | -0.0674 | 0.0469 | 0.1876 | 0.5628 | `SUPPORTED_BUT_STATISTICALLY_UNCERTAIN` |
| **H03** | Gold Trend Momentum | +1 | -0.0526 | 0.1205 | 0.3615 | 1.0000 | `NOT_SUPPORTED` (Negative correlation) |
| **H04** | VIX Shock Safe Haven | +1 | +0.0211 | 0.5340 | 0.7816 | 1.0000 | `NOT_SUPPORTED` ($p = 0.53$) |
| **H05** | Equity Crash Shock | +1 | -0.0142 | 0.6754 | 0.7816 | 1.0000 | `NOT_SUPPORTED` ($p = 0.68$) |
| **H06** | COT Speculative Reversal | -1 | +0.0205 | 0.5451 | 0.7816 | 1.0000 | `NOT_SUPPORTED` ($p = 0.55$) |
| **H07** | ETF Flow Persistence | +1 | +0.0244 | 0.4728 | 0.7816 | 1.0000 | `NOT_SUPPORTED` ($p = 0.47$) |
| **H08** | CPI Upside Surprise | +1 | -0.0102 | 0.7634 | 0.8328 | 1.0000 | `NOT_SUPPORTED` ($p = 0.76$) |
| **H09** | NFP Upside Surprise | -1 | -0.0189 | 0.5772 | 0.7816 | 1.0000 | `NOT_SUPPORTED` ($p = 0.58$) |
| **H10** | FOMC Decision Surprise | -1 | -0.0051 | 0.8804 | 0.8804 | 1.0000 | `NOT_SUPPORTED` ($p = 0.88$) |
| **H11** | Breakeven Inflation Expansion | +1 | +0.0412 | 0.2241 | 0.5378 | 1.0000 | `NOT_SUPPORTED` ($p = 0.22$) |
| **H12** | 1-Week Mean Reversion | -1 | -0.0008 | 0.9802 | 0.9802 | 1.0000 | `NOT_SUPPORTED` ($p = 0.98$) |

### Summary
- Significant before correction: **2** (Real Yield and DXY at unadjusted $p < 0.05$).
- Significant after Benjamini-Hochberg FDR correction: **0** ($q_{\text{min}} = 0.14 > 0.05$).
- Significant after Bonferroni correction: **0** ($p_{\text{min}} = 0.28 > 0.05$).
- **Conclusion**: When proper multiple testing adjustments are enforced across the 12 hypotheses, **zero relationships survive at the standard 5% false discovery rate threshold**.

---

## 9. Sub-Period Regime Stability Audit

Recalculating the two strongest relationships across five non-overlapping historical eras demonstrates substantial parameter instability:

| Sub-Period | Weeks ($N$) | Real Yield Correlation | Real Yield $p$-value | DXY Correlation | DXY $p$-value | Annualized Gold Return |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2010–2014** | 260 | **+0.1632** | **0.008** | — | — | +16.3% |
| **2015–2019** | 261 | +0.0439 | 0.480 | -0.0281 | 0.652 | +14.1% |
| **2020–2021** | 105 | +0.0402 | 0.684 | -0.1567 | 0.110 | -6.3% |
| **2022–2023** | 104 | -0.0324 | 0.744 | -0.0628 | 0.527 | +15.9% |
| **2024–2026** | 141 | +0.0943 | 0.266 | -0.1062 | 0.210 | +5.9% |

**Audit Finding**:
- In **four out of five sub-periods**, the real yield correlation with next-week return is statistically indistinguishable from zero ($p > 0.25$).
- The sign of the empirical relationship flips between positive (+0.16 in 2010–2014) and negative (-0.03 in 2022–2023).
- Neither relationship can be described as universal, persistent, or stationary.
