/**
 * API client for Knowledge Graph Service Admin Dashboard
 */

import axios from 'axios'
import type {
  HealthCheck,
  Neo4jHealth,
  RabbitMQHealth,
  BasicHealth,
  GraphStats,
  GraphResponse,
  TopEntity,
  GrowthDataPoint,
  RelationshipStats,
  EntitySearchResult,
  CrossArticleCoverageStats,
  DetailedGraphStats,
  DisambiguationQualityResponse,
  MergeEvent,
  NotApplicableTrendDataPoint,
  RelationshipQualityTrendDataPoint,
} from '@/types/knowledgeGraph'

// Knowledge Graph Service URL (from docker-compose.yml)
const BASE_URL = import.meta.env.VITE_KG_API_URL || 'http://localhost:8111'

// Create axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===========================
// Health Check Endpoints
// ===========================

export const getBasicHealth = async (): Promise<BasicHealth> => {
  const { data } = await apiClient.get<BasicHealth>('/')
  return data
}

export const getServiceHealth = async (): Promise<HealthCheck> => {
  const { data } = await apiClient.get<HealthCheck>('/health/ready')
  return data
}

export const getNeo4jHealth = async (): Promise<Neo4jHealth> => {
  const { data } = await apiClient.get<Neo4jHealth>('/health/neo4j')
  return data
}

export const getRabbitMQHealth = async (): Promise<RabbitMQHealth> => {
  const { data } = await apiClient.get<RabbitMQHealth>('/health/rabbitmq')
  return data
}

// ===========================
// Graph Statistics Endpoints
// ===========================

export const getGraphStats = async (): Promise<GraphStats> => {
  const { data} = await apiClient.get<GraphStats>('/api/v1/graph/stats')
  return data
}

export const getDetailedGraphStats = async (): Promise<DetailedGraphStats> => {
  const { data } = await apiClient.get<DetailedGraphStats>('/api/v1/graph/stats/detailed')
  return data
}

// ===========================
// Graph Query Endpoints
// ===========================

export const getEntityConnections = async (
  entityName: string,
  relationshipType?: string,
  limit: number = 100
): Promise<GraphResponse> => {
  const { data } = await apiClient.get<GraphResponse>(
    `/api/v1/graph/entity/${encodeURIComponent(entityName)}/connections`,
    {
      params: {
        relationship_type: relationshipType,
        limit,
      },
    }
  )
  return data
}

// ===========================
// Phase 2: Analytics Endpoints
// ===========================

export const getTopEntities = async (
  limit: number = 10,
  entityType?: string
): Promise<TopEntity[]> => {
  const { data } = await apiClient.get<TopEntity[]>(
    '/api/v1/graph/analytics/top-entities',
    {
      params: { limit, entity_type: entityType },
    }
  )
  return data
}

export const getGrowthHistory = async (days: number = 30): Promise<GrowthDataPoint[]> => {
  const { data } = await apiClient.get<GrowthDataPoint[]>(
    '/api/v1/graph/analytics/growth-history',
    {
      params: { days },
    }
  )
  return data
}

export const getRelationshipStats = async (): Promise<RelationshipStats> => {
  const { data } = await apiClient.get<RelationshipStats>(
    '/api/v1/graph/analytics/relationship-stats'
  )
  return data
}

export const getCrossArticleCoverage = async (
  topLimit: number = 10
): Promise<CrossArticleCoverageStats> => {
  const { data } = await apiClient.get<CrossArticleCoverageStats>(
    '/api/v1/graph/analytics/cross-article-coverage',
    {
      params: { top_limit: topLimit },
    }
  )
  return data
}

export const getNotApplicableTrends = async (
  days: number = 30
): Promise<NotApplicableTrendDataPoint[]> => {
  const { data } = await apiClient.get<NotApplicableTrendDataPoint[]>(
    '/api/v1/graph/analytics/not-applicable-trends',
    {
      params: { days },
    }
  )
  return data
}

export const getRelationshipQualityTrends = async (
  days: number = 30
): Promise<RelationshipQualityTrendDataPoint[]> => {
  const { data } = await apiClient.get<RelationshipQualityTrendDataPoint[]>(
    '/api/v1/graph/analytics/relationship-quality-trends',
    {
      params: { days },
    }
  )
  return data
}

// ===========================
// Phase 4: Data Quality Endpoints
// ===========================

export const getDisambiguationQuality = async (): Promise<DisambiguationQualityResponse> => {
  const { data } = await apiClient.get<DisambiguationQualityResponse>(
    '/api/v1/graph/quality/disambiguation'
  )
  return data
}

export const getIntegrityCheck = async (): Promise<{
  integrity_percentage: number
  total_issues: number
  total_entities: number
  issues_by_type: Record<string, { count: number; sample: string[] }>
  query_time_ms: number
}> => {
  const { data } = await apiClient.get('/api/v1/graph/quality/integrity')
  return data
}

// ===========================
// Entity Merge History (entity-canonicalization-service)
// ===========================

/**
 * Get entity merge history from canonicalization service.
 * Note: This calls a different service (8112) than the rest of this client (8111).
 */
export const getEntityMergeHistory = async (limit: number = 20): Promise<MergeEvent[]> => {
  // Entity Canonicalization Service URL (port 8112, not 8111)
  const CANON_BASE_URL = import.meta.env.VITE_CANON_API_URL || 'http://localhost:8112'
  const { data } = await axios.get<MergeEvent[]>(
    `${CANON_BASE_URL}/api/v1/canonicalization/history/merges`,
    {
      params: { limit }
    }
  )
  return data
}

// ===========================
// Phase 3: Entity Search (to be implemented in backend)
// ===========================

export const searchEntities = async (
  _query: string,
  _limit: number = 10
): Promise<EntitySearchResult[]> => {
  // TODO: Backend endpoint not yet implemented
  // const { data} = await apiClient.get<EntitySearchResult[]>('/api/v1/graph/search', {
  //   params: { query: _query, limit: _limit },
  // })
  // return data

  // Temporary: Return empty array
  return []
}
