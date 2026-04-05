import { useQuery } from '@tanstack/react-query';
import { getIntelligenceOverview } from './intelligenceApi';
import type { OverviewResponse } from '../types/intelligence.types';

export function useIntelligenceOverview(refetchInterval: number = 60000) {
  return useQuery<OverviewResponse>({
    queryKey: ['intelligence', 'overview'],
    queryFn: getIntelligenceOverview,
    refetchInterval,
    staleTime: 30000,
  });
}
