// frontend/src/features/geo-map/hooks/useAnomalies.ts

import { useQuery } from '@tanstack/react-query';

interface AnomalyData {
  entity: string;
  entity_type: string;
  current_count: number;
  baseline_avg: number;
  baseline_stddev: number;
  deviation_factor: number;
  is_anomaly: boolean;
  trend: 'spike' | 'elevated' | 'normal' | 'low';
  category_breakdown: Record<string, number>;
}

interface AnomalyResponse {
  period: string;
  baseline_days: number;
  anomalies: AnomalyData[];
  escalating_regions: string[];
}

const getApiBase = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:8115/api/v1/geo/security`;
};

export function useAnomalies(period = '24h', minDeviation = 1.5) {
  return useQuery<AnomalyResponse>({
    queryKey: ['security', 'anomalies', period, minDeviation],
    queryFn: async () => {
      const response = await fetch(
        `${getApiBase()}/anomalies?period=${period}&min_deviation=${minDeviation}`
      );
      if (!response.ok) throw new Error('Failed to fetch anomalies');
      return response.json();
    },
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}
