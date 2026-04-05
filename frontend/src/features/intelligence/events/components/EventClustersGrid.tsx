/**
 * EventClustersGrid Component
 *
 * Grid display of event clusters with filtering
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Grid3X3,
  TrendingUp,
  Filter,
  RefreshCw,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEventClusters } from '../api/useEventClusters';
import { RiskBadge } from './RiskBadge';
import type { EventCluster, EventCategory, RiskLevel } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor, formatTimeAgo } from '../types/events.types';

interface EventClustersGridProps {
  onClusterClick?: (cluster: EventCluster) => void;
  pageSize?: number;
  className?: string;
}

export function EventClustersGrid({
  onClusterClick,
  pageSize = 12,
  className,
}: EventClustersGridProps) {
  const [page, setPage] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState<EventCategory | undefined>();
  const [riskFilter, setRiskFilter] = useState<RiskLevel | undefined>();
  const [trendingOnly, setTrendingOnly] = useState(false);

  const { data, isLoading, error, refetch } = useEventClusters({
    category: categoryFilter,
    risk_level: riskFilter,
    trending_only: trendingOnly,
    page,
    per_page: pageSize,
  });

  const categories: EventCategory[] = ['breaking', 'developing', 'trend', 'recurring', 'anomaly'];
  const riskLevels: RiskLevel[] = ['low', 'medium', 'high', 'critical'];

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center gap-3 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load event clusters</p>
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
              <Grid3X3 className="h-5 w-5" />
              Event Clusters
            </CardTitle>
            <CardDescription>
              {data?.total || 0} clusters found
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          <Filter className="h-4 w-4 text-muted-foreground" />

          {/* Category filter */}
          <select
            value={categoryFilter || ''}
            onChange={(e) => {
              setCategoryFilter(e.target.value as EventCategory || undefined);
              setPage(1);
            }}
            className="px-2 py-1 text-sm border rounded bg-background"
          >
            <option value="">All categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat} className="capitalize">
                {cat}
              </option>
            ))}
          </select>

          {/* Risk filter */}
          <select
            value={riskFilter || ''}
            onChange={(e) => {
              setRiskFilter(e.target.value as RiskLevel || undefined);
              setPage(1);
            }}
            className="px-2 py-1 text-sm border rounded bg-background"
          >
            <option value="">All risk levels</option>
            {riskLevels.map((level) => (
              <option key={level} value={level} className="capitalize">
                {level}
              </option>
            ))}
          </select>

          {/* Trending toggle */}
          <Button
            variant={trendingOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setTrendingOnly(!trendingOnly);
              setPage(1);
            }}
          >
            <TrendingUp className="h-4 w-4 mr-1" />
            Trending
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="p-4 border rounded-lg">
                <Skeleton className="h-5 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2 mb-3" />
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.clusters.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No clusters found matching your filters
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data?.clusters.map((cluster) => (
                <div
                  key={cluster.id}
                  className={cn(
                    'p-4 border rounded-lg transition-all cursor-pointer',
                    'hover:border-primary/50 hover:shadow-md',
                    cluster.trending && 'border-orange-500/50 bg-orange-500/5'
                  )}
                  onClick={() => onClusterClick?.(cluster)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium line-clamp-1 flex-1">{cluster.name}</h4>
                    {cluster.trending && (
                      <TrendingUp className="h-4 w-4 text-orange-500 shrink-0" />
                    )}
                  </div>

                  <div className="flex items-center gap-2 mb-3">
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
                    <RiskBadge level={cluster.risk_level} size="sm" showIcon={false} />
                  </div>

                  <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                    <span>{cluster.events_count} events</span>
                    <span>Avg: {cluster.avg_risk_score.toFixed(0)}</span>
                  </div>

                  {cluster.top_entities.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {cluster.top_entities.slice(0, 3).map((entity) => (
                        <Badge key={entity} variant="secondary" className="text-xs">
                          {entity}
                        </Badge>
                      ))}
                      {cluster.top_entities.length > 3 && (
                        <span className="text-xs text-muted-foreground">
                          +{cluster.top_entities.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground mt-2">
                    Last activity: {formatTimeAgo(cluster.last_activity)}
                  </p>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6 pt-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
