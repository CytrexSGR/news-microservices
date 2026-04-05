/**
 * Security Data Hooks
 *
 * React Query hooks for fetching security view data
 */

import { useQuery } from '@tanstack/react-query';
import { securityApi } from '../api/securityApi';
import { useGeoMapStore } from '../store/geoMapStore';
import type { SecurityFilters, ThreatLevel } from '../types/security.types';

// =============================================================================
// Helper: Convert timeRange to days
// =============================================================================

function timeRangeToDays(timeRange: string): number {
  switch (timeRange) {
    case 'today':
      return 1;
    case '7d':
      return 7;
    case '30d':
      return 30;
    default:
      return 7;
  }
}

// =============================================================================
// Hooks
// =============================================================================

/**
 * Fetch security overview dashboard data
 */
export function useSecurityOverview(minPriority: number = 5) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);

  return useQuery({
    queryKey: ['security', 'overview', days, minPriority],
    queryFn: () => securityApi.getOverview(days, minPriority),
    staleTime: 60_000, // 1 minute
    refetchInterval: 120_000, // 2 minutes
  });
}

/**
 * Fetch paginated security events
 */
export function useSecurityEvents(
  additionalFilters: Partial<SecurityFilters> = {},
  page: number = 1,
  perPage: number = 50
) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);
  const region = filters.regions.length === 1 ? filters.regions[0] : undefined;

  return useQuery({
    queryKey: [
      'security',
      'events',
      days,
      additionalFilters.min_priority ?? 5,
      additionalFilters.category,
      additionalFilters.country,
      region,
      additionalFilters.threat_level,
      page,
      perPage,
    ],
    queryFn: () =>
      securityApi.getEvents({
        days,
        min_priority: additionalFilters.min_priority ?? 5,
        category: additionalFilters.category,
        country: additionalFilters.country,
        region: additionalFilters.region ?? region,
        threat_level: additionalFilters.threat_level,
        page,
        per_page: perPage,
      }),
    staleTime: 30_000,
  });
}

/**
 * Fetch country threat summaries
 */
export function useCountryThreats(
  minPriority: number = 5,
  minEvents: number = 1,
  limit: number = 50
) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);
  const region = filters.regions.length === 1 ? filters.regions[0] : undefined;

  return useQuery({
    queryKey: ['security', 'countries', days, minPriority, region, minEvents, limit],
    queryFn: () =>
      securityApi.getCountryThreats(days, minPriority, region, minEvents, limit),
    staleTime: 60_000,
  });
}

/**
 * Fetch detailed threat profile for a country
 */
export function useCountryThreatDetail(isoCode: string | null) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);

  return useQuery({
    queryKey: ['security', 'country', isoCode, days],
    queryFn: () => (isoCode ? securityApi.getCountryDetail(isoCode, days) : null),
    enabled: !!isoCode,
    staleTime: 60_000,
  });
}

/**
 * Fetch security markers for map
 */
export function useSecurityMarkers(
  minPriority: number = 6,
  threatLevel?: ThreatLevel,
  limit: number = 200
) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);
  const region = filters.regions.length === 1 ? filters.regions[0] : undefined;

  // Filter categories to security-relevant ones
  const securityCategories = filters.categories.filter((c) =>
    ['CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS'].includes(c)
  );
  const categories =
    securityCategories.length > 0
      ? securityCategories
      : ['CONFLICT', 'SECURITY', 'HUMANITARIAN'];

  return useQuery({
    queryKey: ['security', 'markers', days, minPriority, categories, region, limit],
    queryFn: () =>
      securityApi.getMarkers(days, minPriority, categories, region, limit),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

/**
 * Fetch critical events only (for alerts)
 */
export function useCriticalEvents(limit: number = 10) {
  const { filters } = useGeoMapStore();
  const days = timeRangeToDays(filters.timeRange);

  return useQuery({
    queryKey: ['security', 'events', 'critical', days, limit],
    queryFn: async () => {
      const result = await securityApi.getEvents({
        days,
        min_priority: 9, // Critical only
        per_page: limit,
      });
      return result.events;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
