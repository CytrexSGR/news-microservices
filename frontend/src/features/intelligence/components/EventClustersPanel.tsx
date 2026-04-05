/**
 * EventClustersPanel - Grouped events display with filtering
 *
 * Shows intelligence clusters with risk scores, event counts, and timeline
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Filter,
  ExternalLink,
} from 'lucide-react';
import { useEventClusters } from '../api/useEventClusters';
import { CompactRiskBadge } from './RiskScoreCard';
import type { ClusterDetail } from '../types/intelligence.types';

interface EventClustersPanelProps {
  timeWindow?: '1h' | '6h' | '12h' | '24h' | 'week' | 'month';
  sortBy?: 'risk_score' | 'event_count' | 'last_updated';
  onClusterClick?: (cluster: ClusterDetail) => void;
}

export function EventClustersPanel({
  timeWindow,
  sortBy = 'risk_score',
  onClusterClick,
}: EventClustersPanelProps) {
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [selectedTimeWindow, setSelectedTimeWindow] = useState<string | undefined>(timeWindow);
  const [selectedSortBy, setSelectedSortBy] = useState(sortBy);

  const { data, isLoading, error, refetch } = useEventClusters({
    time_window: selectedTimeWindow as any,
    sort_by: selectedSortBy,
    page,
    per_page: 10,
  });

  const toggleClusterExpansion = (clusterId: string) => {
    const newExpanded = new Set(expandedClusters);
    if (newExpanded.has(clusterId)) {
      newExpanded.delete(clusterId);
    } else {
      newExpanded.add(clusterId);
    }
    setExpandedClusters(newExpanded);
  };

  const getCategoryColor = (category?: string): string => {
    switch (category) {
      case 'geo': return 'bg-blue-500/10 text-blue-500';
      case 'finance': return 'bg-green-500/10 text-green-500';
      case 'tech': return 'bg-purple-500/10 text-purple-500';
      default: return 'bg-gray-500/10 text-gray-500';
    }
  };

  const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (error) {
    return (
      <Card className="p-4 bg-destructive/10 border-destructive">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="h-5 w-5" />
          <p>Failed to load clusters. Please try again.</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Event Clusters</CardTitle>
            <CardDescription>
              {data?.total || 0} active clusters grouped by topic
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={selectedTimeWindow || ''}
              onChange={(e) => setSelectedTimeWindow(e.target.value || undefined)}
              className="px-2 py-1 text-sm border rounded bg-background"
            >
              <option value="">All time</option>
              <option value="1h">Last hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
              <option value="week">This week</option>
            </select>
            <select
              value={selectedSortBy}
              onChange={(e) => setSelectedSortBy(e.target.value as any)}
              className="px-2 py-1 text-sm border rounded bg-background"
            >
              <option value="risk_score">Risk Score</option>
              <option value="event_count">Event Count</option>
              <option value="last_updated">Recent</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="p-4 border rounded-lg">
                <div className="flex justify-between mb-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-5 w-16" />
                </div>
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </div>
        ) : data?.clusters.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No clusters found for the selected filters
          </div>
        ) : (
          <div className="space-y-3">
            {data?.clusters.map((cluster) => {
              const isExpanded = expandedClusters.has(cluster.id);
              return (
                <div
                  key={cluster.id}
                  className="p-4 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
                  onClick={() => onClusterClick?.(cluster)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 flex-1">
                      <h4 className="font-medium line-clamp-1">{cluster.name}</h4>
                      {cluster.category && (
                        <Badge variant="outline" className={getCategoryColor(cluster.category)}>
                          {cluster.category}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <CompactRiskBadge score={cluster.risk_score} size="sm" />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleClusterExpansion(cluster.id);
                        }}
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{cluster.event_count} events</span>
                    <span>{cluster.unique_sources} sources</span>
                    <span className="flex items-center gap-1">
                      {cluster.risk_delta > 0 ? (
                        <TrendingUp className="h-3 w-3 text-red-500" />
                      ) : cluster.risk_delta < 0 ? (
                        <TrendingDown className="h-3 w-3 text-green-500" />
                      ) : null}
                      {cluster.risk_delta !== 0 && cluster.risk_delta != null && (
                        <span className={cluster.risk_delta > 0 ? 'text-red-500' : 'text-green-500'}>
                          {cluster.risk_delta > 0 ? '+' : ''}{(cluster.risk_delta ?? 0).toFixed(1)}
                        </span>
                      )}
                    </span>
                    <span>{formatTimeAgo(cluster.last_updated)}</span>
                  </div>

                  {/* Keywords */}
                  {cluster.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {cluster.keywords.slice(0, isExpanded ? undefined : 5).map((keyword) => (
                        <span
                          key={keyword}
                          className="px-2 py-0.5 text-xs bg-secondary rounded-full"
                        >
                          {keyword}
                        </span>
                      ))}
                      {!isExpanded && cluster.keywords.length > 5 && (
                        <span className="px-2 py-0.5 text-xs text-muted-foreground">
                          +{cluster.keywords.length - 5} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t space-y-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Sentiment</p>
                          <p className={`font-medium ${
                            (cluster.avg_sentiment ?? 0) > 0 ? 'text-green-500' :
                            (cluster.avg_sentiment ?? 0) < 0 ? 'text-red-500' : 'text-muted-foreground'
                          }`}>
                            {(cluster.avg_sentiment ?? 0).toFixed(2)}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Time Window</p>
                          <p className="font-medium">{cluster.time_window || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">First Seen</p>
                          <p className="font-medium">{new Date(cluster.first_seen).toLocaleDateString()}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Status</p>
                          <p className="font-medium">
                            {cluster.is_active ? (
                              <span className="text-green-500">Active</span>
                            ) : (
                              <span className="text-muted-foreground">Inactive</span>
                            )}
                          </p>
                        </div>
                      </div>

                      {/* Mini Timeline */}
                      {cluster.timeline.length > 0 && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-2">Event Activity (7 days)</p>
                          <div className="flex items-end gap-1 h-12">
                            {cluster.timeline.map((point, idx) => {
                              const maxCount = Math.max(...cluster.timeline.map(p => p.event_count));
                              const height = maxCount > 0 ? (point.event_count / maxCount) * 100 : 0;
                              return (
                                <div
                                  key={idx}
                                  className="flex-1 bg-primary/20 rounded-t hover:bg-primary/40 transition-colors"
                                  style={{ height: `${Math.max(height, 4)}%` }}
                                  title={`${point.event_count} events on ${new Date(point.date).toLocaleDateString()}`}
                                />
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {data && data.total > 10 && (
          <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {Math.ceil(data.total / 10)}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= Math.ceil(data.total / 10)}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
