import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DLQStats, DLQEntry, DLQListParams, DLQListResponse } from '../types/scraping.types';

/**
 * Query keys for DLQ
 */
export const dlqStatsQueryKey = ['scraping', 'dlq', 'stats'] as const;
export const dlqEntriesQueryKey = ['scraping', 'dlq', 'entries'] as const;
export const dlqEntryQueryKey = (id: number) => ['scraping', 'dlq', 'entry', id] as const;

/**
 * Fetch DLQ statistics
 */
async function fetchDLQStats(): Promise<DLQStats> {
  return mcpClient.callTool<DLQStats>('scraping_get_dlq_stats');
}

/**
 * Fetch DLQ entries list
 */
async function fetchDLQEntries(params?: DLQListParams): Promise<DLQListResponse> {
  return mcpClient.callTool<DLQListResponse>('scraping_list_dlq_entries', params || {});
}

/**
 * Fetch single DLQ entry
 */
async function fetchDLQEntry(id: number): Promise<DLQEntry> {
  return mcpClient.callTool<DLQEntry>('scraping_get_dlq_entry', { id });
}

/**
 * Hook to fetch DLQ statistics
 *
 * @param options - React Query options
 * @returns Query result with DLQ stats
 *
 * @example
 * ```tsx
 * const { data } = useDLQStats();
 * console.log(`${data?.pending_retry_count} entries pending retry`);
 * ```
 */
export function useDLQStats(
  options?: Omit<UseQueryOptions<DLQStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: dlqStatsQueryKey,
    queryFn: fetchDLQStats,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto-refresh every minute
    ...options,
  });
}

/**
 * Hook to fetch DLQ entries list
 */
export function useDLQEntries(
  params?: DLQListParams,
  options?: Omit<UseQueryOptions<DLQListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...dlqEntriesQueryKey, params],
    queryFn: () => fetchDLQEntries(params),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch a single DLQ entry
 */
export function useDLQEntry(
  id: number,
  options?: Omit<UseQueryOptions<DLQEntry>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: dlqEntryQueryKey(id),
    queryFn: () => fetchDLQEntry(id),
    enabled: id > 0,
    staleTime: 60000,
    ...options,
  });
}
