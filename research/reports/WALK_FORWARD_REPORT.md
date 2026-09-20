# Purged Walk-Forward Predictive Performance Report
**Generated:** 2026-09-20 10:54:46 UTC
**Out-of-Sample Testing Window:** 2018 to 2026 (454 weeks across 8 expanding folds)

## Executive Summary
This validation enforces an expanding 8-fold walk-forward structure with an initial 8-year minimum training window (2010–2017) and an explicit **1-week embargo** between train and test windows.

## 1. Out-of-Sample Performance Comparison (Models vs Baselines)
| Model | Directional_Accuracy_Pct | Information_Coefficient | IC_p_value | RMSE | MAE | Annualized_Sharpe | Brier_Score | AUC_ROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline 4: Real Yield Only | 55.95 | 0.0316 | 0.5014 | 0.0219 | 0.0174 | 0.65 | 0.307 | 0.5375 |
| RandomForest | 52.64 | 0.0188 | 0.6899 | 0.0221 | 0.0176 | 0.59 | 0.3164 | 0.5102 |
| Ridge | 53.96 | 0.0172 | 0.715 | 0.0224 | 0.0178 | 0.56 | 0.3276 | 0.511 |
| Baseline 5: DXY Return Only | 51.98 | 0.0084 | 0.8578 | 0.0218 | 0.0173 | 0.24 | 0.4609 | 0.4741 |
| HistGradientBoosting | 52.86 | 0.002 | 0.966 | 0.0225 | 0.0178 | 0.37 | 0.3186 | 0.4964 |
| Baseline 2: Lag Return (AR1) | 51.98 | -0.0615 | 0.1907 | 0.0218 | 0.0174 | 0.24 | 0.4786 | 0.5199 |
| Lasso | 51.98 | -0.0681 | 0.1477 | 0.0219 | 0.0174 | 0.24 | 0.2953 | 0.4632 |
| ElasticNet | 51.98 | -0.0716 | 0.1276 | 0.022 | 0.0175 | 0.24 | 0.2907 | 0.4665 |
| Baseline 1: Historical Mean | 51.98 | -0.0776 | 0.0985 | 0.0218 | 0.0174 | 0.24 | 0.2511 | 0.4549 |
| Baseline 6: Macro Surprises Only | 51.54 | -0.0792 | 0.0917 | 0.0219 | 0.0174 | 0.13 | 0.3936 | 0.4938 |
| Baseline 3: Gold Trend Only | 52.2 | -0.0809 | 0.0851 | 0.0221 | 0.0175 | 0.14 | 0.2562 | 0.4557 |


## 2. Statistical Bootstrap Verification (2,000 Block Resamples)
- **Block Size:** 8 weeks (accounting for serial dependency)
- **Mean Resampled Information Coefficient (IC):** 0.0339
- **95% Bootstrap Confidence Interval for IC:** [-0.0666, 0.1336]
- **P(IC > 0):** 74.3%
- **Mean Resampled Sharpe Ratio:** 0.67
- **95% Bootstrap Confidence Interval for Sharpe:** [-0.02, 1.33]

## 3. Probability Calibration Analysis (Reliability)
Calibration of multi-target logistic probability estimator for $P(R_{t+1} > 0)$:
| bin | mean_predicted | empirical_frequency | count | ece |
| --- | --- | --- | --- | --- |
| (0.043699999999999996, 0.368] | 0.28463533340476405 | 0.5054945054945055 | 91 | 0.22085917208974143 |
| (0.368, 0.47] | 0.4229616935030639 | 0.5384615384615384 | 91 | 0.11549984495847454 |
| (0.47, 0.582] | 0.527408069593877 | 0.5666666666666667 | 90 | 0.03925859707278967 |
| (0.582, 0.723] | 0.6497583721151928 | 0.46153846153846156 | 91 | 0.18821991057673126 |
| (0.723, 0.988] | 0.823994523083307 | 0.5274725274725275 | 91 | 0.2965219956107795 |


## 4. OOS Feature Rank Stability Across Folds
| Feature | Mean Importance | Std Dev | Fold Count |
| --- | --- | --- | --- |
| gold_return_12w | 0.07480014877652288 | 0.156355723132208 | 40 |
| cot_percentile_x_gold_trend | 0.03592047143866089 | 0.06935926566827721 | 40 |
| real_yield_shock_z | 0.02534306607065523 | 0.04446684053751752 | 40 |
| gold_distance_20w | 0.02046012263401601 | 0.03059912096319968 | 40 |
| dxy_return_4w | 0.014789148937078691 | 0.02389988729158858 | 40 |
| etf_flow_change | 0.011867159163509958 | 0.01695404557050346 | 40 |
| hy_oas_change_1w | 0.010505590458232615 | 0.01348567373707498 | 40 |
| delta_real_yield_4w | 0.010122652161870018 | 0.01355028692071922 | 40 |
| gold_distance_50w | 0.00945202023792379 | 0.013884005800277247 | 40 |
| delta_real_yield_1w | 0.009092798817085187 | 0.010999252192786177 | 40 |
| vix_percentile | 0.00901998829893456 | 0.014425249184363304 | 40 |
| gold_ma_50w | 0.008421326133598282 | 0.012419933715216958 | 40 |
| yield_transmission | 0.008095517826426672 | 0.010629271183094093 | 40 |
| delta_nominal_yield_1w | 0.007954614972183843 | 0.010179936084929148 | 40 |
| gold_return_4w | 0.007515981698860828 | 0.009926755486548375 | 40 |

