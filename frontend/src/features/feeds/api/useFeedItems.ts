import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedItem } from '../types';

interface UseFeedItemsParams {
  feedId: string;
  limit?: number;
  offset?: number;
}

/**
 * Fetch feed items (articles) for a specific feed
 */
export function useFeedItems({ feedId, limit = 20, offset = 0 }: UseFeedItemsParams) {
  return useQuery<FeedItem[]>({
    queryKey: ['feedItems', feedId, limit, offset],
    queryFn: async () => {
      const { data } = await feedApi.get(
        `/feeds/${feedId}/items`,
        {
          params: { limit, offset }
        }
      );
      return data;
    },
    enabled: !!feedId,
  });
}
