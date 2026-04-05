/**
 * useOsintAlerts - OSINT Alerts List Query Hook
 *
 * Fetches OSINT alerts with filtering and pagination
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { OsintAlertsResponse, AlertSeverity } from '../types/osint.types';

interface AlertFilters {
  instance_id?: string;
  severity?: AlertSeverity;
  acknowledged?: boolean;
  page?: number;
  per_page?: number;
}

export function useOsintAlerts(
  filters: AlertFilters = {},
  refetchInterval: number = 15000
) {
  return useQuery<OsintAlertsResponse>({
    queryKey: ['osint', 'alerts', filters],
    queryFn: async () => {
      return mcpClient.callTool<OsintAlertsResponse>('list_osint_alerts', {
        instance_id: filters.instance_id,
        severity: filters.severity,
        acknowledged: filters.acknowledged,
        page: filters.page ?? 1,
        per_page: filters.per_page ?? 20,
      });
    },
    refetchInterval,
    staleTime: 10000,
  });
}

/**
 * Hook to get unacknowledged alerts count
 */
export function useUnacknowledgedAlertsCount(refetchInterval: number = 15000) {
  const { data, isLoading } = useOsintAlerts(
    { acknowledged: false, per_page: 1 },
    refetchInterval
  );

  return {
    count: data?.total ?? 0,
    isLoading,
  };
}
