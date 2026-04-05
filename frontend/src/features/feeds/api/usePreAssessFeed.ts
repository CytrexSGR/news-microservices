import { useMutation } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { PreAssessmentRequest, PreAssessmentResponse } from '../types/createFeed';

export function usePreAssessFeed() {
  return useMutation({
    mutationFn: async (data: PreAssessmentRequest): Promise<PreAssessmentResponse> => {
      // Send URL as query parameter
      const response = await feedApi.post<PreAssessmentResponse>(
        '/feeds/pre-assess',
        null,
        {
          params: { url: data.url },
        }
      );
      return response.data;
    },
  });
}
