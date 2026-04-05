/**
 * useRiskHistory Hook
 *
 * Fetches historical risk score data for visualization
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { RiskHistoryResponse } from '../types/events.types';

export type RiskHistoryTimeframe = '24h' | '7d' | '30d' | '90d';

interface RiskHistoryOptions {
  timeframe?: RiskHistoryTimeframe;
  cluster_id?: string;
}

export function useRiskHistory(
  options: RiskHistoryOptions = {},
  refetchInterval: number = 300000
) {
  const { timeframe = '7d', cluster_id } = options;

  return useQuery<RiskHistoryResponse>({
    queryKey: ['intelligence', 'events', 'risk-history', timeframe, cluster_id],
    queryFn: async () => {
      return mcpClient.callTool<RiskHistoryResponse>('get_risk_history', {
        timeframe,
        cluster_id,
      });
    },
    refetchInterval,
    staleTime: 60000,
  });
}
