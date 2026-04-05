/**
 * Escalation API Hooks for Intelligence Interpretation Layer
 *
 * TanStack Query hooks for fetching escalation data from clustering-service.
 * Provides reactive data fetching with caching, refetching, and error handling.
 *
 * @module features/intelligence/api/escalation
 */

import { useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { createApiClient } from '@/shared/api';
import type {
  EscalationSummary,
  ClusterEscalation,
  RegimeType,
  AlertType,
} from '../types/escalation';

// =============================================================================
// Backend Response Types (actual API response shape)
// =============================================================================

interface BackendDomainEscalation {
  domain: string;
  level: number;
  score: string;
  confidence: number;
}

interface BackendRegimeState {
  regime: string;
  confidence: number;
  vix_level: number | null;
  fear_greed_index: number | null;
  timestamp: string | null;
}

interface BackendCorrelationAlert {
  id: string;
  correlation_type: string;
  fmp_regime: string;
  escalation_level: number;
  confidence: string;
  reasoning: string | null;
  detected_at: string;
  expires_at: string | null;
  related_cluster_count: number;
}

interface BackendEscalationSummary {
  geopolitical: BackendDomainEscalation;
  military: BackendDomainEscalation;
  economic: BackendDomainEscalation;
  combined_level: number;
  combined_score: string;
  market_regime: BackendRegimeState | null;
  correlation_alerts: BackendCorrelationAlert[];
  cluster_count: number;
  calculated_at: string;
}

// =============================================================================
// Response Transformation
// =============================================================================

/**
 * Transform backend API response to frontend EscalationSummary format
 */
function transformEscalationSummary(backend: BackendEscalationSummary): EscalationSummary {
  // Map market_regime to regime
  const regime = {
    type: (backend.market_regime?.regime || 'UNKNOWN') as RegimeType,
    score: backend.market_regime?.confidence ?? 0,
    since: backend.market_regime?.timestamp ?? undefined,
  };

  // Create finance indicators from market regime data
  const finance = {
    vix: backend.market_regime?.vix_level ?? null,
    vixChange: null, // Not available from backend
    dxy: null, // Not available from backend
    yieldSpread: null, // Not available from backend
    carryTrade: null, // Not available from backend
  };

  // Create heatmap from aggregated domain scores (single "Global" region for now)
  const heatmap = [
    {
      region: 'Global',
      geopolitical: parseFloat(backend.geopolitical.score),
      military: parseFloat(backend.military.score),
      economic: parseFloat(backend.economic.score),
    },
  ];

  // Transform correlation alerts
  const alerts = backend.correlation_alerts.map((alert) => ({
    type: alert.correlation_type as AlertType,
    message: alert.reasoning || `${alert.correlation_type}: ${alert.fmp_regime} regime detected`,
    timestamp: alert.detected_at,
    confidence: parseFloat(alert.confidence),
    clusterId: undefined, // Backend uses related_cluster_count, not single ID
  }));

  return {
    regime,
    finance,
    heatmap,
    alerts,
  };
}

// =============================================================================
// Configuration
// =============================================================================

/**
 * Clustering Service base URL for escalation endpoints
 * Note: Escalation endpoints are on the clustering-service (port 8122)
 */
const CLUSTERING_BASE_URL =
  import.meta.env.VITE_CLUSTERING_API_URL ||
  `http://${window.location.hostname}:8122/api/v1`;

/**
 * Clustering API client instance
 * Pre-configured with auth interceptor and error handling
 */
export const clusteringApi = createApiClient(CLUSTERING_BASE_URL);

/**
 * Base path for escalation endpoints
 */
const ESCALATION_BASE = '/escalation';

// =============================================================================
// Query Keys
// =============================================================================

/**
 * Query keys for escalation data
 * Use these for cache invalidation and optimistic updates
 */
export const escalationQueryKeys = {
  /** All escalation queries */
  all: ['escalation'] as const,
  /** Escalation summary queries */
  summary: () => [...escalationQueryKeys.all, 'summary'] as const,
  /** Cluster-specific escalation queries */
  cluster: (clusterId: string) => [...escalationQueryKeys.all, 'cluster', clusterId] as const,
  /** Cluster escalation with recalculate flag */
  clusterWithOptions: (clusterId: string, recalculate?: boolean) =>
    [...escalationQueryKeys.cluster(clusterId), { recalculate }] as const,
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook for fetching escalation summary
 *
 * Returns aggregated escalation data including:
 * - Current market regime status
 * - Financial indicators (VIX, DXY, yields)
 * - Regional escalation heatmap
 * - Active correlation alerts
 *
 * @param options - Query options
 * @param options.refetchInterval - Auto-refetch interval in ms (default: 60000)
 * @param options.enabled - Whether to enable the query (default: true)
 * @returns Query result with escalation summary
 *
 * @example
 * ```tsx
 * function EscalationDashboard() {
 *   const { data, isLoading, error } = useEscalationSummary();
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error) return <Error message={error.message} />;
 *
 *   return (
 *     <div>
 *       <RegimeIndicator regime={data.regime} />
 *       <AlertList alerts={data.alerts} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useEscalationSummary(options?: {
  refetchInterval?: number;
  enabled?: boolean;
}): UseQueryResult<EscalationSummary> {
  const { refetchInterval = 60000, enabled = true } = options || {};

  return useQuery({
    queryKey: escalationQueryKeys.summary(),
    queryFn: async () => {
      const response = await clusteringApi.get<BackendEscalationSummary>(
        `${ESCALATION_BASE}/summary`
      );
      // Transform backend response to frontend format
      return transformEscalationSummary(response.data);
    },
    refetchInterval,
    staleTime: 30000, // Consider fresh for 30 seconds
    enabled,
  });
}

/**
 * Hook for fetching escalation data for a specific cluster
 *
 * Returns detailed escalation breakdown including:
 * - Domain scores (geopolitical, military, economic)
 * - Combined score and level
 * - Signal breakdown (embedding, content, keywords)
 * - FMP market correlation data
 *
 * @param clusterId - UUID of the cluster to fetch
 * @param options - Query options
 * @param options.recalculate - Force recalculation of escalation (default: false)
 * @param options.enabled - Whether to enable the query (default: true)
 * @returns Query result with cluster escalation data
 *
 * @example
 * ```tsx
 * function ClusterEscalationPanel({ clusterId }: { clusterId: string }) {
 *   const { data, isLoading, refetch } = useClusterEscalation(clusterId);
 *
 *   return (
 *     <div>
 *       {data && (
 *         <>
 *           <LevelBadge level={data.level} />
 *           <DomainScores
 *             geopolitical={data.geopolitical}
 *             military={data.military}
 *             economic={data.economic}
 *           />
 *           <button onClick={() => refetch()}>Refresh</button>
 *         </>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useClusterEscalation(
  clusterId: string,
  options?: { recalculate?: boolean; enabled?: boolean }
): UseQueryResult<ClusterEscalation> {
  const { recalculate = false, enabled = true } = options || {};

  return useQuery({
    queryKey: escalationQueryKeys.clusterWithOptions(clusterId, recalculate),
    queryFn: async () => {
      const params = recalculate ? '?recalculate=true' : '';
      const response = await clusteringApi.get<ClusterEscalation>(
        `${ESCALATION_BASE}/clusters/${clusterId}${params}`
      );
      return response.data;
    },
    enabled: enabled && !!clusterId,
    staleTime: 60000, // Consider fresh for 1 minute
  });
}

/**
 * Hook for invalidating escalation cache
 *
 * Use this after mutations that affect escalation data
 * (e.g., after a new cluster is created or articles are added)
 *
 * @returns Object with invalidation functions
 *
 * @example
 * ```tsx
 * function RefreshButton() {
 *   const { invalidateAll, invalidateSummary, invalidateCluster } = useEscalationInvalidation();
 *
 *   return (
 *     <button onClick={invalidateAll}>
 *       Refresh All Escalation Data
 *     </button>
 *   );
 * }
 * ```
 */
export function useEscalationInvalidation() {
  const queryClient = useQueryClient();

  return {
    /** Invalidate all escalation queries */
    invalidateAll: () =>
      queryClient.invalidateQueries({ queryKey: escalationQueryKeys.all }),

    /** Invalidate only the summary query */
    invalidateSummary: () =>
      queryClient.invalidateQueries({ queryKey: escalationQueryKeys.summary() }),

    /** Invalidate a specific cluster's escalation data */
    invalidateCluster: (clusterId: string) =>
      queryClient.invalidateQueries({ queryKey: escalationQueryKeys.cluster(clusterId) }),
  };
}

// =============================================================================
// Prefetch Functions
// =============================================================================

/**
 * Prefetch escalation summary
 *
 * Use this in route loaders or hover handlers to prefetch data
 *
 * @param queryClient - TanStack Query client instance
 * @returns Promise that resolves when prefetch is complete
 */
export async function prefetchEscalationSummary(
  queryClient: ReturnType<typeof useQueryClient>
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: escalationQueryKeys.summary(),
    queryFn: async () => {
      const response = await clusteringApi.get<BackendEscalationSummary>(
        `${ESCALATION_BASE}/summary`
      );
      return transformEscalationSummary(response.data);
    },
    staleTime: 30000,
  });
}

/**
 * Prefetch cluster escalation data
 *
 * @param queryClient - TanStack Query client instance
 * @param clusterId - UUID of the cluster to prefetch
 * @returns Promise that resolves when prefetch is complete
 */
export async function prefetchClusterEscalation(
  queryClient: ReturnType<typeof useQueryClient>,
  clusterId: string
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: escalationQueryKeys.cluster(clusterId),
    queryFn: async () => {
      const response = await clusteringApi.get<ClusterEscalation>(
        `${ESCALATION_BASE}/clusters/${clusterId}`
      );
      return response.data;
    },
    staleTime: 60000,
  });
}
