import { useQuery } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { FeedAssessment } from '../types';

export interface AssessmentHistoryItem extends FeedAssessment {
  id: string;
  created_at: string;
}

export const useAssessmentHistory = (feedId: string, limit = 10) => {
  return useQuery<AssessmentHistoryItem[]>({
    queryKey: ['feeds', feedId, 'assessment-history', limit],
    queryFn: async () => {
      const { data } = await feedApi.get(
        `/feeds/${feedId}/assessment-history?limit=${limit}`
      );
      return data;
    },
    enabled: !!feedId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
