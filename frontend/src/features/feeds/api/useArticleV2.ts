import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';

/**
 * Hook to fetch V2 analysis for a specific article from feed-service API.
 *
 * Returns article metadata and pipeline_execution data from article_analysis table.
 * (Note: content-analysis-v2 was archived 2025-11-24, analysis now handled by feed-service)
 *
 * @param itemId - UUID of the feed item (article)
 */
export const useArticleV2 = (itemId: string) => {
  return useQuery({
    queryKey: ['article', 'v2', itemId],
    queryFn: async () => {
      // Note: baseURL already includes /api/v1 (see .env.local)
      const { data } = await feedApi.get(`/feeds/items/${itemId}`);

      // Transform API response: map pipeline_execution → v2_analysis
      // Backend returns 'pipeline_execution' but frontend expects 'v2_analysis'
      const pipelineData = data.pipeline_execution || data.v2_analysis;

      // Generate agents_executed array from tier2_summary keys
      // Frontend expects: agents_executed: string[]
      // Backend provides: tier2_summary: { [agentName]: {...} }
      const agentsExecuted = pipelineData?.tier2_summary
        ? Object.keys(pipelineData.tier2_summary)
        : [];

      return {
        ...data,
        v2_analysis: {
          ...pipelineData,
          agents_executed: agentsExecuted,  // Add missing field for frontend
        },
      };
    },
    enabled: !!itemId,
    refetchOnWindowFocus: true,   // Enable auto-refresh on tab focus
    refetchOnMount: true,          // Refetch on component mount
    staleTime: 30 * 1000,          // Cache for 30 seconds (reduced from 5 minutes)
  });
};
