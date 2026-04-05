/**
 * useOsintTemplates - OSINT Templates List Query Hook
 *
 * Fetches all available OSINT templates
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { OsintTemplate, OsintTemplatesResponse } from '../types/osint.types';

export function useOsintTemplates(refetchInterval: number = 120000) {
  return useQuery<OsintTemplatesResponse>({
    queryKey: ['osint', 'templates'],
    queryFn: async () => {
      return mcpClient.callTool<OsintTemplatesResponse>('list_osint_templates');
    },
    refetchInterval,
    staleTime: 60000,
  });
}

/**
 * Convenience hook to get templates grouped by category
 */
export function useOsintTemplatesByCategory(refetchInterval: number = 120000) {
  const { data, isLoading, error, refetch } = useOsintTemplates(refetchInterval);

  const groupedTemplates = data?.templates.reduce(
    (acc, template) => {
      const category = template.category;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(template);
      return acc;
    },
    {} as Record<string, OsintTemplate[]>
  ) ?? {};

  return {
    templates: data?.templates ?? [],
    groupedTemplates,
    total: data?.total ?? 0,
    isLoading,
    error,
    refetch,
  };
}
