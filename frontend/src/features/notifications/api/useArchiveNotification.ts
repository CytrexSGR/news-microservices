/**
 * useArchiveNotification Hook
 *
 * Mutation hook to archive/unarchive notifications.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { Notification } from '../types';

interface ArchiveResponse {
  success: boolean;
  notification_id: number;
  archived_at?: string;
  unarchived?: boolean;
}

interface BulkArchiveResponse {
  success: boolean;
  count: number;
  notification_ids: number[];
}

/**
 * Hook to archive a single notification
 *
 * @example
 * ```tsx
 * const archiveNotification = useArchiveNotification();
 * archiveNotification.mutate(123);
 * ```
 */
export function useArchiveNotification() {
  const queryClient = useQueryClient();

  return useMutation<ArchiveResponse, Error, number>({
    mutationFn: async (notificationId: number) => {
      // Note: This uses a hypothetical archive endpoint
      // Adjust based on actual MCP tool availability
      const response = await mcpClient.callTool<ArchiveResponse>(
        'archive_notification',
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
            archived_at: data.archived_at,
            status: 'archived' as const,
          };
        }
      );

      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['notifications', 'history'] });
    },
  });
}

/**
 * Hook to unarchive a notification
 */
export function useUnarchiveNotification() {
  const queryClient = useQueryClient();

  return useMutation<ArchiveResponse, Error, number>({
    mutationFn: async (notificationId: number) => {
      const response = await mcpClient.callTool<ArchiveResponse>(
        'unarchive_notification',
        { notification_id: notificationId }
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

/**
 * Hook to archive multiple notifications
 */
export function useBulkArchive() {
  const queryClient = useQueryClient();

  return useMutation<BulkArchiveResponse, Error, number[]>({
    mutationFn: async (notificationIds: number[]) => {
      const results = await Promise.all(
        notificationIds.map((id) =>
          mcpClient.callTool<ArchiveResponse>('archive_notification', {
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
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

/**
 * Hook to delete a notification permanently
 */
export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean }, Error, number>({
    mutationFn: async (notificationId: number) => {
      const response = await mcpClient.callTool<{ success: boolean }>(
        'delete_notification',
        { notification_id: notificationId }
      );
      return response;
    },
    onSuccess: (_, notificationId) => {
      // Remove from cache
      queryClient.removeQueries({
        queryKey: ['notifications', 'detail', notificationId],
      });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
