====================================================
GOLD WEEKLY AI — 52-WEEK TRADING BACKTEST
====================================================

Test Period: 2010-02-05 through 2026-09-11
N weeks: 867
Starting Capital: $10,000
Execution Model: friday_close; signal at Friday close, one-week hold to Friday close

PRIMARY RESULT

Strategy: Recursive AI, fixed 1x notional, bias threshold 0.10, pure signal -> hold -> exit
Total Return: 26469.07%
Net Return: 26469.07% (primary run uses 0 bps round-trip cost and 0.00% slippage)
Annualized Return: 39.77%
Sharpe: 2.29
Max Drawdown: -12.53%
Win Rate: 58.58%
Profit Factor: 2.81
Number of Trades: 787

## Would this have been profitable?

Yes, but only as a historical result before costs. With $10,000, the ending capital before costs would have been $2,656,906.66; this statement is descriptive of the completed sample only and is not a forecast.

## Benchmark comparison

| Strategy | Return | Sharpe | Max drawdown | Win rate | Profit factor | Trades |
|---|---:|---:|---:|---:|---:|---:|
| Buy & Hold Gold | 442.38% | 0.71 | -40.27% | 53.98% | 1.28 | 867 |
| Always Long | 442.38% | 0.71 | -40.27% | 53.98% | 1.28 | 867 |
| Always Short | -88.09% | -0.71 | -89.40% | 46.02% | 0.78 | 867 |
| Static AI Model | -77.91% | -0.49 | -85.38% | 48.82% | 0.82 | 844 |
| Raw expected-return sign | -53.54% | -0.20 | -62.28% | 47.87% | 0.93 | 862 |
| Recursive bias sign | -54.32% | -0.21 | -62.77% | 47.87% | 0.93 | 865 |
| Recursive thresholded | 26469.07% | 2.29 | -12.53% | 58.58% | 2.81 | 787 |

## Recursive value and raw-model comparison

The paired recursive-minus-static mean weekly difference was 0.8155%, with bootstrap 95% CI
[0.5836%, 1.0691%] and paired permutation p-value 0.000.
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

- **PROFITABILITY:** 26469.07% cumulative over 867 realized weeks.
- **RISK:** maximum drawdown -12.53%; annualized volatility 15.15%.
- **ROBUSTNESS:** threshold, period, execution, cost, slippage, and stop/target sensitivities are evaluation outputs, not optimization.
- **COST SENSITIVITY:** use the explicit round-trip assumptions in the sensitivity CSV.
- **RECURSIVE VALUE:** paired incremental estimate 0.8155%; no claim of detectable improvement without statistical support.
- **REGIME DEPENDENCE:** do not infer a regime edge from LOW SAMPLE or VERY LOW SAMPLE groups.
- **FAILURE MODES:** losing trades and archetypes are retained in the trade log; no losing period is hidden.
- **DATA LIMITATIONS:** weekly OHLC cannot establish the order of same-week stop and target hits; conservative and optimistic runs are required.
- **NEXT EXPERIMENT:** freeze this specification, reserve a new untouched test period, and validate with higher-frequency execution data.

## Reproduction

`python -m research.trading.weekly_trade_backtest --all`
