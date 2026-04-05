/**
 * useEntityClusters Hook
 *
 * Query hook for fetching entity clusters (top entities by alias count).
 */
import { useQuery } from '@tanstack/react-query';
import { getEntityClusters } from './entitiesApi';
import type { EntityType, EntityCluster } from '../types/entities.types';

interface UseEntityClustersOptions {
  type?: EntityType;
  limit?: number;
  enabled?: boolean;
  refetchInterval?: number;
}

export function useEntityClusters(options?: UseEntityClustersOptions) {
  const { type, limit = 20, enabled = true, refetchInterval } = options || {};

  return useQuery<{ top_entities_by_aliases: EntityCluster[] }>({
    queryKey: ['entities', 'clusters', type, limit],
    queryFn: () => getEntityClusters(type, limit),
    enabled,
    refetchInterval,
    staleTime: 60000, // 1 minute
  });
}
