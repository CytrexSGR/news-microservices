/**
 * NotificationList Component
 *
 * Paginated list of notifications with virtualization support.
 */

import { useState, useCallback } from 'react';
import { Loader2, RefreshCw, InboxIcon } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';
import { useNotifications, useBulkMarkAsRead } from '../../api';
import type { Notification, NotificationFilterOptions } from '../../types';
import { NotificationItem } from './NotificationItem';
import { NotificationFilter } from './NotificationFilter';
import { NotificationActions } from './NotificationActions';

interface NotificationListProps {
  className?: string;
}

export function NotificationList({ className }: NotificationListProps) {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState<NotificationFilterOptions>({
    status: 'all',
    channel: 'all',
    dateRange: 'all',
  });

  const { data: notifications, isLoading, error, refetch, isRefetching } = useNotifications({
    params: {
      status: filters.status === 'all' ? undefined : filters.status,
      channel: filters.channel === 'all' ? undefined : filters.channel,
    },
    refetchInterval: 30000,
  });

  const bulkMarkAsRead = useBulkMarkAsRead();

  const handleSelect = useCallback((id: number, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (!notifications) return;
    if (selectedIds.size === notifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(notifications.map((n) => n.id)));
    }
  }, [notifications, selectedIds.size]);

  const handleBulkAction = useCallback(
    async (action: 'read' | 'archive' | 'delete') => {
      const ids = Array.from(selectedIds);
      if (ids.length === 0) return;

      if (action === 'read') {
        await bulkMarkAsRead.mutateAsync(ids);
      }
      // TODO: Handle archive and delete

      setSelectedIds(new Set());
    },
    [selectedIds, bulkMarkAsRead]
  );

  const handleFilterChange = useCallback((newFilters: NotificationFilterOptions) => {
    setFilters(newFilters);
    setSelectedIds(new Set());
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-destructive mb-4">Failed to load notifications</p>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <NotificationFilter value={filters} onChange={handleFilterChange} />
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            {isRefetching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            <span className="ml-2 hidden sm:inline">Refresh</span>
          </Button>
        </div>
      </div>

      {/* Bulk actions */}
      {selectedIds.size > 0 && (
        <NotificationActions
          selectedCount={selectedIds.size}
          totalCount={notifications?.length ?? 0}
          onSelectAll={handleSelectAll}
          onAction={handleBulkAction}
          isLoading={bulkMarkAsRead.isPending}
        />
      )}

      {/* List */}
      {isLoading && (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="p-4 border rounded-lg">
              <div className="flex gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-3 w-1/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoading && notifications && notifications.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <InboxIcon className="h-16 w-16 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No notifications</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            {filters.status !== 'all' || filters.channel !== 'all'
              ? 'No notifications match your current filters. Try adjusting the filters.'
              : "You don't have any notifications yet. They'll appear here when you receive them."}
          </p>
        </div>
      )}

      {!isLoading && notifications && notifications.length > 0 && (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              selected={selectedIds.has(notification.id)}
              onSelect={(selected) => handleSelect(notification.id, selected)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
