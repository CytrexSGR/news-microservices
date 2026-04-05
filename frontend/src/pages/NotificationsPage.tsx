/**
 * NotificationsPage
 *
 * Full notifications page with:
 * - Notification list with filters (all/unread)
 * - Mark as read actions
 * - Preferences tab
 */

import { useState } from 'react';
import { Bell, Settings, Filter } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import {
  NotificationList,
  NotificationPreferences,
  useNotifications,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
} from '@/features/notifications';
import type { NotificationStatus, NotificationChannel } from '@/features/notifications';

type FilterStatus = 'all' | NotificationStatus;
type FilterChannel = 'all' | NotificationChannel;

export function NotificationsPage() {
  const [activeTab, setActiveTab] = useState<'notifications' | 'preferences'>('notifications');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [channelFilter, setChannelFilter] = useState<FilterChannel>('all');

  const {
    data: notifications,
    isLoading,
    isRefetching,
    refetch,
  } = useNotifications({
    params: {
      status: statusFilter === 'all' ? undefined : statusFilter,
      channel: channelFilter === 'all' ? undefined : channelFilter,
      limit: 100,
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const markAsReadMutation = useMarkNotificationAsRead();
  const markAllAsReadMutation = useMarkAllNotificationsAsRead();

  const handleMarkAsRead = (id: number) => {
    markAsReadMutation.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const handleRefresh = () => {
    refetch();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Notifications</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your notifications and preferences
          </p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="preferences" className="gap-2">
            <Settings className="h-4 w-4" />
            Preferences
          </TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="mt-6">
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-4 mb-6 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Status:</label>
              <Select
                value={statusFilter}
                onValueChange={(value) => setStatusFilter(value as FilterStatus)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="retrying">Retrying</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Channel:</label>
              <Select
                value={channelFilter}
                onValueChange={(value) => setChannelFilter(value as FilterChannel)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                  <SelectItem value="webhook">Webhook</SelectItem>
                  <SelectItem value="push">Push</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1" />

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setStatusFilter('all');
                setChannelFilter('all');
              }}
            >
              Clear Filters
            </Button>
          </div>

          {/* Notification List */}
          <div className="bg-card border border-border rounded-lg">
            <NotificationList
              notifications={notifications}
              isLoading={isLoading}
              isRefetching={isRefetching}
              onRefresh={handleRefresh}
              onMarkAsRead={handleMarkAsRead}
              onMarkAllAsRead={handleMarkAllAsRead}
              emptyMessage={
                statusFilter !== 'all' || channelFilter !== 'all'
                  ? 'No notifications match your filters'
                  : 'No notifications yet'
              }
            />
          </div>
        </TabsContent>

        <TabsContent value="preferences" className="mt-6">
          <div className="max-w-2xl">
            <NotificationPreferences />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
