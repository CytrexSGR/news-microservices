/**
 * EventsTimeline Component
 *
 * Displays a timeline of cluster events and changes
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Link2,
  AlertTriangle,
  GitMerge,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TimelineEntry } from '../types/events.types';

interface EventsTimelineProps {
  entries: TimelineEntry[];
  maxEntries?: number;
  className?: string;
}

function getEventIcon(type: TimelineEntry['event_type']) {
  switch (type) {
    case 'article_added':
      return <FileText className="h-4 w-4" />;
    case 'entity_linked':
      return <Link2 className="h-4 w-4" />;
    case 'risk_changed':
      return <AlertTriangle className="h-4 w-4" />;
    case 'cluster_merged':
      return <GitMerge className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
}

function getEventColor(type: TimelineEntry['event_type']) {
  switch (type) {
    case 'article_added':
      return 'bg-blue-500';
    case 'entity_linked':
      return 'bg-purple-500';
    case 'risk_changed':
      return 'bg-orange-500';
    case 'cluster_merged':
      return 'bg-green-500';
    default:
      return 'bg-gray-500';
  }
}

function getEventLabel(type: TimelineEntry['event_type']) {
  switch (type) {
    case 'article_added':
      return 'Article Added';
    case 'entity_linked':
      return 'Entity Linked';
    case 'risk_changed':
      return 'Risk Changed';
    case 'cluster_merged':
      return 'Cluster Merged';
    default:
      return 'Event';
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function EventsTimeline({
  entries,
  maxEntries = 20,
  className,
}: EventsTimelineProps) {
  const displayEntries = entries.slice(0, maxEntries);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Activity Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        {displayEntries.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No timeline events available
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-border" />

            <div className="space-y-4">
              {displayEntries.map((entry, index) => (
                <div key={index} className="relative pl-8">
                  {/* Timeline dot */}
                  <div
                    className={cn(
                      'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center text-white ring-4 ring-background',
                      getEventColor(entry.event_type)
                    )}
                  >
                    {getEventIcon(entry.event_type)}
                  </div>

                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="outline" className="text-xs">
                        {getEventLabel(entry.event_type)}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    </div>

                    {/* Entry details */}
                    {entry.details && Object.keys(entry.details).length > 0 && (
                      <div className="text-sm text-muted-foreground mt-1">
                        {entry.event_type === 'article_added' && entry.details.title && (
                          <p className="line-clamp-1">{entry.details.title as string}</p>
                        )}
                        {entry.event_type === 'entity_linked' && entry.details.entity && (
                          <p>Linked entity: {entry.details.entity as string}</p>
                        )}
                        {entry.event_type === 'risk_changed' && (
                          <p>
                            Risk changed from {entry.details.old_score as number} to{' '}
                            {entry.details.new_score as number}
                          </p>
                        )}
                        {entry.event_type === 'cluster_merged' && entry.details.merged_from && (
                          <p>Merged from cluster: {entry.details.merged_from as string}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {entries.length > maxEntries && (
              <div className="text-center mt-4 text-sm text-muted-foreground">
                Showing {maxEntries} of {entries.length} events
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
