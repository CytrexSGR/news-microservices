/**
 * Strategy Lab Type Definitions
 *
 * Comprehensive TypeScript types matching the backend Strategy Lab schema.
 * Backend models: services/prediction-service/app/models/strategy.py
 */

// ============================================================================
// Regime Types
// ============================================================================

export type RegimeType = 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'

export type RegimeDetectionProvider = 'threshold' | 'freqai' | 'hmm'

export interface RegimeDetectionConfig {
  provider: RegimeDetectionProvider
  config: Record<string, any>
}

// ============================================================================
// Direction Detection Types
// ============================================================================

/**
 * Configuration for automatic direction detection (BULLISH/BEARISH/NEUTRAL).
 *
 * Determines when to allow Long vs Short entries based on market conditions.
 * All parameters are ML-ready - can be optimized via hyperparameter tuning.
 *
 * Signal System:
 * - EMA Alignment: 3-EMA hierarchy (short > medium > long = BULLISH)
 * - RSI Position: Above/below midline indicates momentum direction
 * - HTF Trend: Higher timeframe confirmation for stronger signals
 *
 * Entry Filtering:
 * - BULLISH direction → Only Long entries allowed
 * - BEARISH direction → Only Short entries allowed
 * - NEUTRAL direction → Both directions allowed (with caution)
 */
export interface DirectionDetectionConfig {
  /** Enable automatic direction detection for entry filtering */
  enabled: boolean

  // EMA settings for trend direction (3-EMA system)
  /** Short-term EMA period (e.g., 20, 21, 12, 9). Range: 5-50 */
  ema_short_period: number
  /** Medium-term EMA period (e.g., 50, 55, 26). Range: 20-100 */
  ema_medium_period: number
  /** Long-term EMA period (e.g., 200, 100, 89). Range: 50-500 */
  ema_long_period: number

  // RSI settings for momentum confirmation
  /** RSI period for momentum detection. Range: 5-30 */
  rsi_period: number
  /** RSI threshold above which indicates bullish momentum. Range: 30-70 */
  rsi_bullish_threshold: number
  /** RSI threshold below which indicates bearish momentum. Range: 30-70 */
  rsi_bearish_threshold: number

  // Higher timeframe confirmation
  /** Higher timeframe for confirmation (e.g., "4h", "1d") */
  htf_timeframe: Timeframe
  /** Require HTF EMA alignment for direction confirmation */
  require_htf_confirmation: boolean

  // Signal agreement settings
  /** Minimum signals (out of 3: EMA, RSI, HTF) that must agree. Range: 1-3 */
  min_agreement: number
}

/**
 * Default direction detection configuration values
 */
export const DEFAULT_DIRECTION_CONFIG: DirectionDetectionConfig = {
  enabled: true,
  ema_short_period: 20,
  ema_medium_period: 50,
  ema_long_period: 200,
  rsi_period: 14,
  rsi_bullish_threshold: 50.0,
  rsi_bearish_threshold: 50.0,
  htf_timeframe: '4h',
  require_htf_confirmation: true,
  min_agreement: 2,
}

// ============================================================================
// Indicator Types
// ============================================================================

export type IndicatorType =
  | 'RSI'
  | 'EMA'
  | 'SMA'
  | 'MACD'
  | 'ATR'
  | 'BBANDS'
  | 'ADX'
  | 'BBW'
  | 'STOCH'
  | 'OBV'
  | 'VWAP'
  | 'AROON'
  | 'VOLUME_RATIO'

export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

export interface IndicatorDefinition {
  /** Unique identifier with timeframe prefix (e.g., "1h_RSI_14", "4h_EMA_200") */
  id: string
  type: IndicatorType
  timeframe: Timeframe
  params: Record<string, number | string>
}

// ============================================================================
// Formula Engine Types
// ============================================================================

export interface Condition {
  /** Human-readable condition name */
  name: string
  /** SymPy-compatible formula expression
   * Examples:
   * - "1h_RSI_14 < 30 AND 4h_EMA_50 > 4h_EMA_200"
   * - "CrossOver(1h_EMA_50, 1h_EMA_200)"
   * - "1d_EMA_50 > 1d_EMA_50.shift(1)"
   */
  expression: string
  /** Weight for weighted entry logic (0.0 - 1.0) */
  weight?: number
  /** Optional description for UI display */
  description?: string
}

export type EntryMode = 'all' | 'any' | 'weighted'

export interface EntryLogic {
  /** Entry mode: 'all' = all conditions must be true, 'any' = at least one, 'weighted' = confidence score */
  mode: EntryMode
  conditions: Condition[]
  /** Minimum confidence for weighted mode (0.0 - 1.0) */
  min_confidence?: number
}

export interface ExitLogic {
  conditions: Condition[]
  /** SymPy formula for stop loss (e.g., "entry_price - (2.0 * 1h_ATR_14)") */
  stop_loss?: string
  /** SymPy formula for take profit */
  take_profit?: string
  /** SymPy formula for trailing stop */
  trailing_stop?: string
}

export interface RegimeLogic {
  entry: EntryLogic
  exit: ExitLogic
}

// ============================================================================
// Risk Management Types
// ============================================================================

export interface RiskManagement {
  /** SymPy formula for position sizing (e.g., "account_balance * 0.01 / (entry_price - stop_loss)") */
  position_size_formula?: string
  /** Maximum position size as percentage of account (0.0 - 1.0) */
  max_position_size_pct?: number
  /** Maximum leverage allowed */
  max_leverage?: number
}

// ============================================================================
// Strategy Definition
// ============================================================================

export interface StrategyDefinition {
  name: string
  version: number
  description?: string
  /** Regime detection configuration */
  regimeDetection: RegimeDetectionConfig
  /**
   * Direction detection configuration (BULLISH/BEARISH/NEUTRAL filtering).
   * If not provided, defaults to enabled with standard 3-EMA settings.
   */
  directionDetection?: DirectionDetectionConfig
  /** Multi-timeframe indicator definitions */
  indicators: IndicatorDefinition[]
  /** Entry/exit logic per regime type */
  logic: Record<RegimeType, RegimeLogic>
  /** Risk management rules */
  riskManagement: RiskManagement
}

// ============================================================================
// Database Model
// ============================================================================

export interface Strategy {
  id: string
  user_id: string
  name: string
  version: number
  /** Complete strategy JSON definition */
  definition: StrategyDefinition
  is_public: boolean
  created_at: string
  updated_at: string
}

// ============================================================================
// Validation Types
// ============================================================================

export interface FormulaValidationError {
  expression: string
  error: string
}

export interface ValidationResult {
  success: boolean
  errors: FormulaValidationError[]
  warnings?: string[]
}

// ============================================================================
// Legacy Types (for backward compatibility)
// ============================================================================

/** @deprecated Use StrategyDefinition instead */
export type StrategyType = 'rsi' | 'bollinger' | 'ma_crossover' | 'vwap' | 'order_flow'

/** @deprecated Use IndicatorDefinition.params instead */
export type IndicatorParameter = {
  name: string
  type: 'int' | 'float' | 'string' | 'categorical'
  value: number | string
  min?: number
  max?: number
  options?: string[]
  description?: string
}

/** @deprecated Use StrategyDefinition instead */
export type StrategyConfig = {
  type: StrategyType
  parameters: Record<string, number | string>
}
