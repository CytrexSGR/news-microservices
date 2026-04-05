/**
 * useGraphIntegrity Hook
 *
 * Fetches graph integrity metrics including orphaned nodes,
 * broken relationships, and data quality score.
 * Uses MCP tool: get_quality_integrity
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useGraphIntegrity()
 * console.log(data?.data_quality_score)
 * ```
 *
 * @module features/knowledge-graph/api/useGraphIntegrity
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { GraphIntegrity } from '../types/quality';

// ===========================
// Hook Options
// ===========================

export interface UseGraphIntegrityOptions {
  /** Enable/disable query */
  enabled?: boolean;
  /** Stale time in ms */
  staleTime?: number;
  /** Refetch interval in ms */
  refetchInterval?: number;
  /** Include detailed issue examples */
  includeExamples?: boolean;
}

// ===========================
// Query Key Factory
// ===========================

export const graphIntegrityKeys = {
  all: ['knowledge-graph', 'integrity'] as const,
  current: (includeExamples?: boolean) =>
    [...graphIntegrityKeys.all, 'current', { includeExamples }] as const,
};

// ===========================
// API Function
// ===========================

interface IntegrityParams {
  include_examples?: boolean;
}

async function fetchGraphIntegrity(params: IntegrityParams = {}): Promise<GraphIntegrity> {
  return mcpClient.callTool<GraphIntegrity>('get_quality_integrity', {
    include_examples: params.include_examples ?? false,
  });
}

// ===========================
// Hook Implementation
// ===========================

/**
 * Hook to fetch graph integrity metrics.
 *
 * @param options - Query options
 * @returns React Query result with integrity data
 */
export function useGraphIntegrity(options: UseGraphIntegrityOptions = {}) {
  const {
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
    refetchInterval,
    includeExamples = false,
  } = options;

  return useQuery({
    queryKey: graphIntegrityKeys.current(includeExamples),
    queryFn: () => fetchGraphIntegrity({ include_examples: includeExamples }),
    enabled,
    staleTime,
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval,
  });
}

// ===========================
// Derived Data Hooks
// ===========================

/**
 * Hook to get quality score only.
 */
export function useQualityScore() {
  const { data, ...rest } = useGraphIntegrity();

  return {
    score: data?.data_quality_score ?? 0,
    ...rest,
  };
}

/**
 * Hook to get critical issues only.
 */
export function useCriticalIssues() {
  const { data, ...rest } = useGraphIntegrity({ includeExamples: true });

  const criticalIssues = data?.issues.filter((issue) => issue.severity === 'critical') ?? [];

  return {
    issues: criticalIssues,
    count: criticalIssues.reduce((acc, issue) => acc + issue.count, 0),
    ...rest,
  };
}

/**
 * Hook to get integrity summary for dashboard widgets.
 */
export function useIntegritySummary() {
  const { data, isLoading, error } = useGraphIntegrity();

  if (!data) {
    return {
      isLoading,
      error,
      summary: null,
    };
  }

  const summary = {
    qualityScore: data.data_quality_score,
    orphanedNodes: data.orphaned_nodes,
    brokenRelationships: data.broken_relationships,
    totalNodes: data.total_nodes,
    totalRelationships: data.total_relationships,
    issueCount: data.issues.length,
    criticalCount: data.issues.filter((i) => i.severity === 'critical').length,
    warningCount: data.issues.filter((i) => i.severity === 'warning').length,
    healthStatus: getHealthStatus(data.data_quality_score),
  };

  return {
    isLoading,
    error,
    summary,
  };
}

/**
 * Get health status label from quality score.
 */
function getHealthStatus(score: number): 'healthy' | 'warning' | 'critical' {
  if (score >= 75) return 'healthy';
  if (score >= 50) return 'warning';
  return 'critical';
}
