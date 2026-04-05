import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedItemWithFeed } from '../types';

export interface UseArticlesParams {
  limit?: number;
  offset?: number;
  feedIds?: string[];
  dateFrom?: string;
  dateTo?: string;
  hasContent?: boolean;
  sentiment?: string | null;
  category?: string | null;
  sourceType?: string | null;
  sortBy?: 'published_at' | 'created_at';
  order?: 'asc' | 'desc';
}

/**
 * Hook to fetch articles across all feeds with filtering and pagination.
 *
 * Used by the Articles section for cross-feed article listings.
 */
export function useArticles(params: UseArticlesParams = {}) {
  const {
    limit = 20,
    offset = 0,
    feedIds,
    dateFrom,
    dateTo,
    hasContent,
    sentiment,
    category,
    sourceType,
    sortBy = 'created_at',
    order = 'desc',
  } = params;

  return useQuery<FeedItemWithFeed[]>({
    queryKey: ['articles', { limit, offset, feedIds, dateFrom, dateTo, hasContent, sentiment, category, sourceType, sortBy, order }],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.set('limit', limit.toString());
      searchParams.set('offset', offset.toString());
      searchParams.set('sort_by', sortBy);
      searchParams.set('order', order);

      if (feedIds && feedIds.length > 0) {
        searchParams.set('feed_ids', feedIds.join(','));
      }

      if (dateFrom) {
        searchParams.set('date_from', dateFrom);
      }

      if (dateTo) {
        searchParams.set('date_to', dateTo);
      }

      if (hasContent !== undefined) {
        searchParams.set('has_content', hasContent.toString());
      }

      if (sentiment) {
        searchParams.set('sentiment', sentiment);
      }

      if (category) {
        searchParams.set('category', category);
      }

      if (sourceType) {
        searchParams.set('source_type', sourceType);
      }

      const { data } = await feedApi.get(`/feeds/items?${searchParams.toString()}`);

      // Transform API response: map pipeline_execution → v2_analysis
      // Backend returns 'pipeline_execution' but frontend expects 'v2_analysis'
      // V3 analysis is passed through directly (backend returns v3_analysis, frontend uses v3_analysis)
      return data.map((item: any) => ({
        ...item,
        v2_analysis: item.pipeline_execution || item.v2_analysis, // Support both field names
        v3_analysis: item.v3_analysis, // V3 analysis (new - direct pass-through)
      }));
    },
    // Refetch options
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
    // Auto-refresh for articles with incomplete analysis (V2 Pipeline)
    // Also refresh periodically to keep "X minutes ago" timestamps current
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || !Array.isArray(data)) return 30000; // Default: 30s refresh

      // Check if any articles are missing V2 analysis or still processing
      const hasIncompleteAnalysis = data.some(
        (article: any) => {
          // No v2_analysis at all = incomplete
          if (!article.v2_analysis) return true;

          // Pipeline still running (success === null) = incomplete
          if (article.v2_analysis.success === null) return true;

          // Pipeline has error_message = failed but completed
          // Still want to refresh in case it gets reprocessed
          if (article.v2_analysis.error_message) return true;

          // Pipeline execution exists and completed successfully = complete
          return false;
        }
      );

      // Fast refresh (5s) if incomplete, slower refresh (30s) to keep timestamps current
      return hasIncompleteAnalysis ? 5000 : 30000;
    },
  });
}
