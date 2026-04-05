/**
 * SearchAlertsPage Component
 *
 * Page for managing search alert configurations and viewing alert history.
 */

import * as React from 'react';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import {
  Bell,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  Mail,
  Webhook,
  Loader2,
  Search,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { useSavedSearch } from '../api/useSavedSearch';
import {
  useSearchAlerts,
  useSearchAlertHistory,
  useSearchAlertConfig,
  useAcknowledgeAlert,
} from '../api/useSearchAlerts';
import { SearchAlertConfigPanel } from '../components/SearchAlertConfigPanel';
import type { SearchAlertHistoryEntry, AlertChannelType } from '../types/search.types';

// Channel icons
const CHANNEL_ICONS: Record<AlertChannelType, React.ComponentType<{ className?: string }>> = {
  email: Mail,
  webhook: Webhook,
  in_app: Bell,
};

/**
 * Alert history row component
 */
function AlertHistoryRow({
  alert,
  onAcknowledge,
  isAcknowledging,
}: {
  alert: SearchAlertHistoryEntry;
  onAcknowledge: () => void;
  isAcknowledging: boolean;
}) {
  const ChannelIcon = CHANNEL_ICONS[alert.channel];
  const triggeredAt = parseISO(alert.triggered_at);

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-2">
          <ChannelIcon className="h-4 w-4 text-muted-foreground" />
          <span className="capitalize">{alert.channel}</span>
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-0.5">
          <div className="text-sm">
            {format(triggeredAt, 'MMM d, yyyy HH:mm:ss')}
          </div>
          <div className="text-xs text-muted-foreground">
            {formatDistanceToNow(triggeredAt, { addSuffix: true })}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant="secondary">{alert.result_count} results</Badge>
      </TableCell>
      <TableCell>
        {alert.status === 'sent' && (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Sent
          </Badge>
        )}
        {alert.status === 'failed' && (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Failed
          </Badge>
        )}
        {alert.status === 'pending' && (
          <Badge variant="outline">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        )}
      </TableCell>
      <TableCell>
        {alert.error ? (
          <span className="text-sm text-destructive">{alert.error}</span>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </TableCell>
      <TableCell>
        <Button
          variant="ghost"
          size="sm"
          onClick={onAcknowledge}
          disabled={isAcknowledging}
        >
          {isAcknowledging ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            'Acknowledge'
          )}
        </Button>
      </TableCell>
    </TableRow>
  );
}

/**
 * All Alerts Overview Component
 */
function AlertsOverview() {
  const { data: alerts, isLoading, error, refetch, isRefetching } = useSearchAlerts();
  const { data: history, isLoading: historyLoading } = useSearchAlertHistory();
  const { mutate: acknowledge, isPending: isAcknowledging } = useAcknowledgeAlert();
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const handleAcknowledge = (id: string) => {
    setAcknowledgingId(id);
    acknowledge(id, {
      onSettled: () => setAcknowledgingId(null),
    });
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Failed to Load Alerts</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span>{error.message}</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Active Alerts Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary/10">
                <Bell className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {isLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    alerts?.length || 0
                  )}
                </div>
                <p className="text-sm text-muted-foreground">Active Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-green-500/10">
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {historyLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    history?.items.filter((a) => a.status === 'sent').length || 0
                  )}
                </div>
                <p className="text-sm text-muted-foreground">Sent Today</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-destructive/10">
                <XCircle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {historyLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    history?.items.filter((a) => a.status === 'failed').length || 0
                  )}
                </div>
                <p className="text-sm text-muted-foreground">Failed Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Alert History</CardTitle>
              <CardDescription>Recent alert notifications</CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refetch()}
              disabled={isRefetching}
            >
              <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !history?.items.length ? (
            <div className="text-center py-12">
              <Bell className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No alert history yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Channel</TableHead>
                  <TableHead>Triggered</TableHead>
                  <TableHead>Results</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Error</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.items.map((alert) => (
                  <AlertHistoryRow
                    key={alert.id}
                    alert={alert}
                    onAcknowledge={() => handleAcknowledge(alert.id)}
                    isAcknowledging={acknowledgingId === alert.id}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Single Search Alert Configuration
 */
function SingleSearchAlertConfig({ searchId }: { searchId: string }) {
  const navigate = useNavigate();
  const { data: search, isLoading, error } = useSavedSearch(searchId);
  const { data: history, isLoading: historyLoading } = useSearchAlertHistory(searchId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !search) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Search Not Found</AlertTitle>
        <AlertDescription>
          The saved search could not be found.
          <Button
            variant="link"
            className="p-0 h-auto ml-2"
            onClick={() => navigate('/search/saved')}
          >
            Go back to saved searches
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button and header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-xl font-semibold">{search.name}</h2>
          <p className="text-sm text-muted-foreground">
            Configure alerts for this saved search
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Configuration Panel */}
        <SearchAlertConfigPanel
          savedSearchId={searchId}
          savedSearchName={search.name}
        />

        {/* Alert History for this search */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Alert History</CardTitle>
            <CardDescription>
              Recent alerts for this search
            </CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : !history?.items.length ? (
              <div className="text-center py-8">
                <Bell className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No alerts sent for this search yet
                </p>
              </div>
            ) : (
              <ScrollArea className="h-64">
                <div className="space-y-3">
                  {history.items.map((alert) => {
                    const ChannelIcon = CHANNEL_ICONS[alert.channel];
                    return (
                      <div
                        key={alert.id}
                        className="flex items-center justify-between p-3 rounded-lg border"
                      >
                        <div className="flex items-center gap-3">
                          <ChannelIcon className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-sm font-medium">
                              {alert.result_count} new results
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {formatDistanceToNow(parseISO(alert.triggered_at), {
                                addSuffix: true,
                              })}
                            </div>
                          </div>
                        </div>
                        {alert.status === 'sent' ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : alert.status === 'failed' ? (
                          <XCircle className="h-4 w-4 text-destructive" />
                        ) : (
                          <Clock className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function SearchAlertsPage() {
  const { searchId } = useParams<{ searchId?: string }>();
  const navigate = useNavigate();

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" />
            Search Alerts
          </h1>
          <p className="text-muted-foreground mt-1">
            {searchId
              ? 'Configure alert settings for this search'
              : 'Manage all your search alerts'}
          </p>
        </div>
        {!searchId && (
          <Button variant="outline" onClick={() => navigate('/search/saved')}>
            <Search className="h-4 w-4 mr-2" />
            View Saved Searches
          </Button>
        )}
      </div>

      {/* Content */}
      {searchId ? (
        <SingleSearchAlertConfig searchId={searchId} />
      ) : (
        <AlertsOverview />
      )}
    </div>
  );
}
