/**
 * FailedNotificationsList Component
 *
 * Shows DLQ items with retry and purge actions.
 */

import { useState } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Trash2,
  ChevronDown,
  ChevronUp,
  Loader2,
  Mail,
  Webhook,
  Smartphone,
  Search,
  MoreHorizontal,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils';
import { useDLQNotifications, useRetryDLQ, usePurgeDLQ } from '../../api';
import type { NotificationChannel, DLQNotification } from '../../types';

interface FailedNotificationsListProps {
  className?: string;
}

interface ExpandedRowProps {
  notification: DLQNotification;
}

function ExpandedRow({ notification }: ExpandedRowProps) {
  return (
    <TableRow>
      <TableCell colSpan={6} className="bg-muted/30">
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium mb-1">Recipient</h4>
              <p className="text-sm text-muted-foreground font-mono">
                {notification.recipient}
              </p>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-1">Original Send Time</h4>
              <p className="text-sm text-muted-foreground">
                {new Date(notification.original_timestamp).toLocaleString('de-DE')}
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-1">Content Preview</h4>
            <pre className="text-xs bg-background p-3 rounded border overflow-x-auto">
              {notification.content_preview || '(No preview available)'}
            </pre>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-1">Error History</h4>
            <div className="space-y-2">
              {notification.error_history.map((error, idx) => (
                <div
                  key={idx}
                  className="text-xs bg-destructive/10 text-destructive p-2 rounded font-mono"
                >
                  <span className="text-muted-foreground">
                    [{new Date(error.timestamp).toLocaleString('de-DE')}]
                  </span>{' '}
                  {error.message}
                </div>
              ))}
            </div>
          </div>
        </div>
      </TableCell>
    </TableRow>
  );
}

export function FailedNotificationsList({ className }: FailedNotificationsListProps) {
  const { data, isLoading, error, refetch } = useDLQNotifications();
  const retryDLQ = useRetryDLQ();
  const purgeDLQ = usePurgeDLQ();

  const [searchQuery, setSearchQuery] = useState('');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const notifications = data?.notifications ?? [];

  // Filter notifications
  const filteredNotifications = notifications.filter(
    (n) =>
      n.recipient.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.last_error.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredNotifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredNotifications.map((n) => n.id)));
    }
  };

  const handleRetry = async (id: string) => {
    await retryDLQ.mutateAsync({ notification_id: id });
  };

  const handleRetrySelected = async () => {
    for (const id of selectedIds) {
      await retryDLQ.mutateAsync({ notification_id: id });
    }
    setSelectedIds(new Set());
  };

  const handlePurge = async (id: string) => {
    await purgeDLQ.mutateAsync({ notification_id: id });
  };

  const handlePurgeSelected = async () => {
    for (const id of selectedIds) {
      await purgeDLQ.mutateAsync({ notification_id: id });
    }
    setSelectedIds(new Set());
  };

  const getChannelIcon = (channel: NotificationChannel) => {
    switch (channel) {
      case 'email':
        return <Mail className="h-4 w-4" />;
      case 'webhook':
        return <Webhook className="h-4 w-4" />;
      case 'push':
        return <Smartphone className="h-4 w-4" />;
      default:
        return null;
    }
  };

  if (error) {
    return (
      <Card className={cn('border-destructive', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Failed Notifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8">
            <p className="text-destructive mb-4">Failed to load DLQ notifications</p>
            <Button variant="outline" onClick={() => refetch()}>
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
        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Failed Notifications (DLQ)
            </CardTitle>
            <CardDescription>
              Notifications that failed permanently after all retry attempts
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Search and bulk actions */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by recipient or error..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {selectedIds.size > 0 && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetrySelected}
                disabled={retryDLQ.isPending}
              >
                {retryDLQ.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Retry ({selectedIds.size})
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Purge ({selectedIds.size})
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Purge Selected Notifications?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete {selectedIds.size} failed notification(s).
                      This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handlePurgeSelected}
                      className="bg-destructive hover:bg-destructive/90"
                    >
                      Purge
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          )}
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium mb-1">
              {searchQuery ? 'No matching notifications' : 'No failed notifications'}
            </h3>
            <p className="text-sm text-muted-foreground">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'All notifications are being delivered successfully'}
            </p>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === filteredNotifications.length}
                      onChange={toggleSelectAll}
                      className="rounded border-input"
                    />
                  </TableHead>
                  <TableHead className="w-12"></TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Recipient</TableHead>
                  <TableHead>Last Error</TableHead>
                  <TableHead>Attempts</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredNotifications.map((notification) => (
                  <>
                    <TableRow key={notification.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(notification.id)}
                          onChange={() => toggleSelected(notification.id)}
                          className="rounded border-input"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleExpanded(notification.id)}
                        >
                          {expandedIds.has(notification.id) ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="gap-1">
                          {getChannelIcon(notification.channel)}
                          <span className="capitalize">{notification.channel}</span>
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm max-w-[200px] truncate">
                        {notification.recipient}
                      </TableCell>
                      <TableCell className="max-w-[250px]">
                        <span className="text-sm text-destructive truncate block">
                          {notification.last_error}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{notification.retry_count}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleRetry(notification.id)}>
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Retry
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handlePurge(notification.id)}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Purge
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                    {expandedIds.has(notification.id) && (
                      <ExpandedRow notification={notification} />
                    )}
                  </>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Summary */}
        {!isLoading && filteredNotifications.length > 0 && (
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredNotifications.length} of {notifications.length} failed notifications
          </div>
        )}
      </CardContent>
    </Card>
  );
}
