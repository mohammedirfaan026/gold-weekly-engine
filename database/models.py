"""
SQLAlchemy 2.0 ORM models for the Gold Research Terminal.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Float,
    Boolean,
    DateTime,
    Date,
    Text,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from database.db_session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    source_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    source_url = Column(Text, nullable=True)
    frequency = Column(String(32), nullable=False)
    timezone = Column(String(64), nullable=False, default="UTC")
    coverage_start = Column(DateTime(timezone=True), nullable=True)
    coverage_end = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))
    dataset_version = Column(String(32), default="v1.0")


class MarketBar(Base):
    __tablename__ = "market_bars"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    symbol = Column(String(32), nullable=False, index=True)
    timeframe = Column(String(16), nullable=False)
    bar_time = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    source = Column(String(64), default="YahooFinance")
    is_imputed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "bar_time", name="uq_market_bar"),
    )


class MacroEvent(Base):
    __tablename__ = "macro_events"

    event_id = Column(String(64), primary_key=True)
    event_type = Column(String(64), nullable=False, index=True)
    country = Column(String(8), default="US")
    publication_time = Column(DateTime(timezone=True), nullable=False, index=True)
    observation_period = Column(String(32), nullable=True)
    previous_value = Column(Float, nullable=True)
    consensus_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    surprise_absolute = Column(Float, nullable=True)
    surprise_percentage = Column(Float, nullable=True)
    surprise_zscore = Column(Float, nullable=True, index=True)
    surprise_bucket = Column(String(32), nullable=True)
    importance = Column(String(16), default="high")
    source = Column(String(64), default="BLS")
    source_url = Column(Text, nullable=True)
    vintage_mode = Column(String(32), default="REAL_TIME_VINTAGE")
    initial_release = Column(Float, nullable=True)
    revision = Column(Float, default=0.0)
    revision_time = Column(DateTime(timezone=True), nullable=True)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))


class MacroObservation(Base):
    __tablename__ = "macro_observations"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    series_id = Column(String(64), nullable=False, index=True)
    observation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    publication_time = Column(DateTime(timezone=True), nullable=False)
    value = Column(Float, nullable=False)
    revision_number = Column(Integer, default=0)
    source = Column(String(64), default="FRED")
    is_imputed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    __table_args__ = (
        UniqueConstraint("series_id", "observation_time", "revision_number", name="uq_macro_obs"),
    )


class WeeklyFeature(Base):
    __tablename__ = "weekly_features"

    week_ending = Column(String(16), primary_key=True)  # YYYY-MM-DD
    prediction_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    gold_close = Column(Float, nullable=False)
    gold_return_1w = Column(Float, nullable=True)
    gold_return_4w = Column(Float, nullable=True)
    gold_return_12w = Column(Float, nullable=True)
    gold_ma_20w = Column(Float, nullable=True)
    gold_ma_50w = Column(Float, nullable=True)
    gold_trend = Column(Integer, default=0)
    gold_volatility_20w = Column(Float, nullable=True)
    dxy_close = Column(Float, nullable=True)
    dxy_return_1w = Column(Float, nullable=True)
    dxy_return_4w = Column(Float, nullable=True)
    real_yield_10y = Column(Float, nullable=True)
    delta_real_yield_1w = Column(Float, nullable=True)
    delta_real_yield_4w = Column(Float, nullable=True)
    nominal_treasury_10y = Column(Float, nullable=True)
    breakeven_10y = Column(Float, nullable=True)
    vix_close = Column(Float, nullable=True)
    vix_change_1w = Column(Float, nullable=True)
    sp500_close = Column(Float, nullable=True)
    sp500_return_1w = Column(Float, nullable=True)
    wti_close = Column(Float, nullable=True)
    wti_return_1w = Column(Float, nullable=True)
    silver_close = Column(Float, nullable=True)
    silver_return_1w = Column(Float, nullable=True)
    cot_net_speculative = Column(Float, nullable=True)
    cot_percentile_3y = Column(Float, nullable=True)
    etf_weekly_flow_usd_m = Column(Float, nullable=True)
    etf_flow_percentile = Column(Float, nullable=True)
    shock_real_yield_2sigma = Column(Integer, default=0)
    shock_dxy_2sigma = Column(Integer, default=0)
    shock_sp500_2sigma = Column(Integer, default=0)
    shock_vix_2sigma = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    target = relationship("WeeklyTarget", back_populates="feature", uselist=False)
    regimes = relationship("Regime", back_populates="feature")


class WeeklyTarget(Base):
    __tablename__ = "weekly_targets"

    week_ending = Column(String(16), ForeignKey("weekly_features.week_ending"), primary_key=True)
    next_week_gold_return = Column(Float, nullable=True)
    next_week_direction = Column(Integer, nullable=True)
    target_p_up = Column(Integer, nullable=True)
    target_p_plus_1pct = Column(Integer, nullable=True)
    target_p_minus_1pct = Column(Integer, nullable=True)
    next_week_gold_volatility = Column(Float, nullable=True)
    next_week_max_favorable_excursion = Column(Float, nullable=True)
    next_week_max_adverse_excursion = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    feature = relationship("WeeklyFeature", back_populates="target")


class Regime(Base):
    __tablename__ = "regimes"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    week_ending = Column(String(16), ForeignKey("weekly_features.week_ending"), nullable=False)
    dimension = Column(String(32), nullable=False, index=True)
    regime_label = Column(String(32), nullable=False, index=True)
    threshold_low = Column(Float, nullable=True)
    threshold_high = Column(Float, nullable=True)
    lookback_window = Column(Integer, default=750)
    calculation_method = Column(String(64), default="expanding_percentile")
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    feature = relationship("WeeklyFeature", back_populates="regimes")

    __table_args__ = (
        UniqueConstraint("week_ending", "dimension", name="uq_week_regime"),
    )


class ResearchRun(Base):
    __tablename__ = "research_runs"

    run_id = Column(String(64), primary_key=True)
    git_commit = Column(String(64), nullable=False)
    dataset_version = Column(String(32), nullable=False)
    feature_version = Column(String(32), nullable=False)
    model_version = Column(String(32), nullable=False)
    parameters = Column(JSON, default=dict)
    results_summary = Column(JSON, default=dict)
    status = Column(String(32), default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    model_results = relationship("ModelResult", back_populates="run", cascade="all, delete-orphan")
    backtest_run = relationship("BacktestRun", back_populates="research_run", uselist=False, cascade="all, delete-orphan")


class ModelResult(Base):
    __tablename__ = "model_results"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("research_runs.run_id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(64), nullable=False)
    target_name = Column(String(64), nullable=False)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    directional_accuracy_pct = Column(Float, nullable=True)
    balanced_accuracy_pct = Column(Float, nullable=True)
    brier_score = Column(Float, nullable=True)
    information_coefficient = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate_pct = Column(Float, nullable=True)
    calibration_error = Column(Float, nullable=True)
    metrics_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    run = relationship("ResearchRun", back_populates="model_results")

    __table_args__ = (
        UniqueConstraint("run_id", "model_name", "target_name", name="uq_run_model_target"),
    )


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    run_id = Column(String(64), ForeignKey("research_runs.run_id", ondelete="CASCADE"), primary_key=True)
    strategy_name = Column(String(64), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    parameters = Column(JSON, default=dict)
    slippage_bps = Column(Float, default=2.0)
    commission_bps = Column(Float, default=1.5)
    initial_capital = Column(Float, default=100000.0)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    research_run = relationship("ResearchRun", back_populates="backtest_run")
    metrics = relationship("BacktestMetric", back_populates="backtest_run", uselist=False, cascade="all, delete-orphan")


class BacktestMetric(Base):
    __tablename__ = "backtest_metrics"

    run_id = Column(String(64), ForeignKey("backtest_runs.run_id", ondelete="CASCADE"), primary_key=True)
    total_return_pct = Column(Float, nullable=True)
    annualized_return_pct = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)
    win_rate_pct = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    turnover_annualized = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    trade_log = Column(JSON, default=list)
    equity_curve = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc))

    backtest_run = relationship("BacktestRun", back_populates="metrics")


class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"

    check_id = Column(String(64), primary_key=True)
    check_timestamp = Column(DateTime(timezone=True), default=dt.datetime.now(dt.timezone.utc), index=True)
    check_name = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)  # PASS, WARNING, FAIL
    synthetic_values_count = Column(Integer, default=0)
    violations_count = Column(Integer, default=0)
    details = Column(JSON, default=dict)
