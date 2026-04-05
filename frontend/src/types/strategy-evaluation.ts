/**
 * Strategy Evaluation Type Definitions
 *
 * Types for the strategy evaluation endpoint that provides real-time
 * entry/exit condition analysis for trading strategies.
 *
 * Backend endpoint: GET /api/v1/strategies/{id}/evaluate
 * Backend models: services/prediction-service/app/models/strategy.py
 */

// Re-export RegimeType from strategy types
export type { RegimeType } from './strategy'

// ============================================================================
// Direction Detection Types
// ============================================================================

/**
 * Market direction types for trade filtering
 * Determined by 3-EMA alignment, RSI position, and HTF confirmation
 */
export type DirectionType = 'BULLISH' | 'BEARISH' | 'NEUTRAL'

/**
 * Combined regime + direction states for strategy selection
 * Example: TREND regime + BULLISH direction = TREND_BULLISH state
 */
export type CombinedStateType =
  | 'TREND_BULLISH'
  | 'TREND_BEARISH'
  | 'CONSOLIDATION'
  | 'HIGH_VOL_BULLISH'
  | 'HIGH_VOL_BEARISH'
  | 'HIGH_VOL_NEUTRAL'
  | 'NEUTRAL'

/**
 * Direction detection signals breakdown
 * Each signal is True (bullish), False (bearish), or null (neutral/unavailable)
 */
export interface DirectionSignals {
  /** EMA alignment: short > medium > long = bullish */
  ema_alignment: boolean | null
  /** RSI position: above 50 = bullish, below 50 = bearish */
  rsi_position: boolean | null
  /** Higher timeframe trend: same 3-EMA logic on 4h */
  htf_trend: boolean | null
}

// ============================================================================
// Leverage Recommendation Types
// ============================================================================

/**
 * Dynamic leverage recommendation based on market conditions
 * Calculated using ADX (trend strength) and regime stability
 */
export interface RecommendedLeverage {
  /** Calculated leverage value (clamped between min and max) */
  value: number
  /** Minimum allowed leverage (from strategy config) */
  min: number
  /** Maximum allowed leverage (from strategy config) */
  max: number
  /** Formula used for calculation (e.g., "Min(3.0, Max(1.0, 3.0 * (1h_ADX_14 / 40)))") */
  formula: string
  /** Indicator values used in the calculation */
  inputs: Record<string, number>
  /** Confidence in the recommendation (0.0-1.0) */
  confidence: number
}

// ============================================================================
// Main Evaluation Response
// ============================================================================

/**
 * Complete strategy evaluation response
 * Contains current market state and per-regime entry/exit analysis
 */
export interface StrategyEvaluationResponse {
  /** Trading symbol (e.g., "BTC/USDT:USDT") */
  symbol: string
  /** Timeframe for evaluation (e.g., "1h", "4h") */
  timeframe: string
  /** Evaluation timestamp (ISO 8601) */
  timestamp: string
  /** Current market price */
  current_price: number
  /** Currently detected market regime */
  current_regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'
  /** Evaluation results per regime */
  regimes: Record<'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY', RegimeEvaluation>

  // Direction Detection fields
  /** Detected market direction (BULLISH/BEARISH/NEUTRAL) */
  current_direction: DirectionType
  /** Combined regime + direction state */
  combined_state: CombinedStateType
  /** Direction detection confidence (0.0-1.0) based on signal agreement */
  direction_confidence: number
  /** Individual direction signals breakdown */
  direction_signals: DirectionSignals | null
  /** Whether Long entries are allowed based on direction */
  long_allowed: boolean
  /** Whether Short entries are allowed based on direction */
  short_allowed: boolean
  /** Dynamic leverage recommendation based on market conditions */
  recommended_leverage?: RecommendedLeverage | null
}

// ============================================================================
// Trade Direction
// ============================================================================

/**
 * Trade direction for Futures trading
 */
export type TradeDirection = 'long' | 'short'

// ============================================================================
// Regime Evaluation
// ============================================================================

/**
 * Evaluation for a single market regime with Long/Short support for Futures trading
 */
export interface RegimeEvaluation {
  /** True if this is the currently active market regime */
  is_active: boolean

  /** Long entry logic evaluation (bullish conditions) */
  entry_long?: EntryEvaluation
  /** Short entry logic evaluation (bearish conditions) */
  entry_short?: EntryEvaluation
  /** Long exit logic evaluation (SL below entry, TP above) */
  exit_long?: ExitEvaluation
  /** Short exit logic evaluation (SL above entry, TP below) */
  exit_short?: ExitEvaluation

  /** @deprecated Use entry_long instead */
  entry?: EntryEvaluation
  /** @deprecated Use exit_long instead */
  exit?: ExitEvaluation
}

// ============================================================================
// Entry Evaluation
// ============================================================================

/**
 * Entry condition evaluation results
 */
export interface EntryEvaluation {
  /** Whether entry logic is enabled for this regime */
  enabled: boolean
  /** Individual condition evaluations */
  conditions: ConditionEvaluation[]
  /** How conditions are combined: 'all', 'any', or 'weighted_avg' */
  aggregation: 'all' | 'any' | 'weighted_avg'
  /** Minimum threshold for weighted_avg mode (0-1) */
  threshold: number
  /** Calculated score based on aggregation mode (0-1) */
  score: number
  /** Maximum possible score (typically 1.0) */
  max_score: number
  /** True if entry conditions are met and entry is possible */
  entry_possible: boolean
}

/**
 * Single condition evaluation result
 */
export interface ConditionEvaluation {
  /** SymPy expression (e.g., "CrossOver(1h_EMA_50, 1h_EMA_200)") */
  expression: string
  /** Human-readable description */
  description: string
  /** Confidence score (0.0 - 1.0) */
  confidence: number
  /** True if condition is currently satisfied */
  met: boolean
  /** Indicator values used in evaluation */
  indicator_values: Record<string, number>
  /** Error message if evaluation failed */
  error?: string
}

// ============================================================================
// Exit Evaluation
// ============================================================================

/**
 * Exit rules evaluation
 */
export interface ExitEvaluation {
  /** Configured exit rules */
  rules: ExitRuleEvaluation[]
  /** Hypothetical price levels if entering now */
  hypothetical_levels: HypotheticalLevels
}

/**
 * Single exit rule configuration
 */
export interface ExitRuleEvaluation {
  /** Type of exit rule */
  type: ExitRuleType
  /** Human-readable description */
  description: string
  /** Percentage value (e.g., 0.03 for 3% take profit) */
  value?: number
  /** Offset for trailing stop (e.g., 0.005 for 0.5%) */
  offset?: number
  /** Activation threshold for trailing stop (e.g., 0.01 for 1%) */
  activation?: number
  /** Threshold for indicator-based exits */
  threshold?: number
  /** Maximum bars for time-based exit */
  max_bars?: number
  /** Action to take (e.g., "exit_position", "reduce_50pct") */
  action?: string
}

/**
 * Exit rule types
 */
export type ExitRuleType =
  | 'take_profit'
  | 'trailing_stop'
  | 'regime_change'
  | 'time_based'
  | 'rsi_normalization'
  | 'bb_middle'
  | 'stop_loss'

/**
 * Hypothetical price levels if entering at current price
 */
export interface HypotheticalLevels {
  /** Stop loss price (absolute) */
  stop_loss: number
  /** Stop loss as percentage from entry */
  stop_loss_pct: number
  /** Take profit price (absolute) */
  take_profit: number
  /** Take profit as percentage from entry */
  take_profit_pct: number
  /** Price where trailing stop activates (absolute) */
  trailing_activation?: number
  /** Trailing activation as percentage from entry */
  trailing_activation_pct?: number
  /** Current ATR value used for calculations */
  atr_value: number
}

// ============================================================================
// Helper Types for UI Display
// ============================================================================

/**
 * Display-optimized condition state for UI components
 */
export interface ConditionDisplayState {
  expression: string
  description: string
  met: boolean
  confidence: number
  values: Array<{
    name: string
    value: number
    formatted: string
  }>
}

/**
 * Simplified condition status for visual indicators
 */
export type ConditionStatus = 'met' | 'unmet' | 'error'

/**
 * Get simplified status from condition evaluation
 */
export function getConditionStatus(condition: ConditionEvaluation): ConditionStatus {
  if (condition.error) return 'error'
  return condition.met ? 'met' : 'unmet'
}

/**
 * Convert condition to display state
 */
export function toConditionDisplayState(condition: ConditionEvaluation): ConditionDisplayState {
  return {
    expression: condition.expression,
    description: condition.description,
    met: condition.met,
    confidence: condition.confidence,
    values: Object.entries(condition.indicator_values).map(([name, value]) => ({
      name,
      value,
      formatted: typeof value === 'number' ? value.toFixed(2) : String(value),
    })),
  }
}

/**
 * Format percentage for display
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Format price for display
 */
export function formatPrice(price: number, decimals: number = 2): string {
  return price.toFixed(decimals)
}

// ============================================================================
// Aggregation Mode Display
// ============================================================================

export const AGGREGATION_MODE_LABELS: Record<EntryEvaluation['aggregation'], string> = {
  all: 'All Conditions (AND)',
  any: 'Any Condition (OR)',
  weighted_avg: 'Weighted Average',
}

export const AGGREGATION_MODE_DESCRIPTIONS: Record<EntryEvaluation['aggregation'], string> = {
  all: 'All conditions must be met for entry',
  any: 'At least one condition must be met for entry',
  weighted_avg: 'Conditions are weighted by confidence, must exceed threshold',
}

// ============================================================================
// Exit Rule Display
// ============================================================================

export const EXIT_RULE_LABELS: Record<ExitRuleType, string> = {
  take_profit: 'Take Profit',
  trailing_stop: 'Trailing Stop',
  regime_change: 'Regime Change',
  time_based: 'Time-Based Exit',
  rsi_normalization: 'RSI Normalization',
  bb_middle: 'Bollinger Band Middle',
  stop_loss: 'Stop Loss',
}

export const EXIT_RULE_DESCRIPTIONS: Record<ExitRuleType, string> = {
  take_profit: 'Exit when price reaches profit target',
  trailing_stop: 'Dynamic stop that trails price movement',
  regime_change: 'Exit when market regime changes',
  time_based: 'Exit after specified number of bars',
  rsi_normalization: 'Exit when RSI returns to normal range',
  bb_middle: 'Exit when price touches Bollinger Band middle',
  stop_loss: 'Exit when price hits stop loss level',
}

// ============================================================================
// Trade Direction Display
// ============================================================================

export const DIRECTION_LABELS: Record<TradeDirection, string> = {
  long: 'Long ↑',
  short: 'Short ↓',
}

export const DIRECTION_DESCRIPTIONS: Record<TradeDirection, string> = {
  long: 'Bullish position - profit when price goes up',
  short: 'Bearish position - profit when price goes down',
}

export const DIRECTION_COLORS: Record<TradeDirection, string> = {
  long: 'text-green-600 dark:text-green-400',
  short: 'text-red-600 dark:text-red-400',
}

export const DIRECTION_BG_COLORS: Record<TradeDirection, string> = {
  long: 'bg-green-100 dark:bg-green-900/30',
  short: 'bg-red-100 dark:bg-red-900/30',
}

export const DIRECTION_BORDER_COLORS: Record<TradeDirection, string> = {
  long: 'border-green-500',
  short: 'border-red-500',
}

/**
 * Get entry evaluation for a specific direction
 * Handles both new (entry_long/entry_short) and legacy (entry) formats
 */
export function getEntryEvaluation(regime: RegimeEvaluation, direction: TradeDirection): EntryEvaluation | undefined {
  if (direction === 'long') {
    return regime.entry_long ?? regime.entry
  }
  return regime.entry_short
}

/**
 * Get exit evaluation for a specific direction
 * Handles both new (exit_long/exit_short) and legacy (exit) formats
 */
export function getExitEvaluation(regime: RegimeEvaluation, direction: TradeDirection): ExitEvaluation | undefined {
  if (direction === 'long') {
    return regime.exit_long ?? regime.exit
  }
  return regime.exit_short
}

/**
 * Check if a direction is available for evaluation
 */
export function hasDirection(regime: RegimeEvaluation, direction: TradeDirection): boolean {
  return getEntryEvaluation(regime, direction) !== undefined
}

/**
 * Get all available directions for a regime
 */
export function getAvailableDirections(regime: RegimeEvaluation): TradeDirection[] {
  const directions: TradeDirection[] = []
  if (hasDirection(regime, 'long')) directions.push('long')
  if (hasDirection(regime, 'short')) directions.push('short')
  return directions
}

// ============================================================================
// Market Direction Display (Direction Detection)
// ============================================================================

/**
 * Labels for market direction types
 */
export const MARKET_DIRECTION_LABELS: Record<DirectionType, string> = {
  BULLISH: 'Bullish ↑',
  BEARISH: 'Bearish ↓',
  NEUTRAL: 'Neutral ↔',
}

/**
 * Descriptions for market direction types
 */
export const MARKET_DIRECTION_DESCRIPTIONS: Record<DirectionType, string> = {
  BULLISH: 'Market trending upward - Long entries allowed',
  BEARISH: 'Market trending downward - Short entries allowed',
  NEUTRAL: 'No clear direction - Both directions allowed with caution',
}

/**
 * Colors for market direction types
 */
export const MARKET_DIRECTION_COLORS: Record<DirectionType, string> = {
  BULLISH: 'text-green-600 dark:text-green-400',
  BEARISH: 'text-red-600 dark:text-red-400',
  NEUTRAL: 'text-yellow-600 dark:text-yellow-400',
}

/**
 * Background colors for market direction types
 */
export const MARKET_DIRECTION_BG_COLORS: Record<DirectionType, string> = {
  BULLISH: 'bg-green-100 dark:bg-green-900/30',
  BEARISH: 'bg-red-100 dark:bg-red-900/30',
  NEUTRAL: 'bg-yellow-100 dark:bg-yellow-900/30',
}

/**
 * Border colors for market direction types
 */
export const MARKET_DIRECTION_BORDER_COLORS: Record<DirectionType, string> = {
  BULLISH: 'border-green-500',
  BEARISH: 'border-red-500',
  NEUTRAL: 'border-yellow-500',
}

/**
 * Labels for combined state types
 */
export const COMBINED_STATE_LABELS: Record<CombinedStateType, string> = {
  TREND_BULLISH: 'Trend (Bullish)',
  TREND_BEARISH: 'Trend (Bearish)',
  CONSOLIDATION: 'Consolidation',
  HIGH_VOL_BULLISH: 'High Volatility (Bullish)',
  HIGH_VOL_BEARISH: 'High Volatility (Bearish)',
  HIGH_VOL_NEUTRAL: 'High Volatility (Neutral)',
  NEUTRAL: 'Neutral',
}

/**
 * Descriptions for combined state types
 */
export const COMBINED_STATE_DESCRIPTIONS: Record<CombinedStateType, string> = {
  TREND_BULLISH: 'Strong uptrend - Long entries only',
  TREND_BEARISH: 'Strong downtrend - Short entries only',
  CONSOLIDATION: 'Range-bound market - Both directions for mean reversion',
  HIGH_VOL_BULLISH: 'High volatility with bullish bias',
  HIGH_VOL_BEARISH: 'High volatility with bearish bias',
  HIGH_VOL_NEUTRAL: 'High volatility without clear direction',
  NEUTRAL: 'Unclear market state - Trade with caution',
}

/**
 * Labels for direction signals
 */
export const DIRECTION_SIGNAL_LABELS: Record<keyof DirectionSignals, string> = {
  ema_alignment: 'EMA Alignment',
  rsi_position: 'RSI Position',
  htf_trend: 'HTF Trend',
}

/**
 * Descriptions for direction signals
 */
export const DIRECTION_SIGNAL_DESCRIPTIONS: Record<keyof DirectionSignals, string> = {
  ema_alignment: '3-EMA hierarchy: short > medium > long = bullish',
  rsi_position: 'RSI above 50 = bullish momentum',
  htf_trend: 'Higher timeframe (4h) EMA alignment',
}

/**
 * Get signal status label
 */
export function getSignalStatusLabel(value: boolean | null): string {
  if (value === true) return '↑ Bullish'
  if (value === false) return '↓ Bearish'
  return '↔ Neutral'
}

/**
 * Get signal status color class
 */
export function getSignalStatusColor(value: boolean | null): string {
  if (value === true) return 'text-green-600 dark:text-green-400'
  if (value === false) return 'text-red-600 dark:text-red-400'
  return 'text-yellow-600 dark:text-yellow-400'
}

/**
 * Format direction confidence as percentage
 */
export function formatDirectionConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}

/**
 * Get confidence level label
 */
export function getConfidenceLevel(confidence: number): 'high' | 'medium' | 'low' {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.5) return 'medium'
  return 'low'
}

/**
 * Get confidence color class
 */
export function getConfidenceColor(confidence: number): string {
  const level = getConfidenceLevel(confidence)
  switch (level) {
    case 'high':
      return 'text-green-600 dark:text-green-400'
    case 'medium':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'low':
      return 'text-red-600 dark:text-red-400'
  }
}

// ============================================================================
// Leverage Display Helpers
// ============================================================================

/**
 * Format leverage value for display (e.g., "2.25x")
 */
export function formatLeverage(value: number): string {
  return `${value.toFixed(2)}x`
}

/**
 * Format leverage range for display (e.g., "1.0x - 3.0x")
 */
export function formatLeverageRange(min: number, max: number): string {
  return `${min.toFixed(1)}x - ${max.toFixed(1)}x`
}

/**
 * Get leverage level classification
 */
export function getLeverageLevel(value: number, max: number): 'low' | 'medium' | 'high' {
  const ratio = value / max
  if (ratio >= 0.75) return 'high'
  if (ratio >= 0.4) return 'medium'
  return 'low'
}

/**
 * Get leverage color class based on value relative to max
 */
export function getLeverageColor(value: number, max: number): string {
  const level = getLeverageLevel(value, max)
  switch (level) {
    case 'high':
      return 'text-red-600 dark:text-red-400'
    case 'medium':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'low':
      return 'text-green-600 dark:text-green-400'
  }
}

/**
 * Get leverage background color class
 */
export function getLeverageBgColor(value: number, max: number): string {
  const level = getLeverageLevel(value, max)
  switch (level) {
    case 'high':
      return 'bg-red-100 dark:bg-red-900/30'
    case 'medium':
      return 'bg-yellow-100 dark:bg-yellow-900/30'
    case 'low':
      return 'bg-green-100 dark:bg-green-900/30'
  }
}

/**
 * Calculate leverage percentage within range (0-100%)
 */
export function getLeveragePercentage(value: number, min: number, max: number): number {
  if (max === min) return 100
  return Math.round(((value - min) / (max - min)) * 100)
}

/**
 * Get leverage risk label
 */
export function getLeverageRiskLabel(value: number, max: number): string {
  const level = getLeverageLevel(value, max)
  switch (level) {
    case 'high':
      return 'High Risk'
    case 'medium':
      return 'Moderate Risk'
    case 'low':
      return 'Conservative'
  }
}
