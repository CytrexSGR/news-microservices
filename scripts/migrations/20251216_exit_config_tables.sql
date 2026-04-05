-- Migration: Exit Configuration Tables for ATR-based Dynamic SL/TP
-- Date: 2025-12-16
-- Purpose: Support flexible, database-driven exit parameters
-- Key Principle: NO HARDCODED VALUES - all parameters from database config

BEGIN;

-- ============================================================================
-- Part 1: Create Exit Configuration Tables
-- ============================================================================

-- Exit Configuration Table
-- Stores exit parameters per symbol/timeframe/regime combination
CREATE TABLE IF NOT EXISTS ml_lab_exit_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Scope (NULL = default for all)
    symbol VARCHAR(20),           -- e.g., 'XRPUSDT', NULL = global default
    timeframe VARCHAR(10),        -- e.g., '5min', NULL = all timeframes
    regime VARCHAR(20) NOT NULL,  -- 'trending', 'ranging', 'volatile', 'quiet'

    -- ATR-based Exit Parameters
    sl_atr_multiplier DECIMAL(5,2) NOT NULL,      -- Stop Loss ATR multiplier
    tp_atr_multiplier DECIMAL(5,2) NOT NULL,      -- Take Profit ATR multiplier
    min_rr_ratio DECIMAL(4,2) NOT NULL,           -- Minimum R/R for entry

    -- Trailing Stop Parameters
    trailing_activation_rr DECIMAL(4,2),          -- Activate at X:1 R/R
    trailing_distance_atr DECIMAL(4,2),           -- Trail distance in ATR

    -- Position Management
    max_position_hours INT,                       -- Max hold time
    leverage_cap DECIMAL(4,2),                    -- Max leverage for this config

    -- Partial Exit Levels (JSON array)
    partial_exits JSONB,  -- [{"rr": 2.0, "exit_pct": 0.33, "move_stop": "breakeven"}, ...]

    -- Meta
    is_active BOOLEAN DEFAULT TRUE,
    source VARCHAR(20) DEFAULT 'manual',          -- 'manual', 'ml_rl', 'ml_bayesian', 'ml_genetic', 'ml_backtest'
    source_details JSONB,                         -- ML run ID, parameters, etc.
    performance_score DECIMAL(8,4),               -- Tracked performance of this config

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient lookup
CREATE INDEX IF NOT EXISTS idx_exit_config_lookup
    ON ml_lab_exit_config(symbol, timeframe, regime, is_active);
CREATE INDEX IF NOT EXISTS idx_exit_config_source
    ON ml_lab_exit_config(source);
CREATE INDEX IF NOT EXISTS idx_exit_config_active
    ON ml_lab_exit_config(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- Part 2: Parameter Constraints Table
-- ============================================================================

-- Stores soft/hard limits for each parameter
-- All limits are editable via API and available for ML optimization
CREATE TABLE IF NOT EXISTS ml_lab_exit_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    parameter_name VARCHAR(50) NOT NULL UNIQUE,   -- 'sl_atr_multiplier', etc.

    -- Soft Limits (warnings only)
    soft_min DECIMAL(10,4),
    soft_max DECIMAL(10,4),

    -- Hard Limits (enforced)
    hard_min DECIMAL(10,4),
    hard_max DECIMAL(10,4),

    -- Default value for new configs
    default_value DECIMAL(10,4),

    -- Step size for optimization
    step_size DECIMAL(10,4),              -- e.g., 0.1 for ATR multipliers

    -- ML can optimize these constraints too
    is_constraint_optimizable BOOLEAN DEFAULT FALSE,

    -- Meta
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default constraints (all editable via API/frontend)
INSERT INTO ml_lab_exit_constraints
    (parameter_name, soft_min, soft_max, hard_min, hard_max, default_value, step_size, description)
VALUES
    ('sl_atr_multiplier',      1.0, 4.0,   0.5, 6.0,   2.0, 0.25, 'Stop Loss ATR multiplier'),
    ('tp_atr_multiplier',      1.0, 8.0,   0.5, 15.0,  4.0, 0.5,  'Take Profit ATR multiplier'),
    ('min_rr_ratio',           1.0, 4.0,   0.5, 6.0,   2.0, 0.25, 'Minimum Risk/Reward ratio'),
    ('trailing_activation_rr', 0.5, 2.0,   0.25, 3.0,  1.0, 0.25, 'R/R to activate trailing stop'),
    ('trailing_distance_atr',  0.5, 3.0,   0.25, 5.0,  1.5, 0.25, 'Trailing stop ATR distance'),
    ('max_position_hours',     1,   48,    0.5, 168,   24,  1,    'Maximum position hold time (hours)'),
    ('leverage_cap',           1.0, 5.0,   1.0, 10.0,  3.0, 0.5,  'Maximum leverage')
ON CONFLICT (parameter_name) DO NOTHING;

-- ============================================================================
-- Part 3: Configuration History Table (for ML learning)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_lab_exit_config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES ml_lab_exit_config(id),

    -- Snapshot of config at time of trade
    config_snapshot JSONB NOT NULL,

    -- Trade outcome
    trade_id UUID,
    symbol VARCHAR(20),
    pnl_pct DECIMAL(10,4),
    duration_minutes INT,
    exit_reason VARCHAR(50),

    -- For ML training
    features_at_entry JSONB,              -- Market conditions when trade opened

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_config_history_config
    ON ml_lab_exit_config_history(config_id);
CREATE INDEX IF NOT EXISTS idx_config_history_symbol
    ON ml_lab_exit_config_history(symbol);
CREATE INDEX IF NOT EXISTS idx_config_history_created
    ON ml_lab_exit_config_history(created_at);

-- ============================================================================
-- Part 4: Extend Paper Trades Table
-- ============================================================================

ALTER TABLE ml_lab_paper_trades
ADD COLUMN IF NOT EXISTS atr_at_entry DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS stop_loss_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS take_profit_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS regime_at_entry VARCHAR(20),
ADD COLUMN IF NOT EXISTS trailing_stop_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS trailing_activated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS exit_config_id UUID;

-- Add foreign key constraint (separate to handle existing data)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_paper_trades_exit_config'
    ) THEN
        ALTER TABLE ml_lab_paper_trades
        ADD CONSTRAINT fk_paper_trades_exit_config
        FOREIGN KEY (exit_config_id) REFERENCES ml_lab_exit_config(id);
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_paper_trades_regime
    ON ml_lab_paper_trades(regime_at_entry);
CREATE INDEX IF NOT EXISTS idx_paper_trades_exit_config
    ON ml_lab_paper_trades(exit_config_id);

-- ============================================================================
-- Part 5: Insert Default Global Configs (for each regime)
-- ============================================================================

-- These serve as fallback defaults, all editable via API/ML
INSERT INTO ml_lab_exit_config
    (symbol, timeframe, regime, sl_atr_multiplier, tp_atr_multiplier, min_rr_ratio,
     trailing_activation_rr, trailing_distance_atr, max_position_hours, leverage_cap, source)
VALUES
    -- Global defaults (NULL symbol/timeframe = applies to all)
    (NULL, NULL, 'trending', 1.5, 4.5, 3.0, 1.0, 1.5, 48, 3.0, 'initial_setup'),
    (NULL, NULL, 'ranging',  2.0, 3.0, 1.5, 0.5, 1.0, 24, 2.0, 'initial_setup'),
    (NULL, NULL, 'volatile', 3.0, 6.0, 2.0, 1.5, 2.0, 12, 2.0, 'initial_setup'),
    (NULL, NULL, 'quiet',    1.5, 3.0, 2.0, 1.0, 1.5, 24, 2.5, 'initial_setup')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Part 6: Backward Compatibility for Existing Positions
-- ============================================================================

UPDATE ml_lab_paper_trades
SET regime_at_entry = 'quiet',
    trailing_activated = FALSE
WHERE status = 'open'
  AND regime_at_entry IS NULL;

COMMIT;

-- ============================================================================
-- Verification Query (run after migration)
-- ============================================================================
-- SELECT 'ml_lab_exit_config' as table_name, count(*) FROM ml_lab_exit_config
-- UNION ALL
-- SELECT 'ml_lab_exit_constraints', count(*) FROM ml_lab_exit_constraints
-- UNION ALL
-- SELECT 'ml_lab_exit_config_history', count(*) FROM ml_lab_exit_config_history;
