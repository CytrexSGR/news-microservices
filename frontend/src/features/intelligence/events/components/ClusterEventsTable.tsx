/**
 * ClusterEventsTable Component
 *
 * Table view of events within a cluster
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  RefreshCw,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useClusterEvents } from '../api/useClusterEvents';
import type { ClusterArticleEvent } from '../api/useClusterEvents';
import { RiskBadge } from './RiskBadge';
import type { IntelligenceEvent } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor, formatTimeAgo } from '../types/events.types';

// Format date for display (German locale)
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface ClusterEventsTableProps {
  clusterId: string;
  onEventClick?: (event: IntelligenceEvent) => void;
  pageSize?: number;
  className?: string;
}

export function ClusterEventsTable({
  clusterId,
  onEventClick,
  pageSize = 10,
  className,
}: ClusterEventsTableProps) {
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useClusterEvents(
    clusterId,
    { page, per_page: pageSize }
  );

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center justify-center gap-3 text-destructive">
            <AlertTriangle className="h-8 w-8" />
            <p>Failed to load cluster events</p>
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
            <CardTitle className="text-lg">Cluster Events</CardTitle>
            <CardDescription>
              {data?.total || 0} events in this cluster
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : data?.events.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No events in this cluster
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[35%]">Title</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Published</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.events.map((event) => {
                    // Cast to extended type with article metadata
                    const articleEvent = event as ClusterArticleEvent;
                    return (
                      <TableRow
                        key={event.id}
                        className="cursor-pointer hover:bg-accent/50"
                        onClick={() => onEventClick?.(event)}
                      >
                        <TableCell className="font-medium">
                          <div className="line-clamp-2">{event.title}</div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {articleEvent.source_name || '-'}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm whitespace-nowrap">
                          {formatDate(articleEvent.published_at)}
                        </TableCell>
                        <TableCell>
                          <RiskBadge
                            level={event.risk_level}
                            score={event.risk_score}
                            size="sm"
                            showIcon={false}
                          />
                        </TableCell>
                        <TableCell>
                          {event.url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(event.url, '_blank', 'noopener,noreferrer');
                              }}
                              title="Open original article"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t">
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
