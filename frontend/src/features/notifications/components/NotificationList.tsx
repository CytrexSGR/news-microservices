/**
 * NotificationList Component
 *
 * Displays a list of notifications with loading and empty states.
 */

import { Bell, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { NotificationItem } from './NotificationItem';
import type { Notification } from '../types';

interface NotificationListProps {
  notifications: Notification[] | undefined;
  isLoading: boolean;
  isRefetching?: boolean;
  onRefresh?: () => void;
  onMarkAsRead?: (id: number) => void;
  onMarkAllAsRead?: () => void;
  compact?: boolean;
  maxItems?: number;
  emptyMessage?: string;
}

export function NotificationList({
  notifications,
  isLoading,
  isRefetching,
  onRefresh,
  onMarkAsRead,
  onMarkAllAsRead,
  compact = false,
  maxItems,
  emptyMessage = 'No notifications',
}: NotificationListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: compact ? 3 : 5 }).map((_, i) => (
          <div key={i} className={compact ? 'px-3 py-2' : 'p-4'}>
            <div className="flex items-start gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
                {!compact && <Skeleton className="h-3 w-1/4" />}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const displayNotifications = maxItems
    ? notifications?.slice(0, maxItems)
    : notifications;

  if (!displayNotifications || displayNotifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Bell className="h-12 w-12 text-muted-foreground/50 mb-3" />
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            className="mt-3"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        )}
      </div>
    );
  }

  return (
    <div>
      {!compact && onMarkAllAsRead && displayNotifications.length > 0 && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-border">
          <span className="text-sm text-muted-foreground">
            {displayNotifications.length} notification{displayNotifications.length !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-2">
            {onRefresh && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRefresh}
                disabled={isRefetching}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isRefetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onMarkAllAsRead}
            >
              Mark all as read
            </Button>
          </div>
        </div>
      )}

      <div className={compact ? '' : 'space-y-2 p-4'}>
        {displayNotifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onMarkAsRead={onMarkAsRead}
            compact={compact}
          />
        ))}
      </div>

      {maxItems && notifications && notifications.length > maxItems && (
        <div className="px-3 py-2 text-center border-t border-border">
          <span className="text-xs text-muted-foreground">
            +{notifications.length - maxItems} more
          </span>
        </div>
      )}
    </div>
  );
}
