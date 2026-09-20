"""
Event study execution pipeline script.
Runs statistical event studies across all macroeconomic releases, surprise buckets, regimes,
reversals, and speeds. Generates interactive visual figures.
Usage:
    python run_event_study.py
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.statistics.event_study import EventStudyEngine
from src.statistics.conditional_matrix import ConditionalMatrixEngine
from src.statistics.speed_analysis import SpeedAnalyzer
from src.statistics.reversal_analysis import ReversalAnalyzer
from src.visualization.event_plots import EventPlotter
from src.visualization.regime_plots import RegimePlotter


def main():
    print("=== Running Macroeconomic Event Studies for Gold ===")
    events_file = "data/processed/events_master.parquet"
    if not os.path.exists(events_file):
        print(f"Error: Master events dataset not found at {events_file}. Please run build_dataset.py first.")
        sys.exit(1)

    df = pd.read_parquet(events_file)
    if "surprise_bucket" not in df.columns and "surprise_zscore" in df.columns:
        from src.normalization.surprise_calculator import SurpriseCalculator
        df["surprise_bucket"] = df["surprise_zscore"].apply(SurpriseCalculator.bucket_surprise)
    os.makedirs("reports/figures", exist_ok=True)

    # 1. Base Event Study by Type
    print("\n[1/5] Calculating robust event study metrics across all horizons...")
    study_df = EventStudyEngine.run_event_study_by_type(df)
    study_df.to_csv("reports/event_study_summary.csv", index=False)
    print("  [OK] Computed sample sizes, medians, means, trimmed means, and bootstrap 95% CIs.")

    # 2. Surprise Size Analysis
    print("\n[2/5] Evaluating macro surprise elasticity (Standardized Z buckets)...")
    surprise_df = EventStudyEngine.run_event_study_by_surprise_bucket(df)
    surprise_df.to_csv("reports/surprise_bucket_study.csv", index=False)
    print("  [OK] Bucketed surprises: extreme_neg, large_neg, neutral, large_pos, extreme_pos.")

    # 3. Directional Asymmetry Analysis
    print("\n[3/5] Testing directional reaction asymmetry (Positive vs Negative surprises)...")
    asym_df = EventStudyEngine.run_directional_asymmetry_study(df)
    asym_df.to_csv("reports/directional_asymmetry_study.csv", index=False)
    print("  [OK] Calculated win rates and Mann-Whitney U asymmetry p-values.")

    # 4. Response Speed & Reversals
    print("\n[4/5] Computing pricing speed and reversal vs continuation frequencies...")
    speed_df = SpeedAnalyzer.analyze_response_speed_by_event(df)
    reversal_df = ReversalAnalyzer.analyze_reversals_by_event(df)
    speed_df.to_csv("reports/speed_study.csv", index=False)
    reversal_df.to_csv("reports/reversal_study.csv", index=False)
    print("  [OK] Speed distribution (% of weekly move in 5m, 1h, 4h, 1d) and reversal frequencies calculated.")

    # 5. Conditional Response Matrices & Visual Figures
    print("\n[5/5] Generating 2D conditional matrices and interactive Plotly figures...")
    cond_matrices = ConditionalMatrixEngine.generate_all_conditional_matrices(df)
    
    # Render Figures for Key Events
    key_events = ["CPI", "Nonfarm Payrolls", "FOMC Rate Decision", "ISM Manufacturing"]
    for evt in key_events:
        if evt in df["event_type"].values:
            # Trajectory plot
            clean_name = evt.lower().replace(" ", "_")
            EventPlotter.plot_response_trajectory(df, evt, output_path=f"reports/figures/trajectory_{clean_name}.html")
            EventPlotter.plot_surprise_vs_return_scatter(df, evt, output_path=f"reports/figures/scatter_{clean_name}.html")
            
            # Heatmap of Real Yield & DXY regimes
            if evt in cond_matrices:
                if "regime_real_yield" in cond_matrices[evt]:
                    RegimePlotter.plot_conditional_matrix_heatmap(
                        cond_matrices[evt]["regime_real_yield"],
                        output_path=f"reports/figures/heatmap_real_yield_{clean_name}.html",
                    )
                if "regime_dxy" in cond_matrices[evt]:
                    RegimePlotter.plot_conditional_matrix_heatmap(
                        cond_matrices[evt]["regime_dxy"],
                        output_path=f"reports/figures/heatmap_dxy_{clean_name}.html",
                    )

    print(f"  [OK] Interactive figures saved to reports/figures/")
    print("\n=== Event Study Analysis Completed Successfully! ===")


if __name__ == "__main__":
    main()
