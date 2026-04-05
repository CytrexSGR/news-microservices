/**
 * useGraphQuality - Graph Quality Report Query Hook
 *
 * Fetches the current graph quality metrics and recommendations
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { GraphQualityReport } from '../types/osint.types';

export function useGraphQuality(refetchInterval: number = 60000) {
  return useQuery<GraphQualityReport>({
    queryKey: ['osint', 'graph-quality'],
    queryFn: async () => {
      return mcpClient.callTool<GraphQualityReport>('analyze_graph_quality');
    },
    refetchInterval,
    staleTime: 30000,
  });
}
