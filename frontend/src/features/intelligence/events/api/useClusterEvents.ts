/**
 * useClusterEvents Hook
 *
 * Fetches articles belonging to a specific cluster via REST API.
 * Transforms backend ClusterArticle data to frontend IntelligenceEvent format.
 */
import { useQuery } from '@tanstack/react-query';
import { getClusterArticles } from './clusterApi';
import type { ClusterArticle } from './clusterApi';
import type { IntelligenceEvent, RiskLevel, EventCategory } from '../types/events.types';

// Extended event type with additional article metadata
export interface ClusterArticleEvent extends IntelligenceEvent {
  published_at?: string;
  source_name?: string;
}

// Extended response type with ClusterArticleEvent
export interface ClusterArticleEventsResponse {
  cluster_id: string;
  events: ClusterArticleEvent[];
  total: number;
  page: number;
  per_page: number;
}

function transformArticleToEvent(article: ClusterArticle): ClusterArticleEvent {
  // Default values since backend doesn't provide all fields
  const riskLevel: RiskLevel = 'low';
  const category: EventCategory = 'recurring';

  return {
    id: article.id,
    title: article.title || 'Untitled Article',
    description: '', // Not available from backend
    category,
    risk_level: riskLevel,
    risk_score: (article.similarity_score || 0) * 10, // Scale 0-1 to 0-10
    entities: [], // Not available from backend
    sources: article.source_name ? [article.source_name] : [],
    first_seen: article.joined_at || article.published_at || new Date().toISOString(),
    last_updated: article.joined_at || article.published_at || new Date().toISOString(),
    article_count: 1,
    url: article.url || undefined, // Original article URL
    // Additional fields for display
    published_at: article.published_at || undefined,
    source_name: article.source_name || undefined,
  };
}

interface ClusterEventsOptions {
  page?: number;
  per_page?: number;
}

export function useClusterEvents(
  clusterId: string | undefined,
  options: ClusterEventsOptions = {},
  enabled: boolean = true
) {
  const { page = 1, per_page = 20 } = options;
  const offset = (page - 1) * per_page;

  return useQuery<ClusterArticleEventsResponse>({
    queryKey: ['intelligence', 'events', 'cluster-events', clusterId, page, per_page],
    queryFn: async () => {
      if (!clusterId) {
        throw new Error('Cluster ID is required');
      }

      const response = await getClusterArticles(clusterId, {
        limit: per_page,
        offset,
      });

      // Transform backend articles to frontend events
      const events = response.articles.map(transformArticleToEvent);

      return {
        cluster_id: clusterId,
        events,
        total: response.pagination.total,
        page,
        per_page,
      };
    },
    enabled: !!clusterId && enabled,
    staleTime: 30000,
  });
}
