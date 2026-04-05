/**
 * TradingIndicatorCard Component
 *
 * Displays a single technical indicator (RSI, MACD, EMA, or Volume)
 * with color-coded status badges and trend indicators.
 *
 * Features:
 * - Responsive card layout
 * - Color-coded badges (green/red/gray)
 * - Trend arrows (up/down)
 * - Formatted numbers
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Sparkline } from './Sparkline';

export interface IndicatorCardProps {
  title: string;
  value: string | number;
  status: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'OVERSOLD' | 'OVERBOUGHT' | 'HIGH' | 'NORMAL' | 'LOW' | 'ABOVE' | 'BELOW';
  description?: string;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  sparklineData?: number[];
  sparklineColor?: string;
}

const statusColors = {
  BULLISH: 'bg-green-100 text-green-800 border-green-300',
  OVERSOLD: 'bg-green-100 text-green-800 border-green-300',
  ABOVE: 'bg-green-100 text-green-800 border-green-300',
  HIGH: 'bg-green-100 text-green-800 border-green-300',

  BEARISH: 'bg-red-100 text-red-800 border-red-300',
  OVERBOUGHT: 'bg-red-100 text-red-800 border-red-300',
  BELOW: 'bg-red-100 text-red-800 border-red-300',

  NEUTRAL: 'bg-gray-100 text-gray-800 border-gray-300',
  NORMAL: 'bg-gray-100 text-gray-800 border-gray-300',
  LOW: 'bg-gray-100 text-gray-800 border-gray-300',
};

const TrendIcon = ({ trend }: { trend?: 'up' | 'down' | 'neutral' }) => {
  if (!trend) return null;

  if (trend === 'up') {
    return <TrendingUp className="h-5 w-5 text-green-600" />;
  }
  if (trend === 'down') {
    return <TrendingDown className="h-5 w-5 text-red-600" />;
  }
  return <Minus className="h-5 w-5 text-gray-600" />;
};

export const TradingIndicatorCard: React.FC<IndicatorCardProps> = ({
  title,
  value,
  status,
  description,
  subtitle,
  trend,
  sparklineData,
  sparklineColor,
}) => {
  // Determine sparkline color based on status if not provided
  const chartColor = sparklineColor || (
    status === 'BULLISH' || status === 'OVERSOLD' || status === 'HIGH' || status === 'ABOVE'
      ? '#10b981' // green
      : status === 'BEARISH' || status === 'OVERBOUGHT' || status === 'BELOW'
        ? '#ef4444' // red
        : '#6b7280' // gray
  );

  return (
    <Card className="hover:shadow-md transition-shadow h-full flex flex-col">
      <CardHeader className="pb-1 pt-2 px-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold">{title}</CardTitle>
          <TrendIcon trend={trend} />
        </div>
      </CardHeader>
      <CardContent className="px-3 pb-2 flex-1 flex flex-col">
        <div className="space-y-1 flex-1 flex flex-col">
          {/* Main Value */}
          <div className="text-lg font-bold">
            {typeof value === 'number' ? value.toFixed(2) : value}
          </div>

          {/* Sparkline */}
          {sparklineData && sparklineData.length > 0 && (
            <div className="-mx-1">
              <Sparkline data={sparklineData} color={chartColor} height={30} />
            </div>
          )}

          {/* Status Badge */}
          <Badge
            variant="outline"
            className={cn(
              'text-xs font-medium',
              statusColors[status] || statusColors.NEUTRAL
            )}
          >
            {status}
          </Badge>

          {/* Description (optional) */}
          {description && (
            <p className="text-xs text-muted-foreground line-clamp-1">
              {description}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TradingIndicatorCard;
