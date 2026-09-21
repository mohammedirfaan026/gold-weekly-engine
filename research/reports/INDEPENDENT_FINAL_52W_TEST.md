# Independent Final 52-Week Trading Evaluation

**Evaluation window:** prediction weeks 2025-09-19 through 2026-09-11  
**Realized trade weeks:** 2025-09-26 through 2026-09-18  
**Observations:** 52 completed prediction weeks  
**Execution:** Friday close, one-week hold  
**Starting capital:** $10,000  

This evaluation was run after freezing the configurations below. The locked baseline and exploratory configuration are reported separately. The exploratory configuration is post-hoc and must not be treated as unbiased confirmation.

## Locked pre-specified baseline

- Recursive model
- Bias threshold: 0.10
- Pure signal -> hold -> exit
- No corridor stops or targets
- Fixed 1x notional

| Cost/slippage assumption | Return | Ending capital | Sharpe | Maximum drawdown | Trades | Win rate |
|---|---:|---:|---:|---:|---:|---:|
| 0 bps / 0.00% | 21.64% | $12,163.84 | 1.47 | -5.47% | 38 | 63.16% |
| 10 bps / 0.05% round trip | 14.93% | $11,492.62 | 1.07 | -6.12% | 38 | 57.89% |

## Current exploratory configuration

- Recursive model
- Bias threshold: 0.05
- Corridor stops enabled
- Stop: 2.5%
- Target: 2.0%
- Conservative ambiguous stop/target handling
- Fixed 1x notional

| Cost/slippage assumption | Return | Ending capital | Sharpe | Maximum drawdown | Trades | Win rate |
|---|---:|---:|---:|---:|---:|---:|
| 0 bps / 0.00% | 50.15% | $15,015.18 | 3.42 | -3.68% | 44 | 68.18% |
| 10 bps / 0.05% round trip | 40.64% | $14,063.88 | 2.89 | -4.47% | 44 | 63.64% |
| 20 bps / 0.10% round trip | 31.72% | $13,171.57 | 2.36 | -5.37% | 44 | 59.09% |

## Benchmarks

- Buy and hold: -0.05%, Sharpe 0.08, maximum drawdown -11.27%
- Raw expected-return sign: +16.16%, Sharpe 1.00, maximum drawdown -9.52%
- Recursive bias sign: +16.16%, Sharpe 1.00, maximum drawdown -9.52%

## Recursive incremental analysis

For the locked baseline, recursive minus static mean weekly return difference was **+0.2522%**, with bootstrap 95% confidence interval **[-0.3667%, +0.8842%]** and paired permutation p-value **0.414**. This does not establish statistically detectable incremental recursive value over the 52-week sample.

For the exploratory configuration, the paired difference was **+0.7653%**, with bootstrap 95% confidence interval **[+0.2506%, +1.3143%]** and permutation p-value **0.007**. Because this configuration was developed after observing prior results, this statistic is exploratory and subject to selection bias.

## Integrity checks

The backtest reported:

- Training rows end before the evaluation window.
- Prediction is generated before the next-week OHLC is accessed.
- Post-mortem and recursive updates occur only after the realized week closes.
- Pre-trade volatility uses only information available at prediction time.
- The final row without a realized following week is excluded.
- Leakage audit passed.
- Full test suite passed: 56 tests.

## Conclusion

The locked baseline was profitable in this one-year historical sample and remained positive under the tested cost/slippage assumption, but the confidence interval for recursive incremental value includes zero. The exploratory strategy produced higher returns, but its result is not an unbiased out-of-sample confirmation because its threshold and corridor risk controls were selected after prior evaluation. This is evidence for continued shadow testing and discretionary decision support, not proof of a durable future edge.
