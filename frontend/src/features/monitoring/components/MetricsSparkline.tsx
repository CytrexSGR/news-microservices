/**
 * MetricsSparkline Component
 *
 * Displays a small inline sparkline chart for metrics visualization.
 */

import { useMemo } from 'react';
import type { MetricsSparklineProps } from '../types';

export function MetricsSparkline({
  data,
  color = '#3b82f6',
  height = 24,
  width = 80,
}: MetricsSparklineProps) {
  const pathData = useMemo(() => {
    if (!data || data.length < 2) return '';

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, width, height]);

  if (!data || data.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground text-xs"
        style={{ width, height }}
      >
        No data
      </div>
    );
  }

  // Calculate trend
  const trend = data[data.length - 1] - data[0];
  const trendColor = trend > 0 ? '#22c55e' : trend < 0 ? '#ef4444' : color;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Area under the line */}
      <path
        d={`${pathData} L ${width},${height} L 0,${height} Z`}
        fill={`url(#gradient-${color.replace('#', '')})`}
      />

      {/* Main line */}
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Last point indicator */}
      <circle
        cx={width}
        cy={height - ((data[data.length - 1] - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1)) * (height - 4) - 2}
        r="2"
        fill={trendColor}
      />
    </svg>
  );
}
