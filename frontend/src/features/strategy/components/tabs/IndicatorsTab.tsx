/**
 * IndicatorsTab Component
 *
 * Displays live market indicators and strategy definition indicators
 * with real-time updates based on selected symbol and timeframe.
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Activity,
  TrendingUp,
  Clock,
  Target,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import type { Strategy, StrategyDefinition } from '../../types';
import { EditableField } from '../shared/EditableField';
import { useStrategyEditContext } from '../../context';
import type { Timeframe, IndicatorsSnapshot } from '@/types/indicators';
import { AVAILABLE_TIMEFRAMES, TIMEFRAME_LABELS } from '@/types/indicators';
import { BYBIT_SYMBOLS } from '@/constants/symbols';
import { formatPrice } from '@/features/trading/utils/formatters';
import type { IndicatorConfig } from '../../types';

// ============================================================================
// Sub-Component: IndicatorParameters
// ============================================================================

interface IndicatorParametersProps {
  indicator: IndicatorConfig;
  indicatorIndex: number;
}

function IndicatorParameters({ indicator, indicatorIndex }: IndicatorParametersProps) {
  // Try to use context if available (wrapped in provider), otherwise render static
  try {
    const { isEditMode, updateIndicatorParam, isPending } = useStrategyEditContext();

    if (!indicator.params || Object.keys(indicator.params).length === 0) {
      return null;
    }

    return (
      <div>
        <p className="text-sm font-medium mb-2">Parameters:</p>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(indicator.params).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}:</span>
              <EditableField
                value={value as number}
                type="number"
                canEdit={isEditMode && !isPending}
                showEditIndicator={isEditMode}
                onSave={(newValue) =>
                  updateIndicatorParam(indicatorIndex, key, newValue as number)
                }
                className="justify-end"
                inputClassName="w-20"
                min={1}
                max={500}
                step={1}
              />
            </div>
          ))}
        </div>
      </div>
    );
  } catch {
    // Fallback to static display if not wrapped in provider
    if (!indicator.params || Object.keys(indicator.params).length === 0) {
      return null;
    }

    return (
      <div>
        <p className="text-sm font-medium mb-2">Parameters:</p>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(indicator.params).map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm">
              <span className="text-muted-foreground">{key}:</span>
              <span className="font-mono">{String(value)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
}

// ============================================================================
// Main Component
// ============================================================================

interface IndicatorsTabProps {
  definition: StrategyDefinition;
  selectedSymbol: string;
  selectedTimeframe: Timeframe;
  onSymbolChange: (symbol: string) => void;
  onTimeframeChange: (timeframe: Timeframe) => void;
  indicators: IndicatorsSnapshot | null;
  isLoading: boolean;
  error: Error | null;
}

export function IndicatorsTab({
  definition,
  selectedSymbol,
  selectedTimeframe,
  onSymbolChange,
  onTimeframeChange,
  indicators,
  isLoading,
  error,
}: IndicatorsTabProps) {
  return (
    <div className="space-y-4">
      {/* Live Indicators Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Live Market Indicators
              </CardTitle>
              <CardDescription>
                Real-time technical indicators for {selectedSymbol.replace('USDT', '/USDT')}
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              {/* Symbol Selector */}
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <Select value={selectedSymbol} onValueChange={onSymbolChange}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Select symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    {BYBIT_SYMBOLS.map((s) => (
                      <SelectItem key={s.symbol} value={s.symbol}>
                        {s.base}/USDT - {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {/* Timeframe Selector */}
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <Select
                  value={selectedTimeframe}
                  onValueChange={(value) => onTimeframeChange(value as Timeframe)}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Select timeframe" />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_TIMEFRAMES.map((tf) => (
                      <SelectItem key={tf} value={tf}>
                        {TIMEFRAME_LABELS[tf]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Activity className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading indicators...
              </span>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                {error.message ||
                  'Failed to load indicators. Insufficient data for this timeframe.'}
              </AlertDescription>
            </Alert>
          )}

          {indicators && !isLoading && (
            <div className="space-y-6">
              {/* Market Regime Detection */}
              {indicators.regime && (
                <div className="p-4 bg-primary/5 border-l-4 border-primary rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Market Regime
                    </h4>
                    <Badge
                      variant={
                        indicators.regime === 'TREND'
                          ? 'default'
                          : indicators.regime === 'HIGH_VOLATILITY'
                          ? 'destructive'
                          : 'secondary'
                      }
                      className="text-sm px-3 py-1"
                    >
                      {indicators.regime.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {indicators.regime === 'TREND' &&
                      'Strong directional movement detected. Focus on trend-following indicators: ADX, EMA, Volume.'}
                    {indicators.regime === 'CONSOLIDATION' &&
                      'Sideways market movement. Focus on range indicators: BBW, RSI, ADX (low).'}
                    {indicators.regime === 'HIGH_VOLATILITY' &&
                      'High volatility detected. Use wider stops and focus on: ATR, Bollinger Bands, ADX.'}
                  </div>
                </div>
              )}

              {/* EMA Section */}
              {indicators.ema && (
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-sm">
                      Exponential Moving Averages (EMA)
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          indicators.ema.trend === 'BULLISH' ? 'default' : 'destructive'
                        }
                      >
                        {indicators.ema.trend}
                      </Badge>
                      <Badge variant="outline">
                        {indicators.ema.position} EMA200
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    {indicators.ema.ema10 && (
                      <div className="p-3 bg-background rounded border">
                        <p className="text-xs text-muted-foreground mb-1">EMA 10</p>
                        <p className="text-lg font-mono font-semibold">
                          ${indicators.ema.ema10.toFixed(2)}
                        </p>
                      </div>
                    )}
                    {indicators.ema.ema20 && (
                      <div className="p-3 bg-background rounded border">
                        <p className="text-xs text-muted-foreground mb-1">EMA 20</p>
                        <p className="text-lg font-mono font-semibold">
                          ${indicators.ema.ema20.toFixed(2)}
                        </p>
                      </div>
                    )}
                    {indicators.ema.ema50 && (
                      <div className="p-3 bg-background rounded border">
                        <p className="text-xs text-muted-foreground mb-1">EMA 50</p>
                        <p className="text-lg font-mono font-semibold">
                          ${indicators.ema.ema50.toFixed(2)}
                        </p>
                      </div>
                    )}
                    <div className="p-3 bg-background rounded border">
                      <p className="text-xs text-muted-foreground mb-1">EMA 200</p>
                      <p className="text-lg font-mono font-semibold">
                        ${indicators.ema.ema200.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  {/* Trend Hierarchy Score */}
                  {typeof indicators.ema.trend_hierarchy_score !== 'undefined' && (
                    <div className="p-3 bg-background rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium">Trend Hierarchy Score</p>
                        <Badge
                          variant={
                            indicators.ema.trend_hierarchy_score >= 3
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {indicators.ema.trend_hierarchy_score} / 4
                        </Badge>
                      </div>
                      <div className="space-y-1 text-xs text-muted-foreground">
                        <div className="flex items-center gap-2">
                          {indicators.ema.price_above_ema10 ? (
                            <CheckCircle2 className="h-3 w-3 text-green-600" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-600" />
                          )}
                          <span>
                            Price {indicators.ema.price_above_ema10 ? '>' : '<'} EMA10
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {indicators.ema.ema10_above_ema20 ? (
                            <CheckCircle2 className="h-3 w-3 text-green-600" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-600" />
                          )}
                          <span>
                            EMA10 {indicators.ema.ema10_above_ema20 ? '>' : '<'} EMA20
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {indicators.ema.ema20_above_ema50 ? (
                            <CheckCircle2 className="h-3 w-3 text-green-600" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-600" />
                          )}
                          <span>
                            EMA20 {indicators.ema.ema20_above_ema50 ? '>' : '<'} EMA50
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {indicators.ema.ema50_above_ema200 ? (
                            <CheckCircle2 className="h-3 w-3 text-green-600" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-600" />
                          )}
                          <span>
                            EMA50 {indicators.ema.ema50_above_ema200 ? '>' : '<'} EMA200
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-muted-foreground">
                          <strong>Current Price:</strong>{' '}
                          {formatPrice(indicators.ema.current_price)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Other Key Indicators */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* RSI */}
                {indicators.rsi && (
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <h4 className="font-semibold text-sm mb-3">RSI (Relative Strength)</h4>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl font-mono font-bold">
                        {indicators.rsi.value.toFixed(2)}
                      </span>
                      <Badge
                        variant={
                          indicators.rsi.signal === 'OVERSOLD'
                            ? 'default'
                            : indicators.rsi.signal === 'OVERBOUGHT'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {indicators.rsi.signal}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {indicators.rsi.interpretation}
                    </p>
                  </div>
                )}

                {/* MACD */}
                {indicators.macd && (
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <h4 className="font-semibold text-sm mb-3">MACD</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">MACD:</span>
                        <span className="font-mono">
                          {indicators.macd.macd.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Signal:</span>
                        <span className="font-mono">
                          {indicators.macd.signal.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Histogram:</span>
                        <span
                          className={`font-mono ${
                            indicators.macd.histogram >= 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {indicators.macd.histogram.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {indicators.macd.interpretation}
                    </p>
                  </div>
                )}

                {/* Volume */}
                {indicators.volume && (
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <h4 className="font-semibold text-sm mb-3">Volume Analysis</h4>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-muted-foreground">Ratio vs MA:</span>
                      <Badge
                        variant={
                          indicators.volume.signal === 'HIGH' ? 'default' : 'secondary'
                        }
                      >
                        {indicators.volume.ratio.toFixed(2)}x
                      </Badge>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Current:</span>
                        <span className="font-mono">
                          {indicators.volume.current_volume.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">MA:</span>
                        <span className="font-mono">
                          {indicators.volume.volume_ma.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <Badge variant="outline" className="mt-2">
                      {indicators.volume.signal}
                    </Badge>
                  </div>
                )}
              </div>

              {/* Timestamp */}
              <div className="text-xs text-muted-foreground text-center pt-2 border-t">
                Last updated: {new Date(indicators.timestamp).toLocaleString()} (
                {indicators.timeframe})
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Strategy Definition Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>
            Strategy Definition Indicators ({definition.indicators.length})
          </CardTitle>
          <CardDescription>
            Complete list of technical indicators configured in this strategy
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {definition.indicators.map((indicator, idx) => (
              <div
                key={idx}
                className="p-3 bg-muted/50 rounded-lg border space-y-2"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline" className="text-xs">
                    {indicator.timeframe}
                  </Badge>
                  <Badge className="text-xs">{indicator.type}</Badge>
                </div>
                <p className="font-mono text-sm font-medium truncate" title={indicator.id}>
                  {indicator.id}
                </p>
                {indicator.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {indicator.description}
                  </p>
                )}
                <IndicatorParameters indicator={indicator} indicatorIndex={idx} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
