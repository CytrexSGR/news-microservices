/**
 * QueueChart Component
 *
 * Trend chart showing notification queue metrics over time.
 */

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Clock, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';

interface QueueChartProps {
  className?: string;
}

type TimeRange = '1h' | '6h' | '24h' | '7d';
type ChartType = 'line' | 'area';

// Mock data - in production this would come from an API
function generateMockData(range: TimeRange) {
  const points = {
    '1h': 12,
    '6h': 24,
    '24h': 48,
    '7d': 168,
  }[range];

  const now = new Date();
  const data = [];

  for (let i = points; i >= 0; i--) {
    const time = new Date(now);
    switch (range) {
      case '1h':
        time.setMinutes(time.getMinutes() - i * 5);
        break;
      case '6h':
        time.setMinutes(time.getMinutes() - i * 15);
        break;
      case '24h':
        time.setMinutes(time.getMinutes() - i * 30);
        break;
      case '7d':
        time.setHours(time.getHours() - i);
        break;
    }

    // Generate realistic-looking data with some variance
    const baseProcessed = 50 + Math.random() * 100;
    const basePending = 20 + Math.random() * 30;
    const baseRetrying = Math.random() * 10;
    const baseDlq = Math.random() < 0.1 ? Math.floor(Math.random() * 3) : 0;

    data.push({
      time: time.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      fullTime: time.toISOString(),
      processed: Math.floor(baseProcessed),
      pending: Math.floor(basePending),
      retrying: Math.floor(baseRetrying),
      dlq: baseDlq,
    });
  }

  return data;
}

export function QueueChart({ className }: QueueChartProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('1h');
  const [chartType, setChartType] = useState<ChartType>('area');
  const [isLoading, setIsLoading] = useState(false);

  // In production, this would use a query hook
  const data = generateMockData(timeRange);

  const handleRangeChange = (range: TimeRange) => {
    setIsLoading(true);
    setTimeRange(range);
    // Simulate loading
    setTimeout(() => setIsLoading(false), 300);
  };

  const ChartComponent = chartType === 'area' ? AreaChart : LineChart;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Queue Metrics
            </CardTitle>
            <CardDescription>
              Notification throughput and queue depth over time
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={chartType} onValueChange={(v) => setChartType(v as ChartType)}>
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="area">Area</SelectItem>
                <SelectItem value="line">Line</SelectItem>
              </SelectContent>
            </Select>
            <Select value={timeRange} onValueChange={(v) => handleRangeChange(v as TimeRange)}>
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">1 Hour</SelectItem>
                <SelectItem value="6h">6 Hours</SelectItem>
                <SelectItem value="24h">24 Hours</SelectItem>
                <SelectItem value="7d">7 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ChartComponent data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Legend />

              {chartType === 'area' ? (
                <>
                  <Area
                    type="monotone"
                    dataKey="processed"
                    name="Processed"
                    stackId="1"
                    stroke="hsl(var(--chart-1))"
                    fill="hsl(var(--chart-1))"
                    fillOpacity={0.4}
                  />
                  <Area
                    type="monotone"
                    dataKey="pending"
                    name="Pending"
                    stackId="2"
                    stroke="hsl(var(--chart-2))"
                    fill="hsl(var(--chart-2))"
                    fillOpacity={0.4}
                  />
                  <Area
                    type="monotone"
                    dataKey="retrying"
                    name="Retrying"
                    stackId="3"
                    stroke="hsl(var(--chart-3))"
                    fill="hsl(var(--chart-3))"
                    fillOpacity={0.4}
                  />
                  <Area
                    type="monotone"
                    dataKey="dlq"
                    name="DLQ"
                    stackId="4"
                    stroke="hsl(var(--destructive))"
                    fill="hsl(var(--destructive))"
                    fillOpacity={0.4}
                  />
                </>
              ) : (
                <>
                  <Line
                    type="monotone"
                    dataKey="processed"
                    name="Processed"
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="pending"
                    name="Pending"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="retrying"
                    name="Retrying"
                    stroke="hsl(var(--chart-3))"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="dlq"
                    name="DLQ"
                    stroke="hsl(var(--destructive))"
                    strokeWidth={2}
                    dot={false}
                  />
                </>
              )}
            </ChartComponent>
          </ResponsiveContainer>
        )}

        {/* Summary stats */}
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-2xl font-bold text-[hsl(var(--chart-1))]">
              {data.reduce((sum, d) => sum + d.processed, 0).toLocaleString()}
            </p>
            <p className="text-xs text-muted-foreground">Total Processed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-[hsl(var(--chart-2))]">
              {Math.round(data.reduce((sum, d) => sum + d.pending, 0) / data.length)}
            </p>
            <p className="text-xs text-muted-foreground">Avg Pending</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-[hsl(var(--chart-3))]">
              {data.reduce((sum, d) => sum + d.retrying, 0)}
            </p>
            <p className="text-xs text-muted-foreground">Total Retries</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-destructive">
              {data.reduce((sum, d) => sum + d.dlq, 0)}
            </p>
            <p className="text-xs text-muted-foreground">DLQ Items</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
