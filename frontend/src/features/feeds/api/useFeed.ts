import { useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { feedApi } from '@/api/axios';
import type { Feed } from '../types';

export const useFeed = (feedId: string): UseQueryResult<Feed, Error> => {
  const queryClient = useQueryClient();
  const previousStatusRef = useRef<string | undefined>(undefined);

  const query = useQuery<Feed>({
    queryKey: ['feeds', 'detail', feedId],
    queryFn: async () => {
      const { data } = await feedApi.get(`/feeds/${feedId}`);
      return data;
    },
    enabled: !!feedId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if assessment is pending (synced with backend polling)
      if (query.state.data?.assessment?.assessment_status === 'pending') {
        return 2000;
      }
      // Stop polling when status is not pending
      return false;
    },
  });

  // Track status changes and trigger explicit refetch on completion
  useEffect(() => {
    const currentStatus = query.data?.assessment?.assessment_status;
    const previousStatus = previousStatusRef.current;

    // Detect transition from 'pending' to 'completed' or 'failed'
    if (
      previousStatus === 'pending' &&
      (currentStatus === 'completed' || currentStatus === 'failed')
    ) {
      // Explicit refetch to ensure UI updates immediately with full assessment data
      queryClient.invalidateQueries({ queryKey: ['feeds', 'detail', feedId] });
    }

    // Update ref for next comparison
    previousStatusRef.current = currentStatus;
  }, [query.data?.assessment?.assessment_status, feedId, queryClient]);

  return query as UseQueryResult<Feed, Error>;
};
