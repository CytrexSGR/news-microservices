/**
 * useLatestEvents Hook
 *
 * Fetches the latest intelligence events
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { LatestEventsResponse, EventFilters } from '../types/events.types';

export function useLatestEvents(
  filters: EventFilters = {},
  refetchInterval: number = 30000
) {
  return useQuery<LatestEventsResponse>({
    queryKey: ['intelligence', 'events', 'latest', filters],
    queryFn: async () => {
      return mcpClient.callTool<LatestEventsResponse>('get_latest_events', {
        category: filters.category,
        risk_level: filters.risk_level,
        limit: filters.limit || 50,
        offset: filters.offset || 0,
      });
    },
    refetchInterval,
    staleTime: 15000,
  });
}
