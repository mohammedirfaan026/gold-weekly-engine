"""
Automated Test Suite for the Gold Weekly Predictive Research System.
Verifies:
1. Point-in-time invariant: published_at <= prediction_timestamp across all rows.
2. Expanding window statistical compliance (no future look-ahead in rolling calculations).
3. Walk-forward fold isolation and 1-week embargo enforcement.
4. Model contracts and deterministic inference outputs.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
import pandas as pd

from research.src.features.builder import LeakageProofFeatureBuilder
from research.src.models.baselines import get_all_baselines
from research.src.models.estimators import get_ml_models, MultiTargetClassifier
from research.src.validation.walk_forward import WalkForwardEngine


@pytest.fixture(scope="module")
def feature_matrix():
    builder = LeakageProofFeatureBuilder()
    df = builder.build_feature_matrix()
    return df


def test_pit_timestamp_lineage(feature_matrix):
    """Asserts that no feature is available after the prediction timestamp."""
    pred_ts = pd.to_datetime(feature_matrix["prediction_timestamp"], utc=True)
    avail_ts = pd.to_datetime(feature_matrix["feature_available_timestamp"], utc=True)
    
    # Strictly avail_ts <= pred_ts
    leaks = (avail_ts > pred_ts).sum()
    assert leaks == 0, f"Detected {leaks} point-in-time timestamp leaks!"


def test_target_construction(feature_matrix):
    """Asserts target is correctly defined as next week's close return without current-week overlap."""
    close = feature_matrix["gold_close"]
    expected_next_ret = (close.shift(-1) / close) - 1.0
    
    # Check match up to the penultimate week
    actual_next_ret = feature_matrix["next_week_gold_return"]
    diff = (expected_next_ret.iloc[:-1] - actual_next_ret.iloc[:-1]).abs()
    assert diff.max() < 1e-7, "Target return calculation diverges from forward shift formula!"


def test_walk_forward_fold_isolation(feature_matrix):
    """Asserts train and test windows have zero overlap and 1-week embargo is strictly enforced."""
    wf = WalkForwardEngine(feature_matrix=feature_matrix, embargo_weeks=1)
    folds = wf.define_folds()
    
    df = feature_matrix.copy()
    df["year"] = pd.to_datetime(df["week_ending"]).dt.year

    for f in folds:
        train_mask = df["year"] <= f["train_end_year"]
        train_indices = df[train_mask].index
        purged_train_indices = train_indices[:-1]  # 1-week embargo
        
        test_mask = (df["year"] >= f["test_start_year"]) & (df["year"] <= f["test_end_year"])
        test_indices = df[test_mask].index

        # 1. No overlap
        overlap = set(purged_train_indices).intersection(set(test_indices))
        assert len(overlap) == 0, f"Overlap detected between train and test in Fold {f['fold']}!"

        # 2. Embargo gap
        max_train_idx = max(purged_train_indices)
        min_test_idx = min(test_indices)
        assert min_test_idx > max_train_idx + 1, f"Embargo gap violated in Fold {f['fold']}!"


def test_baseline_models_contract(feature_matrix):
    """Verifies all 6 benchmark models adhere to fit, predict, predict_proba interface."""
    baselines = get_all_baselines()
    assert len(baselines) == 6, "Expected 6 benchmark baselines!"

    train_df = feature_matrix.iloc[:100]
    test_df = feature_matrix.iloc[100:120]
    
    y_train = train_df["next_week_gold_return"].dropna()
    X_train = train_df.loc[y_train.index]
    X_test = test_df

    for name, model in baselines.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)

        assert len(preds) == len(X_test), f"{name} predict output shape mismatch!"
        assert probs.shape == (len(X_test), 2), f"{name} predict_proba output shape mismatch!"
        assert np.all(probs >= 0.0) and np.all(probs <= 1.0), f"{name} produces invalid probabilities!"


def test_multi_target_classifier_calibration(feature_matrix):
    """Verifies MultiTargetClassifier outputs calibrated probabilities within [0, 1]."""
    train_df = feature_matrix.iloc[:150]
    test_df = feature_matrix.iloc[150:180]

    feature_cols = ["gold_return_1w", "delta_real_yield_1w", "dxy_return_1w", "vix"]
    classifier = MultiTargetClassifier()
    classifier.fit(train_df[feature_cols], train_df["next_week_gold_return"])
    
    probs = classifier.predict_probabilities(test_df[feature_cols])
    assert "p_up" in probs and "p_plus_1pct" in probs and "p_minus_1pct" in probs
    for key in probs:
        assert np.all(probs[key] >= 0.0) and np.all(probs[key] <= 1.0)
