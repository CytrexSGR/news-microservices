/**
 * useQueueStats Hook
 *
 * Query hooks for notification queue statistics (Admin only).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  QueueStatistics,
  QueueStatsResponse,
  DLQListResponse,
  DLQItem,
  RetryDLQResponse,
  DetailedHealthResponse,
} from '../types';

/**
 * Hook to fetch queue statistics
 *
 * @example
 * ```tsx
 * const { data: stats, isLoading } = useQueueStats();
 * ```
 */
export function useQueueStats() {
  return useQuery<QueueStatistics>({
    queryKey: ['notifications', 'queue', 'stats'],
    queryFn: async () => {
      const response = await mcpClient.callTool<QueueStatsResponse>(
        'get_notification_queue_stats',
        {}
      );
      return response.queue_stats;
    },
    refetchInterval: 10000, // Poll every 10 seconds
    staleTime: 5000,
  });
}

/**
 * Hook to fetch dead letter queue items
 */
export function useDLQItems(limit = 100) {
  return useQuery<DLQItem[]>({
    queryKey: ['notifications', 'queue', 'dlq', limit],
    queryFn: async () => {
      const response = await mcpClient.callTool<DLQListResponse>(
        'list_dlq_items',
        { limit }
      );
      return response.dlq_items;
    },
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 15000,
  });
}

/**
 * Hook to retry a DLQ item
 */
export function useRetryDLQItem() {
  const queryClient = useQueryClient();

  return useMutation<RetryDLQResponse, Error, number>({
    mutationFn: async (notificationId: number) => {
      const response = await mcpClient.callTool<RetryDLQResponse>(
        'retry_dlq_item',
        { notification_id: notificationId }
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to retry all DLQ items
 */
export function useRetryAllDLQ() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; retried_count: number }, Error, void>({
    mutationFn: async () => {
      // Get all DLQ items first
      const dlqResponse = await mcpClient.callTool<DLQListResponse>(
        'list_dlq_items',
        { limit: 1000 }
      );

      // Retry each one
      const results = await Promise.all(
        dlqResponse.dlq_items.map((item) =>
          mcpClient
            .callTool<RetryDLQResponse>('retry_dlq_item', {
              notification_id: item.notification_id,
            })
            .catch(() => null)
        )
      );

      const successful = results.filter((r) => r?.status === 'success');

      return {
        success: true,
        retried_count: successful.length,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to get detailed system health (Admin)
 */
export function useDetailedHealth() {
  return useQuery<DetailedHealthResponse>({
    queryKey: ['notifications', 'health', 'detailed'],
    queryFn: async () => {
      const response = await mcpClient.callTool<DetailedHealthResponse>(
        'get_detailed_health',
        {}
      );
      return response;
    },
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 15000,
  });
}

/**
 * Hook to get user rate limits (Admin)
 */
export function useUserRateLimits(userId: string | undefined) {
  return useQuery({
    queryKey: ['notifications', 'rate-limits', userId],
    queryFn: async () => {
      if (!userId) throw new Error('User ID required');
      const response = await mcpClient.callTool<{
        user_id: string;
        rate_limits: Record<string, unknown>;
      }>('get_user_rate_limits', { user_id: userId });
      return response;
    },
    enabled: !!userId,
    staleTime: 30000,
  });
}

/**
 * Hook to reset user rate limits (Admin)
 */
export function useResetUserRateLimits() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean }, Error, string>({
    mutationFn: async (userId: string) => {
      const response = await mcpClient.callTool<{ success: boolean }>(
        'reset_user_rate_limits',
        { user_id: userId }
      );
      return response;
    },
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'rate-limits', userId],
      });
    },
  });
}

// =============================================================================
// Alias hooks for component compatibility
// =============================================================================

/**
 * Alias for useDLQItems - returns wrapped response for component compatibility
 */
export function useDLQNotifications() {
  const query = useDLQItems();
  return {
    ...query,
    data: query.data ? { notifications: query.data } : undefined,
  };
}

/**
 * Alias for useRetryDLQItem with string ID support
 */
export function useRetryDLQ() {
  const queryClient = useQueryClient();

  return useMutation<RetryDLQResponse, Error, { notification_id: string }>({
    mutationFn: async ({ notification_id }) => {
      const response = await mcpClient.callTool<RetryDLQResponse>(
        'retry_dlq_item',
        { notification_id: parseInt(notification_id, 10) }
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to purge (permanently delete) a DLQ item
 */
export function usePurgeDLQ() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean }, Error, { notification_id: string }>({
    mutationFn: async ({ notification_id }) => {
      const response = await mcpClient.callTool<{ success: boolean }>(
        'purge_dlq_item',
        { notification_id: parseInt(notification_id, 10) }
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['notifications', 'queue'],
      });
    },
  });
}

/**
 * Hook to get global rate limit status
 */
export function useRateLimits() {
  return useQuery({
    queryKey: ['notifications', 'rate-limits', 'global'],
    queryFn: async () => {
      const response = await mcpClient.callTool<{
        limits: Record<string, unknown>;
      }>('get_rate_limits', {});
      return response;
    },
    staleTime: 30000,
  });
}
