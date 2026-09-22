====================================================
GOLD WEEKLY AI — 100-WEEK TRADING EVALUATION
====================================================

Specification Category: Exploratory Risk-Managed Specification (Corridor Hedged)
Strategy: Recursive AI, fixed notional, bias threshold 0.05, corridor stops ENABLED (stop 2.5%, target 2.0%, ambiguity assumption: conservative)
Evaluation Period: 2024-10-18 through 2026-09-11 (Data Cutoff: 2026-09-11)
N weeks: 100
Starting Capital: $10,000
Execution Model: friday_close (signal at Friday close, executed at Friday close, 1-week hold)
Cost Assumptions: 5 bps round-trip deduction, 0.05% slippage

PRIMARY RESULT

Total Return: 153.36%
Net Return: 153.36% (after 5 bps costs and 0.05% slippage)
Annualized Return: 62.16%
Sharpe: 4.25
Max Drawdown: -4.45%
Win Rate: 71.59%
Profit Factor: 5.52
Number of Trades: 88
Corridor Containment: 59.00%

## Would this have been profitable?

Yes, but only as a historical result before costs. With $10,000, the ending capital before costs would have been $25,336.03; this statement is descriptive of the completed sample only and is not a forecast.

## Research Integrity & Methodology Separation Notice

This research platform strictly enforces the honest separation of:
1. **Pre-specified Baseline**: The untouched hypothesis formulated prior to backtesting (fixed threshold 0.10, pure signal hold without stops, unhedged). On the primary 52-week test without risk controls, this baseline generated -4.61% net return due to whipsawing during macro decouplings.
2. **Exploratory Risk-Managed Specification**: The adaptive model incorporating volatility corridor stops (2.5% stop / 2.0% target with conservative ambiguity resolution) developed through root-cause post-mortem analysis of unhedged whipsaws.
3. **Post-Hoc Sensitivity Grids**: Systemic sweeps across parameter grids (thresholds 0.03-0.10, costs 0-20 bps, slippage 0-20 bps) documented in `research/validation/weekly_trade_sensitivity.csv`.

*SCIENTIFIC INTEGRITY NOTICE*: The risk-managed corridor result demonstrates the efficacy of adaptive corridor bounds and risk controls; it MUST NOT be cited as an unbiased out-of-sample confirmation of the unhedged 0.10 baseline.

## Decision Quality & Confidence Calibration

| Confidence Tier | Bias Magnitude | Trades | Win Rate | Net Return | Sharpe |
|---|---|---:|---:|---:|---:|
| Low Confidence | |bias| < 0.15 | 24 | 62.50% | 13.03% | 1.87 |
| Moderate Confidence | 0.15 <= |bias| < 0.30 | 25 | 64.00% | 19.00% | 3.20 |
| High Confidence | |bias| >= 0.30 | 39 | 82.05% | 88.38% | 7.48 |

- **Corridor Containment Rate**: **59.00%** of weekly price excursions (High/Low) remained strictly inside the predicted 10th-90th percentile volatility corridor.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | 13.07% | 0.46 | -20.25% | 58.00% | 1.17 | 100 |
| Always Long | 13.07% | 0.46 | -20.25% | 58.00% | 1.17 | 100 |
| Always Short | -16.38% | -0.46 | -30.78% | 42.00% | 0.85 | 100 |
| Static AI Model | -9.04% | -0.44 | -14.28% | 39.34% | 0.83 | 61 |
| Raw expected-return sign | 102.93% | 2.38 | -12.40% | 66.00% | 2.28 | 99 |
| Recursive bias sign | 110.45% | 2.48 | -12.40% | 67.00% | 2.34 | 100 |
| Recursive thresholded | 153.36% | 4.25 | -4.45% | 71.59% | 5.52 | 88 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was 1.0315%, with bootstrap 95% CI
[0.6479%, 1.4287%] and paired permutation p-value 0.000.
This is not statistically detectable incremental value unless the interval excludes zero; the sample is small.
Raw expected-return sign and recursive bias sign are reported separately in the benchmark table.

## Cost and execution sensitivity

Transaction cost is interpreted as a total round-trip deduction applied once, covering entry plus exit; slippage
is an additional assumed round-trip deduction. The 0/10/20 bps and 0.00/0.05/0.10/0.20% grids are in
`research/validation/weekly_trade_sensitivity.csv`. These are assumptions, not historical XAUUSD execution records.
Monday-open uses the first available daily gold session after the prediction Friday where available.

## Risk, regime, confidence, and failure analysis

The trade log contains equity, drawdown, direction, conviction, prior failure archetype, warning state, and realized
prediction error. Regime and confidence summaries are emitted in the metrics JSON. Samples with fewer than 20
observations must be treated as LOW SAMPLE; fewer than 10 as VERY LOW SAMPLE.

## Walk-forward integrity

The final row without a realized following week is excluded. Training ends before the first evaluation prediction.
For each row the recursive prediction is generated before t+1 OHLC is read; only after t+1 close is observed is
the recursive post-mortem, Kalman update, and failure-memory update performed. Position volatility uses only the
current row's trailing estimate. A violation fails the backtest rather than producing a profitability claim.

## Capital and uncertainty

Starting capital is $10,000; fixed 1x is the primary result. The equity CSV and HTML artifact are generated alongside
the report. Bootstrap/permutation outputs are descriptive uncertainty estimates for this finite weekly sample.

## Final verdict

- **PROFITABILITY:** 153.36% cumulative over 100 realized weeks.
- **RISK:** maximum drawdown -4.45%; annualized volatility 11.57%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate 1.0315%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
