/**
 * @deprecated This file is deprecated. Use @/features/narrative/api instead.
 *
 * This file will be removed in a future version.
 *
 * Migration guide:
 * ```typescript
 * // Old (deprecated):
 * import { getNarrativeOverview, analyzeText } from '@/api/narrative';
 *
 * // New:
 * import { getNarrativeOverview, analyzeText } from '@/features/narrative/api';
 * // or
 * import { getNarrativeOverview, analyzeText } from '@/features/narrative';
 * ```
 *
 * Key changes:
 * - Uses native fetch instead of axios
 * - Returns { data, error } wrapper instead of throwing
 * - Improved TypeScript types with strict typing
 * - Better documentation and examples
 *
 * @see {@link @/features/narrative/api} for the new implementation
 */

// Re-export everything from the new location for backwards compatibility
export {
  getNarrativeOverview,
  listFrames,
  createFrame,
  listClusters,
  updateClusters,
  getBiasComparison,
  analyzeText,
  getCacheStats,
  clearCache,
  narrativeEndpoints,
} from '@/features/narrative/api';

// Re-export types
export type {
  // Core Types
  FrameType,
  BiasLabel,
  Perspective,
  NarrativeFrame,
  FrameEntities,
  NarrativeCluster,
  BiasAnalysis,
  LanguageIndicators,
  TopNarrative,

  // Request DTOs
  NarrativeFrameCreate,
  TextAnalyzerOptions,
  TextAnalyzerInput,

  // Query Parameters
  FramesListParams,
  ClustersListParams,
  BiasComparisonParams,
  OverviewParams,

  // Response DTOs
  NarrativeOverview,
  FramesListResponse,
  BiasComparisonResponse,
  ClusterUpdateResponse,
  DetectedFrame,
  BiasResult,
  TextAnalysisResult,
  CacheStatsResponse,
  CacheClearResponse,
  ApiResponse,
} from '@/features/narrative/api';

// ============================================================================
// DEPRECATED: Legacy axios-based exports for backwards compatibility
// These will be removed in a future version
// ============================================================================

import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

/**
 * @deprecated Use the new fetch-based API from @/features/narrative/api
 */
const narrativeApi = axios.create({
  baseURL: import.meta.env.VITE_NARRATIVE_API_URL || 'http://localhost:8119/api/v1/narrative',
});

// Add auth interceptor
narrativeApi.interceptors.request.use(
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

/**
 * @deprecated Use analyzeText from @/features/narrative/api instead.
 *
 * Analyze text for narrative frames, entities, and sentiment
 *
 * Performance: ~150ms without cache, ~3ms with cache
 *
 * @param input - Text to analyze with optional source and options
 * @returns Detailed analysis including frames, bias, entities, and sentiment
 */
export const analyzeTextDetailed = async (
  input: { text: string; source?: string }
): Promise<{
  frames: Array<{
    frame_type: string;
    confidence: number;
    text_excerpt: string;
    entities: {
      persons: string[];
      organizations: string[];
      locations: string[];
    };
    match_count: number;
  }>;
  bias: {
    bias_score: number;
    bias_label: string;
    sentiment: number;
    language_indicators: {
      left_markers: number;
      right_markers: number;
      emotional_positive: number;
      emotional_negative: number;
    };
    perspective: string;
    source: string | null;
  };
  text_length: number;
  analyzed_at: string;
  from_cache: boolean;
}> => {
  console.warn(
    '[DEPRECATED] analyzeTextDetailed from @/api/narrative is deprecated. ' +
    'Use analyzeText from @/features/narrative/api instead.'
  );
  const { text, source } = input;
  const response = await narrativeApi.post(`/analyze/text`, null, {
    params: { text, source },
  });
  return response.data;
};

/**
 * @deprecated Use the new fetch-based API from @/features/narrative/api
 */
export { narrativeApi };
