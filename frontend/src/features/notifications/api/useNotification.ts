/**
 * useNotification Hook
 *
 * Fetches a single notification by ID.
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { Notification } from '../types';

interface UseNotificationOptions {
  enabled?: boolean;
}

/**
 * Hook to fetch a single notification by ID
 *
 * @example
 * ```tsx
 * const { data: notification, isLoading } = useNotification(123);
 * ```
 */
export function useNotification(
  notificationId: number | undefined,
  options: UseNotificationOptions = {}
) {
  const { enabled = true } = options;

  return useQuery<Notification>({
    queryKey: ['notifications', 'detail', notificationId],
    queryFn: async () => {
      if (!notificationId) {
        throw new Error('Notification ID is required');
      }
      const response = await mcpClient.callTool<Notification>(
        'get_notification',
        { notification_id: notificationId }
      );
      return response;
    },
    enabled: enabled && !!notificationId,
    staleTime: 60000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}
