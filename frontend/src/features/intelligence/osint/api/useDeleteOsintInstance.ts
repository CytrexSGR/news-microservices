/**
 * useDeleteOsintInstance - Delete OSINT Instance Mutation Hook
 *
 * Deletes an OSINT monitoring instance
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

interface DeleteResponse {
  success: boolean;
  instance_id: string;
}

export function useDeleteOsintInstance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (instanceId: string): Promise<DeleteResponse> => {
      return mcpClient.callTool<DeleteResponse>('delete_osint_instance', {
        instance_id: instanceId,
      });
    },
    onSuccess: () => {
      // Invalidate instances list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['osint', 'instances'] });
    },
  });
}
