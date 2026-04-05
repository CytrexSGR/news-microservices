/**
 * PerformanceChart Component
 *
 * Displays performance metrics in a line chart using Recharts.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import type { PerformanceChartProps, TimeSeriesPoint } from '../types';

/**
 * Format timestamp for X-axis display
 */
function formatXAxis(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Custom tooltip component
 */
function CustomTooltip({
  active,
  payload,
  label,
  unit,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  unit?: string;
}) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
        <p className="text-xs text-muted-foreground mb-1">
          {label ? new Date(label).toLocaleString('de-DE') : ''}
        </p>
        <p className="text-sm font-semibold text-foreground">
          {payload[0].value.toFixed(2)} {unit || ''}
        </p>
      </div>
    );
  }
  return null;
}

export function PerformanceChart({
  data,
  title,
  color = '#3b82f6',
  unit = '',
  isLoading = false,
}: PerformanceChartProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
        <div className="h-4 bg-muted rounded w-32 mb-4 animate-pulse" />
        <div className="h-48 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
        <h4 className="font-medium text-foreground mb-4">{title}</h4>
        <div className="h-48 flex items-center justify-center text-muted-foreground">
          No data available
        </div>
      </div>
    );
  }

  // Transform data for recharts
  const chartData = data.map((point) => ({
    timestamp: point.timestamp,
    value: point.value,
  }));

  // Calculate min/max for Y axis
  const values = data.map((d) => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.1 || 1;

  return (
    <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-foreground">{title}</h4>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>
            Min: {minValue.toFixed(1)} {unit}
          </span>
          <span>|</span>
          <span>
            Max: {maxValue.toFixed(1)} {unit}
          </span>
        </div>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <defs>
              <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatXAxis}
              tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[minValue - padding, maxValue + padding]}
              tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value.toFixed(0)}${unit}`}
              width={50}
            />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill={`url(#gradient-${title})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
