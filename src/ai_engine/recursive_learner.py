"""
Recursive Self-Improving Gold AI Engine.
Implements an online adaptive learning system that:
1. Performs automated post-mortems on realized weekly predictions.
2. Decomposes forecast misses into 4 empirical failure archetypes.
3. Adapts state weights via an Attribution-Gated Kalman Filter.
4. Maintains a Failure Memory Bank to apply reflexive hedges against repeat errors.
"""

from __future__ import annotations
import enum
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine


class FailureArchetype(enum.Enum):
    IN_LINE = "IN_LINE_ACCURATE"
    COUNTER_TREND_EXHAUSTION = "COUNTER_TREND_EXHAUSTION"
    MACRO_DECOUPLING = "MACRO_DECOUPLING"
    VOLATILITY_LIQUIDATION = "VOLATILITY_LIQUIDATION"
    TREND_MOMENTUM_OVERRIDE = "TREND_MOMENTUM_OVERRIDE"
    UNCLASSIFIED_DISPERSION = "UNCLASSIFIED_DISPERSION"


class ErrorAttributionEngine:
    """
    Automated Post-Mortem & Root-Cause Forensic Classifier.
    Analyzes why a prediction missed and identifies the underlying macroeconomic mechanism.
    """

    @staticmethod
    def evaluate_miss(
        predicted_ret: float,
        actual_ret: float,
        predicted_bias: float,
        delta_real_yield: float,
        dxy_ret: float,
        vix: float,
        gold_distance_20w: float,
        corridor_high: Optional[float] = None,
        corridor_low: Optional[float] = None,
        actual_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Decomposes the prediction outcome and attributes error to an empirical archetype.
        """
        pred_dir = 1 if predicted_ret > 0 else 0
        actual_dir = 1 if actual_ret > 0 else 0
        is_directional_error = (pred_dir != actual_dir)
        raw_error = predicted_ret - actual_ret
        abs_error = abs(raw_error)

        # Check corridor breach
        corridor_breach = "NONE"
        if corridor_high is not None and corridor_low is not None and actual_price is not None:
            if actual_price > corridor_high:
                corridor_breach = "UPSIDE_RESISTANCE_BREACH"
            elif actual_price < corridor_low:
                corridor_breach = "DOWNSIDE_SUPPORT_BREACH"

        # Baseline: accurate prediction
        if not is_directional_error and abs_error < 0.015:
            return {
                "archetype": FailureArchetype.IN_LINE,
                "archetype_str": FailureArchetype.IN_LINE.value,
                "is_error": False,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": False,
                "is_structural_shift": False,
                "primary_cause": "Forecast aligned within tolerance.",
            }

        # Archetype 1: VOLATILITY_LIQUIDATION
        # High market volatility / risk-off liquidation
        if vix > 22.0 or (vix > 18.0 and abs_error > 0.03):
            return {
                "archetype": FailureArchetype.VOLATILITY_LIQUIDATION,
                "archetype_str": FailureArchetype.VOLATILITY_LIQUIDATION.value,
                "is_error": True,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": True,
                "is_structural_shift": False,
                "primary_cause": f"Equity market turbulence (VIX = {vix:.1f}) triggered cross-asset margin liquidations.",
            }

        # Archetype 2: COUNTER_TREND_EXHAUSTION
        # Severe yield drop (delta_real_yield < -0.07 bps) or spike, but gold pulled back (mean-reversion)
        if delta_real_yield < -0.06 and actual_ret < -0.005:
            return {
                "archetype": FailureArchetype.COUNTER_TREND_EXHAUSTION,
                "archetype_str": FailureArchetype.COUNTER_TREND_EXHAUSTION.value,
                "is_error": True,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": False,
                "is_structural_shift": False,
                "primary_cause": f"Severe weekly yield drop ({delta_real_yield*100:+.1f} bps) triggered post-rally exhaustion pullback.",
            }
        if delta_real_yield > 0.06 and actual_ret > 0.005:
            return {
                "archetype": FailureArchetype.COUNTER_TREND_EXHAUSTION,
                "archetype_str": FailureArchetype.COUNTER_TREND_EXHAUSTION.value,
                "is_error": True,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": False,
                "is_structural_shift": False,
                "primary_cause": f"Sharp weekly yield spike ({delta_real_yield*100:+.1f} bps) met aggressive dip-buying absorption.",
            }

        # Archetype 3: MACRO_DECOUPLING
        # Dollar strengthened or yields rose, but gold surged anyway (sovereign / safe-haven accumulation)
        if (dxy_ret > 0.005 or delta_real_yield > 0.03) and actual_ret > 0.015:
            return {
                "archetype": FailureArchetype.MACRO_DECOUPLING,
                "archetype_str": FailureArchetype.MACRO_DECOUPLING.value,
                "is_error": True,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": False,
                "is_structural_shift": True,
                "primary_cause": f"Gold decoupled from macro headwinds (USD {dxy_ret*100:+.1f}%, Yields {delta_real_yield*100:+.1f} bps) via sovereign accumulation.",
            }

        # Archetype 4: TREND_MOMENTUM_OVERRIDE
        # Strong moving-average trend continued upward despite mild negative macro deltas
        if gold_distance_20w > 0.03 and actual_ret > 0.01:
            return {
                "archetype": FailureArchetype.TREND_MOMENTUM_OVERRIDE,
                "archetype_str": FailureArchetype.TREND_MOMENTUM_OVERRIDE.value,
                "is_error": True,
                "raw_error": round(raw_error, 4),
                "abs_error": round(abs_error, 4),
                "corridor_breach": corridor_breach,
                "is_transient_noise": False,
                "is_structural_shift": False,
                "primary_cause": f"Structural 20-week momentum (+{gold_distance_20w*100:.1f}%) overpowered short-term macro fluctuations.",
            }

        # Fallback
        return {
            "archetype": FailureArchetype.UNCLASSIFIED_DISPERSION,
            "archetype_str": FailureArchetype.UNCLASSIFIED_DISPERSION.value,
            "is_error": True,
            "raw_error": round(raw_error, 4),
            "abs_error": round(abs_error, 4),
            "corridor_breach": corridor_breach,
            "is_transient_noise": False,
            "is_structural_shift": False,
            "primary_cause": "Unclassified price dispersion / unscheduled flow shock.",
        }


class FailureMemoryBank:
    """
    Contextual Memory Bank of Historical Failure Modes.
    Allows the model to query upcoming market conditions against past mistake patterns
    and trigger reflexive risk mitigation.
    """

    FEATURE_KEYS = [
        "delta_real_yield_1w",
        "dxy_return_1w",
        "gold_distance_20w",
        "vix",
    ]

    def __init__(self, max_records: int = 150):
        self.max_records = max_records
        self.memory: List[Dict[str, Any]] = []

    def record_failure(
        self,
        week: str,
        features: Dict[str, float],
        archetype: FailureArchetype,
        error: float,
        actual_ret: float,
    ):
        """Stores a failure pattern in the memory bank."""
        if archetype == FailureArchetype.IN_LINE:
            return  # do not store accurate predictions

        vec = np.array([features.get(k, 0.0) for k in self.FEATURE_KEYS], dtype=float)
        norm_val = np.linalg.norm(vec)
        if norm_val > 1e-6:
            vec_unit = vec / norm_val
        else:
            vec_unit = vec

        record = {
            "week": week,
            "archetype": archetype,
            "archetype_str": archetype.value,
            "vector": vec,
            "vector_unit": vec_unit,
            "error": error,
            "actual_ret": actual_ret,
        }
        self.memory.append(record)
        if len(self.memory) > self.max_records:
            self.memory.pop(0)

    def query_reflexive_risk(self, current_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Computes similarity between current market setup and past failures.
        Returns risk score, matching archetype, and recommended hedge adjustment.
        """
        if not self.memory:
            return {
                "max_similarity": 0.0,
                "matching_archetype": "NONE",
                "most_similar_week": "NONE",
                "reflexive_warning": False,
                "confidence_multiplier": 1.0,
                "corridor_widening_factor": 1.0,
                "bias_tilt": 0.0,
            }

        curr_vec = np.array([current_features.get(k, 0.0) for k in self.FEATURE_KEYS], dtype=float)
        norm_curr = np.linalg.norm(curr_vec)
        if norm_curr > 1e-6:
            curr_unit = curr_vec / norm_curr
        else:
            curr_unit = curr_vec

        best_sim = -1.0
        best_rec = None

        for rec in self.memory:
            sim = float(np.dot(curr_unit, rec["vector_unit"]))
            if sim > best_sim:
                best_sim = sim
                best_rec = rec

        best_sim_clamped = max(0.0, min(1.0, best_sim))

        if best_sim_clamped >= 0.75 and best_rec is not None:
            arch = best_rec["archetype"]
            # Apply reflexive adjustments depending on failure type
            if arch == FailureArchetype.COUNTER_TREND_EXHAUSTION:
                # Tilt against extension
                bias_tilt = -0.05 if best_rec["actual_ret"] < 0 else +0.05
                conf_mult = 0.70
                corridor_factor = 1.25
            elif arch == FailureArchetype.VOLATILITY_LIQUIDATION:
                bias_tilt = 0.0
                conf_mult = 0.50
                corridor_factor = 1.40
            elif arch == FailureArchetype.MACRO_DECOUPLING:
                bias_tilt = +0.03
                conf_mult = 0.80
                corridor_factor = 1.15
            else:
                bias_tilt = 0.0
                conf_mult = 0.85
                corridor_factor = 1.10

            return {
                "max_similarity": round(best_sim_clamped, 3),
                "matching_archetype": best_rec["archetype_str"],
                "most_similar_week": best_rec["week"],
                "reflexive_warning": True,
                "confidence_multiplier": conf_mult,
                "corridor_widening_factor": corridor_factor,
                "bias_tilt": bias_tilt,
            }

        return {
            "max_similarity": round(best_sim_clamped, 3),
            "matching_archetype": best_rec["archetype_str"] if best_rec else "NONE",
            "most_similar_week": best_rec["week"] if best_rec else "NONE",
            "reflexive_warning": False,
            "confidence_multiplier": 1.0,
            "corridor_widening_factor": 1.0,
            "bias_tilt": 0.0,
        }


class RecursiveKalmanEstimator:
    """
    Attribution-Gated Online Kalman Filter for Recursive Macro Betas.
    Maintains dynamic feature weights updated weekly with error-adaptive Kalman gain.
    """

    FEATURE_COLS = [
        "delta_real_yield_1w",
        "dxy_return_1w",
        "delta_breakeven_1w",
        "gold_distance_20w",
    ]

    def __init__(self, initial_q: float = 1e-4, baseline_r: float = 4e-4):
        self.k = len(self.FEATURE_COLS) + 1  # 4 features + 1 intercept
        # Initial weights: intercept ~ +0.002, yield ~ -0.01, dxy ~ -0.03, breakeven ~ +0.01, trend ~ +0.02
        self.w = np.array([0.002, 0.0, -0.03, 0.01, 0.02], dtype=float)
        self.P = np.eye(self.k) * 0.01
        self.Q = np.eye(self.k) * initial_q
        self.R0 = baseline_r
        self.feature_means = np.zeros(len(self.FEATURE_COLS))
        self.feature_stds = np.ones(len(self.FEATURE_COLS))
        self.target_std = 0.02
        self.history_updates = 0

    def warm_start(self, train_df: pd.DataFrame, target_series: pd.Series):
        """Initializes weights on historical training sample."""
        clean_idx = target_series.dropna().index
        sub_X = train_df.loc[clean_idx, self.FEATURE_COLS].fillna(0.0).values
        sub_y = target_series.loc[clean_idx].values

        self.feature_means = np.mean(sub_X, axis=0)
        self.feature_stds = np.std(sub_X, axis=0)
        self.feature_stds[self.feature_stds < 1e-5] = 1.0
        self.target_std = float(np.std(sub_y)) if np.std(sub_y) > 1e-5 else 0.02

        # Scale features
        X_scaled = (sub_X - self.feature_means) / self.feature_stds
        X_design = np.column_stack([np.ones(len(X_scaled)), X_scaled])

        # Bayesian linear regression solution for initial w and P
        from sklearn.linear_model import BayesianRidge
        br = BayesianRidge().fit(X_scaled, sub_y)
        self.w = np.concatenate([[br.intercept_], br.coef_])
        self.P = np.eye(self.k) * 0.005
        self.R0 = float(np.var(sub_y - br.predict(X_scaled))) if len(sub_y) > 10 else 4e-4
        self.history_updates = len(sub_y)

    def get_design_vector(self, row_dict: Dict[str, float]) -> np.ndarray:
        raw_vals = np.array([float(row_dict.get(c, 0.0)) for c in self.FEATURE_COLS])
        scaled_vals = (raw_vals - self.feature_means) / self.feature_stds
        return np.concatenate([[1.0], scaled_vals])

    def predict(self, row_dict: Dict[str, float]) -> Tuple[float, float]:
        """
        Computes expected return and bounded bias score using current recursive weights.
        Returns: (expected_return, bias_score)
        """
        x = self.get_design_vector(row_dict)
        exp_ret = float(np.dot(x, self.w))
        
        # Continuous bias score via tanh scaling relative to target std
        z = exp_ret / (1.5 * self.target_std)
        bias_score = float(np.tanh(z * 0.75))
        return exp_ret, bias_score

    def update_with_post_mortem(
        self,
        past_row_dict: Dict[str, float],
        realized_return: float,
        attribution: Dict[str, Any],
    ):
        """
        Executes Kalman measurement update with attribution-based noise gating.
        """
        x = self.get_design_vector(past_row_dict)
        pred_y = float(np.dot(x, self.w))
        residual = realized_return - pred_y

        # Attribution-gated measurement noise R_t
        arch = attribution.get("archetype", FailureArchetype.IN_LINE)
        if arch == FailureArchetype.VOLATILITY_LIQUIDATION:
            # External shock: inflate noise to freeze/dampen weight adaptation
            R_t = self.R0 * 8.0
        elif arch == FailureArchetype.MACRO_DECOUPLING:
            # Structural regime shift: deflate noise to accelerate learning
            R_t = self.R0 * 0.4
        elif arch == FailureArchetype.COUNTER_TREND_EXHAUSTION:
            R_t = self.R0 * 0.8
        else:
            R_t = self.R0

        # Time update (prior prediction step)
        P_prior = self.P + self.Q

        # Measurement update (correction step)
        S = float(np.dot(x, np.dot(P_prior, x)) + R_t)
        K = np.dot(P_prior, x) / S  # Kalman gain vector

        self.w = self.w + K * residual
        self.P = np.dot(np.eye(self.k) - np.outer(K, x), P_prior)

        # Soft stabilization bounds to prevent divergence
        # w[0] = intercept
        self.w[0] = np.clip(self.w[0], -0.01, 0.01)
        # w[1] = delta_real_yield_1w (allow mild empirical reversal slope up to +0.035, clamp extreme negative)
        self.w[1] = np.clip(self.w[1], -0.05, 0.04)
        # w[2] = dxy_return_1w (penalize positive USD exposure beyond +0.02)
        self.w[2] = np.clip(self.w[2], -0.06, 0.02)
        # w[3] = delta_breakeven_1w
        self.w[3] = np.clip(self.w[3], -0.02, 0.04)
        # w[4] = gold_distance_20w
        self.w[4] = np.clip(self.w[4], -0.01, 0.05)

        self.history_updates += 1


class RecursiveSelfImprovingEngine:
    """
    Master Recursive Self-Improving Engine.
    Unifies the Post-Mortem Forensic Evaluator, Failure Memory Bank, and Recursive Kalman Filter.
    """

    def __init__(self):
        self.attribution_engine = ErrorAttributionEngine()
        self.kalman_model = RecursiveKalmanEstimator()
        self.memory_bank = FailureMemoryBank()
        self.last_prediction: Optional[Dict[str, Any]] = None
        self.is_initialized_ = False

    def initialize(self, training_matrix: pd.DataFrame):
        """Warm-starts the recursive engine on completed historical matrix."""
        clean_df = training_matrix.dropna(subset=["next_week_gold_return"]).reset_index(drop=True)
        self.kalman_model.warm_start(clean_df, clean_df["next_week_gold_return"])
        self.is_initialized_ = True

    def process_prior_week_outcome(
        self,
        week: str,
        features_dict: Dict[str, float],
        realized_return: float,
        actual_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Step 1: Runs automated post-mortem on the completed week and updates recursive weights.
        """
        if not self.is_initialized_:
            raise RuntimeError("Engine must be initialized before processing weekly outcomes.")

        pred_ret = self.last_prediction.get("recursive_expected_return", self.last_prediction.get("expected_return", 0.002)) if self.last_prediction else 0.002
        pred_bias = self.last_prediction.get("recursive_bias_score", self.last_prediction.get("bias_score", 0.0)) if self.last_prediction else 0.0
        c_high = self.last_prediction.get("corridor_high") if self.last_prediction else None
        c_low = self.last_prediction.get("corridor_low") if self.last_prediction else None

        attribution = self.attribution_engine.evaluate_miss(
            predicted_ret=pred_ret,
            actual_ret=realized_return,
            predicted_bias=pred_bias,
            delta_real_yield=features_dict.get("delta_real_yield_1w", 0.0),
            dxy_ret=features_dict.get("dxy_return_1w", 0.0),
            vix=features_dict.get("vix", 15.0),
            gold_distance_20w=features_dict.get("gold_distance_20w", 0.0),
            corridor_high=c_high,
            corridor_low=c_low,
            actual_price=actual_price,
        )

        # Update Kalman weights
        self.kalman_model.update_with_post_mortem(features_dict, realized_return, attribution)

        # If it was an error, record in memory bank
        if attribution["is_error"]:
            self.memory_bank.record_failure(
                week=week,
                features=features_dict,
                archetype=attribution["archetype"],
                error=attribution["raw_error"],
                actual_ret=realized_return,
            )

        post_mortem_summary = {
            "week_evaluated": week,
            "realized_return": round(realized_return * 100.0, 2),
            "predicted_return": round(pred_ret * 100.0, 2),
            "error": round(attribution["raw_error"] * 100.0, 2),
            "archetype": attribution["archetype_str"],
            "primary_cause": attribution["primary_cause"],
            "updated_weights": {
                "intercept": round(float(self.kalman_model.w[0]), 4),
                "beta_real_yield": round(float(self.kalman_model.w[1]), 4),
                "beta_dxy": round(float(self.kalman_model.w[2]), 4),
                "beta_breakeven": round(float(self.kalman_model.w[3]), 4),
                "beta_trend_20w": round(float(self.kalman_model.w[4]), 4),
            },
        }

        return post_mortem_summary

    def predict_upcoming_week(
        self,
        week: str,
        current_features_dict: Dict[str, float],
        current_gold_price: float,
        baseline_corridor_high: float,
        baseline_corridor_low: float,
    ) -> Dict[str, Any]:
        """
        Step 2: Generates adaptive forecast for upcoming week incorporating reflexive hedge adjustments.
        """
        if not self.is_initialized_:
            raise RuntimeError("Engine must be initialized before generating predictions.")

        # 1. Base recursive Kalman prediction
        raw_pred_ret, raw_bias_score = self.kalman_model.predict(current_features_dict)

        # 2. Query Failure Memory Bank
        reflexive_res = self.memory_bank.query_reflexive_risk(current_features_dict)

        # 3. Apply reflexive adjustments
        adj_bias_score = raw_bias_score * reflexive_res["confidence_multiplier"] + reflexive_res["bias_tilt"]
        adj_bias_score = float(np.clip(adj_bias_score, -1.0, 1.0))
        adj_pred_ret = raw_pred_ret + (reflexive_res["bias_tilt"] * self.kalman_model.target_std)

        # 4. Volatility corridor adaptation
        base_half_width = (baseline_corridor_high - baseline_corridor_low) / 2.0
        adj_half_width = base_half_width * reflexive_res["corridor_widening_factor"]
        expected_center = current_gold_price * (1.0 + adj_pred_ret)
        adj_corridor_high = round(expected_center + adj_half_width, 2)
        adj_corridor_low = round(expected_center - adj_half_width, 2)

        # Bias category
        if adj_bias_score >= 0.25:
            cat = "BULLISH_BIAS"
        elif adj_bias_score <= -0.25:
            cat = "BEARISH_BIAS"
        else:
            cat = "NEUTRAL"

        prediction_res = {
            "prediction_week": week,
            "current_gold_price": current_gold_price,
            "recursive_expected_return": round(adj_pred_ret, 4),
            "recursive_expected_return_pct": round(adj_pred_ret * 100.0, 2),
            "recursive_bias_score": round(adj_bias_score, 3),
            "recursive_bias_category": cat,
            "corridor_high": adj_corridor_high,
            "corridor_low": adj_corridor_low,
            "corridor_width_dollar": round(adj_corridor_high - adj_corridor_low, 2),
            "reflexive_warning_active": reflexive_res["reflexive_warning"],
            "failure_similarity_score": reflexive_res["max_similarity"],
            "matching_failure_archetype": reflexive_res["matching_archetype"],
            "similar_historical_failure_week": reflexive_res["most_similar_week"],
            "current_weights": {
                "intercept": round(float(self.kalman_model.w[0]), 4),
                "beta_real_yield": round(float(self.kalman_model.w[1]), 4),
                "beta_dxy": round(float(self.kalman_model.w[2]), 4),
                "beta_breakeven": round(float(self.kalman_model.w[3]), 4),
                "beta_trend_20w": round(float(self.kalman_model.w[4]), 4),
            },
        }

        self.last_prediction = prediction_res
        return prediction_res
