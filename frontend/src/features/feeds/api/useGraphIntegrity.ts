/**
 * Graph Integrity API Hook
 *
 * Fetches data quality metrics from the Knowledge Graph service
 * including orphaned nodes, broken relationships, and quality scores.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * Issue found during graph integrity check
 */
export interface GraphIntegrityIssue {
  type: 'orphan' | 'broken_rel' | 'duplicate' | 'missing_property' | 'invalid_reference';
  count: number;
  severity: 'low' | 'medium' | 'high';
  description?: string;
}

/**
 * Result from graph integrity check
 */
export interface GraphIntegrityResult {
  /** Number of nodes with no relationships */
  orphaned_nodes: number;
  /** Number of relationships with invalid source/target */
  broken_relationships: number;
  /** Total nodes in the graph */
  total_nodes: number;
  /** Total relationships in the graph */
  total_relationships: number;
  /** Overall data quality score (0-100) */
  data_quality_score: number;
  /** Detailed list of issues found */
  issues: GraphIntegrityIssue[];
  /** Timestamp of the last integrity check */
  last_checked?: string;
  /** Node counts by type */
  nodes_by_type?: Record<string, number>;
  /** Relationship counts by type */
  relationships_by_type?: Record<string, number>;
}

/**
 * Query key for graph integrity data
 */
export const graphIntegrityQueryKey = ['feeds', 'graph-integrity'] as const;

/**
 * Hook to fetch graph integrity metrics from Knowledge Graph service
 *
 * @example
 * ```tsx
 * const { data, isLoading, refetch } = useGraphIntegrity();
 *
 * if (data) {
 *   console.log(`Quality Score: ${data.data_quality_score}`);
 *   console.log(`Orphaned Nodes: ${data.orphaned_nodes}`);
 * }
 * ```
 */
export const useGraphIntegrity = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: graphIntegrityQueryKey,
    queryFn: async () => {
      const result = await mcpClient.callTool<GraphIntegrityResult>(
        'get_quality_integrity',
        {},
        { timeout: 60000 } // Allow 60s for potentially slow graph queries
      );
      return result;
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000, // Consider data stale after 30 seconds
    enabled: options?.enabled !== false,
  });
};

/**
 * Hook to manually trigger a graph integrity check
 */
export const useRefreshGraphIntegrity = () => {
  const queryClient = useQueryClient();

  return {
    refresh: () => queryClient.invalidateQueries({ queryKey: graphIntegrityQueryKey }),
  };
};
