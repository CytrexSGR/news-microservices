import { useQuery } from '@tanstack/react-query'
import { getAssessmentHistory } from '@/lib/api/feedServiceAdmin'
import type { AssessmentHistoryResponse } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch assessment history for a specific feed
 * @param feedId - Feed ID
 * @param limit - Number of history entries to fetch (default: 10)
 * @param enabled - Whether the query should run (default: true)
 */
export const useAssessmentHistory = (
  feedId: string,
  limit: number = 10,
  enabled: boolean = true
) => {
  return useQuery<AssessmentHistoryResponse>({
    queryKey: ['feed-service', 'feeds', feedId, 'assessment-history', limit],
    queryFn: () => getAssessmentHistory(feedId, limit),
    enabled: enabled && !!feedId,
  })
}
