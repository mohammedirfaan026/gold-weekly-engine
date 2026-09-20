# Gold Weekly Response Engine

An institutional-grade quantitative research platform designed to historically reconstruct how gold (XAUUSD spot and COMEX Gold futures) responds over the following trading week to macroeconomic announcements, market shocks, positioning cycles, and broader financial conditions (2010 to present).

> **Core Research Question:**  
> *When a specific macro or market event happens, what does gold do over the following week, under what market conditions, and how consistent is that response?*

---

## 1. System Architecture

The codebase follows a strictly decoupled, modular quantitative design:

```text
gold-reaction-engine/
│
├── README.md                           # System documentation and usage guide
├── requirements.txt                    # Pinned Python package dependencies
├── .env.example                        # API keys template (FRED, etc.)
├── config.yaml                         # Central system, regime, and path settings
│
├── data/
│   ├── raw/                            # Raw data store
│   ├── processed/                      # Normalized event-level master dataset (events_master.parquet)
│   ├── market/                         # Clean multi-asset historical series (Gold, DXY, Equities, VIX, etc.)
│   ├── macro/                          # FRED macroeconomic series (TIPS real yields, Treasuries, HY OAS)
│   ├── events/                         # Curated economic event calendar with expanding Z-scores
│   └── weekly/                         # Master Friday-to-Friday research dataset (gold_weekly_master.parquet)
│
├── database/
│   └── gold_research.db                # SQLite database with relational tables: events_master, weekly_master
│
├── reports/
│   ├── gold_weekly_research_report.md  # Executive quantitative research report (Markdown)
│   ├── gold_weekly_research_report.html# Formatted standalone report with interactive links (HTML)
│   ├── figures/                        # 17 interactive Plotly charts (trajectories, scatters, heatmaps, dashboards)
│   └── *.csv                           # Summary statistical CSV tables
│
├── notebooks/
│   └── gold_research_exploration.ipynb # Interactive research and SQL exploration notebook
│
├── tests/                              # Automated pytest suite (18 unit & integration tests)
│
├── src/
│   ├── ingestion/                      # Market, macro, COT, ETF, and event data fetchers
│   ├── normalization/                  # Point-in-time surprise calculator and data cleaners
│   ├── timestamps/                     # Point-in-time manager & Friday close session locator
│   ├── market_state/                   # Pre-event multi-asset snapshot reconstructor
│   ├── regime_engine/                  # Percentile-based regime classification
│   ├── event_engine/                   # Multi-window response, references A-E, MFE/MAE, speed, reversals
│   ├── weekly_engine/                  # Master weekly dataset builder & multi-event aggregator
│   ├── statistics/                     # Bootstrap CIs, trimmed means, conditional matrices, shocks, COT
│   ├── visualization/                  # Plotly interactive charting engine
│   └── reporting/                      # Automated Markdown & HTML report generator
│
├── ingest_data.py                      # CLI: Data ingestion pipeline
├── build_dataset.py                    # CLI: Pre-event reconstruction & dataset assembly
├── run_event_study.py                  # CLI: Statistical event study execution
├── run_weekly_analysis.py              # CLI: Weekly regression, shock, and positioning analysis
└── generate_report.py                  # CLI: Report compilation
```

---

## 2. Core Quantitative Foundations

### A. Point-in-Time Correctness (Mandatory Rule)
- For every observation, the system enforces **`observation_time`** vs **`publication_time`**.
- Data points are strictly filtered to be accessible only after their verified publication timestamp:
  - **CFTC Commitments of Traders**: Observation date is Tuesday, publication date is Friday 15:30 ET.
  - **BLS/BEA Macro Releases**: Observation month $M$ is published during month $M+1$ at 08:30 ET.
  - **Yields & Spreads**: Daily series publish the following morning.
- **Surprise Z-Scores**: Historical standard deviation of surprises $\sigma_t^{\text{exp}}$ is calculated using an **expanding window backward only**, ensuring no forward-looking standard deviation enters historical z-scores.

### B. Reference Price Definitions
To distinguish whether gold's move began with the event itself or was already underway:
- **Reference A**: Price immediately before event (closest reliable pre-event bar/tick).
- **Reference B**: 5-minute close before event.
- **Reference C**: 1-hour close before event.
- **Reference D**: Same-day official close.
- **Reference E**: Previous Friday close.

### C. Measured Horizons & Path Metrics
For every event, gold's path is tracked across:
`+1m`, `+5m`, `+15m`, `+30m`, `+1h`, `+2h`, `+4h`, `+1d`, `+3d`, `+5d`, and **Next Friday Close**.
Metrics captured at each window:
- Cumulative Return & Absolute Return
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Maximum Drawdown & Maximum Run-up
- Realized Volatility Pre vs Post Event
- Information Pricing Speed (% of total weekly move realized within 5m, 1h, 4h, 1d, and remaining days)
- Reversal Classification (`initial continuation`, `partial reversal`, `full reversal`, `muted initial`).

### D. Objective Regime Classifications
Thresholds are dynamically computed from rolling 3-year empirical percentiles:
- **Real Yield Regime** (4-week $\Delta$ 10Y TIPS): `falling` ($\le 33.3\%$), `neutral`, `rising` ($> 66.7\%$).
- **DXY Regime** (4-week return): `weakening`, `neutral`, `strengthening`.
- **Gold Trend**: `bullish` ($P > \text{MA}_{20w} > \text{MA}_{50w}$), `bearish`, `sideways`.
- **VIX Regime**: `low` ($< 25$th percentile), `normal`, `high` ($> 75$th percentile).
- **Gold Volatility**: `low`, `normal`, `high`.

---

## 3. Quick Start & Execution

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Verification Test Suite
```powershell
python -m pytest tests/ -v
```

### 3. Execute End-to-End Pipeline
```powershell
# Step 1: Ingest market, macro, COT, ETF, and event calendar
python ingest_data.py --start-year 2010

# Step 2: Reconstruct pre-event states, regimes, and build master datasets
python build_dataset.py

# Step 3: Run comprehensive statistical event studies
python run_event_study.py

# Step 4: Run continuous weekly analysis (shocks, positioning, regression)
python run_weekly_analysis.py

# Step 5: Compile research reports and interactive dashboards
python generate_report.py
```

---

## 4. Key Empirical Insights from the Engine

| Domain | Empirical Finding |
| :--- | :--- |
| **Positioning Contrarian Edge** | When CFTC COT Net Speculative positioning is severely depressed ($<10$th percentile), Gold generates a forward 1-week median return of **+0.45%** ($p = 0.015$, 58.1% win rate). Extreme long positioning ($>90$th percentile) exhibits flat-to-negative forward drift (-0.08%). |
| **ETF Flow Capitulation** | Severe physical ETF outflows ($<20$th percentile) act as a contrarian buy signal with forward weekly return of **+0.40%** ($p = 0.019$). |
| **Flight to Safety** | Following severe S&P 500 crashes ($<-3\sigma$ weekly move), Gold exhibits a median forward weekly return of **+1.51%** (85.7% positive response rate, $p = 0.047$). |
| **Reversal Dynamics** | Immediate 1-hour post-event reactions reverse direction by the Friday close in **28–33%** of events, while continuation occurs in **42–48%** of releases. |
| **Pricing Speed** | On average, ~35–45% of the weekly reaction occurs within the first hour of announcement, with ~55–65% driven by subsequent macro transmission drift over the remainder of the week. |

---

## 5. Visualizations & Reports

- **Markdown Report**: `reports/gold_weekly_research_report.md`
- **Styled HTML Report**: `reports/gold_weekly_research_report.html`
- **Interactive Figures**: `reports/figures/`
  - `weekly_macro_dashboard.html`: 3-panel overlay of Gold price, TIPS real yields, DXY, and COT positioning.
  - `trajectory_cpi.html` & `trajectory_fomc_rate_decision.html`: Event path distributions ($T=0$ to Next Friday close).
  - `scatter_cpi.html`: Standardized surprise Z-score vs Next Friday Return with OLS slope.
  - `heatmap_real_yield_cpi.html`: 2D conditional matrix cross-tabulating CPI surprise buckets against Real Yield regimes.
