# Independent 100-Trade Portfolio Test

**Target:** 100 filled trades on model predictions
**Starting capital:** $10,000
**Execution:** Friday close → 1-week hold (point-in-time recursive prediction)

## Portfolio results

| Spec | Window | Trades (L/S) | Ending $ | Return | Sharpe | MaxDD | Win% | vs Buy&Hold |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Locked baseline (th=0.10, no stops, 10bps+5bps slip) | 2024-02-23 -> 2026-09-18 | 100 (60/40) | $18,859.84 | 88.60% | 1.97 | -5.82% | 60.0% | 15.47% |
| Shadow-frozen exploratory (th=0.05, corridor, 10bps+5bps slip) | 2024-06-28 -> 2026-09-18 | 100 (60/40) | $26,778.42 | 167.78% | 3.94 | -4.28% | 67.0% | 20.34% |
| Exploratory zero-cost (th=0.05, corridor, 0 cost) | 2024-06-28 -> 2026-09-18 | 100 (60/40) | $31,063.56 | 210.64% | 4.49 | -3.41% | 74.0% | 20.34% |

## Primary portfolio (Shadow-frozen, after costs)

- Start: **$10,000** → End: **$26,778.42**
- Peak / trough capital: $27,877.51 / $9,713.15
- Expectancy / trade: 0.865%
- Avg winner / loser: 1.907% / -0.832%
- Best / worst trade: 4.95% / -2.12%

## Is it production ready?

**No.** `production_ready = False`

**Live market use:** Decision-support / discretionary shadow only. Do NOT auto-route or size live capital solely on model output.

**Recommended mode:** SHADOW / PAPER with human discretionary confirmation

### Blockers

- No live broker/order-routing integration exists (research CLI + decision brief only).
- Weekly OHLC cannot resolve same-bar stop vs target order; live fills will differ.
- No completed forward shadow period yet under the frozen 2026-09-18 protocol.
- Transaction costs/slippage are assumptions, not measured XAUUSD execution records.

### Why not production

- Historical backtest edge != live edge; sample selection and corridor params were explored after seeing results.
- Recursive incremental value was not consistently detectable on the locked 52w baseline.
- No autonomous execution, kill-switch ops, or broker reconciliation stack.
- Shadow protocol Phase 1 (13 weeks) has not completed from the freeze date.

### Warnings

- Large gap between locked baseline and exploratory corridor spec — corridor result is post-hoc and not unbiased OOS proof.

## Bottom line

The model can generate a researched weekly bias and a simulated portfolio.
On this independent 100-trade sample after costs, treat it as **research / shadow decision-support**,
not as a production auto-trader for real live capital.

Artifacts: `D:\Gold\research\trading\output\independent_100`
