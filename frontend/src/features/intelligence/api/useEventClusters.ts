import { useQuery } from '@tanstack/react-query';
import { getClusters, getClusterDetail, getClusterEvents } from './intelligenceApi';
import type { ClustersResponse, ClusterDetail, ClusterEventsResponse } from '../types/intelligence.types';

interface ClusterFilters {
  min_events?: number;
  time_range?: number;
  time_window?: '1h' | '6h' | '12h' | '24h' | 'week' | 'month';
  sort_by?: 'risk_score' | 'event_count' | 'last_updated';
  page?: number;
  per_page?: number;
}

export function useEventClusters(
  filters: ClusterFilters = {},
  refetchInterval: number = 60000
) {
  return useQuery<ClustersResponse>({
    queryKey: ['intelligence', 'clusters', filters],
    queryFn: () => getClusters(filters),
    refetchInterval,
    staleTime: 30000,
  });
}

export function useClusterDetail(clusterId: string | undefined, enabled: boolean = true) {
  return useQuery<ClusterDetail>({
    queryKey: ['intelligence', 'cluster', clusterId],
    queryFn: () => getClusterDetail(clusterId!),
    enabled: !!clusterId && enabled,
    staleTime: 30000,
  });
}

export function useClusterEvents(
  clusterId: string | undefined,
  page: number = 1,
  perPage: number = 20
) {
  return useQuery<ClusterEventsResponse>({
    queryKey: ['intelligence', 'cluster-events', clusterId, page, perPage],
    queryFn: () => getClusterEvents(clusterId!, { page, per_page: perPage }),
    enabled: !!clusterId,
    staleTime: 30000,
  });
}
