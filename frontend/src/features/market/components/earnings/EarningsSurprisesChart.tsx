/**
 * EarningsSurprisesChart Component
 * Bar chart showing historical EPS estimated vs actual with surprise indicators
 */

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import { TrendingUp, TrendingDown, Target } from 'lucide-react';
import { useEarningsSurprises, useEarningsSurpriseStats } from '../../api/useEarningsSurprises';
import type { EarningsSurprise } from '../../types/earnings.types';
import { getSurpriseType, getSurpriseColor } from '../../types/earnings.types';

interface EarningsSurprisesChartProps {
  symbol: string;
  showStats?: boolean;
  className?: string;
}

interface ChartDataPoint {
  quarter: string;
  estimated: number;
  actual: number;
  surprise: number;
  surprisePercent: number;
  date: string;
  isBeat: boolean;
  isMiss: boolean;
}

function formatQuarter(quarter: string, year?: number): string {
  return year ? `${quarter}'${String(year).slice(-2)}` : quarter;
}

export function EarningsSurprisesChart({
  symbol,
  showStats = true,
  className,
}: EarningsSurprisesChartProps) {
  const { data: surprises, isLoading, error } = useEarningsSurprises(symbol);
  const { stats } = useEarningsSurpriseStats(symbol);

  const chartData = useMemo<ChartDataPoint[]>(() => {
    if (!surprises) return [];

    return surprises
      .slice()
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(-12) // Last 12 quarters
      .map((s) => ({
        quarter: formatQuarter(s.fiscal_quarter),
        estimated: s.eps_estimated,
        actual: s.eps_actual,
        surprise: s.eps_actual - s.eps_estimated,
        surprisePercent: s.surprise_percent,
        date: s.date,
        isBeat: s.eps_actual > s.eps_estimated,
        isMiss: s.eps_actual < s.eps_estimated,
      }));
  }, [surprises]);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load earnings surprises for {symbol}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!surprises || surprises.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Earnings History - {symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            No earnings history available for {symbol}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle>Earnings History - {symbol}</CardTitle>

          {showStats && stats && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span className="text-sm">
                  <span className="font-semibold text-green-600">{stats.beats}</span>
                  <span className="text-muted-foreground"> beats</span>
                </span>
              </div>
              <div className="flex items-center gap-1">
                <TrendingDown className="h-4 w-4 text-red-600" />
                <span className="text-sm">
                  <span className="font-semibold text-red-600">{stats.misses}</span>
                  <span className="text-muted-foreground"> misses</span>
                </span>
              </div>
              <Badge variant="outline" className="text-xs">
                {stats.beatRate.toFixed(0)}% beat rate
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="quarter"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis
                tickFormatter={(value) => `$${value.toFixed(2)}`}
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: 'rgba(0, 0, 0, 0.1)' }}
              />
              <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" />

              {/* Estimated EPS */}
              <Bar
                dataKey="estimated"
                fill="hsl(var(--muted-foreground))"
                name="Estimated"
                radius={[4, 4, 0, 0]}
                opacity={0.5}
              />

              {/* Actual EPS - color coded by beat/miss */}
              <Bar dataKey="actual" name="Actual" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.isBeat
                        ? 'hsl(142, 76%, 36%)' // green-600
                        : entry.isMiss
                          ? 'hsl(0, 84%, 60%)' // red-500
                          : 'hsl(var(--muted-foreground))'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-muted-foreground opacity-50" />
            <span className="text-xs text-muted-foreground">Estimated</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-600" />
            <span className="text-xs text-muted-foreground">Beat</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-xs text-muted-foreground">Miss</span>
          </div>
        </div>

        {/* Streak Indicator */}
        {stats && stats.streak.count > 1 && (
          <div className="mt-4 text-center">
            <Badge
              variant={stats.streak.type === 'beat' ? 'default' : 'destructive'}
              className="text-sm"
            >
              {stats.streak.count}-quarter {stats.streak.type} streak
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    dataKey: string;
    payload: ChartDataPoint;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;
  const surpriseType = getSurpriseType(data.actual, data.estimated);

  return (
    <div className="bg-popover border rounded-lg shadow-lg p-3">
      <div className="font-semibold mb-2">{label}</div>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Estimated:</span>
          <span className="font-mono">${data.estimated.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Actual:</span>
          <span className="font-mono">${data.actual.toFixed(2)}</span>
        </div>
        <div className="flex justify-between gap-4 pt-1 border-t">
          <span className="text-muted-foreground">Surprise:</span>
          <span className={`font-mono font-semibold ${getSurpriseColor(surpriseType)}`}>
            {data.surprise >= 0 ? '+' : ''}${data.surprise.toFixed(2)} (
            {data.surprisePercent >= 0 ? '+' : ''}
            {data.surprisePercent.toFixed(1)}%)
          </span>
        </div>
      </div>
    </div>
  );
}

export default EarningsSurprisesChart;
