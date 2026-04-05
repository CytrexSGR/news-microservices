/**
 * Content-Analysis-V3 API Client
 *
 * API endpoints for the V3 cost-optimized analysis pipeline.
 *
 * V3 Architecture:
 * - Tier 0: Fast triage (keep/discard)
 * - Tier 1: Foundation extraction (entities, relations, topics)
 * - Tier 2: Specialist analysis (5 modules)
 * - Cost: $0.00028 per article (96.7% reduction vs V2)
 */

import axios from 'axios';
import type {
  AnalyzeArticleRequest,
  AnalyzeArticleResponse,
  AnalysisStatusResponse,
  AnalysisResultsResponse,
  Tier0DatabaseRow,
  Tier1ResultsDatabaseResponse,
  Tier2ResultsDatabaseResponse,
  TriageDecision,
  Tier1Results,
  Tier2Results,
  mapTier0Row,
  mapTier1Results,
  mapTier2Results,
} from '@/features/feeds/types/analysisV3';

/**
 * Base URL for Content-Analysis-V3 service
 * Default: http://localhost:8117 (Docker port)
 */
const BASE_API_URL =
  import.meta.env.VITE_ANALYSIS_V3_API_URL || 'http://localhost:8117';

/**
 * Create axios instance for V3 API
 */
const apiClient = axios.create({
  baseURL: BASE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Start analysis for a single article
 *
 * POST /api/v1/analyze
 *
 * @param request Article data and configuration
 * @returns Analysis status
 */
export const analyzeArticle = async (
  request: AnalyzeArticleRequest
): Promise<AnalyzeArticleResponse> => {
  const { data } = await apiClient.post<AnalyzeArticleResponse>(
    `${BASE_API_URL}/api/v1/analyze`,
    request
  );
  return data;
};

/**
 * Get current analysis status for an article
 *
 * GET /api/v1/status/{article_id}
 *
 * @param articleId Article UUID
 * @returns Current analysis status
 */
export const getAnalysisStatus = async (
  articleId: string
): Promise<AnalysisStatusResponse> => {
  const { data } = await apiClient.get<AnalysisStatusResponse>(
    `${BASE_API_URL}/api/v1/status/${articleId}`
  );
  return data;
};

/**
 * Get complete analysis results (all tiers)
 *
 * GET /api/v1/results/{article_id}
 *
 * @param articleId Article UUID
 * @returns Complete analysis results (Tier0, Tier1, Tier2)
 */
export const getAnalysisResults = async (
  articleId: string
): Promise<AnalysisResultsResponse> => {
  const { data } = await apiClient.get<AnalysisResultsResponse>(
    `${BASE_API_URL}/api/v1/results/${articleId}`
  );
  return data;
};

/**
 * Get Tier0 (triage) results only
 *
 * GET /api/v1/results/{article_id}/tier0
 *
 * @param articleId Article UUID
 * @returns Tier0 triage decision (raw database row)
 */
export const getTier0Results = async (
  articleId: string
): Promise<TriageDecision> => {
  const { data } = await apiClient.get<Tier0DatabaseRow>(
    `${BASE_API_URL}/api/v1/results/${articleId}/tier0`
  );
  return mapTier0Row(data);
};

/**
 * Get Tier1 (foundation extraction) results only
 *
 * GET /api/v1/results/{article_id}/tier1
 *
 * @param articleId Article UUID
 * @returns Tier1 results (entities, relations, topics, scores)
 */
export const getTier1Results = async (
  articleId: string
): Promise<Tier1Results> => {
  const { data } = await apiClient.get<Tier1ResultsDatabaseResponse>(
    `${BASE_API_URL}/api/v1/results/${articleId}/tier1`
  );
  return mapTier1Results(data);
};

/**
 * Get Tier2 (specialist analysis) results only
 *
 * GET /api/v1/results/{article_id}/tier2
 *
 * @param articleId Article UUID
 * @returns Tier2 specialist results
 */
export const getTier2Results = async (
  articleId: string
): Promise<Tier2Results> => {
  const { data } = await apiClient.get<Tier2ResultsDatabaseResponse>(
    `${BASE_API_URL}/api/v1/results/${articleId}/tier2`
  );
  return mapTier2Results(data);
};

/**
 * Check if V3 analysis exists for article
 *
 * Convenience method to quickly check if article has been analyzed.
 *
 * @param articleId Article UUID
 * @returns True if analysis exists, false otherwise
 */
export const hasV3Analysis = async (articleId: string): Promise<boolean> => {
  try {
    const status = await getAnalysisStatus(articleId);
    return status.tier0_complete;
  } catch (error) {
    // 404 or other error means no analysis
    return false;
  }
};

/**
 * Get combined Tier0 + Tier1 + Tier2 results
 *
 * Convenience method for complete analysis data.
 *
 * @param articleId Article UUID
 * @returns Combined tier results or null if not found
 */
export const getCompleteAnalysis = async (articleId: string): Promise<{
  tier0: TriageDecision;
  tier1: Tier1Results | null;
  tier2: Tier2Results | null;
} | null> => {
  try {
    const results = await getAnalysisResults(articleId);

    if (!results.tier0) {
      return null;
    }

    return {
      tier0: mapTier0Row(results.tier0 as any), // API returns raw row
      tier1: results.tier1 ? (results.tier1 as Tier1Results) : null,
      tier2: results.tier2 ? (results.tier2 as Tier2Results) : null,
    };
  } catch (error) {
    return null;
  }
};

/**
 * Batch fetch V3 analysis for multiple articles
 *
 * Note: API doesn't have native batch endpoint, so this makes parallel requests.
 *
 * @param articleIds Array of article UUIDs
 * @returns Map of article_id → analysis results
 */
export const batchGetAnalysis = async (
  articleIds: string[]
): Promise<
  Map<
    string,
    {
      tier0: TriageDecision;
      tier1: Tier1Results | null;
      tier2: Tier2Results | null;
    } | null
  >
> => {
  const results = new Map<
    string,
    {
      tier0: TriageDecision;
      tier1: Tier1Results | null;
      tier2: Tier2Results | null;
    } | null
  >();

  // Fetch all in parallel
  const promises = articleIds.map(async (id) => {
    const analysis = await getCompleteAnalysis(id);
    results.set(id, analysis);
  });

  await Promise.all(promises);

  return results;
};
