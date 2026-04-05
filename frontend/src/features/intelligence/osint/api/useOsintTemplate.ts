/**
 * useOsintTemplate - Single OSINT Template Query Hook
 *
 * Fetches a specific OSINT template by name
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { OsintTemplate } from '../types/osint.types';

export function useOsintTemplate(templateName: string | undefined, enabled: boolean = true) {
  return useQuery<OsintTemplate>({
    queryKey: ['osint', 'template', templateName],
    queryFn: async () => {
      return mcpClient.callTool<OsintTemplate>('get_osint_template', {
        template_name: templateName,
      });
    },
    enabled: !!templateName && enabled,
    staleTime: 60000,
  });
}
