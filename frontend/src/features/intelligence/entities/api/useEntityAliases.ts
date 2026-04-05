/**
 * useEntityAliases Hook
 *
 * Query hook for fetching aliases of a canonical entity.
 */
import { useQuery } from '@tanstack/react-query';
import { getEntityAliases } from './entitiesApi';
import type { EntityType } from '../types/entities.types';

interface UseEntityAliasesOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

export function useEntityAliases(
  canonicalName: string | null,
  entityType: EntityType | null,
  options?: UseEntityAliasesOptions
) {
  const { enabled = true, refetchInterval } = options || {};

  return useQuery<string[]>({
    queryKey: ['entities', 'aliases', canonicalName, entityType],
    queryFn: () => getEntityAliases(canonicalName!, entityType!),
    enabled: enabled && !!canonicalName && !!entityType,
    refetchInterval,
    staleTime: 300000, // 5 minutes - aliases don't change often
  });
}
