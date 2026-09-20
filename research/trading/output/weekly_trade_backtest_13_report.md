====================================================
GOLD WEEKLY AI — 52-WEEK TRADING BACKTEST
====================================================

Test Period: 2026-06-19 through 2026-09-11
N weeks: 13
Starting Capital: $10,000
Execution Model: friday_close; signal at Friday close, one-week hold to Friday close

PRIMARY RESULT

Strategy: Recursive AI, fixed 1x notional, bias threshold 0.10, pure signal -> hold -> exit
Total Return: 8.13%
Net Return: 8.13% (primary run uses 0 bps round-trip cost and 0.00% slippage)
Annualized Return: 36.70%
Sharpe: 3.36
Max Drawdown: -1.61%
Win Rate: 84.62%
Profit Factor: 3.77
Number of Trades: 13

## Would this have been profitable?

Yes, but only as a historical result before costs. With $10,000, the ending capital before costs would have been $10,812.92; this statement is descriptive of the completed sample only and is not a forecast.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | -3.15% | -0.63 | -7.43% | 53.85% | 0.79 | 13 |
| Always Long | -3.15% | -0.63 | -7.43% | 53.85% | 0.79 | 13 |
| Always Short | 2.48% | 0.63 | -4.16% | 46.15% | 1.26 | 13 |
| Static AI Model | 7.66% | 4.00 | -0.22% | 75.00% | 35.64 | 8 |
| Raw expected-return sign | -10.53% | -2.54 | -14.49% | 53.85% | 0.39 | 13 |
| Recursive bias sign | -10.53% | -2.54 | -14.49% | 53.85% | 0.39 | 13 |
| Recursive thresholded | 8.13% | 3.36 | -1.61% | 84.62% | 3.77 | 13 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was 0.0368%, with bootstrap 95% CI
[-0.4171%, 0.4697%] and paired permutation p-value 0.784.
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

- **PROFITABILITY:** 8.13% cumulative over 13 realized weeks.
- **RISK:** maximum drawdown -1.61%; annualized volatility 9.45%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate 0.0368%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
