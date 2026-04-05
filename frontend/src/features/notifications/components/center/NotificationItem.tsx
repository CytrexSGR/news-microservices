/**
 * NotificationItem Component
 *
 * Single notification item with actions.
 */

import { formatDistanceToNow, format } from 'date-fns';
import {
  Mail,
  Bell,
  Webhook,
  Smartphone,
  AlertCircle,
  CheckCircle,
  Clock,
  MoreVertical,
  Eye,
  Archive,
  Trash2,
  RotateCcw,
} from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { cn } from '@/lib/utils';
import { useMarkNotificationAsRead, useArchiveNotification } from '../../api';
import type { Notification, NotificationChannel, NotificationStatus } from '../../types';

interface NotificationItemProps {
  notification: Notification;
  selected?: boolean;
  onSelect?: (selected: boolean) => void;
}

export function NotificationItem({
  notification,
  selected = false,
  onSelect,
}: NotificationItemProps) {
  const [expanded, setExpanded] = useState(false);
  const markAsRead = useMarkNotificationAsRead();
  const archive = useArchiveNotification();

  const isUnread = notification.status === 'pending' || notification.status === 'sent';
  const isFailed = notification.status === 'failed';

  const handleMarkAsRead = () => {
    if (isUnread) {
      markAsRead.mutate(notification.id);
    }
  };

  const handleArchive = () => {
    archive.mutate(notification.id);
  };

  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
    addSuffix: true,
  });

  const fullDate = format(new Date(notification.created_at), 'PPpp');

  return (
    <div
      className={cn(
        'border rounded-lg transition-all',
        isUnread && 'border-primary/30 bg-primary/5',
        selected && 'ring-2 ring-primary',
        'hover:shadow-sm'
      )}
    >
      <div className="p-4">
        <div className="flex items-start gap-4">
          {/* Checkbox */}
          {onSelect && (
            <input
              type="checkbox"
              checked={selected}
              onChange={(e) => onSelect(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
          )}

          {/* Icon */}
          <div
            className={cn(
              'flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center',
              isFailed
                ? 'bg-destructive/10 text-destructive'
                : 'bg-primary/10 text-primary'
            )}
          >
            <ChannelIcon channel={notification.channel} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4
                    className={cn(
                      'font-medium',
                      isUnread ? 'text-foreground' : 'text-muted-foreground'
                    )}
                  >
                    {notification.subject || 'Notification'}
                  </h4>
                  {isUnread && (
                    <span className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </div>

                <p
                  className={cn(
                    'text-sm text-muted-foreground mt-1',
                    !expanded && 'line-clamp-2'
                  )}
                  onClick={() => setExpanded(!expanded)}
                >
                  {notification.content}
                </p>

                {notification.content.length > 150 && (
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-xs text-primary hover:underline mt-1"
                  >
                    {expanded ? 'Show less' : 'Show more'}
                  </button>
                )}
              </div>

              {/* Actions */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                    <span className="sr-only">Actions</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {isUnread && (
                    <DropdownMenuItem onClick={handleMarkAsRead}>
                      <Eye className="h-4 w-4 mr-2" />
                      Mark as read
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleArchive}>
                    <Archive className="h-4 w-4 mr-2" />
                    Archive
                  </DropdownMenuItem>
                  {isFailed && (
                    <DropdownMenuItem>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Retry
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-destructive">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-3 mt-3 flex-wrap">
              <StatusBadge status={notification.status} />
              <ChannelBadge channel={notification.channel} />
              <span
                className="text-xs text-muted-foreground flex items-center gap-1"
                title={fullDate}
              >
                <Clock className="h-3 w-3" />
                {timeAgo}
              </span>
            </div>

            {/* Error message */}
            {notification.error_message && (
              <div className="mt-3 p-2 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 inline-block mr-1" />
                {notification.error_message}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
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
 * Status badge component
 */
function StatusBadge({ status }: { status: NotificationStatus }) {
  switch (status) {
    case 'sent':
      return (
        <Badge variant="default" className="bg-green-100 text-green-700">
          <CheckCircle className="h-3 w-3 mr-1" />
          Sent
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="destructive">
          <AlertCircle className="h-3 w-3 mr-1" />
          Failed
        </Badge>
      );
    case 'pending':
      return (
        <Badge variant="secondary" className="bg-amber-100 text-amber-700">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      );
    case 'retrying':
      return (
        <Badge variant="secondary" className="bg-amber-100 text-amber-700">
          <RotateCcw className="h-3 w-3 mr-1 animate-spin" />
          Retrying
        </Badge>
      );
    case 'read':
      return (
        <Badge variant="outline">
          <Eye className="h-3 w-3 mr-1" />
          Read
        </Badge>
      );
    case 'archived':
      return (
        <Badge variant="outline">
          <Archive className="h-3 w-3 mr-1" />
          Archived
        </Badge>
      );
    default:
      return null;
  }
}

/**
 * Channel badge component
 */
function ChannelBadge({ channel }: { channel: NotificationChannel }) {
  return (
    <Badge variant="outline" className="text-xs">
      <ChannelIcon channel={channel} />
      <span className="ml-1 capitalize">{channel}</span>
    </Badge>
  );
}
