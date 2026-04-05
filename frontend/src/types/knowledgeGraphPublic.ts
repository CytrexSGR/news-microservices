/**
 * TypeScript types for Knowledge Graph Public Feature (Phase 4)
 *
 * This file extends existing admin types from knowledgeGraph.ts with public-facing
 * types for entity search, pathfinding, article entities, and React Flow visualization.
 *
 * Backend Models Reference:
 * - app/models/search.py → EntitySearchResult, EntitySearchResponse
 * - app/models/pathfinding.py → PathNode, PathRelationship, PathResult, PathfindingResponse
 * - app/models/articles.py → ArticleEntity, ArticleEntitiesResponse
 *
 * @see {@link knowledgeGraph.ts} for admin types (GraphNode, GraphEdge, GraphResponse)
 */

// Re-export shared types from knowledgeGraph.ts to avoid duplication
export type {
  GraphNode,
  GraphEdge,
  GraphResponse,
  GraphStats,
  EntityTypeDistribution,
} from './knowledgeGraph'

// ===========================
// Entity Search Types (Phase 4 - Public API)
// ===========================

/**
 * Single entity search result with metadata and connection count.
 * Maps to backend EntitySearchResult from app/models/search.py
 */
export interface EntitySearchResult {
  name: string
  type: string // PERSON, ORGANIZATION, LOCATION, EVENT, PRODUCT, etc.
  last_seen: string | null // ISO 8601 datetime string
  connection_count: number
  wikidata_id: string | null
}

/**
 * Complete entity search response with results and metadata.
 * Maps to backend EntitySearchResponse from app/models/search.py
 */
export interface EntitySearchResponse {
  results: EntitySearchResult[]
  total_results: number
  query_time_ms: number
  query: string
  entity_type_filter: string | null
}

/**
 * Entity search request parameters.
 * Used for search API calls.
 */
export interface EntitySearchRequest {
  query: string
  entity_type?: string // Optional filter by entity type
  limit?: number // Max results to return (default: 10)
}

// ===========================
// Pathfinding Types (Phase 4 - Public API)
// ===========================

/**
 * Node in a graph path.
 * Maps to backend PathNode from app/models/pathfinding.py
 */
export interface PathNode {
  name: string
  type: string // Entity type
}

/**
 * Relationship in a graph path.
 * Maps to backend PathRelationship from app/models/pathfinding.py
 */
export interface PathRelationship {
  type: string // Relationship type (WORKS_FOR, LOCATED_IN, etc.)
  confidence: number // 0.0 - 1.0
  evidence: string | null // Optional evidence supporting relationship
}

/**
 * Single path result between two entities.
 * Maps to backend PathResult from app/models/pathfinding.py
 */
export interface PathResult {
  length: number // Number of hops in path
  nodes: PathNode[] // Ordered list of nodes
  relationships: PathRelationship[] // Ordered list of relationships
}

/**
 * Complete pathfinding response.
 * Maps to backend PathfindingResponse from app/models/pathfinding.py
 *
 * NOTE: Backend uses entity1/entity2, we map to from_entity/to_entity for clarity
 */
export interface PathfindingResponse {
  paths: PathResult[]
  shortest_path_length: number
  query_time_ms: number
  from_entity: string // Maps to backend's entity1
  to_entity: string // Maps to backend's entity2
  max_depth: number
  total_paths_found: number
}

/**
 * Pathfinding request parameters.
 * Used for pathfinding API calls.
 */
export interface PathfindingRequest {
  from_entity: string
  to_entity: string
  max_depth?: number // Maximum path length to search (default: 5)
  limit?: number // Max paths to return (default: 5)
}

// ===========================
// Article-Entity Types (Phase 4 - Public API)
// ===========================

/**
 * Entity extracted from an article with extraction metadata.
 * Maps to backend ArticleEntity from app/models/articles.py
 */
export interface ArticleEntity {
  name: string
  type: string // Entity type
  confidence: number // 0.0 - 1.0
  mention_count: number // Number of mentions in article
  wikidata_id: string | null
  first_mention_index?: number // Character index of first mention (optional)
}

/**
 * Complete article entities response.
 * Maps to backend ArticleEntitiesResponse from app/models/articles.py
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
 * Article entities request parameters.
 * Used for article entities API calls.
 */
export interface ArticleEntitiesRequest {
  article_id: string
  entity_type?: string // Optional filter by entity type
  min_confidence?: number // Optional minimum confidence threshold (0.0-1.0)
}

// ===========================
// React Flow Visualization Types (Phase 4 - Frontend)
// ===========================

/**
 * Graph layout configuration for React Flow visualization.
 * Controls node positioning algorithms and visual spacing.
 */
export interface GraphLayoutConfig {
  type: 'force' | 'hierarchical' | 'radial'
  nodeSpacing: number // Distance between nodes in pixels
  edgeLength: number // Preferred edge length in pixels
  iterations: number // Number of layout algorithm iterations
  centerForce?: number // Strength of centering force (for force layout)
  repulsionForce?: number // Strength of node repulsion (for force layout)
}

/**
 * Default layout configurations for different graph types.
 */
export const DEFAULT_LAYOUTS: Record<string, GraphLayoutConfig> = {
  force: {
    type: 'force',
    nodeSpacing: 150,
    edgeLength: 200,
    iterations: 300,
    centerForce: 0.05,
    repulsionForce: 100,
  },
  hierarchical: {
    type: 'hierarchical',
    nodeSpacing: 100,
    edgeLength: 150,
    iterations: 50,
  },
  radial: {
    type: 'radial',
    nodeSpacing: 120,
    edgeLength: 180,
    iterations: 100,
  },
}

/**
 * Entity node for React Flow visualization.
 * Extends GraphNode with React Flow specific properties.
 */
export interface EntityNode {
  id: string // Unique identifier (entity name)
  type: 'entity' // React Flow node type
  position: { x: number; y: number } // Position on canvas
  data: {
    label: string // Display name
    entityType: string // PERSON, ORGANIZATION, etc.
    connectionCount: number // Number of connections
    wikidataId?: string // Optional Wikidata identifier
    isSelected?: boolean // UI selection state
    isHovered?: boolean // UI hover state
  }
  // React Flow optional properties
  draggable?: boolean
  selectable?: boolean
  connectable?: boolean
}

/**
 * Relationship edge for React Flow visualization.
 * Extends GraphEdge with React Flow specific properties.
 */
export interface RelationshipEdge {
  id: string // Unique identifier (source-target-type)
  type: 'smoothstep' | 'straight' | 'bezier' // React Flow edge type
  source: string // Source node ID
  target: string // Target node ID
  animated: boolean // Whether edge is animated
  data: {
    relationshipType: string // WORKS_FOR, LOCATED_IN, etc.
    confidence: number // 0.0 - 1.0
    evidence?: string // Optional evidence
    mentionCount?: number // Number of co-occurrences
  }
  // React Flow optional properties
  label?: string // Edge label to display
  labelStyle?: React.CSSProperties
  labelBgStyle?: React.CSSProperties
  markerEnd?: {
    type: 'arrow' | 'arrowclosed'
    color?: string
  }
}

/**
 * Complete React Flow graph data structure.
 */
export interface ReactFlowGraphData {
  nodes: EntityNode[]
  edges: RelationshipEdge[]
  layoutConfig: GraphLayoutConfig
}

// ===========================
// Filter & UI State Types (Phase 4 - Frontend)
// ===========================

/**
 * Filter state for graph visualization and queries.
 * Used to control which entities/relationships are displayed.
 */
export interface FilterState {
  entityTypes: string[] // Selected entity types to show
  relationshipTypes: string[] // Selected relationship types to show
  minConfidence: number // Minimum confidence threshold (0.0 - 1.0)
  minConnectionCount?: number // Minimum number of connections (optional)
  dateRange?: {
    start: Date
    end: Date
  }
  searchQuery?: string // Optional search filter
}

/**
 * Default filter state (show all).
 */
export const DEFAULT_FILTERS: FilterState = {
  entityTypes: [],
  relationshipTypes: [],
  minConfidence: 0.0,
}

/**
 * UI state for graph visualization.
 * Tracks user interactions and display preferences.
 */
export interface GraphUIState {
  selectedEntity: string | null // Currently selected entity ID
  hoveredEntity: string | null // Currently hovered entity ID
  layoutType: 'force' | 'hierarchical' | 'radial'
  zoomLevel: number // Current zoom level (0.1 - 2.0)
  panPosition: { x: number; y: number } // Canvas pan position
  isLoading: boolean // Whether graph is loading
  error: string | null // Error message if any
  showLabels: boolean // Whether to show edge labels
  showLegend: boolean // Whether to show entity type legend
}

/**
 * Default UI state.
 */
export const DEFAULT_UI_STATE: GraphUIState = {
  selectedEntity: null,
  hoveredEntity: null,
  layoutType: 'force',
  zoomLevel: 1.0,
  panPosition: { x: 0, y: 0 },
  isLoading: false,
  error: null,
  showLabels: true,
  showLegend: true,
}

// ===========================
// Entity Detail Panel Types (Phase 4 - Frontend)
// ===========================

/**
 * Detailed entity information for detail panel.
 * Combines data from multiple API endpoints.
 */
export interface EntityDetail {
  name: string
  type: string
  wikidataId: string | null
  connectionCount: number
  lastSeen: string | null
  // Extended metadata
  connections: Array<{
    name: string
    type: string
    relationshipType: string
    confidence: number
  }>
  articles: Array<{
    id: string
    title: string
    url: string | null
    publishedAt: string
    mentionCount: number
  }>
  // Statistics
  totalArticles: number
  firstSeen: string | null
  averageConfidence: number
}

/**
 * Entity detail request parameters.
 */
export interface EntityDetailRequest {
  entity_name: string
  include_connections?: boolean
  include_articles?: boolean
  connections_limit?: number
  articles_limit?: number
}

// ===========================
// Graph Interaction Events (Phase 4 - Frontend)
// ===========================

/**
 * Graph interaction event types.
 */
export type GraphEventType =
  | 'node:click'
  | 'node:doubleClick'
  | 'node:hover'
  | 'edge:click'
  | 'edge:hover'
  | 'canvas:click'
  | 'selection:change'

/**
 * Graph interaction event data.
 */
export interface GraphEvent {
  type: GraphEventType
  timestamp: number
  data: {
    nodeId?: string
    edgeId?: string
    position?: { x: number; y: number }
    selectedNodes?: string[]
    selectedEdges?: string[]
  }
}

// ===========================
// API Response Types (Phase 4 - Public API)
// ===========================

/**
 * Standard API error response.
 */
export interface APIError {
  error: string
  detail?: string
  status_code: number
}

/**
 * API response wrapper with loading state.
 */
export interface APIResponse<T> {
  data: T | null
  loading: boolean
  error: APIError | null
}

// ===========================
// Autocomplete Types (Phase 4 - Public API)
// ===========================

/**
 * Autocomplete suggestion for entity search.
 * Lightweight version of EntitySearchResult.
 */
export interface AutocompleteSuggestion {
  name: string
  type: string
  connection_count: number
  wikidata_id: string | null
}

/**
 * Autocomplete response.
 */
export interface AutocompleteResponse {
  suggestions: AutocompleteSuggestion[]
  query: string
  query_time_ms: number
}

// ===========================
// Type Guards (Phase 4 - Utility)
// ===========================

/**
 * Type guard to check if a value is an EntityNode.
 */
export function isEntityNode(node: unknown): node is EntityNode {
  return (
    typeof node === 'object' &&
    node !== null &&
    'id' in node &&
    'type' in node &&
    'position' in node &&
    'data' in node &&
    (node as EntityNode).type === 'entity'
  )
}

/**
 * Type guard to check if a value is a RelationshipEdge.
 */
export function isRelationshipEdge(edge: unknown): edge is RelationshipEdge {
  return (
    typeof edge === 'object' &&
    edge !== null &&
    'id' in edge &&
    'source' in edge &&
    'target' in edge &&
    'data' in edge
  )
}

/**
 * Type guard to check if a value is an APIError.
 */
export function isAPIError(error: unknown): error is APIError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    'status_code' in error
  )
}

// ===========================
// Utility Types (Phase 4)
// ===========================

/**
 * Entity type for type safety.
 */
export enum EntityType {
  PERSON = 'PERSON',
  ORGANIZATION = 'ORGANIZATION',
  LOCATION = 'LOCATION',
  EVENT = 'EVENT',
  PRODUCT = 'PRODUCT',
  MISC = 'MISC',
  OTHER = 'OTHER',
  NOT_APPLICABLE = 'NOT_APPLICABLE'
}

/**
 * Relationship type for common relationships.
 */
export enum RelationshipType {
  WORKS_FOR = 'WORKS_FOR',
  LOCATED_IN = 'LOCATED_IN',
  MANAGES = 'MANAGES',
  PART_OF = 'PART_OF',
  AFFILIATED_WITH = 'AFFILIATED_WITH',
  RELATED_TO = 'RELATED_TO'
}

/**
 * Color mapping for entity types (for visualization).
 */
export const ENTITY_TYPE_COLORS: Record<string, string> = {
  PERSON: '#3B82F6', // Blue
  ORGANIZATION: '#10B981', // Green
  LOCATION: '#F59E0B', // Amber
  EVENT: '#EF4444', // Red
  PRODUCT: '#8B5CF6', // Purple
  MISC: '#6B7280', // Gray
  OTHER: '#6B7280', // Gray
  NOT_APPLICABLE: '#9CA3AF', // Light Gray
}

/**
 * Icon mapping for entity types (for visualization).
 */
export const ENTITY_TYPE_ICONS: Record<string, string> = {
  PERSON: '👤',
  ORGANIZATION: '🏢',
  LOCATION: '📍',
  EVENT: '📅',
  PRODUCT: '📦',
  MISC: '🔖',
  OTHER: '❓',
  NOT_APPLICABLE: '⚪',
}

// ===========================
// Export Summary
// ===========================

/**
 * Summary of types defined in this file:
 *
 * Search Types (3):
 * - EntitySearchResult, EntitySearchResponse, EntitySearchRequest
 *
 * Pathfinding Types (5):
 * - PathNode, PathRelationship, PathResult, PathfindingResponse, PathfindingRequest
 *
 * Article-Entity Types (3):
 * - ArticleEntity, ArticleEntitiesResponse, ArticleEntitiesRequest
 *
 * React Flow Types (3):
 * - GraphLayoutConfig, EntityNode, RelationshipEdge, ReactFlowGraphData
 *
 * Filter & UI State Types (4):
 * - FilterState, GraphUIState, DEFAULT_FILTERS, DEFAULT_UI_STATE
 *
 * Entity Detail Types (2):
 * - EntityDetail, EntityDetailRequest
 *
 * Event Types (2):
 * - GraphEventType, GraphEvent
 *
 * API Response Types (3):
 * - APIError, APIResponse, AutocompleteSuggestion, AutocompleteResponse
 *
 * Type Guards (3):
 * - isEntityNode, isRelationshipEdge, isAPIError
 *
 * Utility Types (5):
 * - EntityType (enum), RelationshipType (enum), ENTITY_TYPE_COLORS, ENTITY_TYPE_ICONS, DEFAULT_LAYOUTS
 *
 * Total: 33 types/interfaces/enums + 3 type guards + 4 constants = 40 exports
 */
