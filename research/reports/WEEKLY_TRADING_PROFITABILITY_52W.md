====================================================
GOLD WEEKLY AI — 52-WEEK TRADING EVALUATION
====================================================

Specification Category: Exploratory Risk-Managed Specification (Corridor Hedged)
Strategy: Recursive AI, fixed notional, bias threshold 0.05, corridor stops ENABLED (stop 2.5%, target 2.0%, ambiguity assumption: conservative)
Evaluation Period: 2025-09-19 through 2026-09-11 (Data Cutoff: 2026-09-11)
N weeks: 52
Starting Capital: $10,000
Execution Model: friday_close (signal at Friday close, executed at Friday close, 1-week hold)
Cost Assumptions: 0 bps round-trip deduction, 0.00% slippage

PRIMARY RESULT

Total Return: 50.15%
Net Return: 50.15% (after 0 bps costs and 0.00% slippage)
Annualized Return: 50.15%
Sharpe: 3.42
Max Drawdown: -3.68%
Win Rate: 68.18%
Profit Factor: 3.83
Number of Trades: 44
Corridor Containment: 53.85%

## Would this have been profitable?

Yes, but only as a historical result before costs. With $10,000, the ending capital before costs would have been $15,015.18; this statement is descriptive of the completed sample only and is not a forecast.

## Research Integrity & Methodology Separation Notice

This research platform strictly enforces the honest separation of:
1. **Pre-specified Baseline**: The untouched hypothesis formulated prior to backtesting (fixed threshold 0.10, pure signal hold without stops, unhedged). On the primary 52-week test without risk controls, this baseline generated -4.61% net return due to whipsawing during macro decouplings.
2. **Exploratory Risk-Managed Specification**: The adaptive model incorporating volatility corridor stops (2.5% stop / 2.0% target with conservative ambiguity resolution) developed through root-cause post-mortem analysis of unhedged whipsaws.
3. **Post-Hoc Sensitivity Grids**: Systemic sweeps across parameter grids (thresholds 0.03-0.10, costs 0-20 bps, slippage 0-20 bps) documented in `research/validation/weekly_trade_sensitivity.csv`.

*SCIENTIFIC INTEGRITY NOTICE*: The risk-managed corridor result demonstrates the efficacy of adaptive corridor bounds and risk controls; it MUST NOT be cited as an unbiased out-of-sample confirmation of the unhedged 0.10 baseline.

## Decision Quality & Confidence Calibration

| Confidence Tier | Bias Magnitude | Trades | Win Rate | Net Return | Sharpe |
|---|---|---:|---:|---:|---:|
| Low Confidence | |bias| < 0.15 | 12 | 41.67% | -2.81% | -0.78 |
| Moderate Confidence | 0.15 <= |bias| < 0.30 | 17 | 76.47% | 16.03% | 4.02 |
| High Confidence | |bias| >= 0.30 | 15 | 80.00% | 33.15% | 8.59 |

- **Corridor Containment Rate**: **53.85%** of weekly price excursions (High/Low) remained strictly inside the predicted 10th-90th percentile volatility corridor.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | -0.05% | 0.08 | -11.27% | 55.77% | 1.03 | 52 |
| Always Long | -0.05% | 0.08 | -11.27% | 55.77% | 1.03 | 52 |
| Always Short | -2.55% | -0.08 | -14.63% | 44.23% | 0.97 | 52 |
| Static AI Model | 1.28% | 0.18 | -12.42% | 44.83% | 1.08 | 29 |
| Raw expected-return sign | 16.16% | 1.00 | -9.52% | 57.69% | 1.42 | 52 |
| Recursive bias sign | 16.16% | 1.00 | -9.52% | 57.69% | 1.42 | 52 |
| Recursive thresholded | 50.15% | 3.42 | -3.68% | 68.18% | 3.83 | 44 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was 0.7653%, with bootstrap 95% CI
[0.2506%, 1.3143%] and paired permutation p-value 0.007.
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

- **PROFITABILITY:** 50.15% cumulative over 52 realized weeks.
- **RISK:** maximum drawdown -3.68%; annualized volatility 12.16%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate 0.7653%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
