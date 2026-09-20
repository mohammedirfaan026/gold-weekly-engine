"""
Unified Driver for the Gold Weekly Predictive Research System.
Executes the end-to-end research pipeline:
1. Feature Matrix & Lineage Dictionary generation (PIT compliance, expanding statistics)
2. Data Quality & Lineage Audit (timestamps, gaps, missingness, vintages)
3. 8-Fold Purged & Embargoed Walk-Forward Validation (Baselines vs ML models)
4. Sequential Information Layer Ablation (Layers A through G)
5. Multiple Testing Control (Benjamini-Hochberg FDR, Block Bootstrap, Structural Breaks)
6. Synthesis of 5 Mandatory Reports and 4 Interactive Visualizations

Usage:
    python run_research.py
"""

from __future__ import annotations
import os
import sys
import time
import argparse
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from research.src.features.builder import LeakageProofFeatureBuilder
from research.src.features.dictionary import FeatureDictionaryGenerator
from research.src.audit.data_quality import DataQualityAuditor
from research.src.validation.walk_forward import WalkForwardEngine
from research.src.validation.ablation import FeatureAblationEngine
from research.src.statistics.hypothesis_testing import HypothesisTestingEngine
from research.src.reporting.report_generator import ResearchReportGenerator


def run_pipeline(quick: bool = False):
    start_time = time.time()
    print("=" * 80)
    print("GOLD WEEKLY RESPONSE ENGINE: PREDICTIVE RESEARCH PIPELINE")
    print("=" * 80)

    # 1. Feature Engineering & Point-in-Time Matrix
    print("\n[Step 1/6] Building Leakage-Proof Feature Matrix...")
    builder = LeakageProofFeatureBuilder()
    matrix = builder.build_feature_matrix()
    os.makedirs("research/features", exist_ok=True)
    matrix_path = "research/features/feature_matrix.parquet"
    matrix.to_parquet(matrix_path, index=False)
    print(f" -> Matrix assembled: {matrix.shape[0]} trading weeks, {matrix.shape[1]} columns.")
    print(f" -> Saved to: {matrix_path}")

    # Feature Dictionary
    print("\n[Step 2/6] Generating Comprehensive Feature Dictionary & Lineage...")
    dict_gen = FeatureDictionaryGenerator(feature_matrix=matrix)
    feat_dict = dict_gen.generate_dictionary()
    dict_path = "research/features/feature_dictionary.csv"
    feat_dict.to_csv(dict_path, index=False)
    print(f" -> Feature dictionary documented: {len(feat_dict)} entries.")
    print(f" -> Saved to: {dict_path}")

    # Data Quality Audit
    print("\n[Step 3/6] Executing Data Quality & Lineage Audit...")
    auditor = DataQualityAuditor(feature_matrix=matrix, feature_dictionary=feat_dict)
    audit_results = auditor.run_full_audit()
    print(" -> Data quality audit complete.")
    print(f"    - Missing values: {len(audit_results['missing_values'][audit_results['missing_values']['null_count'] > 0])} columns with nulls.")
    print(f"    - Timestamp leaks: {audit_results['timestamp_lineage']['violations_count']} detected.")
    print(f"    - Report saved to: research/reports/DATA_QUALITY_REPORT.md")

    # Walk-Forward Validation
    print("\n[Step 4/6] Running Purged and Embargoed Walk-Forward Validation (2018-2026)...")
    wf_engine = WalkForwardEngine(feature_matrix=matrix, embargo_weeks=1)
    oos_df, metrics_df, stability_df, calibration_df = wf_engine.run_walk_forward()
    
    os.makedirs("research/validation", exist_ok=True)
    oos_path = "research/validation/walk_forward_results.csv"
    calib_path = "research/validation/calibration.csv"
    stab_path = "research/validation/feature_stability.csv"

    oos_df.to_csv(oos_path, index=False)
    calibration_df.to_csv(calib_path, index=False)
    stability_df.to_csv(stab_path, index=False)
    print(f" -> Walk-forward complete: {len(oos_df)} out-of-sample weeks evaluated.")
    print(f" -> Top Model: {metrics_df.iloc[0]['Model']} (IC = {metrics_df.iloc[0]['Information_Coefficient']}, DA = {metrics_df.iloc[0]['Directional_Accuracy_Pct']}%)")

    # Sequential Feature Ablation
    print("\n[Step 5/6] Running Sequential Feature Ablation (Layers A through G)...")
    ablation_engine = FeatureAblationEngine(feature_matrix=matrix)
    ablation_df = ablation_engine.run_ablation()
    ablation_path = "research/validation/ablation_results.csv"
    ablation_df.to_csv(ablation_path, index=False)
    print(" -> Information layer ablation complete.")

    # Hypothesis Testing, FDR Control, and Bootstrap
    print("\n[Step 6/6] Applying Multiple Testing Control & Structural Break Tests...")
    ht_engine = HypothesisTestingEngine(feature_matrix=matrix, oos_results=oos_df)
    ledger_df, mt_df = ht_engine.build_hypothesis_ledger()
    breaks_df = ht_engine.test_structural_breaks()

    # Block Bootstrap on Top Model
    top_model_name = metrics_df.iloc[0]["Model"]
    top_pred_col = f"pred_{top_model_name}"
    n_boot = 500 if quick else 2000
    boot_stats = ht_engine.run_block_bootstrap(
        series_pred=oos_df[top_pred_col].values,
        series_true=oos_df["actual_return"].values,
        block_size=8,
        n_bootstraps=n_boot,
    )

    os.makedirs("research/statistics", exist_ok=True)
    ledger_df.to_csv("research/statistics/hypothesis_ledger.csv", index=False)
    mt_df.to_csv("research/statistics/multiple_testing.csv", index=False)
    breaks_df.to_csv("research/statistics/structural_breaks.csv", index=False)
    pd.DataFrame([boot_stats]).to_csv("research/statistics/bootstrap_results.csv", index=False)
    print(" -> Hypothesis testing and FDR adjustments complete.")
    print(f"    - Confirmed Hypotheses (FDR q < 0.05): {(ledger_df['statistical_verdict'] == 'REJECT_NULL (Confirmed)').sum()} / {len(ledger_df)}")

    # Reporting & Visualizations
    print("\nSynthesizing Research Reports and Interactive Visualizations...")
    reporter = ResearchReportGenerator(
        feature_matrix=matrix,
        feature_dictionary=feat_dict,
        oos_results=oos_df,
        metrics_df=metrics_df,
        stability_df=stability_df,
        calibration_df=calibration_df,
        ablation_df=ablation_df,
        hypothesis_ledger=ledger_df,
        break_tests_df=breaks_df,
        bootstrap_stats=boot_stats,
    )
    reporter.generate_all_reports_and_figures()
    print(" -> Generated: FEATURE_REPORT.md, WALK_FORWARD_REPORT.md, ABLATION_REPORT.md, FINAL_RESEARCH_REPORT.md")
    print(" -> Interactive Figures saved to: research/figures/")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed:.1f} SECONDS")
    print("=" * 80)
    print("\nSummary of Out-of-Sample Performance:")
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gold Weekly Predictive Research System")
    parser.add_argument("--quick", action="store_true", help="Run with fewer bootstrap resamples for speed")
    args = parser.parse_args()
    run_pipeline(quick=args.quick)
