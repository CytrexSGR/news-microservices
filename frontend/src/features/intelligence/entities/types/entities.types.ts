/**
 * Entity Canonicalization Types
 *
 * Types for the Entity Canonicalization sub-feature of the Intelligence module.
 * These types map to the entity-canonicalization-service API (port 8112).
 */

// ===========================
// Entity Types
// ===========================

export type EntityType =
  | 'PERSON'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'EVENT'
  | 'PRODUCT'
  | 'OTHER'
  | 'MISC'
  | 'NOT_APPLICABLE';

export type CanonicalizationSource = 'exact' | 'fuzzy' | 'semantic' | 'wikidata' | 'new';

// ===========================
// Canonicalization Request/Response
// ===========================

export interface CanonicalizeRequest {
  entity_name: string;
  entity_type: EntityType;
  language?: string;
}

export interface CanonicalEntity {
  canonical_name: string;
  canonical_id: string | null;
  aliases: string[];
  confidence: number;
  source: CanonicalizationSource;
  entity_type: EntityType;
  processing_time_ms?: number;
}

// ===========================
// Batch Canonicalization
// ===========================

export interface BatchCanonRequest {
  entities: CanonicalizeRequest[];
}

export interface BatchCanonResponse {
  results: CanonicalEntity[];
  total_processed: number;
  total_time_ms: number;
}

export interface AsyncBatchCanonResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  message: string;
  total_entities: number;
}

// ===========================
// Entity Clusters
// ===========================

export interface EntityCluster {
  canonical_name: string;
  canonical_id: string | null;
  entity_type: EntityType;
  alias_count: number;
  wikidata_linked: boolean;
  variants?: string[];
  count?: number;
  last_seen?: string;
}

// ===========================
// Statistics
// ===========================

export interface SourceBreakdown {
  exact: number;
  fuzzy: number;
  semantic: number;
  wikidata: number;
  new: number;
}

export interface CanonStats {
  total_canonical_entities: number;
  total_aliases: number;
  wikidata_linked: number;
  wikidata_coverage_percent: number;
  deduplication_ratio: number;
  source_breakdown: SourceBreakdown;
  entity_type_distribution: Record<EntityType, number>;
  top_entities_by_aliases: EntityCluster[];
  entities_without_qid: number;
  avg_cache_hit_time_ms: number | null;
  cache_hit_rate: number | null;
  total_api_calls_saved: number;
  estimated_cost_savings_monthly: number;
}

export interface BasicCanonStats {
  total_canonical_entities: number;
  total_aliases: number;
  wikidata_linked: number;
  coverage_percentage: number;
  cache_hit_rate: number | null;
}

// ===========================
// Async Job Types
// ===========================

export interface AsyncJobStats {
  total_entities: number;
  processed_entities: number;
  successful: number;
  failed: number;
}

export interface AsyncJob {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  stats: AsyncJobStats;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface AsyncJobResult {
  job_id: string;
  results: CanonicalEntity[];
  total_processed: number;
  total_time_ms: number;
}

// ===========================
// Entity Aliases
// ===========================

export interface EntityAlias {
  alias: string;
  source: 'wikidata' | 'detected' | 'manual';
  confidence: number;
  frequency: number;
}

export interface AliasInfo {
  alias: string;
  canonical_name: string;
  canonical_id: string | null;
  created_at: string;
}

// ===========================
// Entity History
// ===========================

export type EntityHistoryEventType = 'created' | 'merged' | 'alias_added' | 'updated';

export interface EntityHistoryEntry {
  id: string;
  timestamp: string;
  event_type: EntityHistoryEventType;
  details: Record<string, unknown>;
}

export interface MergeEvent {
  id: string;
  timestamp: string;
  source_entity: string;
  source_type: EntityType;
  target_entity: string;
  target_type: EntityType;
  merge_method: CanonicalizationSource;
  confidence: number;
}

// ===========================
// Reprocessing Types
// ===========================

export interface ReprocessingStats {
  total_entities: number;
  processed_entities: number;
  duplicates_found: number;
  entities_merged: number;
  qids_added: number;
  errors: number;
}

export type ReprocessingPhase =
  | 'analyzing'
  | 'fuzzy_matching'
  | 'semantic_matching'
  | 'wikidata_lookup'
  | 'merging'
  | 'updating';

export interface ReprocessingStatus {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress_percent: number;
  current_phase: ReprocessingPhase | null;
  stats: ReprocessingStats;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  dry_run: boolean;
}

// ===========================
// Trend Data
// ===========================

export interface EntityTypeTrendData {
  date: string;
  PERSON: number;
  ORGANIZATION: number;
  LOCATION: number;
  EVENT: number;
  PRODUCT: number;
  OTHER: number;
  MISC: number;
  NOT_APPLICABLE: number;
}

export interface EntityTypeTrendsResponse {
  trends: EntityTypeTrendData[];
  days: number;
  total_entities: number;
}

// ===========================
// Utility Types
// ===========================

export interface EntityTypeConfig {
  type: EntityType;
  label: string;
  color: string;
  icon: string;
}

export const ENTITY_TYPE_CONFIGS: EntityTypeConfig[] = [
  { type: 'PERSON', label: 'Person', color: 'text-blue-500', icon: 'User' },
  { type: 'ORGANIZATION', label: 'Organization', color: 'text-purple-500', icon: 'Building2' },
  { type: 'LOCATION', label: 'Location', color: 'text-green-500', icon: 'MapPin' },
  { type: 'EVENT', label: 'Event', color: 'text-orange-500', icon: 'Calendar' },
  { type: 'PRODUCT', label: 'Product', color: 'text-pink-500', icon: 'Package' },
  { type: 'OTHER', label: 'Other', color: 'text-gray-500', icon: 'HelpCircle' },
  { type: 'MISC', label: 'Misc', color: 'text-gray-400', icon: 'MoreHorizontal' },
  { type: 'NOT_APPLICABLE', label: 'N/A', color: 'text-gray-300', icon: 'X' },
];

export function getEntityTypeConfig(type: EntityType): EntityTypeConfig {
  return ENTITY_TYPE_CONFIGS.find((c) => c.type === type) || ENTITY_TYPE_CONFIGS[5];
}

export function getConfidenceLevel(confidence: number): 'high' | 'medium' | 'low' {
  if (confidence >= 0.9) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

export function getConfidenceColor(confidence: number): string {
  const level = getConfidenceLevel(confidence);
  switch (level) {
    case 'high':
      return 'text-green-500';
    case 'medium':
      return 'text-yellow-500';
    case 'low':
      return 'text-red-500';
  }
}
