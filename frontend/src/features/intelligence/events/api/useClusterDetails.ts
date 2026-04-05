/**
 * useClusterDetails Hook
 *
 * Fetches detailed information for a specific cluster via REST API.
 * Transforms backend data to frontend ClusterDetails format.
 */
import { useQuery } from '@tanstack/react-query';
import { getClusterById } from './clusterApi';
import type { ClusterDetailBackend } from './clusterApi';
import type { ClusterDetails, EventCategory, RiskLevel } from '../types/events.types';

/**
 * Transform backend cluster data to frontend ClusterDetails format
 */
function transformToClusterDetails(backend: ClusterDetailBackend): ClusterDetails {
  // Determine category based on status and is_breaking
  let category: EventCategory = 'recurring';
  if (backend.is_breaking) {
    category = 'breaking';
  } else if (backend.status === 'active' && backend.article_count > 10) {
    category = 'developing';
  } else if (backend.tension_score && backend.tension_score > 0.7) {
    category = 'trend';
  }

  // Determine risk level based on tension_score
  let riskLevel: RiskLevel = 'low';
  const tensionScore = backend.tension_score || 0;
  if (tensionScore >= 0.8) {
    riskLevel = 'critical';
  } else if (tensionScore >= 0.6) {
    riskLevel = 'high';
  } else if (tensionScore >= 0.4) {
    riskLevel = 'medium';
  }

  // Extract entity names from primary_entities
  const topEntities = backend.primary_entities?.map(e => e.name) || [];

  return {
    id: backend.id,
    name: backend.title,
    category,
    events_count: backend.article_count,
    risk_level: riskLevel,
    avg_risk_score: tensionScore * 10, // Scale 0-1 to 0-10
    top_entities: topEntities,
    created_at: backend.first_seen_at,
    last_activity: backend.last_updated_at,
    trending: backend.is_breaking || (backend.article_count > 5 && backend.status === 'active'),
    // These fields are not available from the backend yet
    events: [],
    related_clusters: [],
    keywords: [],
    timeline: [],
  };
}

export function useClusterDetails(
  clusterId: string | undefined,
  enabled: boolean = true
) {
  return useQuery<ClusterDetails>({
    queryKey: ['intelligence', 'events', 'cluster', clusterId],
    queryFn: async () => {
      if (!clusterId) {
        throw new Error('Cluster ID is required');
      }
      const backend = await getClusterById(clusterId);
      return transformToClusterDetails(backend);
    },
    enabled: !!clusterId && enabled,
    staleTime: 30000,
  });
}
