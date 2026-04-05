/**
 * useErrorLogs Hook
 *
 * Fetches recent error logs with filtering capabilities.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ErrorLog, ErrorLogFilters, PaginatedResponse } from '../types';

const QUERY_KEY_PREFIX = ['monitoring', 'error-logs'];

/**
 * Fetch error logs from MCP orchestration server
 */
async function fetchErrorLogs(filters?: ErrorLogFilters): Promise<PaginatedResponse<ErrorLog>> {
  return mcpClient.callTool<PaginatedResponse<ErrorLog>>('get_error_logs', {
    service: filters?.service,
    level: filters?.level,
    start_time: filters?.start_time,
    end_time: filters?.end_time,
    limit: filters?.limit ?? 50,
    offset: filters?.offset ?? 0,
  });
}

export interface UseErrorLogsOptions {
  /** Filter options */
  filters?: ErrorLogFilters;
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch error logs with filtering
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useErrorLogs({
 *   filters: { service: 'feed-service', level: 'error', limit: 100 },
 *   autoRefresh: true
 * });
 * ```
 */
export function useErrorLogs({
  filters,
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseErrorLogsOptions = {}) {
  const queryClient = useQueryClient();
  const queryKey = [...QUERY_KEY_PREFIX, filters];

  const query = useQuery<PaginatedResponse<ErrorLog>>({
    queryKey,
    queryFn: () => fetchErrorLogs(filters),
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY_PREFIX });
  };

  // Derived data
  const logs = query.data?.items ?? [];
  const totalLogs = query.data?.total ?? 0;
  const hasMore = query.data?.has_more ?? false;

  // Count by level
  const errorCount = logs.filter((l) => l.level === 'error').length;
  const warningCount = logs.filter((l) => l.level === 'warning').length;
  const criticalCount = logs.filter((l) => l.level === 'critical').length;

  return {
    ...query,
    logs,
    totalLogs,
    hasMore,
    errorCount,
    warningCount,
    criticalCount,
    invalidate,
  };
}

export { QUERY_KEY_PREFIX as ERROR_LOGS_QUERY_KEY_PREFIX };
