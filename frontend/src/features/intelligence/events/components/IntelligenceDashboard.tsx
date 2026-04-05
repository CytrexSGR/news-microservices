/**
 * IntelligenceDashboard Component
 *
 * Main dashboard with overview metrics and charts
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  LayoutDashboard,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Activity,
  Layers,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useIntelligenceOverview } from '../api/useIntelligenceOverview';
import { RiskBadge, CompactRiskBadge } from './RiskBadge';
import { RiskHistoryChart } from './RiskHistoryChart';
import type { EventCluster, IntelligenceEvent, RiskLevel, EventCategory } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor, formatTimeAgo } from '../types/events.types';

interface IntelligenceDashboardProps {
  onClusterClick?: (cluster: EventCluster) => void;
  onEventClick?: (event: IntelligenceEvent) => void;
  className?: string;
}

export function IntelligenceDashboard({
  onClusterClick,
  onEventClick,
  className,
}: IntelligenceDashboardProps) {
  const { data, isLoading, error, refetch } = useIntelligenceOverview();

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center gap-3 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load intelligence overview</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const riskLevels: RiskLevel[] = ['low', 'medium', 'high', 'critical'];
  const categories: EventCategory[] = ['breaking', 'developing', 'trend', 'recurring', 'anomaly'];

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-6 w-6" />
          <div>
            <h2 className="text-xl font-bold">Intelligence Dashboard</h2>
            <p className="text-sm text-muted-foreground">
              Last updated: {formatTimeAgo(data.last_updated)}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <Activity className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold mt-2">{data.total_events}</p>
            <p className="text-sm text-muted-foreground">Total Events</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <Layers className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold mt-2">{data.active_clusters}</p>
            <p className="text-sm text-muted-foreground">Active Clusters</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold mt-2">{(data.avg_risk_score ?? 0).toFixed(1)}</p>
            <p className="text-sm text-muted-foreground">Avg Risk Score</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold mt-2">{data.trending_clusters.length}</p>
            <p className="text-sm text-muted-foreground">Trending Clusters</p>
          </CardContent>
        </Card>
      </div>

      {/* Risk Distribution & Category Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {riskLevels.map((level) => {
                const count = data.risk_distribution[level] || 0;
                const percentage = data.total_events > 0
                  ? (count / data.total_events) * 100
                  : 0;

                return (
                  <div key={level} className="flex items-center gap-3">
                    <RiskBadge level={level} size="sm" showIcon={false} />
                    <div className="flex-1">
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            level === 'critical' && 'bg-red-500',
                            level === 'high' && 'bg-orange-500',
                            level === 'medium' && 'bg-yellow-500',
                            level === 'low' && 'bg-green-500'
                          )}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-medium w-12 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Events by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {categories.map((category) => {
                const count = data.events_by_category[category] || 0;
                const percentage = data.total_events > 0
                  ? (count / data.total_events) * 100
                  : 0;

                return (
                  <div key={category} className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={cn(
                        'capitalize text-xs w-24 justify-center',
                        getCategoryBgColor(category),
                        getCategoryColor(category)
                      )}
                    >
                      {category}
                    </Badge>
                    <div className="flex-1">
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-medium w-12 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk History Chart */}
      <RiskHistoryChart />

      {/* Trending Clusters & Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trending Clusters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-orange-500" />
              Trending Clusters
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.trending_clusters.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No trending clusters
              </div>
            ) : (
              <div className="space-y-3">
                {data.trending_clusters.slice(0, 5).map((cluster) => (
                  <div
                    key={cluster.id}
                    className="p-3 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => onClusterClick?.(cluster)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-sm line-clamp-1">{cluster.name}</h4>
                      <CompactRiskBadge score={cluster.avg_risk_score} size="sm" />
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge
                        variant="outline"
                        className={cn(
                          'capitalize text-xs',
                          getCategoryBgColor(cluster.category),
                          getCategoryColor(cluster.category)
                        )}
                      >
                        {cluster.category}
                      </Badge>
                      <span>{cluster.events_count} events</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Events */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Recent Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.recent_events.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No recent events
              </div>
            ) : (
              <div className="space-y-3">
                {data.recent_events.slice(0, 5).map((event) => (
                  <div
                    key={event.id}
                    className="p-3 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                    onClick={() => onEventClick?.(event)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-sm line-clamp-1">{event.title}</h4>
                      <RiskBadge level={event.risk_level} size="sm" showIcon={false} />
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge
                        variant="outline"
                        className={cn(
                          'capitalize text-xs',
                          getCategoryBgColor(event.category),
                          getCategoryColor(event.category)
                        )}
                      >
                        {event.category}
                      </Badge>
                      <span>{formatTimeAgo(event.last_updated)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
