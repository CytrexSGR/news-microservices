/**
 * NotificationDropdown Component
 *
 * Quick-view dropdown showing recent notifications.
 * Displays last 5 notifications with actions.
 */

import { Bell, Settings, CheckCheck, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';
import { useRecentNotifications, useMarkAllNotificationsAsRead } from '../../api';
import { NotificationDropdownItem } from './NotificationDropdownItem';

interface NotificationDropdownProps {
  onClose: () => void;
  onViewAll: () => void;
}

export function NotificationDropdown({
  onClose,
  onViewAll,
}: NotificationDropdownProps) {
  const { data, isLoading, error } = useRecentNotifications(5);
  const markAllAsRead = useMarkAllNotificationsAsRead();

  const notifications = data?.notifications ?? [];
  const hasNotifications = notifications.length > 0;
  const hasMore = data?.has_more ?? false;

  const handleMarkAllRead = () => {
    markAllAsRead.mutate();
  };

  return (
    <div
      className={cn(
        'absolute right-0 top-full mt-2 w-80 sm:w-96',
        'bg-popover border rounded-lg shadow-lg z-50',
        'animate-in fade-in-0 zoom-in-95 slide-in-from-top-2'
      )}
      role="dialog"
      aria-label="Notifications"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4" />
          <h3 className="font-semibold">Notifications</h3>
        </div>
        <div className="flex items-center gap-1">
          {hasNotifications && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMarkAllRead}
              disabled={markAllAsRead.isPending}
              title="Mark all as read"
            >
              <CheckCheck className="h-4 w-4" />
            </Button>
          )}
          <Link to="/settings/notifications" onClick={onClose}>
            <Button variant="ghost" size="sm" title="Notification settings">
              <Settings className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="max-h-[400px] overflow-y-auto">
        {isLoading && (
          <div className="p-4 space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Failed to load notifications
          </div>
        )}

        {!isLoading && !error && !hasNotifications && (
          <div className="p-8 text-center">
            <Bell className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">
              No notifications yet
            </p>
          </div>
        )}

        {!isLoading && !error && hasNotifications && (
          <div className="divide-y">
            {notifications.map((notification) => (
              <NotificationDropdownItem
                key={notification.id}
                notification={notification}
                onClose={onClose}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {hasNotifications && (
        <div className="border-t px-4 py-3">
          <Button
            variant="ghost"
            className="w-full justify-center gap-2"
            onClick={onViewAll}
          >
            View all notifications
            <ExternalLink className="h-4 w-4" />
          </Button>
          {hasMore && (
            <p className="text-xs text-center text-muted-foreground mt-1">
              And more...
            </p>
          )}
        </div>
      )}
    </div>
  );
}
