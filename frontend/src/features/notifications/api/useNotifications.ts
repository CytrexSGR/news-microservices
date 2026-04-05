/**
 * useNotifications Hook
 *
 * Fetches user notifications with optional filters.
 * Provides automatic polling for real-time updates.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getNotifications,
  getNotification,
  markNotificationAsRead,
  markAllNotificationsAsRead,
} from './notificationApi';
import type { NotificationsListParams, Notification } from '../types';

export const notificationQueryKeys = {
  all: ['notifications'] as const,
  list: (params?: NotificationsListParams) => [...notificationQueryKeys.all, 'list', params] as const,
  detail: (id: number) => [...notificationQueryKeys.all, 'detail', id] as const,
  unreadCount: () => [...notificationQueryKeys.all, 'unread-count'] as const,
};

export interface UseNotificationsOptions {
  params?: NotificationsListParams;
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * Fetch notifications list with optional filters
 */
export function useNotifications(options?: UseNotificationsOptions) {
  const { params, enabled = true, refetchInterval } = options || {};

  return useQuery<Notification[]>({
    queryKey: notificationQueryKeys.list(params),
    queryFn: () => getNotifications(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled,
    refetchInterval,
  });
}

/**
 * Fetch a single notification by ID
 */
export function useNotification(id: number, enabled = true) {
  return useQuery<Notification>({
    queryKey: notificationQueryKeys.detail(id),
    queryFn: () => getNotification(id),
    staleTime: 60 * 1000, // 1 minute
    enabled: enabled && !!id,
  });
}

/**
 * Get unread notification count
 * Uses the notifications list and filters client-side
 *
 * NOTE: notification-service (8105) was archived and replaced by n8n workflows.
 * Polling is disabled until a replacement is implemented.
 */
export function useUnreadNotificationCount(_refetchInterval = 30000) {
  // DISABLED: notification-service was archived (2025-12)
  // Return static empty data to prevent console errors
  // TODO: Re-enable when n8n-based notification system is ready
  const isServiceAvailable = false;

  const { data: notifications, isLoading } = useNotifications({
    params: { limit: 100 },
    enabled: isServiceAvailable, // Disabled - service archived
    refetchInterval: isServiceAvailable ? _refetchInterval : undefined,
  });

  // For now, count "pending" status as unread since backend doesn't track read status
  // This should be updated when proper read status is implemented
  const unreadCount = notifications?.filter(
    (n) => n.status === 'pending' || n.status === 'sent'
  ).length || 0;

  return {
    unreadCount,
    isLoading: isServiceAvailable ? isLoading : false,
    notifications: notifications || [],
  };
}

/**
 * Mark a notification as read
 */
export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => markNotificationAsRead(id),
    onSuccess: (updatedNotification) => {
      // Update the notification in cache
      queryClient.setQueryData<Notification>(
        notificationQueryKeys.detail(updatedNotification.id),
        updatedNotification
      );

      // Invalidate list queries to refresh
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}

/**
 * Mark all notifications as read
 */
export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => markAllNotificationsAsRead(),
    onSuccess: () => {
      // Invalidate all notification queries
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}
