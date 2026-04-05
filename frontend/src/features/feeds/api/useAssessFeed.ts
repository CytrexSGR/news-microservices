import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';

interface AssessmentResponse {
  message: string;
  feed_id: string;
  status: string;
}

export const useAssessFeed = () => {
  const queryClient = useQueryClient();

  return useMutation<AssessmentResponse, Error, string>({
    mutationFn: async (feedId: string) => {
      const { data } = await feedApi.post(`/feeds/${feedId}/assess`);
      return data;
    },
    onSuccess: (_, feedId) => {
      // Invalidate feed detail query to refetch updated assessment data
      queryClient.invalidateQueries({ queryKey: ['feeds', 'detail', feedId] });
    },
  });
};
