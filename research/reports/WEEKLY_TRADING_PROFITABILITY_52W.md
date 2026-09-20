====================================================
GOLD WEEKLY AI — 52-WEEK TRADING BACKTEST
====================================================

Test Period: 2025-09-19 through 2026-09-11
N weeks: 52
Starting Capital: $10,000
Execution Model: friday_close; signal at Friday close, one-week hold to Friday close

PRIMARY RESULT

Strategy: Recursive AI, fixed 1x notional, bias threshold 0.10, pure signal -> hold -> exit
Total Return: -4.61%
Net Return: -4.61% (primary run uses 0 bps round-trip cost and 0.00% slippage)
Annualized Return: -4.61%
Sharpe: -0.34
Max Drawdown: -9.82%
Win Rate: 25.00%
Profit Factor: 0.85
Number of Trades: 29

## Would this have been profitable?

No; the primary historical result was a loss. With $10,000, the ending capital before costs would have been $9,538.74; this statement is descriptive of the completed sample only and is not a forecast.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | -0.05% | 0.08 | -11.27% | 55.77% | 1.03 | 52 |
| Always Long | -0.05% | 0.08 | -11.27% | 55.77% | 1.03 | 52 |
| Always Short | -2.55% | -0.08 | -14.63% | 44.23% | 0.97 | 52 |
| Static AI Model | 0.00% | 0.00 | 0.00% | 0.00% | inf | 0 |
| Raw expected-return sign | 7.51% | 0.52 | -12.30% | 46.15% | 1.20 | 52 |
| Recursive bias sign | 7.89% | 0.55 | -12.06% | 46.15% | 1.21 | 51 |
| Recursive thresholded | -4.61% | -0.34 | -9.82% | 25.00% | 0.85 | 29 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was -0.0778%, with bootstrap 95% CI
[-0.5112%, 0.3784%] and paired permutation p-value 0.724.
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

- **PROFITABILITY:** -4.61% cumulative over 52 realized weeks.
- **RISK:** maximum drawdown -9.82%; annualized volatility 11.76%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate -0.0778%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
