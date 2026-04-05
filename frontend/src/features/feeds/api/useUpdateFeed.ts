import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { Feed } from '../types';

interface UpdateFeedVariables {
  feedId: string;
  updates: Partial<Feed>;
}

export function useUpdateFeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ feedId, updates }: UpdateFeedVariables) => {
      const response = await feedApi.put<Feed>(
        `/feeds/${feedId}`,
        updates
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      // Invalidate and refetch queries
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      queryClient.invalidateQueries({ queryKey: ['feed', variables.feedId] });
    },
  });
}
