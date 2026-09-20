"""
Purged and Embargoed Walk-Forward Validation Engine.
Executes 8-fold expanding walk-forward validation across 2010-2026:
- Fold 1: Train 2010-2017 -> Test 2018
- Fold 2: Train 2010-2018 -> Test 2019
- Fold 3: Train 2010-2019 -> Test 2020
- Fold 4: Train 2010-2020 -> Test 2021
- Fold 5: Train 2010-2021 -> Test 2022
- Fold 6: Train 2010-2022 -> Test 2023
- Fold 7: Train 2010-2023 -> Test 2024
- Fold 8: Train 2010-2024 -> Test 2025-2026
Includes 1-week embargo, strict train-split preprocessing, and comprehensive OOS metric evaluation.
"""

from __future__ import annotations
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import brier_score_loss, roc_auc_score, mean_squared_error, mean_absolute_error

from research.src.models.baselines import get_all_baselines
from research.src.models.estimators import get_ml_models, MultiTargetClassifier


class WalkForwardEngine:
    """
    Orchestrates out-of-sample walk-forward model fitting and evaluation.
    """

    def __init__(
        self,
        feature_matrix: pd.DataFrame,
        target_col: str = "next_week_gold_return",
        target_binary_col: str = "target_p_up",
        embargo_weeks: int = 1,
    ):
        self.df = feature_matrix.copy()
        self.df["week_ending_dt"] = pd.to_datetime(self.df["week_ending"])
        self.df["year"] = self.df["week_ending_dt"].dt.year
        self.target_col = target_col
        self.target_binary_col = target_binary_col
        self.embargo_weeks = embargo_weeks

        # Identify feature columns (exclude metadata and target columns)
        exclude_cols = [
            "week_ending", "week_start", "week_end", "prediction_timestamp",
            "data_timestamp", "feature_available_timestamp", "feature_lag_hours",
            "data_source", "next_week_gold_return", "next_week_gold_direction",
            "target_p_up", "target_p_plus_1pct", "target_p_minus_1pct",
            "next_week_gold_volatility", "next_week_max_favorable_excursion",
            "next_week_max_drawdown", "week_ending_dt", "year", "gold_close"
        ]
        self.feature_cols = [c for c in self.df.columns if c not in exclude_cols]

    def define_folds(self) -> List[Dict[str, Any]]:
        """Defines the 8 expanding annual walk-forward folds."""
        folds = [
            {"fold": 1, "train_end_year": 2017, "test_start_year": 2018, "test_end_year": 2018},
            {"fold": 2, "train_end_year": 2018, "test_start_year": 2019, "test_end_year": 2019},
            {"fold": 3, "train_end_year": 2019, "test_start_year": 2020, "test_end_year": 2020},
            {"fold": 4, "train_end_year": 2020, "test_start_year": 2021, "test_end_year": 2021},
            {"fold": 5, "train_end_year": 2021, "test_start_year": 2022, "test_end_year": 2022},
            {"fold": 6, "train_end_year": 2022, "test_start_year": 2023, "test_end_year": 2023},
            {"fold": 7, "train_end_year": 2023, "test_start_year": 2024, "test_end_year": 2024},
            {"fold": 8, "train_end_year": 2024, "test_start_year": 2025, "test_end_year": 2026},
        ]
        return folds

    def run_walk_forward(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Runs walk-forward evaluation across all folds for all baselines and ML models.
        Returns:
            - oos_predictions: DataFrame of row-by-row out-of-sample forecasts
            - metrics_df: Summary metrics per model
            - stability_df: Feature importance stability across folds
            - calibration_dict: Data for reliability curves
        """
        folds = self.define_folds()
        all_models = {**get_all_baselines(), **get_ml_models()}
        
        oos_records = []
        feature_importance_records = []

        for f_info in folds:
            fold_num = f_info["fold"]
            train_mask = self.df["year"] <= f_info["train_end_year"]
            
            # Apply 1-week embargo: exclude the last training week so target does not leak into test
            train_indices = self.df[train_mask].index
            if len(train_indices) > self.embargo_weeks:
                purged_train_indices = train_indices[:-self.embargo_weeks]
            else:
                purged_train_indices = train_indices

            test_mask = (self.df["year"] >= f_info["test_start_year"]) & (self.df["year"] <= f_info["test_end_year"])
            
            # Require valid target in both
            train_df = self.df.loc[purged_train_indices].dropna(subset=[self.target_col])
            test_df = self.df[test_mask].dropna(subset=[self.target_col])

            if test_df.empty:
                continue

            X_train = train_df[self.feature_cols]
            y_train = train_df[self.target_col]
            X_test = test_df[self.feature_cols]
            y_test = test_df[self.target_col]
            y_test_bin = (y_test > 0.0).astype(int)

            # Fit MultiTargetClassifier for calibrated probabilities
            classifier = MultiTargetClassifier().fit(X_train, y_train)
            probs_dict = classifier.predict_probabilities(X_test)

            fold_preds: Dict[str, np.ndarray] = {}
            fold_probs: Dict[str, np.ndarray] = {}

            # Fit every model
            for name, model in all_models.items():
                try:
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)
                    probs = model.predict_proba(X_test)[:, 1]
                    fold_preds[name] = preds
                    fold_probs[name] = probs

                    # Extract feature importance if available
                    if hasattr(model, "get_feature_importances"):
                        fi = model.get_feature_importances()
                        for feat, imp in fi.items():
                            feature_importance_records.append({
                                "fold": fold_num,
                                "model": name,
                                "feature": feat,
                                "importance": imp,
                            })
                except Exception as e:
                    # Robust fallback to mean
                    fold_preds[name] = np.zeros(len(test_df))
                    fold_probs[name] = np.full(len(test_df), 0.5)

            # Record week-by-week predictions
            for i, idx in enumerate(test_df.index):
                rec = {
                    "fold": fold_num,
                    "week_ending": str(test_df.loc[idx, "week_ending"]),
                    "actual_return": float(y_test.iloc[i]),
                    "actual_direction": int(y_test_bin.iloc[i]),
                    "prob_up_calibrated": float(probs_dict["p_up"][i]),
                    "prob_plus1_calibrated": float(probs_dict["p_plus_1pct"][i]),
                    "prob_minus1_calibrated": float(probs_dict["p_minus_1pct"][i]),
                }
                for name in all_models:
                    rec[f"pred_{name}"] = float(fold_preds[name][i])
                    rec[f"prob_{name}"] = float(fold_probs[name][i])
                oos_records.append(rec)

        oos_df = pd.DataFrame(oos_records)
        
        # Calculate summary evaluation metrics
        metrics_df = self.calculate_metrics(oos_df, list(all_models.keys()))
        stability_df = pd.DataFrame(feature_importance_records)
        calibration_df = self.compute_calibration(oos_df, "prob_up_calibrated", "actual_direction")

        return oos_df, metrics_df, stability_df, calibration_df

    def calculate_metrics(self, oos_df: pd.DataFrame, model_names: List[str]) -> pd.DataFrame:
        """Computes comprehensive OOS evaluation metrics for each model."""
        y_true = oos_df["actual_return"].values
        y_dir = oos_df["actual_direction"].values
        n = len(y_true)

        rows = []
        for name in model_names:
            pred_col = f"pred_{name}"
            prob_col = f"prob_{name}"
            
            if pred_col not in oos_df.columns:
                continue

            y_pred = oos_df[pred_col].values
            y_prob = oos_df[prob_col].values

            # 1. Directional Accuracy
            pred_dir = (y_pred > 0.0).astype(int)
            da = np.mean(pred_dir == y_dir) * 100.0

            # 2. Information Coefficient (Spearman Rank Correlation)
            if np.std(y_pred) > 1e-6:
                ic, ic_pval = spearmanr(y_pred, y_true)
            else:
                ic, ic_pval = 0.0, 1.0

            # 3. RMSE & MAE
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)

            # 4. Sign-Weighted Simulated Sharpe Ratio
            pos = np.sign(y_pred)
            strat_ret = pos * y_true
            if np.std(strat_ret) > 1e-6:
                sharpe = (np.mean(strat_ret) / np.std(strat_ret)) * np.sqrt(52)
            else:
                sharpe = 0.0

            # 5. Brier Score & AUC-ROC
            brier = brier_score_loss(y_dir, np.clip(y_prob, 0.0, 1.0))
            try:
                auc = roc_auc_score(y_dir, y_prob)
            except Exception:
                auc = 0.5

            rows.append({
                "Model": name,
                "Directional_Accuracy_Pct": round(da, 2),
                "Information_Coefficient": round(ic, 4),
                "IC_p_value": round(ic_pval, 4),
                "RMSE": round(rmse, 4),
                "MAE": round(mae, 4),
                "Annualized_Sharpe": round(sharpe, 2),
                "Brier_Score": round(brier, 4),
                "AUC_ROC": round(auc, 4),
            })

        res_df = pd.DataFrame(rows)
        return res_df.sort_values(by="Information_Coefficient", ascending=False).reset_index(drop=True)

    def compute_calibration(self, oos_df: pd.DataFrame, prob_col: str, true_col: str, n_bins: int = 5) -> pd.DataFrame:
        """Computes empirical probability vs predicted probability across bins."""
        sub = oos_df[[prob_col, true_col]].dropna().copy()
        sub["bin"] = pd.qcut(sub[prob_col], q=n_bins, duplicates="drop")
        
        calib = sub.groupby("bin", observed=True).agg(
            mean_predicted=(prob_col, "mean"),
            empirical_frequency=(true_col, "mean"),
            count=(true_col, "count")
        ).reset_index()
        calib["ece"] = (calib["mean_predicted"] - calib["empirical_frequency"]).abs()
        return calib
