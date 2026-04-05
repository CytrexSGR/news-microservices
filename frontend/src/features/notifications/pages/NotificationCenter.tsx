/**
 * NotificationCenter Page
 *
 * Main page for viewing and managing user notifications.
 * Includes list view, filters, and bulk actions.
 */

import { useState } from 'react';
import { Bell, Settings, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { NotificationList } from '../components/center/NotificationList';
import { NotificationFilter } from '../components/center/NotificationFilter';
import { NotificationActions } from '../components/center/NotificationActions';
import { useNotificationHistory, useUnreadNotificationCount } from '../api';
import type { NotificationStatus, NotificationChannel } from '../types';

export function NotificationCenter() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<NotificationStatus | 'all'>('all');
  const [channel, setChannel] = useState<NotificationChannel | 'all'>('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data: unreadCount } = useUnreadNotificationCount();
  const { refetch, isRefetching } = useNotificationHistory({
    page,
    limit: 20,
    status: status === 'all' ? undefined : status,
    channel: channel === 'all' ? undefined : channel,
  });

  const handleFilterChange = (filters: {
    status?: NotificationStatus | 'all';
    channel?: NotificationChannel | 'all';
  }) => {
    if (filters.status !== undefined) setStatus(filters.status);
    if (filters.channel !== undefined) setChannel(filters.channel);
    setPage(1);
    setSelectedIds([]);
  };

  const handleSelectChange = (ids: string[]) => {
    setSelectedIds(ids);
  };

  const handleBulkActionComplete = () => {
    setSelectedIds([]);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" />
            Notifications
            {unreadCount && unreadCount > 0 && (
              <span className="bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded-full">
                {unreadCount} unread
              </span>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage your notification history
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" asChild>
            <a href="/notifications/preferences">
              <Settings className="h-4 w-4 mr-2" />
              Preferences
            </a>
          </Button>
        </div>
      </div>

      {/* Main content */}
      <Tabs defaultValue="all" className="space-y-4">
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <TabsList>
            <TabsTrigger value="all" onClick={() => handleFilterChange({ status: 'all' })}>
              All
            </TabsTrigger>
            <TabsTrigger value="unread" onClick={() => handleFilterChange({ status: 'unread' })}>
              Unread
              {unreadCount && unreadCount > 0 && (
                <span className="ml-1.5 bg-primary/20 text-xs px-1.5 py-0.5 rounded">
                  {unreadCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="read" onClick={() => handleFilterChange({ status: 'read' })}>
              Read
            </TabsTrigger>
            <TabsTrigger value="archived" onClick={() => handleFilterChange({ status: 'archived' })}>
              Archived
            </TabsTrigger>
          </TabsList>

          <NotificationFilter
            status={status}
            channel={channel}
            onFilterChange={handleFilterChange}
          />
        </div>

        {/* Bulk actions bar */}
        {selectedIds.length > 0 && (
          <NotificationActions
            selectedIds={selectedIds}
            onActionComplete={handleBulkActionComplete}
          />
        )}

        {/* Notification list - same for all tabs, filtered via API */}
        <TabsContent value="all" className="m-0">
          <NotificationList
            page={page}
            status={status === 'all' ? undefined : status}
            channel={channel === 'all' ? undefined : channel}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onPageChange={setPage}
          />
        </TabsContent>
        <TabsContent value="unread" className="m-0">
          <NotificationList
            page={page}
            status="unread"
            channel={channel === 'all' ? undefined : channel}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onPageChange={setPage}
          />
        </TabsContent>
        <TabsContent value="read" className="m-0">
          <NotificationList
            page={page}
            status="read"
            channel={channel === 'all' ? undefined : channel}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onPageChange={setPage}
          />
        </TabsContent>
        <TabsContent value="archived" className="m-0">
          <NotificationList
            page={page}
            status="archived"
            channel={channel === 'all' ? undefined : channel}
            selectedIds={selectedIds}
            onSelectChange={handleSelectChange}
            onPageChange={setPage}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
