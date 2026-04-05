/**
 * NotificationItem Component
 *
 * Displays a single notification with status indicator,
 * timestamp, and action buttons.
 */

import { Mail, Webhook, Bell, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Notification, NotificationChannel, NotificationStatus } from '../types';

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead?: (id: number) => void;
  compact?: boolean;
}

const channelIcons: Record<NotificationChannel, React.ReactNode> = {
  email: <Mail className="h-4 w-4" />,
  webhook: <Webhook className="h-4 w-4" />,
  rabbitmq: <Bell className="h-4 w-4" />,
  push: <Bell className="h-4 w-4" />,
};

const statusIcons: Record<NotificationStatus, React.ReactNode> = {
  sent: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  pending: <Clock className="h-4 w-4 text-yellow-500" />,
  retrying: <AlertCircle className="h-4 w-4 text-orange-500" />,
};

const statusLabels: Record<NotificationStatus, string> = {
  sent: 'Sent',
  failed: 'Failed',
  pending: 'Pending',
  retrying: 'Retrying',
};

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function NotificationItem({
  notification,
  onMarkAsRead,
  compact = false,
}: NotificationItemProps) {
  const { id, channel, status, subject, content, created_at, error_message } = notification;

  const handleClick = () => {
    if (onMarkAsRead && (status === 'pending' || status === 'sent')) {
      onMarkAsRead(id);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className={cn(
          'w-full text-left px-3 py-2 hover:bg-muted/50 transition-colors',
          'border-b border-border last:border-b-0',
          status === 'pending' && 'bg-primary/5'
        )}
      >
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-muted-foreground">
            {channelIcons[channel]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {subject || 'Notification'}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {content.substring(0, 60)}
              {content.length > 60 && '...'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {formatRelativeTime(created_at)}
            </p>
          </div>
          <div className="flex-shrink-0">
            {statusIcons[status]}
          </div>
        </div>
      </button>
    );
  }

  return (
    <div
      className={cn(
        'p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors',
        status === 'pending' && 'bg-primary/5 border-primary/20'
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 p-2 bg-muted rounded-full text-muted-foreground">
          {channelIcons[channel]}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-medium text-foreground">
              {subject || 'Notification'}
            </h4>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              {statusIcons[status]}
              {statusLabels[status]}
            </span>
          </div>

          <p className="text-sm text-muted-foreground line-clamp-2">
            {content}
          </p>

          {error_message && status === 'failed' && (
            <p className="mt-2 text-xs text-red-500 bg-red-500/10 px-2 py-1 rounded">
              Error: {error_message}
            </p>
          )}

          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(created_at)}
            </span>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground capitalize">
                via {channel}
              </span>
              {onMarkAsRead && status !== 'failed' && (
                <button
                  onClick={handleClick}
                  className="text-xs text-primary hover:underline"
                >
                  Mark as read
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
