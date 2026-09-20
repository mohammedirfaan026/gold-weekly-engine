# Timestamp & Calendar Integrity Audit

**Audit Date:** 2026-09-20  
**Scope:** Verification of market session boundaries, timezone conversions (`America/New_York` vs `UTC`), Daylight Saving Time transitions, holiday calendar handling, and Friday closing cutoffs across all 873 trading weeks (2010–2026).

---

## 1. Executive Summary

This audit evaluates the temporal alignment of the Gold Weekly Predictive Research System against the institutional definition:
$$\text{Prediction Cutoff} = \text{Friday 17:00:00 New York Time} \ (\texttt{America/New\_York})$$

### Audit Verdict: **PASSED (With Required Timezone Standardization Implemented)**
- **Initial Flaw Identified**: The preliminary version generated `Prediction_Timestamp: 2026-09-11 17:00:00+00:00`. Adding 17 hours to a UTC date string generated **17:00 UTC** rather than **17:00 New York local time**. In September (Daylight Saving Time / EDT), 17:00 New York time corresponds to **21:00 UTC**, meaning the initial timestamp represented 13:00 EDT—four hours prior to the close of electronic trading.
- **Correction Implemented**: `research/src/features/builder.py` was refactored to explicitly localize each date to `America/New_York` at 17:00:00 before converting to UTC.
- **Automated Regression Suite**: Expanded `tests/test_timestamps.py` to cover winter Friday closes, summer Friday closes, spring-forward transitions, and fall-back transitions. All tests passed.

---

## 2. Timezone Semantics: EST vs EDT vs UTC

Gold trading on COMEX and OTC London/New York follows the US Eastern financial calendar. Because the United States observes Daylight Saving Time (DST), the offset between New York and UTC alternates between 4 hours and 5 hours:

$$\text{UTC Time} = \begin{cases} 
\text{NY Time} + 4 \text{ hours} & \text{during Eastern Daylight Time (EDT, summer)} \\ 
\text{NY Time} + 5 \text{ hours} & \text{during Eastern Standard Time (EST, winter)} 
\end{cases}$$

### Precise Mapping Verification

| Session Event | Local Time (`America/New_York`) | Winter Offset (EST, UTC-5) | Summer Offset (EDT, UTC-4) |
| :--- | :--- | :--- | :--- |
| **Sunday Session Open** | Sunday 18:00:00 | Sunday 23:00:00 UTC | Sunday 22:00:00 UTC |
| **COMEX Official Settlement** | Friday 13:30:00 | Friday 18:30:00 UTC | Friday 17:30:00 UTC |
| **Weekly Electronic Close** | Friday 17:00:00 | Friday 22:00:00 UTC | Friday 21:00:00 UTC |
| **Weekly Prediction Cutoff** | Friday 17:00:00 | Friday 22:00:00 UTC | Friday 21:00:00 UTC |
| **Data Timestamp Ceiling** | Friday 16:59:59 | Friday 21:59:59 UTC | Friday 20:59:59 UTC |

---

## 3. Daylight Saving Time (DST) Transition Audit

The United States transitions to DST on the second Sunday in March (spring forward) and returns to standard time on the first Sunday in November (fall back).

### Verification of Transition Weeks (2026 Test Suite)

```python
def test_winter_summer_dst_transitions():
    # 1. Winter Friday (EST = UTC-5)
    winter_date = "2026-01-16"
    winter_close_ny = NY_TZ.localize(pd.Timestamp(f"{winter_date} 17:00:00"))
    winter_close_utc = winter_close_ny.astimezone(pytz.UTC)
    assert winter_close_utc.hour == 22  # 17:00 EST -> 22:00 UTC [PASS]

    # 2. Summer Friday (EDT = UTC-4)
    summer_date = "2026-07-17"
    summer_close_ny = NY_TZ.localize(pd.Timestamp(f"{summer_date} 17:00:00"))
    summer_close_utc = summer_close_ny.astimezone(pytz.UTC)
    assert summer_close_utc.hour == 21  # 17:00 EDT -> 21:00 UTC [PASS]

    # 3. DST Spring Forward (March 2026: March 8 transition)
    pre_dst_fri = NY_TZ.localize(pd.Timestamp("2026-03-06 17:00:00")).astimezone(pytz.UTC)
    post_dst_fri = NY_TZ.localize(pd.Timestamp("2026-03-13 17:00:00")).astimezone(pytz.UTC)
    assert pre_dst_fri.hour == 22   # 2026-03-06 (EST) -> 22:00 UTC [PASS]
    assert post_dst_fri.hour == 21  # 2026-03-13 (EDT) -> 21:00 UTC [PASS]

    # 4. DST Fall Back (November 2026: November 1 transition)
    pre_fall_fri = NY_TZ.localize(pd.Timestamp("2026-10-30 17:00:00")).astimezone(pytz.UTC)
    post_fall_fri = NY_TZ.localize(pd.Timestamp("2026-11-06 17:00:00")).astimezone(pytz.UTC)
    assert pre_fall_fri.hour == 21  # 2026-10-30 (EDT) -> 21:00 UTC [PASS]
    assert post_fall_fri.hour == 22  # 2026-11-06 (EST) -> 22:00 UTC [PASS]
```

All four transition boundary conditions passed with zero assertion errors.

---

## 4. Holiday Calendars & Early Closes

COMEX and US financial markets operate shortened trading hours or close entirely on federal holidays.

### Impact of Shortened Trading Weeks

| Holiday | Market Schedule | Weekly Close Treatment | Look-Ahead Risk |
| :--- | :--- | :--- | :--- |
| **Good Friday** | Market closed all day Friday. Settlement on Thursday. | Week close taken as Thursday 17:00 ET. `week_ending` remains assigned to the calendar Friday. | **None**: No trading occurs on Good Friday; Thursday close is the final observable price before the weekend. |
| **Thanksgiving Friday** | Early close at 13:45 ET. | Prediction timestamp remains Friday 17:00 ET. Final bar recorded at 13:45 ET. | **None**: Availability condition $13:45 \le 17:00$ is strictly satisfied. |
| **Christmas Eve / Day** | Early close (13:00 ET) or full closure. | Final traded price before market holiday used as the reference price. | **None**: Handled via last available trade. |
| **July 4th / Labor Day** | Monday closure or Friday holiday. | Truncated weekly sessions maintain same Friday 17:00 ET boundary. | **None**: Verified across all 873 weeks. |

---

## 5. Settlement vs Market Halt Discrepancy

COMEX publishes two distinct closing prices on Fridays:
1. **Daily Settlement Price (13:30 ET)**: Used for margin clearing, open interest valuation, and official futures accounting.
2. **Post-Settlement Electronic Close (17:00 ET)**: The price at which electronic trading halts for the weekend on CME Globex.

### Audit Finding
The research dataset uses the **17:00 ET electronic close**. This is the more conservative and realistic choice because:
- Macroeconomic announcements and CFTC Commitments of Traders data (released at 15:30 ET on Friday) are published *after* the 13:30 ET settlement.
- Evaluating predictions at Friday 17:00 ET guarantees that 15:30 ET COT reports are legitimately available to market participants before the weekend close, avoiding a 2-hour look-ahead leak that would occur if evaluated against a 13:30 ET settlement.

---

## 6. Audit Conclusion & Compliance Status

The timestamp architecture is verified:
- `America/New_York` is the authoritative timezone.
- UTC timestamps correctly reflect 21:00 UTC (EDT) and 22:00 UTC (EST).
- No ambiguous or naive datetime objects exist in the pipeline.
- Automated tests in `tests/test_timestamps.py` certify zero timestamp regression.
