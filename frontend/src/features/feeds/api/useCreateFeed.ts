import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedCreateInput } from '../types/createFeed';
import type { Feed } from '../types';

interface CreateFeedResponse extends Feed {}

export function useCreateFeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: FeedCreateInput): Promise<CreateFeedResponse> => {
      const response = await feedApi.post<CreateFeedResponse>('/feeds', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate feeds list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}
