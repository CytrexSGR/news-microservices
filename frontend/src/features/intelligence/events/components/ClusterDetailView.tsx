/**
 * ClusterDetailView Component
 *
 * Displays full cluster details with events and timeline
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Clock,
  Tag,
  Link2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useClusterDetails } from '../api/useClusterDetails';
import { RiskBadge } from './RiskBadge';
import { EventCard } from './EventCard';
import { EventsTimeline } from './EventsTimeline';
import type { ClusterDetails, IntelligenceEvent } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor, formatTimeAgo } from '../types/events.types';

interface ClusterDetailViewProps {
  clusterId: string;
  onBack?: () => void;
  onEventClick?: (event: IntelligenceEvent) => void;
  onRelatedClusterClick?: (clusterId: string) => void;
  className?: string;
}

export function ClusterDetailView({
  clusterId,
  onBack,
  onEventClick,
  onRelatedClusterClick,
  className,
}: ClusterDetailViewProps) {
  const { data: cluster, isLoading, error, refetch } = useClusterDetails(clusterId);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center gap-3 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load cluster details</p>
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
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!cluster) {
    return (
      <Card className={className}>
        <CardContent className="py-12">
          <div className="text-center text-muted-foreground">
            Cluster not found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {onBack && (
                <Button variant="ghost" size="sm" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <div>
                <CardTitle className="flex items-center gap-2">
                  {cluster.name}
                  {cluster.trending && (
                    <TrendingUp className="h-5 w-5 text-orange-500" />
                  )}
                </CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1">
                  <Badge
                    variant="outline"
                    className={cn(
                      'capitalize',
                      getCategoryBgColor(cluster.category),
                      getCategoryColor(cluster.category)
                    )}
                  >
                    {cluster.category}
                  </Badge>
                  <span>{cluster.events_count} events</span>
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <RiskBadge level={cluster.risk_level} score={cluster.avg_risk_score} />
              <Button variant="ghost" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Events</p>
              <p className="text-2xl font-bold">{cluster.events_count}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Avg Risk Score</p>
              <p className="text-2xl font-bold">{cluster.avg_risk_score.toFixed(1)}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Created</p>
              <p className="text-sm font-medium">{formatTimeAgo(cluster.created_at)}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Last Activity</p>
              <p className="text-sm font-medium">{formatTimeAgo(cluster.last_activity)}</p>
            </div>
          </div>

          {/* Keywords */}
          {cluster.keywords.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Keywords
              </h4>
              <div className="flex flex-wrap gap-1">
                {cluster.keywords.map((keyword) => (
                  <Badge key={keyword} variant="secondary">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Top Entities */}
          {cluster.top_entities.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium mb-2">Top Entities</h4>
              <div className="flex flex-wrap gap-1">
                {cluster.top_entities.map((entity) => (
                  <Badge key={entity} variant="outline">
                    {entity}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Related Clusters */}
          {cluster.related_clusters.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <Link2 className="h-4 w-4" />
                Related Clusters
              </h4>
              <div className="flex flex-wrap gap-2">
                {cluster.related_clusters.map((relatedId) => (
                  <Button
                    key={relatedId}
                    variant="outline"
                    size="sm"
                    onClick={() => onRelatedClusterClick?.(relatedId)}
                  >
                    {relatedId}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Timeline */}
      {cluster.timeline.length > 0 && (
        <EventsTimeline entries={cluster.timeline} />
      )}

      {/* Events */}
      {cluster.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Events in Cluster</CardTitle>
            <CardDescription>{cluster.events.length} events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cluster.events.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onClick={onEventClick}
                  showCluster={false}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
