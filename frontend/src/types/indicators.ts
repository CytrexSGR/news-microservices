/**
 * Technical Indicators Type Definitions
 * Based on Prediction Service API responses
 */

export interface RSIIndicator {
  value: number // 0-100
  signal: 'OVERSOLD' | 'NEUTRAL' | 'OVERBOUGHT'
  interpretation: string
}

export interface MACDIndicator {
  macd: number
  signal: number
  histogram: number
  interpretation: string
}

export interface EMAIndicator {
  // Multi-period EMAs (NEW - Phase 1)
  ema10?: number
  ema20?: number
  ema50?: number
  ema200: number // Required for backwards compatibility

  // Current price context
  current_price: number
  position: 'ABOVE' | 'BELOW' // Position relative to EMA200
  trend: 'BULLISH' | 'BEARISH'

  // Trend hierarchy analysis (NEW - Phase 1)
  price_above_ema10?: boolean
  ema10_above_ema20?: boolean
  ema20_above_ema50?: boolean
  ema50_above_ema200?: boolean
  trend_hierarchy_score?: number // 0-4 (how many EMAs in correct bullish order)
}

export interface VolumeIndicator {
  current_volume: number
  volume_ma: number
  ratio: number
  signal: 'HIGH' | 'NORMAL' | 'LOW'
}

// ============================================
// Additional Indicator Interfaces
// ============================================

export interface ADXIndicator {
  adx: number // 0-100
  plus_di: number // +DI (Directional Indicator)
  minus_di: number // -DI (Directional Indicator)
  trend_strength: 'WEAK' | 'MODERATE' | 'STRONG' | 'VERY_STRONG'
  market_phase: 'TRENDING' | 'CONSOLIDATION'
}

export interface ATRIndicator {
  atr: number
  percentage: number // ATR as % of price
  volatility_level: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface BollingerBandsIndicator {
  upper: number
  middle: number
  lower: number
  width: number // Band width (volatility measure - BBW)
  position: 'ABOVE_UPPER' | 'BETWEEN' | 'BELOW_LOWER'
  interpretation: string
}

export interface StochasticRSIIndicator {
  k: number // 0-100
  d: number // 0-100
  signal: 'OVERSOLD' | 'NEUTRAL' | 'OVERBOUGHT'
}

export interface OBVIndicator {
  obv: number
  trend: 'RISING' | 'FALLING' | 'FLAT'
}

export interface VolumeProfileIndicator {
  poc: number // Point of Control
  vah: number // Value Area High
  val: number // Value Area Low
  profile_type: 'BALANCED' | 'P_SHAPED' | 'B_SHAPED'
}

export interface FairValueGapIndicator {
  gaps: Array<{
    start_price: number
    end_price: number
    type: 'BULLISH' | 'BEARISH'
    filled: boolean
  }>
  active_count: number
}

export interface LiquiditySweepsIndicator {
  sweeps: Array<{
    timestamp: string
    price: number
    type: 'HIGH' | 'LOW'
  }>
  recent_count: number
}

export interface FundingRateIndicator {
  current_rate: number // % per 8h
  predicted_rate: number
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
}

export interface OpenInterestIndicator {
  current_oi: number
  oi_change_24h: number // %
  oi_trend: 'RISING' | 'FALLING' | 'STABLE'
}

// ============================================
// Regime Detection Detail Interfaces
// ============================================

export interface DirectionalIndicator {
  plus_di: number
  minus_di: number
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
}

export interface VolumeThresholdIndicator {
  current_volume: number
  avg_volume_10: number
  threshold_2x: number
  above_threshold: boolean
  ratio: number
}

export interface ATRThresholdIndicator {
  current_atr: number
  avg_atr_20: number
  above_average: boolean
  atr_percentile: number
}

export interface EMAHierarchyIndicator {
  ema_10?: number
  ema_20?: number
  ema_50?: number
  ema_200?: number
  hierarchy_valid: boolean
  trend: 'BULLISH' | 'BEARISH' | 'MIXED'
}

// TREND Regime Detection Types
export interface RegimeConditions {
  adx: boolean // ADX > 25
  di_direction: boolean
  ema_hierarchy: boolean
  volume: boolean
  atr: boolean
  bbw: boolean // BBW <= 5%
}

export interface RegimeIndicatorValues {
  adx: number
  bbw: number
  di_direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  plus_di: number
  minus_di: number
  ema_hierarchy_valid: boolean
  volume_above_threshold: boolean
  volume_ratio: number
  atr_above_average: boolean
  atr_percentile: number
}

// CONSOLIDATION Regime Detection Types
export interface ConsolidationConditions {
  adx: boolean // ADX <= 20
  rsi_neutral: boolean // RSI 40-60
  ema_convergence: boolean // EMAs tight & flat
  price_range: boolean // < 5% range width
  volume_low: boolean // < 70% average
  atr_low: boolean // Bottom 30th percentile
  bbw_squeeze: boolean // BBW contraction
}

export interface ConsolidationIndicatorValues {
  rsi: number
  rsi_in_neutral_zone: boolean
  rsi_oscillation_score: number
  ema_converged: boolean
  ema_spread_pct: number
  ema_slope_pct: number
  range_width_pct: number
  range_containment_score: number
  is_tight_range: boolean
  volume_ratio: number
  is_low_volume: boolean
  atr_percentile: number
  is_low_atr: boolean
  bbw_percentile: number
  is_squeeze: boolean
}

export interface ConsolidationDetails {
  conditions_met: number
  conditions_total: number // Always 7
  conditions: ConsolidationConditions
  indicator_values: ConsolidationIndicatorValues
}

// HIGH_VOLATILITY Regime Detection Types
export interface HighVolatilityConditions {
  atr_high: boolean // ATR >= 80th percentile
  bbw_high: boolean // BBW > threshold
  adx_context: 'directional' | 'chaotic' | 'mixed' // Volatility type based on ADX
}

export interface HighVolatilityIndicatorValues {
  atr: number
  atr_percentile: number
  atr_pct: number // ATR as % of price
  bbw: number
  bbw_threshold: number
  adx: number
  volatility_type: 'directional' | 'chaotic' | 'mixed'
}

export interface HighVolatilityDetails {
  conditions_met: number
  conditions_total: number // Always 2 (ATR + BBW; ADX is context only)
  conditions: HighVolatilityConditions
  indicator_values: HighVolatilityIndicatorValues
}

// Combined Regime Details (TREND with optional CONSOLIDATION and HIGH_VOLATILITY)
export interface RegimeDetails {
  confidence: number
  conditions_met: number // For primary regime (TREND)
  conditions_total: number // For primary regime (TREND)
  conditions: RegimeConditions // TREND conditions
  indicator_values: RegimeIndicatorValues // TREND indicators
  consolidation?: ConsolidationDetails | null // CONSOLIDATION-specific details (if calculated)
  high_volatility?: HighVolatilityDetails | null // HIGH_VOLATILITY-specific details (if calculated)
}

// ============================================
// Complete Indicators Snapshot
// ============================================

export interface IndicatorsSnapshot {
  symbol: string
  timeframe: Timeframe // NEW - Phase 2
  timestamp: string

  // All 14 indicators
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator // Extended with multi-period support
  adx: ADXIndicator
  atr: ATRIndicator
  bollinger_bands: BollingerBandsIndicator
  stochastic_rsi: StochasticRSIIndicator
  obv: OBVIndicator
  volume: VolumeIndicator
  volume_profile: VolumeProfileIndicator
  fvg: FairValueGapIndicator
  liquidity_sweeps: LiquiditySweepsIndicator
  funding_rate: FundingRateIndicator
  open_interest: OpenInterestIndicator

  // Regime Detection (NEW - Phase 3)
  regime?: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'
  regime_confidence?: number // 0-1
  regime_details?: RegimeDetails | null // Comprehensive regime breakdown (optional)

  // Legacy fields (keep for backwards compatibility)
  consensus?: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence?: number // 0-1
}

// ============================================
// Timeframe Types (NEW - Phase 2)
// ============================================

export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

export const AVAILABLE_TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']

export const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '1m': '1 Minute',
  '5m': '5 Minutes',
  '15m': '15 Minutes',
  '30m': '30 Minutes',
  '1h': '1 Hour',
  '4h': '4 Hours',
  '1d': '1 Day',
  '1w': '1 Week',
  '1M': '1 Month',
}

export const TIMEFRAME_DURATIONS_MS: Record<Timeframe, number> = {
  '1m': 1 * 60 * 1000,
  '5m': 5 * 60 * 1000,
  '15m': 15 * 60 * 1000,
  '30m': 30 * 60 * 1000,
  '1h': 60 * 60 * 1000,
  '4h': 4 * 60 * 60 * 1000,
  '1d': 24 * 60 * 60 * 1000,
  '1w': 7 * 24 * 60 * 60 * 1000,
  '1M': 30 * 24 * 60 * 60 * 1000,
}

export interface HistoricalIndicator {
  timestamp: string
  rsi: number
  macd_histogram: number
  price_vs_ema200: number // Price / EMA200 ratio
  volume_ratio: number // Volume / Volume MA ratio
}
