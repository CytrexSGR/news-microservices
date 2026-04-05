/**
 * EntityHistoryTimeline - History timeline
 *
 * Displays the history of entity merge/deduplication events.
 */
import { GitMerge, Clock, ChevronRight, RefreshCw, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEntityHistory } from '../api/useEntityHistory';
import type { MergeEvent, CanonicalizationSource } from '../types/entities.types';
import { getEntityTypeConfig, getConfidenceColor } from '../types/entities.types';

interface EntityHistoryTimelineProps {
  limit?: number;
  className?: string;
}

const SourceBadge = ({ source }: { source: CanonicalizationSource }) => {
  const colors: Record<CanonicalizationSource, string> = {
    exact: 'bg-green-100 text-green-700',
    fuzzy: 'bg-yellow-100 text-yellow-700',
    semantic: 'bg-blue-100 text-blue-700',
    wikidata: 'bg-purple-100 text-purple-700',
    new: 'bg-gray-100 text-gray-700',
  };

  return (
    <Badge className={`${colors[source]} border-0 capitalize`}>{source}</Badge>
  );
};

function TimelineEvent({ event }: { event: MergeEvent }) {
  const sourceConfig = getEntityTypeConfig(event.source_type);
  const targetConfig = getEntityTypeConfig(event.target_type);
  const confidenceColor = getConfidenceColor(event.confidence);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative pl-6 pb-6 last:pb-0">
      {/* Timeline line */}
      <div className="absolute left-0 top-2 bottom-0 w-0.5 bg-muted last:hidden" />

      {/* Timeline dot */}
      <div className="absolute left-0 top-2 -translate-x-1/2 w-3 h-3 rounded-full bg-primary border-2 border-background" />

      {/* Event content */}
      <div className="bg-muted/50 rounded-lg p-3 space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitMerge className="h-4 w-4 text-primary" />
            <span className="font-medium text-sm">Entity Merged</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatTimestamp(event.timestamp)}
          </div>
        </div>

        {/* Merge details */}
        <div className="flex items-center gap-2 text-sm">
          <div className="flex items-center gap-1.5">
            <span className="font-medium">{event.source_entity}</span>
            <Badge variant="outline" className={`${sourceConfig.color} text-xs`}>
              {event.source_type}
            </Badge>
          </div>
          <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <div className="flex items-center gap-1.5">
            <span className="font-medium">{event.target_entity}</span>
            <Badge variant="outline" className={`${targetConfig.color} text-xs`}>
              {event.target_type}
            </Badge>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs">
          <SourceBadge source={event.merge_method} />
          <span className={`font-medium ${confidenceColor}`}>
            {(event.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      </div>
    </div>
  );
}

export function EntityHistoryTimeline({ limit = 20, className }: EntityHistoryTimelineProps) {
  const { data: events, isLoading, isError, error, refetch, isRefetching } = useEntityHistory({
    limit,
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5" />
            Merge History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="pl-6">
                <Skeleton className="h-24 w-full rounded-lg" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5" />
            Merge History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 p-4 bg-destructive/10 rounded-lg text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load history: {error?.message}</span>
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
              <GitMerge className="h-5 w-5" />
              Merge History
            </CardTitle>
            <CardDescription>Recent entity deduplication events</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!events || events.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <GitMerge className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No merge events recorded yet</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-0">
              {events.map((event) => (
                <TimelineEvent key={event.id} event={event} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
