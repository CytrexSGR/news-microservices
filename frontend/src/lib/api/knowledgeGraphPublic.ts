/**
 * Public API Client for Knowledge Graph Service
 *
 * Provides typed functions for public-facing endpoints:
 * - Entity search with autocomplete
 * - Pathfinding between entities
 * - Article entity relationships
 * - Entity connections (from admin client)
 *
 * Usage:
 *   import { searchEntities, findPath, getArticleEntities } from '@/lib/api/knowledgeGraphPublic'
 *
 * Base URL configured via environment variable:
 *   VITE_KG_API_URL (default: http://localhost:8111)
 */

import axios from 'axios';
import type { AxiosError } from 'axios';

// ===========================
// Type Definitions
// ===========================

/**
 * Entity search result from autocomplete endpoint
 */
export interface EntitySearchResult {
  name: string
  type: string
  last_seen: string | null
  connection_count: number
  wikidata_id: string | null
}

/**
 * Complete search response with metadata
 */
export interface EntitySearchResponse {
  results: EntitySearchResult[]
  total_results: number
  query_time_ms: number
  query: string
  entity_type_filter: string | null
}

/**
 * Node in a graph path
 */
export interface PathNode {
  name: string
  type: string
}

/**
 * Relationship in a graph path
 */
export interface PathRelationship {
  type: string
  confidence: number
  evidence: string | null
}

/**
 * Single path result between two entities
 */
export interface PathResult {
  length: number
  nodes: PathNode[]
  relationships: PathRelationship[]
}

/**
 * Complete pathfinding response
 */
export interface PathfindingResponse {
  paths: PathResult[]
  shortest_path_length: number
  query_time_ms: number
  entity1: string
  entity2: string
  max_depth: number
  total_paths_found: number
}

/**
 * Entity extracted from an article
 */
export interface ArticleEntity {
  name: string
  type: string
  wikidata_id: string | null
  confidence: number
  mention_count: number
  first_mention_index: number | null
}

/**
 * Article entities response
 */
export interface ArticleEntitiesResponse {
  article_id: string
  article_title: string | null
  article_url: string | null
  total_entities: number
  entities: ArticleEntity[]
  query_time_ms: number
}

/**
 * Graph node (from admin client - used by getEntityConnections)
 */
export interface GraphNode {
  name: string
  type: string
  connection_count: number
  properties?: Record<string, any>
}

/**
 * Graph edge (from admin client - used by getEntityConnections)
 */
export interface GraphEdge {
  source: string
  target: string
  relationship_type: string
  confidence: number
  mention_count: number
  evidence?: string
}

/**
 * Graph query response (from admin client - used by getEntityConnections)
 */
export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  total_nodes: number
  total_edges: number
  query_time_ms: number
}

// ===========================
// Axios Configuration
// ===========================

const BASE_URL = import.meta.env.VITE_KG_API_URL || 'http://localhost:8111'

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30s timeout for complex queries
})

// ===========================
// Error Handling Utility
// ===========================

/**
 * Extract meaningful error message from Axios error
 */
function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>

    // API returned error detail
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail
    }

    // HTTP status code error
    if (axiosError.response?.status) {
      const status = axiosError.response.status
      if (status === 404) return 'Resource not found in knowledge graph'
      if (status === 408) return 'Query timeout - try reducing max_depth or limit'
      if (status === 500) return 'Internal server error - check service logs'
    }

    // Network error
    if (axiosError.code === 'ECONNABORTED') {
      return 'Request timeout - service may be unavailable'
    }
    if (axiosError.code === 'ERR_NETWORK') {
      return 'Network error - cannot reach knowledge graph service'
    }

    return axiosError.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Unknown error occurred'
}

// ===========================
// Public API Functions
// ===========================

/**
 * Search for entities in the knowledge graph
 *
 * Performs full-text search on entity names with case-insensitive matching.
 * Results are ordered by relevance (exact match first, then by connection count).
 *
 * @param query - Search term (1-200 characters)
 * @param limit - Maximum results to return (1-100, default: 10)
 * @param entityType - Optional filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)
 * @returns Entity search results with metadata
 *
 * @example
 * ```typescript
 * const results = await searchEntities('Tesla', 10, 'ORGANIZATION')
 * console.log(`Found ${results.total_results} entities in ${results.query_time_ms}ms`)
 * ```
 */
export async function searchEntities(
  query: string,
  limit: number = 10,
  entityType?: string
): Promise<EntitySearchResponse> {
  try {
    const { data } = await apiClient.get<EntitySearchResponse>('/api/v1/graph/search', {
      params: {
        query,
        limit,
        entity_type: entityType,
      },
    })
    return data
  } catch (error) {
    const message = getErrorMessage(error)
    throw new Error(`Entity search failed: ${message}`)
  }
}

/**
 * Find shortest paths between two entities
 *
 * Uses Neo4j's allShortestPaths() algorithm to find multiple paths up to a maximum depth.
 * Only includes relationships with confidence >= min_confidence.
 *
 * @param entity1 - Source entity name (case-sensitive)
 * @param entity2 - Target entity name (case-sensitive)
 * @param maxDepth - Maximum path length in hops (1-5, default: 3)
 * @param limit - Maximum number of paths to return (1-10, default: 3)
 * @param minConfidence - Minimum relationship confidence (0.0-1.0, default: 0.5)
 * @returns Pathfinding results with all found paths
 *
 * @example
 * ```typescript
 * const result = await findPath('Elon Musk', 'Tesla', 2, 3, 0.7)
 * console.log(`Found ${result.total_paths_found} paths, shortest: ${result.shortest_path_length} hops`)
 * ```
 */
export async function findPath(
  entity1: string,
  entity2: string,
  maxDepth: number = 3,
  limit: number = 3,
  minConfidence: number = 0.5
): Promise<PathfindingResponse> {
  try {
    const { data } = await apiClient.get<PathfindingResponse>(
      `/api/v1/graph/path/${encodeURIComponent(entity1)}/${encodeURIComponent(entity2)}`,
      {
        params: {
          max_depth: maxDepth,
          limit,
          min_confidence: minConfidence,
        },
      }
    )
    return data
  } catch (error) {
    const message = getErrorMessage(error)
    throw new Error(`Pathfinding failed: ${message}`)
  }
}

/**
 * Get all entities extracted from a specific article
 *
 * Retrieves entities that have an EXTRACTED_FROM relationship to the specified article.
 * Results are ordered by confidence score (descending), then mention count.
 *
 * @param articleId - Article identifier (UUID or custom ID)
 * @param entityType - Optional filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)
 * @param limit - Maximum entities to return (1-200, default: 50)
 * @returns Article entities with confidence scores and mention counts
 *
 * @example
 * ```typescript
 * const result = await getArticleEntities('abc123', 'PERSON', 20)
 * console.log(`Found ${result.total_entities} people mentioned in "${result.article_title}"`)
 * ```
 */
export async function getArticleEntities(
  articleId: string,
  entityType?: string,
  limit: number = 50
): Promise<ArticleEntitiesResponse> {
  try {
    const { data } = await apiClient.get<ArticleEntitiesResponse>(
      `/api/v1/graph/articles/${encodeURIComponent(articleId)}/entities`,
      {
        params: {
          entity_type: entityType,
          limit,
        },
      }
    )
    return data
  } catch (error) {
    const message = getErrorMessage(error)
    throw new Error(`Failed to fetch article entities: ${message}`)
  }
}

/**
 * Get entity connections (imported from admin client)
 *
 * Fetches all connections for a specific entity in the knowledge graph.
 * Results include both nodes and edges with full relationship metadata.
 *
 * @param entityName - Entity name to query
 * @param relationshipType - Optional filter by relationship type
 * @param limit - Maximum connections to return (default: 100)
 * @returns Graph response with nodes and edges
 *
 * @example
 * ```typescript
 * const graph = await getEntityConnections('Tesla', 'WORKS_FOR', 50)
 * console.log(`Found ${graph.total_edges} connections`)
 * ```
 */
export async function getEntityConnections(
  entityName: string,
  relationshipType?: string,
  limit: number = 100
): Promise<GraphResponse> {
  try {
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
  } catch (error) {
    const message = getErrorMessage(error)
    throw new Error(`Failed to fetch entity connections: ${message}`)
  }
}
