/**
 * RiskHistoryPage
 *
 * Risk history analysis page with detailed charts
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  BarChart3,
} from 'lucide-react';
import { RiskHistoryChart } from '../components/RiskHistoryChart';
import { useRiskHistory } from '../api/useRiskHistory';
import type { RiskHistoryTimeframe } from '../api/useRiskHistory';
import { CompactRiskBadge } from '../components/RiskBadge';

export function RiskHistoryPage() {
  const [timeframe, setTimeframe] = useState<RiskHistoryTimeframe>('7d');
  const { data, isLoading, error, refetch } = useRiskHistory({ timeframe });

  // Calculate trend
  const calculateTrend = () => {
    if (!data?.history || data.history.length < 2) return { direction: 'stable', percentage: 0 };

    const latest = data.history[data.history.length - 1].risk_score;
    const previous = data.history[0].risk_score;
    const change = ((latest - previous) / previous) * 100;

    return {
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
      percentage: Math.abs(change),
    };
  };

  const trend = calculateTrend();

  // Top risk contributors
  const topContributors = data?.history
    .flatMap((h) => h.top_contributors)
    .reduce((acc, contributor) => {
      acc[contributor] = (acc[contributor] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

  const sortedContributors = topContributors
    ? Object.entries(topContributors)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
    : [];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Risk History Analysis
          </h1>
          <p className="text-muted-foreground">
            Analyze risk trends and patterns over time
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="h-5 w-5 text-muted-foreground" />
              {isLoading ? (
                <Skeleton className="h-5 w-12" />
              ) : (
                <CompactRiskBadge
                  score={data?.history[data.history.length - 1]?.risk_score || 0}
                  size="sm"
                />
              )}
            </div>
            {isLoading ? (
              <Skeleton className="h-8 w-16 mb-1" />
            ) : (
              <p className="text-2xl font-bold">
                {data?.history[data.history.length - 1]?.risk_score.toFixed(1) || '-'}
              </p>
            )}
            <p className="text-sm text-muted-foreground">Current Risk</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              {trend.direction === 'up' ? (
                <TrendingUp className="h-5 w-5 text-red-500" />
              ) : trend.direction === 'down' ? (
                <TrendingDown className="h-5 w-5 text-green-500" />
              ) : (
                <div className="h-5 w-5 border-t-2 border-muted-foreground" />
              )}
            </div>
            {isLoading ? (
              <Skeleton className="h-8 w-16 mb-1" />
            ) : (
              <p className={`text-2xl font-bold ${
                trend.direction === 'up' ? 'text-red-500' :
                trend.direction === 'down' ? 'text-green-500' : ''
              }`}>
                {trend.direction === 'up' ? '+' : trend.direction === 'down' ? '-' : ''}
                {trend.percentage.toFixed(1)}%
              </p>
            )}
            <p className="text-sm text-muted-foreground">Trend ({timeframe})</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {isLoading ? (
              <>
                <Skeleton className="h-5 w-5 mb-2" />
                <Skeleton className="h-8 w-16 mb-1" />
              </>
            ) : (
              <>
                <div className="flex items-center justify-between mb-2">
                  <TrendingUp className="h-5 w-5 text-muted-foreground" />
                </div>
                <p className="text-2xl font-bold">
                  {data?.history
                    ? Math.max(...data.history.map((h) => h.risk_score)).toFixed(1)
                    : '-'}
                </p>
              </>
            )}
            <p className="text-sm text-muted-foreground">Peak Risk</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {isLoading ? (
              <>
                <Skeleton className="h-5 w-5 mb-2" />
                <Skeleton className="h-8 w-16 mb-1" />
              </>
            ) : (
              <>
                <div className="flex items-center justify-between mb-2">
                  <TrendingDown className="h-5 w-5 text-muted-foreground" />
                </div>
                <p className="text-2xl font-bold">
                  {data?.history
                    ? Math.min(...data.history.map((h) => h.risk_score)).toFixed(1)
                    : '-'}
                </p>
              </>
            )}
            <p className="text-sm text-muted-foreground">Lowest Risk</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Chart */}
      <RiskHistoryChart height={400} showEvents />

      {/* Top Contributors */}
      <Card>
        <CardHeader>
          <CardTitle>Top Risk Contributors</CardTitle>
          <CardDescription>
            Most frequent contributors to risk score over the period
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : sortedContributors.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No contributor data available
            </div>
          ) : (
            <div className="space-y-3">
              {sortedContributors.map(([contributor, count], index) => (
                <div key={contributor} className="flex items-center gap-4">
                  <span className="text-lg font-bold text-muted-foreground w-6">
                    {index + 1}.
                  </span>
                  <div className="flex-1">
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{
                          width: `${(count / sortedContributors[0][1]) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{contributor}</span>
                    <span className="text-sm text-muted-foreground">
                      ({count} occurrences)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data Points Table */}
      {data?.history && data.history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Historical Data Points</CardTitle>
            <CardDescription>
              {data.total_points} data points over {timeframe}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background">
                  <tr className="border-b">
                    <th className="text-left py-2">Timestamp</th>
                    <th className="text-right py-2">Risk Score</th>
                    <th className="text-right py-2">Events</th>
                    <th className="text-left py-2">Top Contributor</th>
                  </tr>
                </thead>
                <tbody>
                  {data.history.slice(-20).reverse().map((entry, index) => (
                    <tr key={index} className="border-b border-muted">
                      <td className="py-2">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td className="text-right py-2">
                        <CompactRiskBadge score={entry.risk_score} size="sm" />
                      </td>
                      <td className="text-right py-2">{entry.events_count}</td>
                      <td className="py-2 text-muted-foreground">
                        {entry.top_contributors[0] || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
