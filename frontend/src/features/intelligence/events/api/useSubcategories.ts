/**
 * useSubcategories Hook
 *
 * Fetches subcategories for intelligence events
 */
import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { SubcategoriesResponse, EventCategory } from '../types/events.types';

interface SubcategoryFilters {
  parent_category?: EventCategory;
}

export function useSubcategories(
  filters: SubcategoryFilters = {},
  refetchInterval: number = 120000
) {
  return useQuery<SubcategoriesResponse>({
    queryKey: ['intelligence', 'events', 'subcategories', filters],
    queryFn: async () => {
      return mcpClient.callTool<SubcategoriesResponse>('get_subcategories', {
        parent_category: filters.parent_category,
      });
    },
    refetchInterval,
    staleTime: 60000,
  });
}
