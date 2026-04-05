/**
 * useCreateOsintInstance - Create OSINT Instance Mutation Hook
 *
 * Creates a new OSINT monitoring instance
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  OsintInstanceCreateRequest,
  OsintInstance,
} from '../types/osint.types';

export function useCreateOsintInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: OsintInstanceCreateRequest): Promise<OsintInstance> => {
      return mcpClient.callTool<OsintInstance>('create_osint_instance', {
        template_name: request.template_name,
        name: request.name,
        description: request.description,
        parameters: request.parameters,
        schedule: request.schedule,
        enabled: request.enabled ?? true,
      });
    },
    onSuccess: () => {
      // Invalidate instances list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['osint', 'instances'] });
    },
  });
}
