/**
 * useDatabaseStats Hook
 *
 * Fetches PostgreSQL and Neo4j database statistics with auto-refresh.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DatabaseSystemHealth } from '../types';

const QUERY_KEY = ['monitoring', 'database-stats'];

/**
 * Fetch database stats from MCP orchestration server
 */
async function fetchDatabaseStats(): Promise<DatabaseSystemHealth> {
  return mcpClient.callTool<DatabaseSystemHealth>('get_database_stats');
}

export interface UseDatabaseStatsOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch database statistics
 *
 * @example
 * ```tsx
 * const { data: dbStats, isLoading } = useDatabaseStats({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useDatabaseStats({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseDatabaseStatsOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<DatabaseSystemHealth>({
    queryKey: QUERY_KEY,
    queryFn: fetchDatabaseStats,
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  // Derived data
  const postgresql = query.data?.postgresql ?? null;
  const neo4j = query.data?.neo4j ?? null;
  const overallStatus = query.data?.status ?? 'unknown';

  return {
    ...query,
    postgresql,
    neo4j,
    overallStatus,
    invalidate,
  };
}

export { QUERY_KEY as DATABASE_STATS_QUERY_KEY };
