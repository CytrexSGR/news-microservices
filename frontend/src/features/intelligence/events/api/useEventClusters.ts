/**
 * useEventClusters Hook
 *
 * Fetches event clusters with optional filtering
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EventClustersResponse, ClusterFilters } from '../types/events.types';

export function useEventClusters(
  filters: ClusterFilters = {},
  refetchInterval: number = 60000
) {
  return useQuery<EventClustersResponse>({
    queryKey: ['intelligence', 'events', 'clusters', filters],
    queryFn: async () => {
      return mcpClient.callTool<EventClustersResponse>('get_event_clusters', {
        category: filters.category,
        risk_level: filters.risk_level,
        min_events: filters.min_events,
        trending_only: filters.trending_only,
        page: filters.page || 1,
        per_page: filters.per_page || 20,
      });
    },
    refetchInterval,
    staleTime: 30000,
  });
}
