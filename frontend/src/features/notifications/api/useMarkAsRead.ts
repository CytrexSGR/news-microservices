/**
 * useMarkAsRead Hook
 *
 * Mutation hook to mark notifications as read.
 * Supports single and bulk operations.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { Notification } from '../types';

interface MarkAsReadResponse {
  success: boolean;
  notification_id: number;
  read_at: string;
}

interface BulkMarkAsReadResponse {
  success: boolean;
  count: number;
  notification_ids: number[];
}

/**
 * Hook to mark a single notification as read
 *
 * @example
 * ```tsx
 * const markAsRead = useMarkAsRead();
 * markAsRead.mutate(123);
 * ```
 */
export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation<MarkAsReadResponse, Error, number>({
    mutationFn: async (notificationId: number) => {
      const response = await mcpClient.callTool<MarkAsReadResponse>(
        'mark_notification_read',
        { notification_id: notificationId }
      );
      return response;
    },
    onSuccess: (data, notificationId) => {
      // Update the specific notification in cache
      queryClient.setQueryData<Notification>(
        ['notifications', 'detail', notificationId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            read_at: data.read_at,
            status: 'read' as const,
          };
        }
      );

      // Invalidate list queries to refresh counts
      queryClient.invalidateQueries({ queryKey: ['notifications', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'recent'] });
    },
  });
}

/**
 * Hook to mark multiple notifications as read
 *
 * @example
 * ```tsx
 * const markAllAsRead = useBulkMarkAsRead();
 * markAllAsRead.mutate([1, 2, 3]);
 * ```
 */
export function useBulkMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation<BulkMarkAsReadResponse, Error, number[]>({
    mutationFn: async (notificationIds: number[]) => {
      // Call mark_read for each notification
      // In a real implementation, this would be a bulk endpoint
      const results = await Promise.all(
        notificationIds.map((id) =>
          mcpClient.callTool<MarkAsReadResponse>('mark_notification_read', {
            notification_id: id,
          })
        )
      );

      return {
        success: results.every((r) => r.success),
        count: results.filter((r) => r.success).length,
        notification_ids: notificationIds,
      };
    },
    onSuccess: () => {
      // Invalidate all notification queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllAsRead() {
  const queryClient = useQueryClient();

  return useMutation<BulkMarkAsReadResponse, Error, void>({
    mutationFn: async () => {
      // This would need a dedicated endpoint
      // For now, we fetch unread and mark each
      const response = await mcpClient.callTool<{ notifications: Notification[] }>(
        'get_notification_history',
        { unread_only: true, page_size: 100 }
      );

      const unreadIds = response.notifications
        .filter((n) => !n.read_at)
        .map((n) => n.id);

      if (unreadIds.length === 0) {
        return { success: true, count: 0, notification_ids: [] };
      }

      const results = await Promise.all(
        unreadIds.map((id) =>
          mcpClient.callTool<MarkAsReadResponse>('mark_notification_read', {
            notification_id: id,
          })
        )
      );

      return {
        success: results.every((r) => r.success),
        count: results.filter((r) => r.success).length,
        notification_ids: unreadIds,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
