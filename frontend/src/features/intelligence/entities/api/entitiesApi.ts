/**
 * Entity Canonicalization API Client
 *
 * Provides access to the entity-canonicalization-service endpoints (port 8112).
 * All canonicalization operations go through this client.
 */
import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
import type {
  CanonicalizeRequest,
  CanonicalEntity,
  BatchCanonRequest,
  BatchCanonResponse,
  AsyncBatchCanonResponse,
  CanonStats,
  BasicCanonStats,
  AsyncJob,
  AsyncJobResult,
  MergeEvent,
  EntityType,
} from '../types/entities.types';

// Entity Canonicalization Service URL (from docker-compose.yml)
const BASE_URL = import.meta.env.VITE_CANONICALIZATION_API_URL || 'http://localhost:8112';

// Create axios instance
const entitiesApi = axios.create({
  baseURL: `${BASE_URL}/api/v1/canonicalization`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
entitiesApi.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ===========================
// Single Entity Canonicalization
// ===========================

/**
 * Canonicalize a single entity
 *
 * Multi-stage canonicalization:
 * 1. Exact match in alias store
 * 2. Fuzzy + semantic similarity
 * 3. Wikidata entity linking
 * 4. Create new canonical form
 */
export const canonicalizeEntity = async (
  request: CanonicalizeRequest
): Promise<CanonicalEntity> => {
  const { data } = await entitiesApi.post<CanonicalEntity>('/canonicalize', request);
  return data;
};

// ===========================
// Batch Canonicalization
// ===========================

/**
 * Batch canonicalization for multiple entities (sync)
 *
 * More efficient than individual calls for small batches (< 10 entities).
 */
export const batchCanonicalizeEntities = async (
  request: BatchCanonRequest
): Promise<BatchCanonResponse> => {
  const { data } = await entitiesApi.post<BatchCanonResponse>('/canonicalize/batch', request);
  return data;
};

/**
 * Start async batch canonicalization job
 *
 * Use for large batches (> 10 entities) to avoid timeouts.
 * Returns job_id immediately - poll /jobs/{job_id}/status for progress.
 */
export const batchCanonicalizeEntitiesAsync = async (
  request: BatchCanonRequest
): Promise<AsyncBatchCanonResponse> => {
  const { data } = await entitiesApi.post<AsyncBatchCanonResponse>(
    '/canonicalize/batch/async',
    request
  );
  return data;
};

// ===========================
// Entity Clusters
// ===========================

/**
 * Get top entities by alias count (clusters)
 *
 * Returns entities with the most detected variants/aliases.
 */
export const getEntityClusters = async (
  type?: EntityType,
  limit: number = 20
): Promise<{ top_entities_by_aliases: CanonStats['top_entities_by_aliases'] }> => {
  // Get detailed stats which includes top entities
  const stats = await getDetailedStats();

  let entities = stats.top_entities_by_aliases;

  // Filter by type if specified
  if (type) {
    entities = entities.filter((e) => e.entity_type === type);
  }

  return {
    top_entities_by_aliases: entities.slice(0, limit),
  };
};

// ===========================
// Statistics
// ===========================

/**
 * Get basic canonicalization statistics
 */
export const getBasicStats = async (): Promise<BasicCanonStats> => {
  const { data } = await entitiesApi.get<BasicCanonStats>('/stats');
  return data;
};

/**
 * Get detailed canonicalization statistics
 *
 * Includes:
 * - Basic stats (entities, aliases, wikidata coverage)
 * - Deduplication ratio
 * - Entity type distribution
 * - Top 10 entities by alias count
 * - Performance metrics
 * - Cost savings estimates
 */
export const getDetailedStats = async (): Promise<CanonStats> => {
  const { data } = await entitiesApi.get<CanonStats>('/stats/detailed');
  return data;
};

// ===========================
// Async Job Status
// ===========================

/**
 * Get current status of async batch job
 *
 * Poll this endpoint to check progress.
 */
export const getAsyncJobStatus = async (jobId: string): Promise<AsyncJob> => {
  const { data } = await entitiesApi.get<AsyncJob>(`/jobs/${jobId}/status`);
  return data;
};

/**
 * Get results of completed async batch job
 *
 * Only returns data if job status is 'completed'.
 */
export const getAsyncJobResult = async (jobId: string): Promise<AsyncJobResult> => {
  const { data } = await entitiesApi.get<AsyncJobResult>(`/jobs/${jobId}/result`);
  return data;
};

// ===========================
// Entity Aliases
// ===========================

/**
 * Get all known aliases for a canonical entity
 */
export const getEntityAliases = async (
  canonicalName: string,
  entityType: EntityType
): Promise<string[]> => {
  const { data } = await entitiesApi.get<string[]>(
    `/aliases/${encodeURIComponent(canonicalName)}`,
    {
      params: { entity_type: entityType },
    }
  );
  return data;
};

// ===========================
// Entity History
// ===========================

/**
 * Get recent entity merge events
 *
 * Returns a history of entity deduplication operations.
 */
export const getEntityHistory = async (limit: number = 20): Promise<MergeEvent[]> => {
  const { data } = await entitiesApi.get<MergeEvent[]>('/history/merges', {
    params: { limit },
  });
  return data;
};

// ===========================
// Health Check
// ===========================

/**
 * Health check endpoint
 */
export const getHealthStatus = async (): Promise<{ status: string; service: string }> => {
  const { data } = await entitiesApi.get('/health');
  return data;
};

export { entitiesApi };
