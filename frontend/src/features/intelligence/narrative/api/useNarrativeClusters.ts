import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NarrativeCluster,
  NarrativeClustersResponse,
  ClusterFilters,
} from '../types/narrative.types';

/**
 * Parameters for fetching narrative clusters
 */
export interface NarrativeClustersParams extends ClusterFilters {
  page?: number;
  per_page?: number;
  sort_by?: 'article_count' | 'avg_bias' | 'created_at' | 'last_updated';
  sort_order?: 'asc' | 'desc';
  active_only?: boolean;
  min_frame_count?: number;
  include_entities?: boolean;
  entity_limit?: number;
}

/**
 * Hook for fetching narrative clusters
 *
 * Uses the MCP tool `list_narrative_clusters` to retrieve clusters
 * of related narratives across articles.
 *
 * @param params - Query parameters including filters, pagination, and sorting
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * // Get all clusters
 * const { data, isLoading } = useNarrativeClusters();
 *
 * // With full MCP parameters
 * const { data } = useNarrativeClusters({
 *   dominant_frame: 'conflict',
 *   min_articles: 5,
 *   active_only: true,
 *   min_frame_count: 3,
 *   include_entities: true
 * });
 * ```
 */
export function useNarrativeClusters(
  params?: NarrativeClustersParams,
  enabled: boolean = true
) {
  return useQuery<NarrativeClustersResponse, Error>({
    queryKey: ['narrative', 'clusters', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<NarrativeClustersResponse>(
        'list_narrative_clusters',
        {
          page: params?.page ?? 1,
          per_page: params?.per_page ?? 20,
          dominant_frame: params?.dominant_frame,
          min_articles: params?.min_articles ?? 1,
          // New MCP parameters
          active_only: params?.active_only ?? !params?.include_inactive,
          min_frame_count: params?.min_frame_count ?? 1,
          include_entities: params?.include_entities ?? true,
          entity_limit: params?.entity_limit ?? 10,
          // Legacy parameter support
          include_inactive: params?.include_inactive ?? false,
          sort_by: params?.sort_by ?? 'article_count',
          sort_order: params?.sort_order ?? 'desc',
        }
      );

      return response;
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

/**
 * Hook for fetching a single cluster by ID
 */
export function useNarrativeCluster(clusterId: string, enabled: boolean = true) {
  return useQuery<NarrativeCluster, Error>({
    queryKey: ['narrative', 'clusters', 'detail', clusterId],
    queryFn: async () => {
      const response = await mcpClient.callTool<NarrativeCluster>(
        'list_narrative_clusters',
        {
          cluster_id: clusterId,
        }
      );

      return response;
    },
    enabled: enabled && !!clusterId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook for fetching cluster statistics
 */
export function useClusterStats(enabled: boolean = true) {
  const clustersQuery = useNarrativeClusters({ per_page: 100 }, enabled);

  return {
    ...clustersQuery,
    data: clustersQuery.data
      ? {
          total_clusters: clustersQuery.data.total,
          avg_articles_per_cluster:
            clustersQuery.data.clusters.reduce(
              (sum, c) => sum + c.article_count,
              0
            ) / clustersQuery.data.clusters.length || 0,
          frame_distribution: clustersQuery.data.clusters.reduce(
            (acc, cluster) => {
              acc[cluster.dominant_frame] =
                (acc[cluster.dominant_frame] || 0) + 1;
              return acc;
            },
            {} as Record<string, number>
          ),
        }
      : undefined,
  };
}
