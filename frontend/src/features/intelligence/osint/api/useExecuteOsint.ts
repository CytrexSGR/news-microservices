/**
 * useExecuteOsint - Execute OSINT Instance Mutation Hook
 *
 * Triggers execution of an OSINT monitoring instance
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  ExecuteOsintRequest,
  OsintExecutionResponse,
} from '../types/osint.types';

export function useExecuteOsint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: ExecuteOsintRequest): Promise<OsintExecutionResponse> => {
      return mcpClient.callTool<OsintExecutionResponse>(
        'execute_osint_instance',
        {
          instance_id: request.instance_id,
          parameters: request.parameters,
        },
        { timeout: 120000 } // Execution may take up to 2 minutes
      );
    },
    onSuccess: (data) => {
      // Invalidate instance queries to show updated last_run
      queryClient.invalidateQueries({ queryKey: ['osint', 'instances'] });
      queryClient.invalidateQueries({
        queryKey: ['osint', 'instance', data.execution.instance_id],
      });
      // Invalidate executions list
      queryClient.invalidateQueries({ queryKey: ['osint', 'executions'] });
    },
  });
}
