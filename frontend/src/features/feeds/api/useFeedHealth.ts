import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedHealth } from '../types';

export const useFeedHealth = (feedId: string) => {
  return useQuery<FeedHealth>({
    queryKey: ['feeds', 'health', feedId],
    queryFn: async () => {
      const { data } = await feedApi.get(`/feeds/${feedId}/health`);
      return data;
    },
    enabled: !!feedId,
  });
};
