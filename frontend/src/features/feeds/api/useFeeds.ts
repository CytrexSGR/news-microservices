import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedListResponse } from '../types';

export const useFeeds = () => {
  return useQuery<FeedListResponse>({
    queryKey: ['feeds', 'list'],
    queryFn: async () => {
      const { data } = await feedApi.get('/feeds');
      return data;
    },
  });
};
