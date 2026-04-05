/**
 * useAcknowledgeAlert - Acknowledge OSINT Alert Mutation Hook
 *
 * Marks an OSINT alert as acknowledged
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  AcknowledgeAlertRequest,
  AcknowledgeAlertResponse,
} from '../types/osint.types';

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: AcknowledgeAlertRequest): Promise<AcknowledgeAlertResponse> => {
      return mcpClient.callTool<AcknowledgeAlertResponse>('acknowledge_osint_alert', {
        alert_id: request.alert_id,
        comment: request.comment,
      });
    },
    onSuccess: () => {
      // Invalidate alerts queries
      queryClient.invalidateQueries({ queryKey: ['osint', 'alerts'] });
      queryClient.invalidateQueries({ queryKey: ['osint', 'alert-stats'] });
    },
  });
}
