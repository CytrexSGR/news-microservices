import { useQuery } from '@tanstack/react-query';
import { getLatestEvents, getSubcategories } from './intelligenceApi';
import type { LatestEventsResponse, SubcategoriesResponse } from '../types/intelligence.types';

interface LatestEventsFilters {
  hours?: number;
  limit?: number;
}

export function useLatestEvents(
  filters: LatestEventsFilters = { hours: 4, limit: 20 },
  refetchInterval: number = 30000
) {
  return useQuery<LatestEventsResponse>({
    queryKey: ['intelligence', 'latest-events', filters],
    queryFn: () => getLatestEvents(filters),
    refetchInterval,
    staleTime: 15000,
  });
}

export function useSubcategories(refetchInterval: number = 60000) {
  return useQuery<SubcategoriesResponse>({
    queryKey: ['intelligence', 'subcategories'],
    queryFn: getSubcategories,
    refetchInterval,
    staleTime: 30000,
  });
}

/**
 * Extract trending entities from latest events
 * Returns aggregated counts of persons, organizations, and locations
 */
export function useTrendingEntities(hours: number = 4, limit: number = 50) {
  const { data: eventsData, isLoading, error, refetch } = useLatestEvents({ hours, limit });

  const trendingEntities = {
    persons: new Map<string, number>(),
    organizations: new Map<string, number>(),
    locations: new Map<string, number>(),
  };

  if (eventsData?.events) {
    for (const event of eventsData.events) {
      if (event.entities) {
        for (const person of event.entities.persons || []) {
          trendingEntities.persons.set(
            person,
            (trendingEntities.persons.get(person) || 0) + 1
          );
        }
        for (const org of event.entities.organizations || []) {
          trendingEntities.organizations.set(
            org,
            (trendingEntities.organizations.get(org) || 0) + 1
          );
        }
        for (const loc of event.entities.locations || []) {
          trendingEntities.locations.set(
            loc,
            (trendingEntities.locations.get(loc) || 0) + 1
          );
        }
      }
    }
  }

  // Sort by count and take top entries
  const sortedPersons = Array.from(trendingEntities.persons.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const sortedOrgs = Array.from(trendingEntities.organizations.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const sortedLocations = Array.from(trendingEntities.locations.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return {
    persons: sortedPersons,
    organizations: sortedOrgs,
    locations: sortedLocations,
    totalEvents: eventsData?.total || 0,
    isLoading,
    error,
    refetch,
  };
}
