"""
Gold AI Weekly Bias & Range Engine package.
"""

from src.ai_engine.core_bias import MacroBiasEstimator
from src.ai_engine.range_predictor import WeeklyRangePredictor
from src.ai_engine.tail_risk import TailRiskEstimator
from src.ai_engine.analog_matcher import PointInTimeAnalogMatcher
from src.ai_engine.engine import GoldWeeklyBiasEngine
from src.ai_engine.recursive_learner import (
    FailureArchetype,
    ErrorAttributionEngine,
    FailureMemoryBank,
    RecursiveKalmanEstimator,
    RecursiveSelfImprovingEngine,
)

__all__ = [
    "MacroBiasEstimator",
    "WeeklyRangePredictor",
    "TailRiskEstimator",
    "PointInTimeAnalogMatcher",
    "GoldWeeklyBiasEngine",
    "FailureArchetype",
    "ErrorAttributionEngine",
    "FailureMemoryBank",
    "RecursiveKalmanEstimator",
    "RecursiveSelfImprovingEngine",
]
