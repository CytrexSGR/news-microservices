-- ============================================================================
-- Add Short Entry/Exit Conditions to Strategy
-- ============================================================================
-- This migration adds entry_short and exit_short conditions to all regimes
-- Based on: /home/cytrex/userdocs/crypto-lab/entry_exit/shot_entry_exit.md
--
-- Run with:
--   docker exec postgres psql -U news_user -d news_mcp -f /tmp/add_short_conditions_to_strategy.sql
-- ============================================================================

BEGIN;

-- Strategy ID
DO $$
DECLARE
    strategy_id UUID := '9675ccea-f520-4557-b54c-a98e1972cc1f';
BEGIN

-- ============================================================================
-- TREND Regime: Add entry_short (Trendfolge - Bärenmarkt)
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,TREND,entry_short}',
    '{
        "enabled": true,
        "threshold": 0.7,
        "aggregation": "weighted_avg",
        "description": "Trend-following SHORT entry - bearish momentum",
        "conditions": [
            {
                "expression": "CrossUnder(1h_EMA_50, 1h_EMA_200)",
                "confidence": 1.0,
                "description": "Death Cross - Strong bearish signal"
            },
            {
                "expression": "(1h_RSI_14 < 50) AND (1h_RSI_14 > 30)",
                "confidence": 0.8,
                "description": "RSI in bearish zone but not oversold"
            },
            {
                "expression": "4h_EMA_50 < 4h_EMA_200",
                "confidence": 0.9,
                "description": "Multi-timeframe bearish confirmation"
            },
            {
                "expression": "1d_EMA_50 < 1d_EMA_50.shift(1)",
                "confidence": 0.7,
                "description": "Daily trend is falling"
            },
            {
                "expression": "close < 1h_EMA_20",
                "confidence": 0.6,
                "description": "Price below short-term EMA"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- TREND Regime: Add exit_short
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,TREND,exit_short}',
    '{
        "rules": [
            {
                "type": "take_profit",
                "value": 0.03,
                "description": "3% profit target for SHORT trend trades"
            },
            {
                "type": "trailing_stop",
                "offset": 0.005,
                "activation": 0.01,
                "description": "Trailing stop activates at 1% profit, trails 0.5% above"
            },
            {
                "type": "regime_change",
                "action": "exit",
                "description": "Exit SHORT if regime changes from TREND"
            },
            {
                "type": "stop_loss",
                "formula": "entry_price + (2.5 * 1h_ATR_14)",
                "description": "Stop loss at 2.5x ATR above entry"
            }
        ],
        "conditions": [
            {
                "expression": "CrossOver(1h_EMA_50, 1h_EMA_200)",
                "description": "Golden Cross - trend reversal, exit SHORT"
            },
            {
                "expression": "1h_RSI_14 < 20",
                "description": "RSI deeply oversold - momentum exhausted"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- CONSOLIDATION Regime: Add entry_short (Mean Reversion)
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,CONSOLIDATION,entry_short}',
    '{
        "enabled": true,
        "threshold": 0.6,
        "aggregation": "weighted_avg",
        "description": "Mean reversion SHORT entry - overbought at range top",
        "conditions": [
            {
                "expression": "1h_RSI_14 > 70",
                "confidence": 1.0,
                "description": "RSI overbought (>70) - reversal likely"
            },
            {
                "expression": "close > 1h_BB_upper_20",
                "confidence": 0.9,
                "description": "Price at/above upper Bollinger Band"
            },
            {
                "expression": "1h_ADX_14 < 20",
                "confidence": 0.8,
                "description": "Low trend strength confirms ranging market"
            },
            {
                "expression": "1h_BBW_20 < 0.05",
                "confidence": 0.7,
                "description": "Tight Bollinger Bands - range-bound market"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- CONSOLIDATION Regime: Add exit_short
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,CONSOLIDATION,exit_short}',
    '{
        "rules": [
            {
                "type": "take_profit",
                "value": 0.015,
                "description": "1.5% profit target for mean reversion SHORT"
            },
            {
                "type": "bb_middle",
                "description": "Exit at middle Bollinger Band (mean reversion target)"
            },
            {
                "type": "regime_change",
                "action": "exit",
                "description": "Exit if regime changes from CONSOLIDATION"
            },
            {
                "type": "stop_loss",
                "formula": "entry_price + (1.5 * 1h_ATR_14)",
                "description": "Tighter stop for range trading (1.5x ATR)"
            },
            {
                "type": "time_based",
                "max_bars": 12,
                "description": "Exit after 12 bars if target not reached"
            }
        ],
        "conditions": [
            {
                "expression": "1h_RSI_14 < 50",
                "description": "RSI returned to neutral - target reached"
            },
            {
                "expression": "close < 1h_BB_middle_20",
                "description": "Price returned to middle Bollinger Band"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- HIGH_VOLATILITY Regime: Add entry_short (Vorsicht - Liquidity Sweep)
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,HIGH_VOLATILITY,entry_short}',
    '{
        "enabled": true,
        "threshold": 0.8,
        "aggregation": "weighted_avg",
        "description": "High volatility SHORT entry - liquidity sweep reversal",
        "conditions": [
            {
                "expression": "(1h_RSI_14 > 75) AND (1h_RSI_14.shift(1) > 70)",
                "confidence": 1.0,
                "description": "Extended overbought condition"
            },
            {
                "expression": "close < open AND close < 1h_EMA_20",
                "confidence": 0.9,
                "description": "Bearish candle below short EMA"
            },
            {
                "expression": "1h_ATR_14 > 1h_ATR_SMA_20 * 1.5",
                "confidence": 0.8,
                "description": "ATR confirms high volatility (1.5x average)"
            },
            {
                "expression": "(high - close) > (close - low) * 2",
                "confidence": 0.7,
                "description": "Upper wick dominance - rejection"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- HIGH_VOLATILITY Regime: Add exit_short
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{logic,HIGH_VOLATILITY,exit_short}',
    '{
        "rules": [
            {
                "type": "take_profit",
                "value": 0.02,
                "description": "Quick 2% profit in volatile markets"
            },
            {
                "type": "trailing_stop",
                "offset": 0.01,
                "activation": 0.015,
                "description": "Aggressive trailing at 1.5% profit, 1% trail"
            },
            {
                "type": "regime_change",
                "action": "exit",
                "description": "Exit if volatility normalizes"
            },
            {
                "type": "stop_loss",
                "formula": "entry_price + (3.0 * 1h_ATR_14)",
                "description": "Wider stops for volatility (3x ATR)"
            },
            {
                "type": "time_based",
                "max_bars": 6,
                "description": "Quick exit - max 6 bars in high vol"
            }
        ],
        "conditions": [
            {
                "expression": "1h_RSI_14 < 40",
                "description": "RSI dropped significantly"
            }
        ]
    }'::jsonb
)
WHERE id = strategy_id;

-- ============================================================================
-- Add Bollinger Band indicators if not present
-- ============================================================================
UPDATE predictions.strategies
SET definition = jsonb_set(
    definition,
    '{indicators}',
    (
        SELECT jsonb_agg(ind)
        FROM (
            -- Keep existing indicators
            SELECT jsonb_array_elements(definition->'indicators') as ind
            FROM predictions.strategies WHERE id = strategy_id
            UNION ALL
            -- Add BB upper if not exists
            SELECT '{"id": "1h_BB_upper_20", "type": "BBANDS", "timeframe": "1h", "params": {"period": 20, "band": "upper", "std": 2.0}, "description": "Upper Bollinger Band for resistance"}'::jsonb
            WHERE NOT EXISTS (
                SELECT 1 FROM predictions.strategies s,
                jsonb_array_elements(s.definition->'indicators') as elem
                WHERE s.id = strategy_id AND elem->>'id' = '1h_BB_upper_20'
            )
            UNION ALL
            -- Add BB middle if not exists
            SELECT '{"id": "1h_BB_middle_20", "type": "BBANDS", "timeframe": "1h", "params": {"period": 20, "band": "middle"}, "description": "Middle Bollinger Band (SMA)"}'::jsonb
            WHERE NOT EXISTS (
                SELECT 1 FROM predictions.strategies s,
                jsonb_array_elements(s.definition->'indicators') as elem
                WHERE s.id = strategy_id AND elem->>'id' = '1h_BB_middle_20'
            )
            UNION ALL
            -- Add BB lower if not exists
            SELECT '{"id": "1h_BB_lower_20", "type": "BBANDS", "timeframe": "1h", "params": {"period": 20, "band": "lower", "std": 2.0}, "description": "Lower Bollinger Band for support"}'::jsonb
            WHERE NOT EXISTS (
                SELECT 1 FROM predictions.strategies s,
                jsonb_array_elements(s.definition->'indicators') as elem
                WHERE s.id = strategy_id AND elem->>'id' = '1h_BB_lower_20'
            )
            UNION ALL
            -- Add ATR SMA for volatility comparison if not exists
            SELECT '{"id": "1h_ATR_SMA_20", "type": "SMA", "timeframe": "1h", "params": {"period": 20, "source": "1h_ATR_14"}, "description": "20-period SMA of ATR for volatility baseline"}'::jsonb
            WHERE NOT EXISTS (
                SELECT 1 FROM predictions.strategies s,
                jsonb_array_elements(s.definition->'indicators') as elem
                WHERE s.id = strategy_id AND elem->>'id' = '1h_ATR_SMA_20'
            )
        ) as combined
    )
)
WHERE id = strategy_id;

-- ============================================================================
-- Update version
-- ============================================================================
UPDATE predictions.strategies
SET
    definition = jsonb_set(definition, '{version}', '"1.1.0"'),
    updated_at = NOW()
WHERE id = strategy_id;

RAISE NOTICE 'Successfully added Short Entry/Exit conditions to strategy %', strategy_id;

END $$;

COMMIT;

-- Verify the update
SELECT
    name,
    definition->>'version' as version,
    jsonb_array_length(definition->'indicators') as indicator_count,
    (definition->'logic'->'TREND'->>'entry_short' IS NOT NULL) as has_trend_entry_short,
    (definition->'logic'->'CONSOLIDATION'->>'entry_short' IS NOT NULL) as has_consol_entry_short,
    (definition->'logic'->'HIGH_VOLATILITY'->>'entry_short' IS NOT NULL) as has_highvol_entry_short
FROM predictions.strategies
WHERE id = '9675ccea-f520-4557-b54c-a98e1972cc1f';
