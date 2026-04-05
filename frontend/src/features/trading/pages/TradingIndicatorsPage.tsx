/**
 * TradingIndicatorsPage
 *
 * Comprehensive technical indicators dashboard with 14 real-time indicators:
 * - Trend: RSI, MACD, EMA, ADX, Stochastic RSI
 * - Volatility: Bollinger Bands, ATR
 * - Volume: Volume, OBV, Volume Profile
 * - Market Structure: Fair Value Gaps, Liquidity Sweeps
 * - Derivatives: Funding Rate, Open Interest
 *
 * Features:
 * - 16 symbol selection (all Bybit perpetuals)
 * - 4-column grid layout
 * - Grouped by indicator type
 * - Auto-refresh every 60 seconds
 */

import { useState } from 'react'
import { useIndicators, useHistoricalIndicators } from '../hooks/useIndicators'
import { useOHLCV } from '../hooks/useMarketData'
import { TradingIndicatorCard } from '../components/TradingIndicatorCard'
import { BYBIT_SYMBOLS } from '@/constants/symbols'
import { predictionService } from '@/lib/api/prediction-service'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, TrendingUp, Activity, BarChart3, Boxes } from 'lucide-react'
import { format } from 'date-fns'

// Timeframe options for sparkline charts
const TIMEFRAMES = [
  { value: 1, label: '1h' },
  { value: 6, label: '6h' },
  { value: 12, label: '12h' },
  { value: 24, label: '24h' },
  { value: 168, label: '7d' },
] as const

export default function TradingIndicatorsPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState(24) // Default 24h
  const { data: indicators, isLoading, error } = useIndicators(selectedSymbol)
  const { data: historical } = useHistoricalIndicators(selectedSymbol, {
    // Pass hours parameter to hook
    queryKey: ['indicators', 'historical', selectedSymbol, selectedTimeframe],
    queryFn: () => predictionService.getHistoricalIndicators(selectedSymbol, selectedTimeframe),
  })

  // OHLCV data hook - synchronized with selectedTimeframe
  // Map hours to timeframe string and calculate candle limit
  const getOHLCVParams = (hours: number): { timeframe: '1h' | '4h' | '1d'; limit: number } => {
    // Always use 1h candles and show all hours in the period
    // This ensures: 1h=1, 6h=6, 12h=12, 24h=24, 7d=168 candles
    return { timeframe: '1h', limit: hours }
  }

  const ohlcvParams = getOHLCVParams(selectedTimeframe)
  const { data: ohlcv, isLoading: isLoadingOHLCV } = useOHLCV(
    selectedSymbol,
    ohlcvParams.timeframe,
    ohlcvParams.limit
  )

  // Map historical data to sparkline arrays
  const rsiSparkline = historical?.map(h => h.rsi) || []
  const macdSparkline = historical?.map(h => h.macd_histogram) || []
  const priceVsEmaSparkline = historical?.map(h => h.price_vs_ema200) || []
  const volumeSparkline = historical?.map(h => h.volume_ratio) || []
  const bbWidthSparkline = historical?.map(h => h.bb_width) || []
  const atrSparkline = historical?.map(h => h.atr_percentage) || []
  const adxSparkline = historical?.map(h => h.adx) || []
  const stochRsiSparkline = historical?.map(h => h.stoch_rsi_k) || []
  const obvSparkline = historical?.map(h => h.obv_normalized) || []

  // Market structure sparklines
  const fvgSparkline = historical?.map(h => h.fvg_bullish_count + h.fvg_bearish_count) || []
  const sweepSparkline = historical?.map(h => h.sweep_bullish_count + h.sweep_bearish_count) || []

  // Helper functions for formatting
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)

  const formatDecimal = (value: number, decimals: number = 2) =>
    value.toFixed(decimals)

  const formatPercent = (value: number) =>
    `${(value * 100).toFixed(2)}%`

  const formatMACDHistogram = (value: number) =>
    value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2)

  const formatLargeNumber = (value: number) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
    return formatCurrency(value)
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>Error loading indicators: {error.message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto space-y-4 p-4">
      {/* Header */}
      <div className="space-y-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Technical Indicators</h1>
          <p className="text-sm text-muted-foreground">
            Comprehensive technical analysis across 14 indicators
          </p>
        </div>

        {/* Symbol & Timeframe Selectors */}
        <div className="flex items-center gap-3 flex-wrap">
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Select symbol" />
            </SelectTrigger>
            <SelectContent>
              {BYBIT_SYMBOLS.map((s) => (
                <SelectItem key={s.symbol} value={s.symbol}>
                  {s.name} ({s.base}/USDT)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedTimeframe.toString()} onValueChange={(v) => setSelectedTimeframe(Number(v))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Timeframe" />
            </SelectTrigger>
            <SelectContent>
              {TIMEFRAMES.map((tf) => (
                <SelectItem key={tf.value} value={tf.value.toString()}>
                  {tf.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {indicators && (
            <div className="text-xs text-muted-foreground">
              {new Date(indicators.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Market Consensus & Current Price */}
        {indicators && (
          <Card>
            <CardContent className="py-3 px-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  {/* Current Price */}
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-muted-foreground">Price:</div>
                    <div className="text-lg font-bold">
                      {formatCurrency(indicators.ema.current_price)}
                    </div>
                  </div>
                  {/* Consensus */}
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-muted-foreground">Consensus:</div>
                    <div
                      className={`text-lg font-bold ${
                        indicators.consensus === 'BULLISH'
                          ? 'text-green-600'
                          : indicators.consensus === 'BEARISH'
                            ? 'text-red-600'
                            : 'text-gray-600'
                      }`}
                    >
                      {indicators.consensus}
                    </div>
                  </div>
                </div>
                {/* Confidence */}
                <div className="flex items-center gap-2">
                  <div className="text-xs text-muted-foreground">Confidence:</div>
                  <div className="text-lg font-semibold">
                    {formatPercent(indicators.confidence)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* OHLCV Data */}
        <Card>
          <CardHeader>
            <CardTitle>OHLCV Data ({ohlcvParams.timeframe})</CardTitle>
            {ohlcv && ohlcv.length > 0 && (
              <CardDescription>
                Last {ohlcv.length} candles ({format(new Date(ohlcv[0].timestamp), 'MMM dd, HH:mm')} - {format(new Date(ohlcv[ohlcv.length - 1].timestamp), 'MMM dd, HH:mm')}) • Bybit perpetual futures
              </CardDescription>
            )}
            {(!ohlcv || ohlcv.length === 0) && (
              <CardDescription>
                Last {ohlcvParams.limit} candles • Bybit perpetual futures
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {isLoadingOHLCV && (
              <div className="text-sm text-muted-foreground">Loading OHLCV data...</div>
            )}

            {ohlcv && ohlcv.length > 0 && (() => {
              // Aggregate OHLCV data across the entire period
              const periodOpen = ohlcv[0].open // First candle's open
              const periodHigh = Math.max(...ohlcv.map(c => c.high)) // Highest high
              const periodLow = Math.min(...ohlcv.map(c => c.low)) // Lowest low
              const periodClose = ohlcv[ohlcv.length - 1].close // Last candle's close
              const periodVolume = ohlcv.reduce((sum, c) => sum + c.volume, 0) // Total volume

              return (
                <div className="space-y-3">
                  {/* Period Aggregate */}
                  <div className="p-4 bg-muted rounded-lg space-y-2">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium">Period Summary</span>
                      <span className="text-xs text-muted-foreground">
                        {ohlcv.length} candle{ohlcv.length > 1 ? 's' : ''}
                      </span>
                    </div>
                    {/* OHLCV in one row */}
                    <div className="flex items-center gap-6 text-sm flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Open:</span>
                        <span className="font-medium">
                          ${periodOpen.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">High:</span>
                        <span className="font-medium">
                          ${periodHigh.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Low:</span>
                        <span className="font-medium">
                          ${periodLow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Close:</span>
                        <span className={`font-medium ${
                          periodClose >= periodOpen
                            ? 'text-green-500'
                            : 'text-red-500'
                        }`}>
                          ${periodClose.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Volume:</span>
                        <span className="font-medium">
                          {periodVolume.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}

            {ohlcv && ohlcv.length === 0 && (
              <div className="text-sm text-muted-foreground">No data available</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex h-[400px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Indicators Grid - 5 columns, 3 rows */}
      {indicators && (
        <div className="space-y-4">
          {/* Trend Indicators Section */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              <h2 className="text-sm font-semibold">Trend Indicators</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {/* RSI */}
              <TradingIndicatorCard
                title="RSI (14)"
                value={formatDecimal(indicators.rsi.value, 1)}
                status={indicators.rsi.signal}
                description={indicators.rsi.interpretation}
                sparklineData={rsiSparkline}
              />

              {/* MACD */}
              <TradingIndicatorCard
                title="MACD"
                value={formatMACDHistogram(indicators.macd.histogram)}
                status={indicators.macd.histogram > 0 ? 'BULLISH' : 'BEARISH'}
                description={indicators.macd.interpretation}
                sparklineData={macdSparkline}
              />

              {/* EMA200 */}
              <TradingIndicatorCard
                title="EMA200"
                value={formatCurrency(indicators.ema.ema200)}
                status={indicators.ema.trend}
                description={`Price is ${indicators.ema.position} the 200-period EMA`}
                sparklineData={priceVsEmaSparkline}
              />

              {/* ADX */}
              <TradingIndicatorCard
                title="ADX"
                value={formatDecimal(indicators.adx.adx, 1)}
                status={
                  indicators.adx.trend_strength === 'VERY_STRONG' || indicators.adx.trend_strength === 'STRONG'
                    ? 'BULLISH'
                    : 'NEUTRAL'
                }
                description={`${indicators.adx.trend_strength} ${indicators.adx.market_phase} market`}
                sparklineData={adxSparkline}
              />

              {/* Stochastic RSI */}
              <TradingIndicatorCard
                title="Stochastic RSI"
                value={`K: ${formatDecimal(indicators.stochastic_rsi.k, 1)}`}
                status={indicators.stochastic_rsi.signal}
                description={indicators.stochastic_rsi.interpretation}
                sparklineData={stochRsiSparkline}
              />
            </div>
          </div>

          {/* Volume & Volatility Section */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <h2 className="text-sm font-semibold">Volume & Volatility Indicators</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {/* Volume */}
              <TradingIndicatorCard
                title="Volume"
                value={`${formatDecimal(indicators.volume.ratio, 2)}x MA`}
                status={indicators.volume.signal}
                description={`Volume MA: ${formatDecimal(indicators.volume.volume_ma, 0)}`}
                sparklineData={volumeSparkline}
              />

              {/* OBV */}
              <TradingIndicatorCard
                title="OBV"
                value={formatDecimal(indicators.obv.value, 0)}
                status={
                  indicators.obv.trend === 'RISING'
                    ? 'BULLISH'
                    : indicators.obv.trend === 'FALLING'
                      ? 'BEARISH'
                      : 'NEUTRAL'
                }
                description={`Trend: ${indicators.obv.trend}${indicators.obv.divergence ? ` - ${indicators.obv.divergence}` : ''}`}
                sparklineData={obvSparkline}
              />

              {/* Volume Profile */}
              <TradingIndicatorCard
                title="Volume Profile"
                value={`POC: ${formatCurrency(indicators.volume_profile.poc)}`}
                status={indicators.volume_profile.signal}
                description={indicators.volume_profile.interpretation}
              />

              {/* Bollinger Bands */}
              <TradingIndicatorCard
                title="Bollinger Bands"
                value={`${formatCurrency(indicators.bollinger_bands.middle)}`}
                status={
                  indicators.bollinger_bands.position === 'ABOVE_UPPER'
                    ? 'OVERBOUGHT'
                    : indicators.bollinger_bands.position === 'BELOW_LOWER'
                      ? 'OVERSOLD'
                      : 'NEUTRAL'
                }
                description={indicators.bollinger_bands.interpretation}
                sparklineData={bbWidthSparkline}
              />

              {/* ATR */}
              <TradingIndicatorCard
                title="ATR"
                value={formatCurrency(indicators.atr.value)}
                status={
                  indicators.atr.volatility === 'HIGH'
                    ? 'OVERBOUGHT'
                    : indicators.atr.volatility === 'LOW'
                      ? 'OVERSOLD'
                      : 'NEUTRAL'
                }
                description={`${indicators.atr.volatility} volatility (${formatPercent(indicators.atr.percentage)})`}
                sparklineData={atrSparkline}
              />
            </div>
          </div>

          {/* Market Structure & Derivatives Section */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Boxes className="h-4 w-4" />
              <h2 className="text-sm font-semibold">Market Structure & Derivatives Metrics</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {/* Fair Value Gaps */}
              <TradingIndicatorCard
                title="Fair Value Gaps"
                value={`${indicators.fair_value_gaps.recent_unfilled_bullish} Bull / ${indicators.fair_value_gaps.recent_unfilled_bearish} Bear`}
                status={indicators.fair_value_gaps.signal}
                description={indicators.fair_value_gaps.interpretation}
                sparklineData={fvgSparkline}
              />

              {/* Liquidity Sweeps */}
              <TradingIndicatorCard
                title="Liquidity Sweeps"
                value={`${indicators.liquidity_sweeps.recent_bullish_sweeps} Bull / ${indicators.liquidity_sweeps.recent_bearish_sweeps} Bear`}
                status={indicators.liquidity_sweeps.signal}
                description={indicators.liquidity_sweeps.interpretation}
                sparklineData={sweepSparkline}
              />

              {/* Funding Rate */}
              <TradingIndicatorCard
                title="Funding Rate"
                value={formatPercent(indicators.funding_rate.rate_percent)}
                status={indicators.funding_rate.signal}
                description={indicators.funding_rate.sentiment}
              />

              {/* Open Interest */}
              <TradingIndicatorCard
                title="Open Interest"
                value={formatLargeNumber(indicators.open_interest.value_usd)}
                status={indicators.open_interest.signal}
                description={indicators.open_interest.interpretation}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
