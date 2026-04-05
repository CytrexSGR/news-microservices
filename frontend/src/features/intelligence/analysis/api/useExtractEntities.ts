/**
 * useExtractEntities Hook
 *
 * Query hook for fetching extracted entities from an article.
 * Supports automatic refetching and caching.
 */
import { useQuery } from '@tanstack/react-query';
import { extractEntities } from './analysisApi';
import type { EntitiesResponse, EntityType } from '../types/analysis.types';

interface UseExtractEntitiesOptions {
  /** Article ID to fetch entities for */
  articleId: string;
  /** Whether to enable the query */
  enabled?: boolean;
  /** Stale time in milliseconds (default: 5 minutes) */
  staleTime?: number;
}

export function useExtractEntities({
  articleId,
  enabled = true,
  staleTime = 5 * 60 * 1000,
}: UseExtractEntitiesOptions) {
  const query = useQuery<EntitiesResponse, Error>({
    queryKey: ['analysis', 'entities', articleId],
    queryFn: () => extractEntities(articleId),
    enabled: enabled && !!articleId,
    staleTime,
  });

  // Group entities by type for easier consumption
  const entitiesByType = query.data?.entities.reduce(
    (acc, entity) => {
      if (!acc[entity.type]) {
        acc[entity.type] = [];
      }
      acc[entity.type].push(entity);
      return acc;
    },
    {} as Record<EntityType, typeof query.data.entities>
  );

  // Get unique entity types present in the data
  const entityTypes = Object.keys(entitiesByType || {}) as EntityType[];

  // Get entity counts by type
  const entityCounts = entityTypes.reduce(
    (acc, type) => {
      acc[type] = entitiesByType?.[type]?.length || 0;
      return acc;
    },
    {} as Record<EntityType, number>
  );

  return {
    ...query,
    entities: query.data?.entities || [],
    entitiesByType,
    entityTypes,
    entityCounts,
    totalEntities: query.data?.entity_count || 0,
    extractedAt: query.data?.extracted_at,
  };
}
