"""
Weekly macro analysis pipeline script.
Runs empirical analyses on weekly continuous observations:
market shocks (>2σ moves), CFTC COT positioning cycles, ETF fund flows, and multi-factor regression.
Usage:
    python run_weekly_analysis.py
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.statistics.shock_analysis import MarketShockAnalyzer
from src.statistics.positioning_analysis import PositioningAnalyzer
from src.visualization.weekly_plots import WeeklyPlotter


def run_macro_factor_regression(weekly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes multiple OLS regression of weekly gold returns against continuous macro observations:
    DXY return, Real Yield change, VIX change, SPX return, WTI return, HY OAS change.
    """
    features = [
        "dxy_weekly_return", "real_yield_weekly_change", "vix_weekly_change",
        "spx_weekly_return", "wti_weekly_return", "hy_oas_weekly_change",
        "largest_absolute_surprise"
    ]
    avail = [f for f in features if f in weekly_df.columns]
    sub = weekly_df.dropna(subset=avail + ["weekly_return"]).copy()
    
    if len(sub) < 30:
        return pd.DataFrame()

    y = sub["weekly_return"].values
    X = sub[avail].values
    # Add intercept
    X_mat = np.column_stack([np.ones(len(y)), X])
    
    # OLS closed-form: beta = (X'X)^-1 X'y
    try:
        beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]
        residuals = y - X_mat @ beta
        dof = len(y) - len(beta)
        s2 = np.sum(residuals**2) / dof
        cov_beta = s2 * np.linalg.pinv(X_mat.T @ X_mat)
        se = np.sqrt(np.diag(cov_beta))
        t_stats = beta / se
        p_vals = 2.0 * (1.0 - stats.t.cdf(np.abs(t_stats), dof))

        names = ["Intercept"] + avail
        res_df = pd.DataFrame({
            "factor": names,
            "coefficient": beta,
            "std_error": se,
            "t_statistic": t_stats,
            "p_value": p_vals,
        })
        return res_df
    except Exception:
        return pd.DataFrame()


def main():
    print("=== Running Weekly Macro & Positioning Analysis for Gold ===")
    weekly_file = "data/weekly/gold_weekly_master.parquet"
    if not os.path.exists(weekly_file):
        print(f"Error: Master weekly dataset not found at {weekly_file}. Please run build_dataset.py first.")
        sys.exit(1)

    df = pd.read_parquet(weekly_file)
    os.makedirs("reports/figures", exist_ok=True)

    # 1. Market Shocks Analysis
    print("\n[1/4] Analyzing non-announcement market shocks (>2 sigma / 3 sigma moves)...")
    shocks_df = MarketShockAnalyzer.analyze_shocks(df)
    shocks_df.to_csv("reports/market_shocks_study.csv", index=False)
    print(f"  [OK] Quantified forward 1-week gold drift across {len(shocks_df)} shock archetypes.")

    # 2. CFTC COT Positioning
    print("\n[2/4] Analyzing CFTC COT Net Speculative positioning percentiles...")
    cot_study_df = PositioningAnalyzer.analyze_cot_positioning(df)
    cot_study_df.to_csv("reports/positioning_study.csv", index=False)
    print(f"  [OK] Evaluated forward weekly returns across positioning tiers.")

    # 3. ETF Fund Flows
    print("\n[3/4] Analyzing physical Gold ETF flows (GLD, IAU)...")
    etf_study_df = PositioningAnalyzer.analyze_etf_flows(df)
    etf_study_df.to_csv("reports/etf_flows_study.csv", index=False)
    print(f"  [OK] Evaluated forward weekly returns across ETF flow tiers.")

    # 4. Multi-Factor Regression
    print("\n[4/4] Estimating weekly macro multi-factor return attribution...")
    reg_df = run_macro_factor_regression(df)
    if not reg_df.empty:
        reg_df.to_csv("reports/weekly_regression_summary.csv", index=False)
        print("  [OK] Multi-factor regression estimates calculated.")

    # Interactive Weekly Dashboard
    dashboard_path = "reports/figures/weekly_macro_dashboard.html"
    WeeklyPlotter.plot_macro_overview(df, output_path=dashboard_path)
    print(f"  [OK] Weekly macro dashboard saved to {dashboard_path}")

    print("\n=== Weekly Analysis Completed Successfully! ===")


if __name__ == "__main__":
    main()
