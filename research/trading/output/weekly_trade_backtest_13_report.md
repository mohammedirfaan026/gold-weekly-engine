====================================================
GOLD WEEKLY AI — 52-WEEK TRADING BACKTEST
====================================================

Test Period: 2026-06-19 through 2026-09-11
N weeks: 13
Starting Capital: $10,000
Execution Model: friday_close; signal at Friday close, one-week hold to Friday close

PRIMARY RESULT

Strategy: Recursive AI, fixed 1x notional, bias threshold 0.10, pure signal -> hold -> exit
Total Return: -4.25%
Net Return: -4.25% (primary run uses 0 bps round-trip cost and 0.00% slippage)
Annualized Return: -15.93%
Sharpe: -1.11
Max Drawdown: -6.26%
Win Rate: 23.08%
Profit Factor: 0.56
Number of Trades: 7

## Would this have been profitable?

No; the primary historical result was a loss. With $10,000, the ending capital before costs would have been $9,575.49; this statement is descriptive of the completed sample only and is not a forecast.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | -3.15% | -0.63 | -7.43% | 53.85% | 0.79 | 13 |
| Always Long | -3.15% | -0.63 | -7.43% | 53.85% | 0.79 | 13 |
| Always Short | 2.48% | 0.63 | -4.16% | 46.15% | 1.26 | 13 |
| Static AI Model | 0.00% | 0.00 | 0.00% | 0.00% | inf | 0 |
| Raw expected-return sign | -3.22% | -0.65 | -6.83% | 46.15% | 0.79 | 13 |
| Recursive bias sign | -3.22% | -0.65 | -6.83% | 46.15% | 0.79 | 13 |
| Recursive thresholded | -4.25% | -1.11 | -6.26% | 23.08% | 0.56 | 7 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was -0.3141%, with bootstrap 95% CI
[-1.3002%, 0.7835%] and paired permutation p-value 0.586.
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

- **PROFITABILITY:** -4.25% cumulative over 13 realized weeks.
- **RISK:** maximum drawdown -6.26%; annualized volatility 14.68%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate -0.3141%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
