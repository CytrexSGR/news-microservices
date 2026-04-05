/**
 * useNotificationHistory Hook
 *
 * Fetches paginated notification history for the current user.
 * Supports filtering by status, channel, and date range.
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NotificationHistoryResponse,
  NotificationHistoryParams,
} from '../types';

interface UseNotificationHistoryOptions extends NotificationHistoryParams {
  enabled?: boolean;
  refetchInterval?: number | false;
}

/**
 * Hook to fetch notification history with pagination and filtering
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useNotificationHistory({
 *   page: 1,
 *   page_size: 20,
 *   status: NotificationStatus.SENT,
 * });
 * ```
 */
export function useNotificationHistory(options: UseNotificationHistoryOptions = {}) {
  const {
    enabled = true,
    refetchInterval = false,
    page = 1,
    page_size = 20,
    status,
    channel,
    start_date,
    end_date,
    unread_only,
  } = options;

  return useQuery<NotificationHistoryResponse>({
    queryKey: [
      'notifications',
      'history',
      { page, page_size, status, channel, start_date, end_date, unread_only },
    ],
    queryFn: async () => {
      const response = await mcpClient.callTool<NotificationHistoryResponse>(
        'get_notification_history',
        {
          page,
          page_size,
          ...(status && { status }),
          ...(channel && { channel }),
          ...(start_date && { start_date }),
          ...(end_date && { end_date }),
          ...(unread_only !== undefined && { unread_only }),
        }
      );
      return response;
    },
    enabled,
    refetchInterval,
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get unread notification count only
 * Useful for badge displays
 */
export function useUnreadNotificationCount() {
  return useQuery<number>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const response = await mcpClient.callTool<NotificationHistoryResponse>(
        'get_notification_history',
        {
          page: 1,
          page_size: 1,
          unread_only: true,
        }
      );
      return response.unread_count;
    },
    refetchInterval: 30000, // Poll every 30 seconds for badge updates
    staleTime: 15000,
  });
}

/**
 * Hook to get recent notifications for dropdown preview
 */
export function useRecentNotifications(limit = 5) {
  return useQuery<NotificationHistoryResponse>({
    queryKey: ['notifications', 'recent', limit],
    queryFn: async () => {
      const response = await mcpClient.callTool<NotificationHistoryResponse>(
        'get_notification_history',
        {
          page: 1,
          page_size: limit,
        }
      );
      return response;
    },
    refetchInterval: 60000, // Poll every minute
    staleTime: 30000,
  });
}
