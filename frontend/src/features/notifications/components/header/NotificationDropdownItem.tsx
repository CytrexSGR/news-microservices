/**
 * NotificationDropdownItem Component
 *
 * Single notification item in the dropdown list.
 */

import { formatDistanceToNow } from 'date-fns';
import { Mail, Bell, Webhook, Smartphone, AlertCircle, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useMarkNotificationAsRead } from '../../api';
import type { Notification, NotificationChannel, NotificationStatus } from '../../types';

interface NotificationDropdownItemProps {
  notification: Notification;
  onClose: () => void;
}

export function NotificationDropdownItem({
  notification,
  onClose,
}: NotificationDropdownItemProps) {
  const markAsRead = useMarkNotificationAsRead();

  const isUnread = notification.status === 'pending' || notification.status === 'sent';
  const isFailed = notification.status === 'failed';

  const handleClick = () => {
    if (isUnread) {
      markAsRead.mutate(notification.id);
    }
    onClose();
  };

  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
    addSuffix: true,
  });

  return (
    <Link
      to={`/notifications?id=${notification.id}`}
      onClick={handleClick}
      className={cn(
        'block px-4 py-3 hover:bg-muted/50 transition-colors',
        isUnread && 'bg-primary/5'
      )}
    >
      <div className="flex gap-3">
        {/* Icon */}
        <div
          className={cn(
            'flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center',
            isFailed ? 'bg-destructive/10 text-destructive' : 'bg-primary/10 text-primary'
          )}
        >
          <ChannelIcon channel={notification.channel} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p
              className={cn(
                'text-sm font-medium truncate',
                isUnread && 'text-foreground',
                !isUnread && 'text-muted-foreground'
              )}
            >
              {notification.subject || 'Notification'}
            </p>
            {isUnread && (
              <span className="flex-shrink-0 h-2 w-2 rounded-full bg-primary" />
            )}
          </div>

          <p className="text-sm text-muted-foreground line-clamp-2 mt-0.5">
            {notification.content}
          </p>

          <div className="flex items-center gap-2 mt-1.5">
            <StatusIndicator status={notification.status} />
            <span className="text-xs text-muted-foreground">{timeAgo}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}

/**
 * Channel icon component
 */
function ChannelIcon({ channel }: { channel: NotificationChannel }) {
  switch (channel) {
    case 'email':
      return <Mail className="h-5 w-5" />;
    case 'webhook':
      return <Webhook className="h-5 w-5" />;
    case 'push':
      return <Smartphone className="h-5 w-5" />;
    default:
      return <Bell className="h-5 w-5" />;
  }
}

/**
 * Status indicator component
 */
function StatusIndicator({ status }: { status: NotificationStatus }) {
  switch (status) {
    case 'sent':
      return (
        <span className="flex items-center gap-1 text-xs text-green-600">
          <CheckCircle className="h-3 w-3" />
          Sent
        </span>
      );
    case 'failed':
      return (
        <span className="flex items-center gap-1 text-xs text-destructive">
          <AlertCircle className="h-3 w-3" />
          Failed
        </span>
      );
    case 'pending':
      return (
        <span className="flex items-center gap-1 text-xs text-amber-600">
          <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
          Pending
        </span>
      );
    case 'retrying':
      return (
        <span className="flex items-center gap-1 text-xs text-amber-600">
          <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
          Retrying
        </span>
      );
    default:
      return null;
  }
}
