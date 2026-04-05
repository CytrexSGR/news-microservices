/**
 * IndicatorCharts Component
 *
 * Tab 3 of the Strategy Debugger: Visual timeline of indicators and conditions.
 * Creates interactive charts for each indicator showing:
 * - Indicator values over time
 * - Entry/Exit markers
 * - Condition TRUE/FALSE timeline
 */

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useTheme } from '@/components/ThemeProvider';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  Legend
} from 'recharts';
import { TrendingUp, Activity } from 'lucide-react';

export interface DebugLog {
  timestamp: string;
  event_type: string;
  signal_strength?: number;
  threshold?: number;
  conditions_met: string[];
  conditions_failed: string[];
  decision: string;
  reason: string;
  price?: number;
  indicators: Record<string, any>;
  parameters: Record<string, any>;
}

export interface IndicatorChartsProps {
  logs: DebugLog[];
}

interface ChartDataPoint {
  timestamp: string;
  formattedTime: string;
  [key: string]: any;
}

export const IndicatorCharts: React.FC<IndicatorChartsProps> = ({ logs }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  const chartColors = {
    stroke: isDark ? '#60a5fa' : '#3b82f6',
    fill: isDark ? 'rgba(96, 165, 250, 0.2)' : 'rgba(59, 130, 246, 0.2)',
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
    green: '#10b981',
    red: '#ef4444',
  };

  // Extract and structure chart data
  const chartData = useMemo(() => {
    // Collect all unique indicator keys
    const indicatorKeys = new Set<string>();
    logs.forEach(log => {
      Object.keys(log.indicators).forEach(key => indicatorKeys.add(key));
    });

    // Build time series data
    const timeSeriesData: ChartDataPoint[] = logs.map(log => {
      const dataPoint: ChartDataPoint = {
        timestamp: log.timestamp,
        formattedTime: new Date(log.timestamp).toLocaleTimeString('de-DE', {
          hour: '2-digit',
          minute: '2-digit'
        }),
        price: log.price || 0,
        signalStrength: (log.signal_strength || 0) * 100,
        decision: log.decision,
        conditionsMet: log.conditions_met.length,
        conditionsFailed: log.conditions_failed.length
      };

      // Add all indicators
      Object.entries(log.indicators).forEach(([key, value]) => {
        if (typeof value === 'number') {
          dataPoint[key] = value;
        }
      });

      return dataPoint;
    });

    // Group indicators by type/category
    const priceIndicators = Array.from(indicatorKeys).filter(key =>
      key.toLowerCase().includes('ema') ||
      key.toLowerCase().includes('sma') ||
      key.toLowerCase().includes('price')
    );

    const momentumIndicators = Array.from(indicatorKeys).filter(key =>
      key.toLowerCase().includes('rsi') ||
      key.toLowerCase().includes('macd') ||
      key.toLowerCase().includes('momentum')
    );

    const volumeIndicators = Array.from(indicatorKeys).filter(key =>
      key.toLowerCase().includes('volume') ||
      key.toLowerCase().includes('vol')
    );

    const otherIndicators = Array.from(indicatorKeys).filter(key =>
      !priceIndicators.includes(key) &&
      !momentumIndicators.includes(key) &&
      !volumeIndicators.includes(key)
    );

    return {
      timeSeriesData,
      indicators: {
        price: priceIndicators,
        momentum: momentumIndicators,
        volume: volumeIndicators,
        other: otherIndicators
      }
    };
  }, [logs]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-background border rounded-lg p-3 shadow-lg">
        <p className="text-sm font-semibold mb-2">{data.formattedTime}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-xs" style={{ color: entry.color }}>
            <span className="font-medium">{entry.name}:</span> {entry.value?.toFixed(2)}
          </p>
        ))}
        <div className="mt-2 pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            Decision: <span className={data.decision === 'accepted' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
              {data.decision}
            </span>
          </p>
        </div>
      </div>
    );
  };

  const renderIndicatorChart = (title: string, indicators: string[], type: 'line' | 'area' = 'line') => {
    if (indicators.length === 0) return null;

    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    return (
      <Card key={title}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            {type === 'area' ? (
              <AreaChart data={chartData.timeSeriesData}>
                <defs>
                  {indicators.map((indicator, idx) => (
                    <linearGradient key={indicator} id={`gradient-${indicator}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors[idx % colors.length]} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={colors[idx % colors.length]} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis
                  dataKey="formattedTime"
                  stroke={chartColors.text}
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke={chartColors.text} tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {indicators.map((indicator, idx) => (
                  <Area
                    key={indicator}
                    type="monotone"
                    dataKey={indicator}
                    stroke={colors[idx % colors.length]}
                    fillOpacity={1}
                    fill={`url(#gradient-${indicator})`}
                  />
                ))}
                {/* Entry/Exit markers */}
                {chartData.timeSeriesData.map((point, idx) => (
                  point.decision === 'accepted' ? (
                    <ReferenceDot
                      key={`entry-${idx}`}
                      x={point.formattedTime}
                      y={point[indicators[0]]}
                      r={5}
                      fill={chartColors.green}
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  ) : null
                ))}
              </AreaChart>
            ) : (
              <LineChart data={chartData.timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis
                  dataKey="formattedTime"
                  stroke={chartColors.text}
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke={chartColors.text} tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {indicators.map((indicator, idx) => (
                  <Line
                    key={indicator}
                    type="monotone"
                    dataKey={indicator}
                    stroke={colors[idx % colors.length]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
                {/* Entry markers */}
                {chartData.timeSeriesData.map((point, idx) => (
                  point.decision === 'accepted' ? (
                    <ReferenceDot
                      key={`entry-${idx}`}
                      x={point.formattedTime}
                      y={point[indicators[0]]}
                      r={5}
                      fill={chartColors.green}
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  ) : null
                ))}
              </LineChart>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Signal Strength Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Entry Signal Strength Over Time
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData.timeSeriesData}>
              <defs>
                <linearGradient id="signalGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColors.stroke} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={chartColors.stroke} stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
              <XAxis
                dataKey="formattedTime"
                stroke={chartColors.text}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                stroke={chartColors.text}
                tick={{ fontSize: 12 }}
                domain={[0, 100]}
                label={{ value: 'Signal %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="signalStrength"
                stroke={chartColors.stroke}
                fillOpacity={1}
                fill="url(#signalGradient)"
              />
              {/* Entry markers */}
              {chartData.timeSeriesData.map((point, idx) => (
                point.decision === 'accepted' ? (
                  <ReferenceDot
                    key={`entry-${idx}`}
                    x={point.formattedTime}
                    y={point.signalStrength}
                    r={5}
                    fill={chartColors.green}
                    stroke="#fff"
                    strokeWidth={2}
                  />
                ) : null
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Price Indicators */}
      {renderIndicatorChart('Price & Moving Averages', chartData.indicators.price, 'line')}

      {/* Momentum Indicators */}
      {renderIndicatorChart('Momentum Indicators', chartData.indicators.momentum, 'line')}

      {/* Volume Indicators */}
      {renderIndicatorChart('Volume Analysis', chartData.indicators.volume, 'area')}

      {/* Other Indicators */}
      {renderIndicatorChart('Other Indicators', chartData.indicators.other, 'line')}

      {/* If no indicators found */}
      {chartData.indicators.price.length === 0 &&
       chartData.indicators.momentum.length === 0 &&
       chartData.indicators.volume.length === 0 &&
       chartData.indicators.other.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No indicator data available to chart</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
