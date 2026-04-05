/**
 * BiasChart - Visualize bias analysis using Recharts
 *
 * Provides radar and bar chart visualizations for bias analysis results.
 */
import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { BiasResult, BiasType, BiasDirection } from '../types/narrative.types';
import { getBiasColor, getBiasLabel } from '../types/narrative.types';

// ==================== Radar Chart ====================

interface BiasRadarChartProps {
  biasResult: BiasResult;
  height?: number;
  showLegend?: boolean;
  className?: string;
}

export function BiasRadarChart({
  biasResult,
  height = 300,
  showLegend = true,
  className = '',
}: BiasRadarChartProps) {
  const biasTypes: BiasType[] = ['political', 'ideological', 'commercial', 'emotional', 'source'];

  const radarData = useMemo(() => {
    return biasTypes.map((type) => ({
      type: type.charAt(0).toUpperCase() + type.slice(1),
      value: Math.abs(biasResult.bias_by_type[type] || 0) * 100,
      fullMark: 100,
    }));
  }, [biasResult.bias_by_type]);

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Bias Distribution by Type</CardTitle>
        <CardDescription>
          Strength of bias detected across different categories
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis
              dataKey="type"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fontSize: 10 }}
              tickFormatter={(value) => `${value}%`}
            />
            <Radar
              name="Bias Strength"
              dataKey="value"
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary))"
              fillOpacity={0.5}
            />
            {showLegend && <Legend />}
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Bias Strength']}
            />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ==================== Bar Chart ====================

interface BiasBarChartProps {
  biasResult: BiasResult;
  height?: number;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export function BiasBarChart({
  biasResult,
  height = 250,
  orientation = 'vertical',
  className = '',
}: BiasBarChartProps) {
  const biasTypes: BiasType[] = ['political', 'ideological', 'commercial', 'emotional', 'source'];

  const barData = useMemo(() => {
    return biasTypes.map((type) => {
      const value = biasResult.bias_by_type[type] || 0;
      return {
        type: type.charAt(0).toUpperCase() + type.slice(1),
        value: value * 100,
        direction: value > 0 ? 'right' : value < 0 ? 'left' : 'center',
      };
    });
  }, [biasResult.bias_by_type]);

  const getBarColor = (value: number): string => {
    if (value > 30) return '#ef4444'; // red
    if (value > 0) return '#f97316'; // orange
    if (value < -30) return '#3b82f6'; // blue
    if (value < 0) return '#60a5fa'; // light blue
    return '#6b7280'; // gray
  };

  if (orientation === 'horizontal') {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Bias by Type</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis
                type="number"
                domain={[-100, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <YAxis type="category" dataKey="type" width={80} />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Bias']}
              />
              <ReferenceLine x={0} stroke="#666" />
              <Bar dataKey="value" name="Bias">
                {barData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.value)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Bias by Type</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="type" />
            <YAxis
              domain={[-100, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Bias']}
            />
            <ReferenceLine y={0} stroke="#666" />
            <Bar dataKey="value" name="Bias">
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ==================== Overall Bias Gauge ====================

interface BiasGaugeProps {
  score: number;
  confidence: number;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function BiasGauge({
  score,
  confidence,
  showLabels = true,
  size = 'md',
  className = '',
}: BiasGaugeProps) {
  // Convert -1 to 1 scale to 0-100 for positioning
  const position = ((score + 1) / 2) * 100;
  const biasDirection = getBiasLabel(score);
  const biasColorClass = getBiasColor(biasDirection);

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  const markerSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {showLabels && (
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Left</span>
          <span>Center</span>
          <span>Right</span>
        </div>
      )}
      <div className="relative">
        <div
          className={`w-full rounded-full bg-gradient-to-r from-blue-500 via-gray-300 to-red-500 ${sizeClasses[size]}`}
        />
        <div
          className={`absolute top-1/2 -translate-y-1/2 ${markerSizes[size]} bg-white border-2 border-gray-700 rounded-full shadow-md transition-all duration-300`}
          style={{ left: `calc(${position}% - ${size === 'sm' ? 6 : size === 'md' ? 8 : 10}px)` }}
        />
      </div>
      <div className="flex items-center justify-center gap-2">
        <Badge variant="outline" className={`capitalize ${biasColorClass}`}>
          {biasDirection}
        </Badge>
        <span className="text-sm text-muted-foreground">
          ({score > 0 ? '+' : ''}{score.toFixed(2)})
        </span>
        {confidence && (
          <span className="text-xs text-muted-foreground">
            {(confidence * 100).toFixed(0)}% confidence
          </span>
        )}
      </div>
    </div>
  );
}

// ==================== Bias Comparison Chart ====================

interface BiasComparisonData {
  label: string;
  score: number;
  count?: number;
}

interface BiasComparisonChartProps {
  data: BiasComparisonData[];
  title?: string;
  height?: number;
  className?: string;
}

export function BiasComparisonChart({
  data,
  title = 'Bias Comparison',
  height = 300,
  className = '',
}: BiasComparisonChartProps) {
  const chartData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      value: item.score * 100,
    }));
  }, [data]);

  const getColor = (score: number): string => {
    if (score > 30) return '#ef4444';
    if (score > 0) return '#f97316';
    if (score < -30) return '#3b82f6';
    if (score < 0) return '#60a5fa';
    return '#6b7280';
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              domain={[-100, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis type="category" dataKey="label" width={100} />
            <Tooltip
              formatter={(value: number) => [
                `${value > 0 ? '+' : ''}${value.toFixed(1)}%`,
                'Bias',
              ]}
            />
            <ReferenceLine x={0} stroke="#666" />
            <Bar dataKey="value" name="Bias Score">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ==================== Loading Skeleton ====================

interface BiasChartSkeletonProps {
  height?: number;
  className?: string;
}

export function BiasChartSkeleton({ height = 300, className = '' }: BiasChartSkeletonProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-60 mt-1" />
      </CardHeader>
      <CardContent>
        <Skeleton className="w-full" style={{ height }} />
      </CardContent>
    </Card>
  );
}
