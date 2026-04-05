/**
 * useArticleEntities Hook
 *
 * Fetches all entities extracted from a specific article.
 * Results are ordered by confidence score and mention count.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useArticleEntities('article-123', {
 *   entityType: 'PERSON',
 *   limit: 50
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getArticleEntities } from '@/lib/api/knowledgeGraphPublic'
import type { ArticleEntitiesResponse } from '@/types/knowledgeGraphPublic'

export interface UseArticleEntitiesOptions {
  entityType?: string
  limit?: number
  enabled?: boolean
}

export function useArticleEntities(
  articleId: string | null,
  options?: UseArticleEntitiesOptions
) {
  return useQuery<ArticleEntitiesResponse>({
    queryKey: [
      'knowledge-graph',
      'article-entities',
      articleId,
      options?.entityType,
      options?.limit,
    ],
    queryFn: () =>
      getArticleEntities(
        articleId!,
        options?.entityType,
        options?.limit ?? 50
      ),
    enabled: !!articleId && (options?.enabled ?? true),
    staleTime: 30 * 60 * 1000, // 30 minutes - article entities are stable
    gcTime: 60 * 60 * 1000, // 1 hour
  })
}
