/**
 * RiskHistoryChart Component
 *
 * Line chart showing risk score trends over time using recharts
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import {
  TrendingUp,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useRiskHistory } from '../api/useRiskHistory';
import type { RiskHistoryTimeframe } from '../api/useRiskHistory';

interface RiskHistoryChartProps {
  clusterId?: string;
  height?: number;
  showEvents?: boolean;
  className?: string;
}

const timeframeOptions: { value: RiskHistoryTimeframe; label: string }[] = [
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
];

export function RiskHistoryChart({
  clusterId,
  height = 300,
  showEvents = true,
  className,
}: RiskHistoryChartProps) {
  const [timeframe, setTimeframe] = useState<RiskHistoryTimeframe>('7d');

  const { data, isLoading, error, refetch } = useRiskHistory({
    timeframe,
    cluster_id: clusterId,
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (timeframe === '24h') {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const chartData = data?.history.map((entry) => ({
    ...entry,
    formattedTime: formatTimestamp(entry.timestamp),
  })) || [];

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Risk History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center gap-3 py-8 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load risk history</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Risk History
            </CardTitle>
            <CardDescription>
              Risk score trends over {timeframeOptions.find((t) => t.value === timeframe)?.label.toLowerCase()}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {timeframeOptions.map((option) => (
              <Button
                key={option.value}
                variant={timeframe === option.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeframe(option.value)}
              >
                {option.label}
              </Button>
            ))}
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="w-full" style={{ height }} />
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center text-muted-foreground" style={{ height }}>
            No risk history data available
          </div>
        ) : (
          <div style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                  {showEvents && (
                    <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  )}
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="formattedTime"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  className="text-muted-foreground"
                />
                <YAxis
                  yAxisId="risk"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 100]}
                  className="text-muted-foreground"
                />
                {showEvents && (
                  <YAxis
                    yAxisId="events"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    className="text-muted-foreground"
                  />
                )}
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                  formatter={(value: number, name: string) => {
                    if (name === 'Risk Score') return [(value ?? 0).toFixed(1), name];
                    return [value ?? 0, name];
                  }}
                />
                <Legend />
                <Area
                  yAxisId="risk"
                  type="monotone"
                  dataKey="risk_score"
                  name="Risk Score"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  fill="url(#colorRisk)"
                />
                {showEvents && (
                  <Area
                    yAxisId="events"
                    type="monotone"
                    dataKey="events_count"
                    name="Events"
                    stroke="#22c55e"
                    strokeWidth={2}
                    fill="url(#colorEvents)"
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary stats */}
        {chartData.length > 0 && (
          <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
            <div className="text-center">
              <p className="text-2xl font-bold">
                {(chartData[chartData.length - 1]?.risk_score ?? 0).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">Current Risk</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {(chartData.reduce((sum, d) => sum + (d.risk_score ?? 0), 0) / chartData.length).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">Average Risk</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {Math.max(...chartData.map((d) => d.risk_score ?? 0)).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">Peak Risk</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
