/**
 * TypeScript types for Knowledge Graph Service API
 */

// ===========================
// Health Check Types
// ===========================

export interface HealthCheck {
  status: 'ready' | 'not_ready'
  checks: {
    neo4j: 'healthy' | 'unhealthy' | string
    rabbitmq_consumer: 'healthy' | 'not_connected' | string
  }
  service: string
  message?: string
}

export interface Neo4jHealth {
  status: 'healthy' | 'unhealthy'
  connected: boolean
  version: string
  edition: string
  host: string
}

export interface RabbitMQHealth {
  status: 'healthy' | 'unhealthy'
  connection: 'open' | 'closed'
  channel: 'open' | 'closed'
  exchange: string
  queue: {
    name: string
    message_count: number
    consumer_count: number
    status?: string
  }
  routing_key: string
}

export interface BasicHealth {
  status: string
  service: string
  version: string
  timestamp: string
  uptime_seconds?: number
}

// ===========================
// Graph Statistics Types
// ===========================

export interface GraphStats {
  total_nodes: number
  total_relationships: number
  entity_types: Record<string, number>
}

export interface EntityTypeDistribution {
  entity_type: string
  count: number
  percentage: number
}

// ===========================
// Graph Query Types
// ===========================

export interface GraphNode {
  name: string
  type: string
  connection_count: number
  properties?: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  relationship_type: string
  confidence: number
  mention_count: number
  evidence?: string
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  total_nodes: number
  total_edges: number
  query_time_ms: number
}

// ===========================
// Analytics Types (Phase 2)
// ===========================

export interface TopEntity {
  name: string
  type: string
  connection_count: number
  sample_connections: Array<{
    name: string
    type: string
    relationship_type: string
  }>
}

export interface GrowthDataPoint {
  date: string
  new_nodes: number
  new_relationships: number
  total_nodes: number
  total_relationships: number
}

export interface RelationshipExample {
  source: string
  source_type: string
  target: string
  target_type: string
  confidence: number
  mentions: number
}

export interface RelationshipType {
  type: string
  count: number
  avg_confidence: number
  total_mentions: number
  percentage: number
  quality: 'high' | 'medium' | 'low'
  examples: RelationshipExample[]
}

export interface EntityTypePattern {
  source_type: string
  relationship_type: string
  target_type: string
  count: number
}

export interface QualityInsights {
  high_quality_count: number
  needs_review_count: number
  avg_confidence_overall: number
}

export interface RelationshipWarning {
  type: string
  message: string
  severity: 'info' | 'warning' | 'error'
}

export interface RelationshipStats {
  total_relationships: number
  relationship_types: RelationshipType[]
  patterns: EntityTypePattern[]
  quality_insights: QualityInsights
  warnings: RelationshipWarning[]
}

// ===========================
// Entity Canonicalization Types
// ===========================

export interface TopCanonicalEntity {
  canonical_name: string
  canonical_id: string | null
  entity_type: string
  alias_count: number
  wikidata_linked: boolean
}

export interface SourceBreakdown {
  exact: number
  fuzzy: number
  semantic: number
  wikidata: number
  new: number
}

export interface CanonicalizationStats {
  total_canonical_entities: number
  total_aliases: number
  wikidata_linked: number
  wikidata_coverage_percent: number
  deduplication_ratio: number
  source_breakdown: SourceBreakdown
  entity_type_distribution: Record<string, number>
  top_entities_by_aliases: TopCanonicalEntity[]
  entities_without_qid: number
  avg_cache_hit_time_ms: number | null
  cache_hit_rate: number | null
  total_api_calls_saved: number
  estimated_cost_savings_monthly: number
}

// ===========================
// Batch Reprocessing Types
// ===========================

export interface ReprocessingStatus {
  status: 'idle' | 'running' | 'completed' | 'failed'
  progress_percent: number
  current_phase: 'analyzing' | 'fuzzy_matching' | 'semantic_matching' | 'wikidata_lookup' | 'merging' | 'updating' | null
  stats: {
    total_entities: number
    processed_entities: number
    duplicates_found: number
    entities_merged: number
    qids_added: number
    errors: number
  }
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  dry_run: boolean
}

export interface ReprocessingResult {
  before: {
    total_entities: number
    wikidata_coverage_percent: number
    deduplication_ratio: number
  }
  after: {
    total_entities: number
    wikidata_coverage_percent: number
    deduplication_ratio: number
  }
  changes: {
    entities_merged: number
    qids_added: number
    duplicates_removed: number
  }
  duration_seconds: number
}

// ===========================
// Entity Type Trends Types
// ===========================

export interface EntityTypeTrendData {
  date: string
  PERSON: number
  ORGANIZATION: number
  LOCATION: number
  EVENT: number
  PRODUCT: number
  OTHER: number
  MISC: number
  NOT_APPLICABLE: number
}

export interface EntityTypeTrendsResponse {
  trends: EntityTypeTrendData[]
  days: number
  total_entities: number
}

// ===========================
// Entity Merge History Types
// ===========================

export interface MergeEvent {
  id: string
  timestamp: string
  source_entity: string
  source_type: string
  target_entity: string
  target_type: string
  merge_method: 'exact' | 'fuzzy' | 'semantic' | 'wikidata'
  confidence: number
}

// ===========================
// NOT_APPLICABLE Trend Types
// ===========================

export interface NotApplicableTrendDataPoint {
  date: string // YYYY-MM-DD
  not_applicable_count: number
  total_relationships: number
  not_applicable_ratio: number // 0-1
  not_applicable_percentage: number // 0-100
}

// ===========================
// Relationship Quality Trend Types
// ===========================

export interface RelationshipQualityTrendDataPoint {
  date: string // YYYY-MM-DD
  high_confidence_count: number
  medium_confidence_count: number
  low_confidence_count: number
  total_relationships: number
  high_confidence_ratio: number // 0-1
  medium_confidence_ratio: number // 0-1
  low_confidence_ratio: number // 0-1
  high_confidence_percentage: number // 0-100
  medium_confidence_percentage: number // 0-100
  low_confidence_percentage: number // 0-100
}

// ===========================
// Autocomplete Types (Phase 3)
// ===========================

export interface EntitySearchResult {
  name: string
  type: string
  last_seen: string
}

// ===========================
// Cross-Article Coverage Types
// ===========================

export interface EntityCoverage {
  entity_name: string
  entity_type: string
  wikidata_id?: string | null
  article_count: number
  coverage_percentage: number
  recent_articles?: Array<{
    title: string
    published_at: string
  }>
}

export interface CrossArticleCoverageStats {
  total_articles: number
  total_unique_entities: number
  entities_per_article_avg: number
  articles_per_entity_avg: number
  top_entities: EntityCoverage[]
}

// ===========================
// Data Quality Types (Phase 4)
// ===========================

export interface DetailedGraphStats {
  graph_size: {
    total_nodes: number
    total_relationships: number
    entity_type_distribution: Record<string, number>
  }
  relationship_quality: {
    high_confidence_count: number
    medium_confidence_count: number
    low_confidence_count: number
    high_confidence_ratio: number
    medium_confidence_ratio: number
    low_confidence_ratio: number
  }
  data_completeness: {
    not_applicable_count: number
    not_applicable_ratio: number
    orphaned_entities_count: number
    entities_with_wikidata: number
    wikidata_coverage_ratio: number
  }
  quality_score: number
  top_entities: Array<{
    name: string
    type: string
    connection_count: number
  }>
  query_time_ms: number
}

export interface DisambiguationQualityResponse {
  total_ambiguous_names: number
  total_disambiguation_cases: number
  success_rate: number
  well_disambiguated_count: number
  top_ambiguous_entities: Array<{
    name: string
    type_variations: string[]
    occurrence_count: number
    variations_detail: Array<{
      type: string
      avg_confidence: number
      relationship_count: number
    }>
  }>
  confidence_distribution: {
    high: number
    medium: number
    low: number
    total: number
  }
  query_time_ms: number
}
