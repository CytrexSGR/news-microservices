-- Migration: ML Lab Backtest Tables
-- Date: 2025-12-18
-- Purpose: Create tables for persisting backtest runs and their trades
-- Author: Claude Code
--
-- Tables created:
--   1. ml_lab_backtests - Backtest run metadata and final metrics
--   2. ml_lab_backtest_trades - Individual trades within each backtest
--
-- Usage: Run this migration on the predictions database
--   psql -U prediction -d predictions -f 20251218_backtest_tables.sql

BEGIN;

-- ============================================================================
-- Part 1: Backtest Runs Table
-- ============================================================================
-- Stores metadata and final metrics for each backtest run

CREATE TABLE IF NOT EXISTS ml_lab_backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Configuration
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    initial_capital DECIMAL(18, 2) NOT NULL DEFAULT 10000.00,
    position_size_pct DECIMAL(5, 2) DEFAULT 10.0,
    stop_loss_pct DECIMAL(5, 2),
    take_profit_pct DECIMAL(5, 2),
    use_ml_gates BOOLEAN DEFAULT TRUE,

    -- Date range
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,

    -- Execution info
    status VARCHAR(20) NOT NULL DEFAULT 'running',  -- running, completed, failed
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,

    -- Progress tracking
    candles_processed INTEGER DEFAULT 0,
    total_candles INTEGER DEFAULT 0,
    progress_pct DECIMAL(5, 2) DEFAULT 0.0,

    -- Final metrics (populated on completion)
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate_pct DECIMAL(6, 2),
    total_pnl_pct DECIMAL(10, 4),
    total_pnl_usd DECIMAL(18, 2),
    final_equity DECIMAL(18, 2),
    max_drawdown_pct DECIMAL(8, 4),
    max_drawdown_usd DECIMAL(18, 2),
    sharpe_ratio DECIMAL(8, 4),
    sortino_ratio DECIMAL(8, 4),
    profit_factor DECIMAL(8, 4),
    avg_trade_pnl_pct DECIMAL(8, 4),
    avg_winning_trade_pct DECIMAL(8, 4),
    avg_losing_trade_pct DECIMAL(8, 4),
    max_consecutive_wins INTEGER DEFAULT 0,
    max_consecutive_losses INTEGER DEFAULT 0,
    backtest_duration_seconds DECIMAL(12, 2),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_backtests_symbol ON ml_lab_backtests(symbol);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON ml_lab_backtests(status);
CREATE INDEX IF NOT EXISTS idx_backtests_created ON ml_lab_backtests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtests_symbol_timeframe ON ml_lab_backtests(symbol, timeframe);

-- ============================================================================
-- Part 2: Backtest Trades Table
-- ============================================================================
-- Stores individual trades from each backtest run

CREATE TABLE IF NOT EXISTS ml_lab_backtest_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID NOT NULL REFERENCES ml_lab_backtests(id) ON DELETE CASCADE,

    -- Trade details
    side VARCHAR(10) NOT NULL,  -- long, short
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    entry_price DECIMAL(18, 8) NOT NULL,
    exit_price DECIMAL(18, 8),

    -- P&L
    pnl_pct DECIMAL(10, 4),
    pnl_usd DECIMAL(18, 2),

    -- Exit info
    exit_reason VARCHAR(30),  -- stop_loss, take_profit, trailing_stop, signal, end_of_data

    -- ML Gate predictions (if applicable)
    gate_predictions JSONB,

    -- Order in backtest
    trade_number INTEGER NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_backtest_trades_backtest_id ON ml_lab_backtest_trades(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_side ON ml_lab_backtest_trades(side);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_exit_reason ON ml_lab_backtest_trades(exit_reason);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_entry_time ON ml_lab_backtest_trades(entry_time);

-- ============================================================================
-- Part 3: Equity Curve Storage (optional, for chart visualization)
-- ============================================================================
-- Stores periodic equity snapshots for equity curve visualization

CREATE TABLE IF NOT EXISTS ml_lab_backtest_equity (
    id SERIAL PRIMARY KEY,
    backtest_id UUID NOT NULL REFERENCES ml_lab_backtests(id) ON DELETE CASCADE,

    timestamp TIMESTAMPTZ NOT NULL,
    equity DECIMAL(18, 2) NOT NULL,
    drawdown_pct DECIMAL(8, 4) DEFAULT 0,

    -- Position state at this point
    position_side VARCHAR(10),  -- NULL, long, short
    unrealized_pnl DECIMAL(18, 2) DEFAULT 0
);

-- Index for fetching equity curve
CREATE INDEX IF NOT EXISTS idx_backtest_equity_backtest_timestamp
    ON ml_lab_backtest_equity(backtest_id, timestamp);

-- ============================================================================
-- Part 4: Auto-update trigger for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_backtest_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_backtest_updated_at ON ml_lab_backtests;
CREATE TRIGGER trigger_backtest_updated_at
    BEFORE UPDATE ON ml_lab_backtests
    FOR EACH ROW
    EXECUTE FUNCTION update_backtest_updated_at();

COMMIT;

-- ============================================================================
-- Verification Query (run after migration)
-- ============================================================================
-- SELECT 'ml_lab_backtests' as table_name, count(*) FROM ml_lab_backtests
-- UNION ALL
-- SELECT 'ml_lab_backtest_trades', count(*) FROM ml_lab_backtest_trades
-- UNION ALL
-- SELECT 'ml_lab_backtest_equity', count(*) FROM ml_lab_backtest_equity;
