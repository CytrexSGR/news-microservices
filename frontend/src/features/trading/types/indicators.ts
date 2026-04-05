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
  ema200: number
  current_price: number
  position: 'ABOVE' | 'BELOW'
  trend: 'BULLISH' | 'BEARISH'
}

export interface VolumeIndicator {
  current_volume: number
  volume_ma: number
  ratio: number
  signal: 'HIGH' | 'NORMAL' | 'LOW'
}

export interface BollingerBandsIndicator {
  upper: number
  middle: number
  lower: number
  width: number
  position: 'ABOVE_UPPER' | 'IN_BAND' | 'BELOW_LOWER'
  interpretation: string
}

export interface ATRIndicator {
  value: number
  percentage: number
  volatility: 'LOW' | 'NORMAL' | 'HIGH'
  stop_loss_suggestion: number
}

export interface ADXIndicator {
  adx: number
  plus_di: number
  minus_di: number
  trend_strength: 'WEAK' | 'MODERATE' | 'STRONG' | 'VERY_STRONG'
  market_phase: 'RANGING' | 'TRENDING'
}

export interface StochasticRSIIndicator {
  k: number
  d: number
  signal: 'OVERSOLD' | 'NEUTRAL' | 'OVERBOUGHT'
  interpretation: string
}

export interface OBVIndicator {
  value: number
  trend: 'RISING' | 'FALLING' | 'FLAT'
  divergence: string | null
}

export interface FundingRateIndicator {
  rate: number
  rate_percent: number
  signal: 'BULLISH' | 'NEUTRAL' | 'BEARISH'
  sentiment: string
  next_funding_time: string
}

export interface OpenInterestIndicator {
  value: number
  value_usd: number
  trend: 'RISING' | 'FALLING' | 'FLAT'
  signal: 'STRONG_BULLISH' | 'BULLISH' | 'NEUTRAL' | 'BEARISH' | 'STRONG_BEARISH'
  interpretation: string
}

export interface FairValueGap {
  type: 'bullish' | 'bearish'
  upper: number
  lower: number
  timestamp: string
  candles_ago: number
  filled: boolean
}

export interface FairValueGapsIndicator {
  gaps: FairValueGap[]
  recent_unfilled_bullish: number
  recent_unfilled_bearish: number
  signal: 'BULLISH' | 'NEUTRAL' | 'BEARISH'
  interpretation: string
}

export interface LiquiditySweep {
  type: 'bullish' | 'bearish'
  sweep_level: number
  sweep_price: number
  reversal_close: number
  timestamp: string
  candles_ago: number
  strength: 'WEAK' | 'MODERATE' | 'STRONG'
}

export interface LiquiditySweepsIndicator {
  sweeps: LiquiditySweep[]
  recent_bullish_sweeps: number
  recent_bearish_sweeps: number
  signal: 'BULLISH' | 'NEUTRAL' | 'BEARISH'
  interpretation: string
}

export interface VolumeProfileIndicator {
  poc: number // Point of Control
  vah: number // Value Area High
  val: number // Value Area Low
  current_position: 'ABOVE_VAH' | 'IN_VALUE_AREA' | 'BELOW_VAL'
  signal: 'BULLISH' | 'NEUTRAL' | 'BEARISH'
  interpretation: string
  volume_nodes: number
}

export interface IndicatorsSnapshot {
  symbol: string
  timestamp: string
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator
  volume: VolumeIndicator
  bollinger_bands: BollingerBandsIndicator
  atr: ATRIndicator
  adx: ADXIndicator
  stochastic_rsi: StochasticRSIIndicator
  obv: OBVIndicator
  funding_rate: FundingRateIndicator
  open_interest: OpenInterestIndicator
  fair_value_gaps: FairValueGapsIndicator
  liquidity_sweeps: LiquiditySweepsIndicator
  volume_profile: VolumeProfileIndicator
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number // 0-1
}

export interface HistoricalIndicator {
  timestamp: string
  rsi: number
  macd_histogram: number
  price_vs_ema200: number // Price / EMA200 ratio
  volume_ratio: number // Volume / Volume MA ratio
  bb_width: number // Bollinger Bands width
  atr_percentage: number // ATR as percentage
  adx: number // ADX value
  stoch_rsi_k: number // Stochastic RSI %K
  obv_normalized: number // OBV normalized value
  fvg_bullish_count: number // Unfilled bullish Fair Value Gaps
  fvg_bearish_count: number // Unfilled bearish Fair Value Gaps
  sweep_bullish_count: number // Recent bullish Liquidity Sweeps
  sweep_bearish_count: number // Recent bearish Liquidity Sweeps
}
