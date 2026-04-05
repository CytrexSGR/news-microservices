/**
 * useOsintInstances - OSINT Instances List Query Hook
 *
 * Fetches all OSINT monitoring instances with pagination
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { OsintInstancesResponse, OsintInstance } from '../types/osint.types';

interface InstanceFilters {
  template_name?: string;
  enabled?: boolean;
  page?: number;
  per_page?: number;
}

export function useOsintInstances(
  filters: InstanceFilters = {},
  refetchInterval: number = 30000
) {
  return useQuery<OsintInstancesResponse>({
    queryKey: ['osint', 'instances', filters],
    queryFn: async () => {
      return mcpClient.callTool<OsintInstancesResponse>('list_osint_instances', {
        template_name: filters.template_name,
        enabled: filters.enabled,
        page: filters.page ?? 1,
        per_page: filters.per_page ?? 20,
      });
    },
    refetchInterval,
    staleTime: 15000,
  });
}

/**
 * Hook to get a single instance by ID
 */
export function useOsintInstance(instanceId: string | undefined, enabled: boolean = true) {
  const { data, isLoading, error } = useOsintInstances({}, 0);

  const instance = data?.instances.find((i) => i.id === instanceId);

  return {
    instance,
    isLoading,
    error,
    isNotFound: !isLoading && !instance && enabled,
  };
}
