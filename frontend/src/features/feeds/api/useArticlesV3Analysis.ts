/**
 * Hook to fetch V3 analysis data for articles
 *
 * Since feed-service doesn't yet include V3 analysis in article responses,
 * this hook fetches V3 data separately from content-analysis-v3 service.
 */

import { useQuery } from '@tanstack/react-query';
import { getCompleteAnalysis } from '@/lib/api/contentAnalysisV3';
import type { TriageDecision, Tier1Results, Tier2Results } from '@/features/feeds/types/analysisV3';

export interface V3AnalysisData {
  tier0: TriageDecision;
  tier1: Tier1Results | null;
  tier2: Tier2Results | null;
}

/**
 * Fetch V3 analysis for a single article
 *
 * @param articleId Article UUID
 * @param enabled Whether to enable the query (default: true)
 * @returns V3 analysis data or null if not found
 */
export function useArticleV3Analysis(articleId: string, enabled = true) {
  return useQuery<V3AnalysisData | null>({
    queryKey: ['article-v3-analysis', articleId],
    queryFn: () => getCompleteAnalysis(articleId),
    enabled,
    // Don't refetch automatically - V3 analysis is immutable once complete
    refetchOnWindowFocus: false,
    staleTime: Infinity, // V3 results don't change, cache forever
    retry: 1, // Only retry once if 404 (analysis doesn't exist yet)
  });
}

/**
 * Fetch V3 analysis for multiple articles
 *
 * Returns a Map of article_id → V3 analysis data.
 * Articles without V3 analysis will have null value.
 *
 * @param articleIds Array of article UUIDs
 * @param enabled Whether to enable the query (default: true)
 * @returns Map of article_id → V3 analysis data
 */
export function useBatchArticlesV3Analysis(articleIds: string[], enabled = true) {
  return useQuery<Map<string, V3AnalysisData | null>>({
    queryKey: ['articles-v3-analysis-batch', articleIds.sort().join(',')],
    queryFn: async () => {
      // Fetch all in parallel (limited concurrency handled by browser)
      const results = new Map<string, V3AnalysisData | null>();

      const promises = articleIds.map(async (id) => {
        try {
          const analysis = await getCompleteAnalysis(id);
          results.set(id, analysis);
        } catch (error) {
          // 404 or other error = no V3 analysis yet
          results.set(id, null);
        }
      });

      await Promise.all(promises);
      return results;
    },
    enabled: enabled && articleIds.length > 0,
    // Don't refetch automatically - V3 analysis is immutable
    refetchOnWindowFocus: false,
    staleTime: Infinity,
    retry: false, // Don't retry batch requests
  });
}
