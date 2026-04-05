/**
 * ML Lab Live Indicators Panel
 *
 * Displays all technical indicators in a structured, real-time view
 * with their current values, trigger thresholds, and signals.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Gauge,
  RefreshCw,
  Loader2,
  ArrowUp,
  ArrowDown,
  Minus,
  Zap,
  Target,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

import { liveTradingApi, type LiveIndicatorsResponse, type IndicatorValue } from '../../api/mlLabApi';
import { SYMBOLS, TIMEFRAMES } from '../../utils/constants';

// Signal color mapping
const getSignalColor = (signal?: string): string => {
  if (!signal) return 'text-muted-foreground';
  const colors: Record<string, string> = {
    bullish: 'text-green-500',
    bearish: 'text-red-500',
    neutral: 'text-yellow-500',
    oversold: 'text-green-500',
    overbought: 'text-red-500',
    strong_trend: 'text-blue-500',
    weak_trend: 'text-gray-500',
    squeeze: 'text-purple-500',
    expanded: 'text-orange-500',
    normal: 'text-muted-foreground',
    spike: 'text-red-500',
    high: 'text-orange-500',
    low: 'text-green-500',
  };
  return colors[signal] || 'text-muted-foreground';
};

const getSignalBadgeVariant = (signal?: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
  if (!signal) return 'secondary';
  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    bullish: 'default',
    bearish: 'destructive',
    oversold: 'default',
    overbought: 'destructive',
    strong_trend: 'default',
    squeeze: 'outline',
    spike: 'destructive',
  };
  return variants[signal] || 'secondary';
};

// Format number with appropriate precision
const formatValue = (value: number | boolean | null | undefined, precision: number = 4): string => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (Math.abs(value) < 0.0001) return value.toExponential(2);
  return value.toFixed(precision);
};

// Indicator row component
interface IndicatorRowProps {
  name: string;
  indicator: IndicatorValue;
  precision?: number;
  showThresholds?: boolean;
}

function IndicatorRow({ name, indicator, precision = 4, showThresholds = true }: IndicatorRowProps) {
  const hasThresholds = indicator.thresholds && Object.keys(indicator.thresholds).length > 0;

  return (
    <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{name}</span>
          {indicator.signal && (
            <Badge variant={getSignalBadgeVariant(indicator.signal)} className="text-xs">
              {indicator.signal}
            </Badge>
          )}
        </div>
        <span className="text-xs text-muted-foreground">{indicator.description}</span>
      </div>
      <div className="text-right">
        <div className={`font-mono text-sm font-semibold ${getSignalColor(indicator.signal)}`}>
          {formatValue(indicator.value, precision)}
        </div>
        {showThresholds && hasThresholds && (
          <div className="text-xs text-muted-foreground">
            {Object.entries(indicator.thresholds!).slice(0, 2).map(([key, val]) => (
              <span key={key} className="mr-2">
                {key}: {Array.isArray(val) ? val.join('-') : val}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// RSI Gauge component
function RSIGauge({ value }: { value: number }) {
  const getColor = () => {
    if (value < 30) return 'bg-green-500';
    if (value > 70) return 'bg-red-500';
    if (value < 40 || value > 60) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div className="relative w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      {/* Threshold markers */}
      <div className="absolute left-[30%] top-0 bottom-0 w-0.5 bg-green-300 z-10" />
      <div className="absolute left-[70%] top-0 bottom-0 w-0.5 bg-red-300 z-10" />
      {/* Value indicator */}
      <div
        className={`absolute top-0 bottom-0 w-2 ${getColor()} rounded-full z-20 transition-all duration-300`}
        style={{ left: `calc(${Math.min(Math.max(value, 0), 100)}% - 4px)` }}
      />
    </div>
  );
}

export function LiveIndicatorsPanel() {
  const [data, setData] = useState<LiveIndicatorsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('XRPUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('5min');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchIndicators = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    try {
      const response = await liveTradingApi.getIndicators(selectedSymbol, selectedTimeframe);
      setData(response);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch indicators:', err);
      setError(err instanceof Error ? err.message : 'Failed to load indicators');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedSymbol, selectedTimeframe]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchIndicators();
  }, [fetchIndicators]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => fetchIndicators(true), 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchIndicators]);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-muted-foreground">{error}</p>
            <Button variant="outline" className="mt-4" onClick={() => fetchIndicators()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { price, indicators, signals } = data;

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              <CardTitle>Live Indicators</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SYMBOLS.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant={autoRefresh ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Auto' : 'Manual'}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => fetchIndicators(true)}
                disabled={refreshing}
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Price Overview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="h-5 w-5" />
            Price: {selectedSymbol}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="text-2xl font-bold">${formatValue(price.current, 4)}</div>
              <div className={`text-sm flex items-center gap-1 ${price.change_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {price.change_pct >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                {formatValue(Math.abs(price.change_pct), 2)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">High</div>
              <div className="font-mono">${formatValue(price.high, 4)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Low</div>
              <div className="font-mono">${formatValue(price.low, 4)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Updated</div>
              <div className="text-sm">{new Date(data.timestamp).toLocaleTimeString()}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Signal Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              {signals.trend.direction === 'bullish' ? (
                <TrendingUp className="h-5 w-5 text-green-500" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-500" />
              )}
              <span className="font-medium">Trend</span>
            </div>
            <div className={`text-lg font-bold ${signals.trend.direction === 'bullish' ? 'text-green-500' : 'text-red-500'}`}>
              {signals.trend.direction.toUpperCase()}
            </div>
            <Badge variant="outline" className="mt-1">{signals.trend.strength}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="h-5 w-5 text-blue-500" />
              <span className="font-medium">Momentum</span>
            </div>
            <div className="space-y-1">
              <Badge variant={getSignalBadgeVariant(signals.momentum.rsi_signal)}>
                RSI: {signals.momentum.rsi_signal}
              </Badge>
              <Badge variant={getSignalBadgeVariant(signals.momentum.macd_signal)} className="ml-1">
                MACD: {signals.momentum.macd_signal}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-5 w-5 text-orange-500" />
              <span className="font-medium">Volatility</span>
            </div>
            <div className={`text-lg font-bold ${
              signals.volatility.regime === 'high' ? 'text-orange-500' :
              signals.volatility.regime === 'low' ? 'text-green-500' : 'text-muted-foreground'
            }`}>
              {signals.volatility.regime.toUpperCase()}
            </div>
            <div className="text-xs text-muted-foreground">
              ATR: {formatValue(signals.volatility.atr_pct, 2)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Entry Conditions */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Entry Conditions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <ArrowUp className="h-4 w-4 text-green-500" />
                <span className="font-medium text-green-500">LONG</span>
              </div>
              <div className="space-y-1">
                {Object.entries(signals.entry_conditions.long).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    {value ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={value ? 'text-green-500' : 'text-muted-foreground'}>
                      {key.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <ArrowDown className="h-4 w-4 text-red-500" />
                <span className="font-medium text-red-500">SHORT</span>
              </div>
              <div className="space-y-1">
                {Object.entries(signals.entry_conditions.short).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    {value ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={value ? 'text-green-500' : 'text-muted-foreground'}>
                      {key.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Indicators Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Trend Indicators */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Trend Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <IndicatorRow name="EMA 9" indicator={indicators.trend.ema9} />
            <IndicatorRow name="EMA 20" indicator={indicators.trend.ema20} />
            <IndicatorRow name="EMA 50" indicator={indicators.trend.ema50} />
            <IndicatorRow name="EMA 200" indicator={indicators.trend.ema200} />
            <IndicatorRow name="EMA Cross 9/20" indicator={indicators.trend.ema_cross_9_20} />
            <IndicatorRow name="ADX" indicator={indicators.trend.adx} precision={2} />
          </CardContent>
        </Card>

        {/* Momentum Indicators */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              Momentum Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-sm">RSI (14)</span>
                <span className={`font-mono font-semibold ${getSignalColor(indicators.momentum.rsi.signal)}`}>
                  {formatValue(indicators.momentum.rsi.value, 1)}
                </span>
              </div>
              <RSIGauge value={indicators.momentum.rsi.value as number} />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Oversold (30)</span>
                <span>Overbought (70)</span>
              </div>
            </div>
            <IndicatorRow name="MACD Line" indicator={indicators.momentum.macd_line} precision={6} />
            <IndicatorRow name="MACD Signal" indicator={indicators.momentum.macd_signal} precision={6} />
            <IndicatorRow name="MACD Histogram" indicator={indicators.momentum.macd_histogram} precision={6} />
            <IndicatorRow name="Stochastic %K" indicator={indicators.momentum.stochastic_k} precision={2} />
            <IndicatorRow name="Stochastic %D" indicator={indicators.momentum.stochastic_d} precision={2} />
          </CardContent>
        </Card>

        {/* Volatility Indicators */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Volatility Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <IndicatorRow name="ATR (14)" indicator={indicators.volatility.atr} precision={6} />
            <IndicatorRow name="BB Upper" indicator={indicators.volatility.bollinger_upper} />
            <IndicatorRow name="BB Middle" indicator={indicators.volatility.bollinger_middle} />
            <IndicatorRow name="BB Lower" indicator={indicators.volatility.bollinger_lower} />
            <IndicatorRow name="BB Width" indicator={indicators.volatility.bollinger_width} precision={4} />
            <IndicatorRow name="Keltner Width" indicator={indicators.volatility.keltner_width} precision={4} />
          </CardContent>
        </Card>

        {/* Volume Indicators */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Volume Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <IndicatorRow name="Current Volume" indicator={indicators.volume.current} precision={0} />
            <IndicatorRow name="Volume SMA (20)" indicator={indicators.volume.sma20} precision={0} />
            <IndicatorRow name="Volume Ratio" indicator={indicators.volume.ratio} precision={2} />

            {/* Volume Bar */}
            <div className="mt-4">
              <div className="text-xs text-muted-foreground mb-1">Volume vs Average</div>
              <Progress
                value={Math.min((indicators.volume.ratio.value as number) * 50, 100)}
                className="h-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Low (0.5x)</span>
                <span>Normal (1x)</span>
                <span>High (2x)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gate Thresholds Reference */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">ML Gate Thresholds Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            {Object.entries(data.gate_thresholds).slice(0, 6).map(([gate, conditions]) => (
              <div key={gate} className="border rounded-lg p-3">
                <div className="font-medium capitalize mb-2">{gate} Gate</div>
                <div className="space-y-1 text-xs text-muted-foreground">
                  {Object.entries(conditions).slice(0, 3).map(([condition, values]) => (
                    <div key={condition} className="flex justify-between">
                      <span className="capitalize">{condition}:</span>
                      <span className="font-mono">
                        {typeof values === 'object'
                          ? Object.entries(values as Record<string, number | boolean>).slice(0, 2).map(([k, v]) =>
                              `${k}: ${v}`
                            ).join(', ')
                          : String(values)
                        }
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default LiveIndicatorsPanel;
