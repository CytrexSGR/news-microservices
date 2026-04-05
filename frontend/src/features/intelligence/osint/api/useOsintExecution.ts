/**
 * useOsintExecution - OSINT Execution Results Query Hook
 *
 * Fetches the results of a specific OSINT execution
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { OsintExecution } from '../types/osint.types';

interface ExecutionQueryParams {
  execution_id: string;
}

export function useOsintExecution(
  executionId: string | undefined,
  enabled: boolean = true,
  refetchInterval?: number
) {
  return useQuery<OsintExecution>({
    queryKey: ['osint', 'execution', executionId],
    queryFn: async () => {
      return mcpClient.callTool<OsintExecution>('get_osint_execution', {
        execution_id: executionId,
      });
    },
    enabled: !!executionId && enabled,
    staleTime: 10000,
    // If execution is pending/running, poll more frequently
    refetchInterval: refetchInterval,
  });
}

/**
 * Hook to poll execution status while running
 */
export function useOsintExecutionPolling(
  executionId: string | undefined,
  enabled: boolean = true
) {
  const query = useOsintExecution(executionId, enabled);

  // Determine if we should continue polling
  const shouldPoll =
    enabled &&
    query.data &&
    (query.data.status === 'pending' || query.data.status === 'running');

  return useQuery<OsintExecution>({
    queryKey: ['osint', 'execution', executionId, 'polling'],
    queryFn: async () => {
      return mcpClient.callTool<OsintExecution>('get_osint_execution', {
        execution_id: executionId,
      });
    },
    enabled: !!executionId && shouldPoll,
    refetchInterval: 2000, // Poll every 2 seconds while running
    staleTime: 1000,
  });
}
