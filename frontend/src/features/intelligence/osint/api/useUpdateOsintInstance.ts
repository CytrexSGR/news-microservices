/**
 * useUpdateOsintInstance - Update OSINT Instance Mutation Hook
 *
 * Updates an existing OSINT monitoring instance
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  OsintInstanceUpdateRequest,
  OsintInstance,
} from '../types/osint.types';

interface UpdateInstanceParams {
  instanceId: string;
  data: OsintInstanceUpdateRequest;
}

export function useUpdateOsintInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ instanceId, data }: UpdateInstanceParams): Promise<OsintInstance> => {
      return mcpClient.callTool<OsintInstance>('update_osint_instance', {
        instance_id: instanceId,
        name: data.name,
        description: data.description,
        parameters: data.parameters,
        schedule: data.schedule,
        enabled: data.enabled,
      });
    },
    onSuccess: (_, variables) => {
      // Invalidate the specific instance and list
      queryClient.invalidateQueries({ queryKey: ['osint', 'instances'] });
      queryClient.invalidateQueries({
        queryKey: ['osint', 'instance', variables.instanceId],
      });
    },
  });
}
