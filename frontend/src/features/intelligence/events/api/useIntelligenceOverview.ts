/**
 * useIntelligenceOverview Hook
 *
 * Fetches overview dashboard data for intelligence events
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { IntelligenceOverview } from '../types/events.types';

export function useIntelligenceOverview(refetchInterval: number = 60000) {
  return useQuery<IntelligenceOverview>({
    queryKey: ['intelligence', 'events', 'overview'],
    queryFn: async () => {
      return mcpClient.callTool<IntelligenceOverview>('get_intelligence_overview');
    },
    refetchInterval,
    staleTime: 30000,
  });
}
