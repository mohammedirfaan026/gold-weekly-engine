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

from src.ai_engine.data_freshness import DataFreshnessChecker
from src.ai_engine.confidence_calibrator import ConfidenceCalibrator
from src.ai_engine.no_trade_filter import NoTradeFilter
from src.ai_engine.trade_journal import TradeJournal
from src.ai_engine.decision_brief import WeeklyDecisionBrief

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
    "DataFreshnessChecker",
    "ConfidenceCalibrator",
    "NoTradeFilter",
    "TradeJournal",
    "WeeklyDecisionBrief",
]
