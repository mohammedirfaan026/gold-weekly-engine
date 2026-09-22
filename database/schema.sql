-- Gold Weekly Response Engine: PostgreSQL 16 Relational Schema
-- Implements hybrid storage: Relational metadata, events, features, regimes, runs & metrics in Postgres;
-- High-frequency intraday tick/minute bars in Parquet.

CREATE TABLE IF NOT EXISTS data_sources (
    source_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    source_url TEXT,
    frequency VARCHAR(32) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    coverage_start TIMESTAMPTZ,
    coverage_end TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dataset_version VARCHAR(32) NOT NULL DEFAULT 'v1.0'
);

CREATE TABLE IF NOT EXISTS market_bars (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(16) NOT NULL,
    bar_time TIMESTAMPTZ NOT NULL,
    open NUMERIC(14, 4) NOT NULL,
    high NUMERIC(14, 4) NOT NULL,
    low NUMERIC(14, 4) NOT NULL,
    close NUMERIC(14, 4) NOT NULL,
    volume NUMERIC(16, 2) DEFAULT 0,
    source VARCHAR(64) DEFAULT 'YahooFinance',
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_market_bar UNIQUE (symbol, timeframe, bar_time)
);
CREATE INDEX IF NOT EXISTS idx_market_bars_sym_time ON market_bars (symbol, bar_time DESC);

CREATE TABLE IF NOT EXISTS macro_events (
    event_id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    country VARCHAR(8) NOT NULL DEFAULT 'US',
    publication_time TIMESTAMPTZ NOT NULL,
    observation_period VARCHAR(32),
    previous_value DOUBLE PRECISION,
    consensus_value DOUBLE PRECISION,
    actual_value DOUBLE PRECISION,
    surprise_absolute DOUBLE PRECISION,
    surprise_percentage DOUBLE PRECISION,
    surprise_zscore DOUBLE PRECISION,
    surprise_bucket VARCHAR(32),
    importance VARCHAR(16) DEFAULT 'high',
    source VARCHAR(64) DEFAULT 'BLS',
    source_url TEXT,
    vintage_mode VARCHAR(32) NOT NULL DEFAULT 'REAL_TIME_VINTAGE',
    initial_release DOUBLE PRECISION,
    revision DOUBLE PRECISION DEFAULT 0.0,
    revision_time TIMESTAMPTZ,
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_macro_events_type_pub ON macro_events (event_type, publication_time DESC);
CREATE INDEX IF NOT EXISTS idx_macro_events_zscore ON macro_events (event_type, surprise_zscore);

CREATE TABLE IF NOT EXISTS macro_observations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id VARCHAR(64) NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    publication_time TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    revision_number INT NOT NULL DEFAULT 0,
    source VARCHAR(64) DEFAULT 'FRED',
    is_imputed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_macro_obs UNIQUE (series_id, observation_time, revision_number)
);
CREATE INDEX IF NOT EXISTS idx_macro_obs_series_time ON macro_observations (series_id, observation_time DESC);

CREATE TABLE IF NOT EXISTS weekly_features (
    week_ending VARCHAR(16) PRIMARY KEY, -- YYYY-MM-DD
    prediction_timestamp TIMESTAMPTZ NOT NULL,
    gold_close DOUBLE PRECISION NOT NULL,
    gold_return_1w DOUBLE PRECISION,
    gold_return_4w DOUBLE PRECISION,
    gold_return_12w DOUBLE PRECISION,
    gold_ma_20w DOUBLE PRECISION,
    gold_ma_50w DOUBLE PRECISION,
    gold_trend INT DEFAULT 0, -- 1: bull, 0: side, -1: bear
    gold_volatility_20w DOUBLE PRECISION,
    dxy_close DOUBLE PRECISION,
    dxy_return_1w DOUBLE PRECISION,
    dxy_return_4w DOUBLE PRECISION,
    real_yield_10y DOUBLE PRECISION,
    delta_real_yield_1w DOUBLE PRECISION,
    delta_real_yield_4w DOUBLE PRECISION,
    nominal_treasury_10y DOUBLE PRECISION,
    breakeven_10y DOUBLE PRECISION,
    vix_close DOUBLE PRECISION,
    vix_change_1w DOUBLE PRECISION,
    sp500_close DOUBLE PRECISION,
    sp500_return_1w DOUBLE PRECISION,
    wti_close DOUBLE PRECISION,
    wti_return_1w DOUBLE PRECISION,
    silver_close DOUBLE PRECISION,
    silver_return_1w DOUBLE PRECISION,
    cot_net_speculative DOUBLE PRECISION,
    cot_percentile_3y DOUBLE PRECISION,
    etf_weekly_flow_usd_m DOUBLE PRECISION,
    etf_flow_percentile DOUBLE PRECISION,
    shock_real_yield_2sigma INT DEFAULT 0,
    shock_dxy_2sigma INT DEFAULT 0,
    shock_sp500_2sigma INT DEFAULT 0,
    shock_vix_2sigma INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_weekly_feats_pred_ts ON weekly_features (prediction_timestamp DESC);

CREATE TABLE IF NOT EXISTS weekly_targets (
    week_ending VARCHAR(16) PRIMARY KEY REFERENCES weekly_features(week_ending),
    next_week_gold_return DOUBLE PRECISION,
    next_week_direction INT, -- 1: up, -1: down, 0: flat
    target_p_up INT,
    target_p_plus_1pct INT,
    target_p_minus_1pct INT,
    next_week_gold_volatility DOUBLE PRECISION,
    next_week_max_favorable_excursion DOUBLE PRECISION,
    next_week_max_adverse_excursion DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regimes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    week_ending VARCHAR(16) NOT NULL REFERENCES weekly_features(week_ending),
    dimension VARCHAR(32) NOT NULL, -- 'real_yield', 'dxy', 'vix', 'gold_trend', 'positioning'
    regime_label VARCHAR(32) NOT NULL,
    threshold_low DOUBLE PRECISION,
    threshold_high DOUBLE PRECISION,
    lookback_window INT DEFAULT 750,
    calculation_method VARCHAR(64) DEFAULT 'expanding_percentile',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_week_regime UNIQUE (week_ending, dimension)
);
CREATE INDEX IF NOT EXISTS idx_regimes_dim_label ON regimes (dimension, regime_label);

CREATE TABLE IF NOT EXISTS research_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    git_commit VARCHAR(64) NOT NULL,
    dataset_version VARCHAR(32) NOT NULL,
    feature_version VARCHAR(32) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    results_summary JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'QUEUED', -- QUEUED, RUNNING, COMPLETED, FAILED
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs (status, created_at DESC);

CREATE TABLE IF NOT EXISTS model_results (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES research_runs(run_id) ON DELETE CASCADE,
    model_name VARCHAR(64) NOT NULL,
    target_name VARCHAR(64) NOT NULL,
    rmse DOUBLE PRECISION,
    mae DOUBLE PRECISION,
    directional_accuracy_pct DOUBLE PRECISION,
    balanced_accuracy_pct DOUBLE PRECISION,
    brier_score DOUBLE PRECISION,
    information_coefficient DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    calibration_error DOUBLE PRECISION,
    metrics_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_run_model_target UNIQUE (run_id, model_name, target_name)
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id VARCHAR(64) PRIMARY KEY REFERENCES research_runs(run_id) ON DELETE CASCADE,
    strategy_name VARCHAR(64) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    slippage_bps DOUBLE PRECISION DEFAULT 2.0,
    commission_bps DOUBLE PRECISION DEFAULT 1.5,
    initial_capital DOUBLE PRECISION DEFAULT 100000.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backtest_metrics (
    run_id VARCHAR(64) PRIMARY KEY REFERENCES backtest_runs(run_id) ON DELETE CASCADE,
    total_return_pct DOUBLE PRECISION,
    annualized_return_pct DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    calmar_ratio DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    turnover_annualized DOUBLE PRECISION,
    total_trades INT,
    trade_log JSONB DEFAULT '[]'::jsonb,
    equity_curve JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_checks (
    check_id VARCHAR(64) PRIMARY KEY,
    check_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    check_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL, -- PASS, WARNING, FAIL
    synthetic_values_count INT DEFAULT 0,
    violations_count INT DEFAULT 0,
    details JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_dq_checks_time ON data_quality_checks (check_timestamp DESC);
