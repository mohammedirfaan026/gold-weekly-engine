====================================================
GOLD WEEKLY AI — 52-WEEK TRADING BACKTEST
====================================================

Test Period: 2010-02-05 through 2026-09-11
N weeks: 867
Starting Capital: $10,000
Execution Model: friday_close; signal at Friday close, one-week hold to Friday close

PRIMARY RESULT

Strategy: Recursive AI, fixed 1x notional, bias threshold 0.10, pure signal -> hold -> exit
Total Return: 134.31%
Net Return: 134.31% (primary run uses 0 bps round-trip cost and 0.00% slippage)
Annualized Return: 5.24%
Sharpe: 0.43
Max Drawdown: -33.24%
Win Rate: 41.87%
Profit Factor: 1.18
Number of Trades: 700

## Would this have been profitable?

Yes, but only as a historical result before costs. With $10,000, the ending capital before costs would have been $23,430.75; this statement is descriptive of the completed sample only and is not a forecast.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | 442.38% | 0.71 | -40.27% | 53.98% | 1.28 | 867 |
| Always Long | 442.38% | 0.71 | -40.27% | 53.98% | 1.28 | 867 |
| Always Short | -88.09% | -0.71 | -89.40% | 46.02% | 0.78 | 867 |
| Static AI Model | -67.27% | -0.35 | -73.16% | 43.48% | 0.88 | 792 |
| Raw expected-return sign | 79.54% | 0.30 | -54.15% | 52.02% | 1.11 | 866 |
| Recursive bias sign | 85.39% | 0.31 | -52.66% | 52.13% | 1.11 | 866 |
| Recursive thresholded | 134.31% | 0.43 | -33.24% | 41.87% | 1.18 | 700 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was 0.2223%, with bootstrap 95% CI
[0.0077%, 0.4163%] and paired permutation p-value 0.037.
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

- **PROFITABILITY:** 134.31% cumulative over 867 realized weeks.
- **RISK:** maximum drawdown -33.24%; annualized volatility 14.07%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate 0.2223%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
