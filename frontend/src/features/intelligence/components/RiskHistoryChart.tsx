/**
 * RiskHistoryChart - Historical risk score visualization
 *
 * Shows risk trends over time with interactive chart
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import { TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react';
import { useRiskHistory } from '../api/useRiskScore';
import { getRiskColor } from '../types/intelligence.types';

interface RiskHistoryChartProps {
  days?: number;
  height?: number;
}

export function RiskHistoryChart({ days = 7, height = 200 }: RiskHistoryChartProps) {
  const { data, isLoading, error, refetch } = useRiskHistory(days);

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center gap-2 py-8 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <p>Failed to load risk history</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk History</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full" style={{ height }} />
        </CardContent>
      </Card>
    );
  }

  if (!data?.history.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No risk history available
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxRisk = Math.max(...data.history.map(h => Math.max(h.global_risk, h.geo_risk, h.finance_risk)), 100);
  const chartHeight = height - 40; // Account for labels

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Risk History
          </CardTitle>
          <CardDescription>
            Last {days} days risk trend
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        {/* Legend */}
        <div className="flex items-center gap-6 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-sm">Global</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-sm">Geopolitical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-sm">Financial</span>
          </div>
        </div>

        {/* Chart */}
        <div className="relative" style={{ height: chartHeight }}>
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 bottom-8 w-8 flex flex-col justify-between text-xs text-muted-foreground">
            <span>{(maxRisk ?? 0).toFixed(0)}</span>
            <span>{((maxRisk ?? 0) / 2).toFixed(0)}</span>
            <span>0</span>
          </div>

          {/* Chart area */}
          <div className="ml-10 h-full relative">
            {/* Grid lines */}
            <div className="absolute inset-0 flex flex-col justify-between pb-8">
              {[0, 1, 2].map((i) => (
                <div key={i} className="border-t border-border/50" />
              ))}
            </div>

            {/* Line chart using SVG */}
            <svg
              className="absolute inset-0 w-full"
              style={{ height: chartHeight - 32 }}
              preserveAspectRatio="none"
            >
              {/* Global risk line */}
              <polyline
                fill="none"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                points={data.history.map((point, idx) => {
                  const x = (idx / (data.history.length - 1)) * 100;
                  const y = 100 - (point.global_risk / maxRisk) * 100;
                  return `${x}%,${y}%`;
                }).join(' ')}
              />

              {/* Geo risk line */}
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2"
                strokeDasharray="4,4"
                points={data.history.map((point, idx) => {
                  const x = (idx / (data.history.length - 1)) * 100;
                  const y = 100 - (point.geo_risk / maxRisk) * 100;
                  return `${x}%,${y}%`;
                }).join(' ')}
              />

              {/* Finance risk line */}
              <polyline
                fill="none"
                stroke="#22c55e"
                strokeWidth="2"
                strokeDasharray="2,2"
                points={data.history.map((point, idx) => {
                  const x = (idx / (data.history.length - 1)) * 100;
                  const y = 100 - (point.finance_risk / maxRisk) * 100;
                  return `${x}%,${y}%`;
                }).join(' ')}
              />

              {/* Data points */}
              {data.history.map((point, idx) => {
                const x = (idx / (data.history.length - 1)) * 100;
                const yGlobal = 100 - (point.global_risk / maxRisk) * 100;
                return (
                  <g key={idx}>
                    <circle
                      cx={`${x}%`}
                      cy={`${yGlobal}%`}
                      r="4"
                      fill="hsl(var(--primary))"
                      className="cursor-pointer hover:r-6 transition-all"
                    >
                      <title>
                        {formatDate(point.date)}
                        {'\n'}Global: {(point.global_risk ?? 0).toFixed(1)}
                        {'\n'}Geo: {(point.geo_risk ?? 0).toFixed(1)}
                        {'\n'}Finance: {(point.finance_risk ?? 0).toFixed(1)}
                        {'\n'}Events: {point.event_count ?? 0}
                      </title>
                    </circle>
                  </g>
                );
              })}
            </svg>

            {/* X-axis labels */}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-muted-foreground pt-2">
              {data.history.filter((_, idx) => idx % Math.ceil(data.history.length / 5) === 0 || idx === data.history.length - 1).map((point) => (
                <span key={point.date}>{formatDate(point.date)}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
          <div className="text-center">
            <p className="text-2xl font-bold">{(data.history[data.history.length - 1]?.global_risk ?? 0).toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Current Global</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-500">{(data.history[data.history.length - 1]?.geo_risk ?? 0).toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Current Geo</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-500">{(data.history[data.history.length - 1]?.finance_risk ?? 0).toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Current Finance</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
