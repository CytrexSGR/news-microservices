/**
 * Narrative Service API Client
 *
 * Handles communication with narrative-service (port 8119)
 *
 * Endpoints:
 * - GET  /api/v1/narrative/overview        - Get narrative statistics
 * - GET  /api/v1/narrative/frames          - List narrative frames
 * - POST /api/v1/narrative/frames          - Create new frame
 * - GET  /api/v1/narrative/clusters        - List narrative clusters
 * - POST /api/v1/narrative/clusters/update - Update clusters
 * - GET  /api/v1/narrative/bias            - Get bias comparison
 * - POST /api/v1/narrative/analyze/text    - Analyze text
 * - GET  /api/v1/narrative/cache/stats     - Get cache statistics
 * - POST /api/v1/narrative/cache/clear     - Clear cache
 *
 * @module features/narrative/api
 */

import type {
  NarrativeOverview,
  NarrativeFrame,
  NarrativeFrameCreate,
  NarrativeCluster,
  BiasComparisonResponse,
  FramesListResponse,
  FramesListParams,
  ClustersListParams,
  BiasComparisonParams,
  OverviewParams,
  TextAnalyzerInput,
  TextAnalysisResult,
  ClusterUpdateResponse,
  CacheStatsResponse,
  CacheClearResponse,
} from '../types';

// ============================================================================
// Configuration
// ============================================================================

/**
 * Narrative Service base URL
 * Note: VITE_NARRATIVE_API_URL should contain the full path including /api/v1/narrative
 * Fallback provides full path for localhost development
 */
const API_BASE =
  import.meta.env.VITE_NARRATIVE_API_URL || 'http://localhost:8119/api/v1/narrative';

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Standardized API response wrapper
 */
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// ============================================================================
// Auth Utilities
// ============================================================================

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  try {
    const authStorage = localStorage.getItem('auth-storage');
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      return parsed.state?.token || null;
    }
  } catch {
    // Ignore parse errors
  }
  return null;
}

// ============================================================================
// Fetch Helper
// ============================================================================

/**
 * Fetch helper with error handling and auth
 *
 * @param endpoint - API endpoint (relative to API_BASE)
 * @param options - Fetch options
 * @returns Promise with data or error
 */
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorJson.message || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      return { error: errorMessage };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Build query string from params object
 */
function buildQueryString(params?: Record<string, unknown>): string {
  if (!params) return '';

  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.set(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

// ============================================================================
// Overview API
// ============================================================================

/**
 * Get narrative overview statistics
 *
 * Returns aggregate statistics about frames, clusters, and bias.
 *
 * @param params - Query parameters
 * @param params.days - Number of days to look back (default: 7)
 * @returns Narrative overview statistics
 *
 * @example
 * ```typescript
 * const { data, error } = await getNarrativeOverview({ days: 14 });
 * if (data) {
 *   console.log(`Total frames: ${data.total_frames}`);
 * }
 * ```
 */
export async function getNarrativeOverview(
  params?: OverviewParams
): Promise<ApiResponse<NarrativeOverview>> {
  return fetchApi<NarrativeOverview>(`/overview${buildQueryString(params)}`);
}

// ============================================================================
// Frames API
// ============================================================================

/**
 * List narrative frames with pagination and filters
 *
 * @param params - Query parameters
 * @param params.page - Page number (default: 1)
 * @param params.per_page - Items per page (default: 50, max: 100)
 * @param params.frame_type - Filter by frame type
 * @param params.event_id - Filter by event ID
 * @param params.min_confidence - Minimum confidence threshold (0-1)
 * @returns Paginated list of frames
 *
 * @example
 * ```typescript
 * const { data } = await listFrames({
 *   frame_type: 'victim',
 *   min_confidence: 0.7,
 *   page: 1,
 *   per_page: 20
 * });
 * ```
 */
export async function listFrames(
  params?: FramesListParams
): Promise<ApiResponse<FramesListResponse>> {
  return fetchApi<FramesListResponse>(`/frames${buildQueryString(params)}`);
}

/**
 * Create a new narrative frame
 *
 * Typically called by content analysis service when processing articles.
 *
 * @param frame - Frame data to create
 * @returns Created frame
 *
 * @example
 * ```typescript
 * const { data } = await createFrame({
 *   event_id: 'article-123',
 *   frame_type: 'hero',
 *   confidence: 0.85,
 *   text_excerpt: 'The firefighters saved...'
 * });
 * ```
 */
export async function createFrame(
  frame: NarrativeFrameCreate
): Promise<ApiResponse<NarrativeFrame>> {
  return fetchApi<NarrativeFrame>('/frames', {
    method: 'POST',
    body: JSON.stringify(frame),
  });
}

// ============================================================================
// Clusters API
// ============================================================================

/**
 * List narrative clusters
 *
 * Clusters group similar narrative frames by type and entity overlap.
 *
 * @param params - Query parameters
 * @param params.active_only - Only return active clusters (default: true)
 * @param params.min_frame_count - Minimum frame count filter
 * @param params.limit - Maximum results (default: 50, max: 100)
 * @returns List of clusters
 *
 * @example
 * ```typescript
 * const { data } = await listClusters({
 *   active_only: true,
 *   min_frame_count: 5
 * });
 * ```
 */
export async function listClusters(
  params?: ClustersListParams
): Promise<ApiResponse<NarrativeCluster[]>> {
  return fetchApi<NarrativeCluster[]>(`/clusters${buildQueryString(params)}`);
}

/**
 * Trigger narrative clustering update
 *
 * Analyzes frames from last 7 days and creates/updates clusters.
 * This is typically run as a periodic task.
 *
 * @returns Update result with count of clusters updated
 *
 * @example
 * ```typescript
 * const { data } = await updateClusters();
 * console.log(`Updated ${data.clusters_updated} clusters`);
 * ```
 */
export async function updateClusters(): Promise<
  ApiResponse<ClusterUpdateResponse>
> {
  return fetchApi<ClusterUpdateResponse>('/clusters/update', {
    method: 'POST',
  });
}

// ============================================================================
// Bias API
// ============================================================================

/**
 * Get bias comparison across sources
 *
 * Returns bias distribution and individual source analyses.
 *
 * @param params - Query parameters
 * @param params.event_id - Filter by event ID
 * @param params.days - Days to look back (default: 7)
 * @returns Bias comparison data
 *
 * @example
 * ```typescript
 * const { data } = await getBiasComparison({
 *   event_id: 'article-123',
 *   days: 14
 * });
 * console.log(`Average bias: ${data.avg_bias_score}`);
 * ```
 */
export async function getBiasComparison(
  params?: BiasComparisonParams
): Promise<ApiResponse<BiasComparisonResponse>> {
  return fetchApi<BiasComparisonResponse>(`/bias${buildQueryString(params)}`);
}

// ============================================================================
// Text Analysis API
// ============================================================================

/**
 * Analyze text for narrative frames and bias (CACHED, without persisting)
 *
 * Useful for testing or one-off analysis.
 *
 * Performance: ~150ms without cache, ~3ms with cache
 *
 * @param input - Text analysis input
 * @param input.text - Text to analyze (50-50000 chars)
 * @param input.source - Optional source identifier
 * @returns Analysis result with frames and bias
 *
 * @example
 * ```typescript
 * const { data } = await analyzeText({
 *   text: 'The president announced...',
 *   source: 'reuters'
 * });
 *
 * if (data) {
 *   console.log(`Detected ${data.frames.length} frames`);
 *   console.log(`Bias score: ${data.bias.bias_score}`);
 * }
 * ```
 */
export async function analyzeText(
  input: TextAnalyzerInput
): Promise<ApiResponse<TextAnalysisResult>> {
  const { text, source } = input;
  const params: Record<string, string> = { text };
  if (source) {
    params.source = source;
  }

  return fetchApi<TextAnalysisResult>(`/analyze/text${buildQueryString(params)}`, {
    method: 'POST',
  });
}

// ============================================================================
// Cache Management API
// ============================================================================

/**
 * Get cache statistics
 *
 * Returns cache hit rate, total cached items, etc.
 * Useful for monitoring cache performance.
 *
 * @returns Cache statistics
 *
 * @example
 * ```typescript
 * const { data } = await getCacheStats();
 * if (data?.cache_enabled) {
 *   console.log(`Hit rate: ${data.hit_rate}%`);
 * }
 * ```
 */
export async function getCacheStats(): Promise<ApiResponse<CacheStatsResponse>> {
  return fetchApi<CacheStatsResponse>('/cache/stats');
}

/**
 * Clear cache entries
 *
 * @param pattern - Optional pattern to match (e.g., "narrative:frame:*")
 *                  If not provided, clears all narrative cache entries
 * @returns Clear result
 *
 * @example
 * ```typescript
 * // Clear all cache
 * await clearCache();
 *
 * // Clear specific pattern
 * await clearCache('narrative:frame:*');
 * ```
 */
export async function clearCache(
  pattern?: string
): Promise<ApiResponse<CacheClearResponse>> {
  return fetchApi<CacheClearResponse>(
    `/cache/clear${pattern ? `?pattern=${encodeURIComponent(pattern)}` : ''}`,
    { method: 'POST' }
  );
}

// ============================================================================
// Convenience Endpoints Object
// ============================================================================

/**
 * Narrative API endpoints as an object
 *
 * Alternative to individual function imports.
 *
 * @example
 * ```typescript
 * import { narrativeEndpoints } from '@/features/narrative/api';
 *
 * const overview = await narrativeEndpoints.getOverview({ days: 7 });
 * const frames = await narrativeEndpoints.listFrames({ frame_type: 'victim' });
 * ```
 */
export const narrativeEndpoints = {
  getOverview: getNarrativeOverview,
  listFrames,
  createFrame,
  listClusters,
  updateClusters,
  getBiasComparison,
  analyzeText,
  getCacheStats,
  clearCache,
} as const;
