/**
 * useAlertStats - OSINT Alert Statistics Query Hook
 *
 * Fetches aggregated statistics about OSINT alerts
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { AlertStats } from '../types/osint.types';

export function useAlertStats(refetchInterval: number = 30000) {
  return useQuery<AlertStats>({
    queryKey: ['osint', 'alert-stats'],
    queryFn: async () => {
      return mcpClient.callTool<AlertStats>('get_osint_alert_stats');
    },
    refetchInterval,
    staleTime: 15000,
  });
}
