/**
 * Narrative Analysis Types
 *
 * Types for narrative frame detection, bias analysis, and propaganda indicators.
 * Used by the Intelligence feature's narrative analysis sub-module.
 */

// ==================== Enums ====================

export type BiasType = 'political' | 'ideological' | 'commercial' | 'emotional' | 'source';
export type BiasDirection = 'left' | 'center-left' | 'center' | 'center-right' | 'right';
export type NarrativeType = 'conflict' | 'cooperation' | 'crisis' | 'progress' | 'decline' | 'neutral';

// ==================== Narrative Frames ====================

export interface NarrativeFrame {
  id: string;
  name: string;
  type: NarrativeType;
  description: string;
  keywords: string[];
  example_phrases: string[];
}

// ==================== Analysis Request/Result ====================

export interface NarrativeAnalysisRequest {
  text: string;
  include_bias?: boolean;
  include_propaganda?: boolean;
  language?: string;
}

export interface NarrativeAnalysisResult {
  text_length: number;
  detected_frames: DetectedFrame[];
  overall_narrative: NarrativeType;
  bias_analysis?: BiasResult;
  propaganda_indicators?: PropagandaIndicator[];
  confidence: number;
  cost_usd: number;
  latency_ms: number;
}

// ==================== Detected Frames ====================

export interface DetectedFrame {
  frame: NarrativeFrame;
  confidence: number;
  evidence: string[];
  start_position?: number;
  end_position?: number;
}

// ==================== Bias Analysis ====================

export interface BiasResult {
  overall_bias: BiasDirection;
  bias_score: number; // -1 (left) to 1 (right)
  confidence: number;
  bias_by_type: Record<BiasType, number>;
  indicators: BiasIndicator[];
}

export interface BiasIndicator {
  type: BiasType;
  text: string;
  score: number;
  explanation: string;
}

// ==================== Propaganda Detection ====================

export interface PropagandaIndicator {
  technique: string;
  confidence: number;
  examples: string[];
  description: string;
}

// ==================== Dashboard/Overview ====================

export interface NarrativeOverview {
  total_analyses: number;
  frames_distribution: Record<NarrativeType, number>;
  avg_bias_score: number;
  bias_distribution: Record<BiasDirection, number>;
  trending_frames: NarrativeFrame[];
  recent_analyses: NarrativeAnalysisResult[];
  cost_total_usd: number;
}

// ==================== Clusters ====================

export interface NarrativeCluster {
  id: string;
  name: string;
  dominant_frame: NarrativeType;
  article_count: number;
  avg_bias: number;
  entities: string[];
  created_at: string;
  last_updated: string;
}

// ==================== API Response Types ====================

export interface NarrativeFramesResponse {
  frames: NarrativeFrame[];
  total: number;
}

export interface BiasAnalysisResponse {
  analyses: BiasResult[];
  total: number;
  avg_bias: number;
  period_start: string;
  period_end: string;
}

export interface NarrativeClustersResponse {
  clusters: NarrativeCluster[];
  total: number;
  page: number;
  per_page: number;
}

// ==================== Filter Types ====================

export interface NarrativeFilters {
  frame_type?: NarrativeType;
  bias_direction?: BiasDirection;
  min_confidence?: number;
  date_from?: string;
  date_to?: string;
}

export interface BiasFilters {
  bias_type?: BiasType;
  min_score?: number;
  max_score?: number;
  source?: string;
}

export interface ClusterFilters {
  dominant_frame?: NarrativeType;
  min_articles?: number;
  include_inactive?: boolean;
}

// ==================== Utility Functions ====================

/**
 * Get display color for bias direction
 */
export function getBiasColor(direction: BiasDirection): string {
  switch (direction) {
    case 'left':
      return 'text-blue-600';
    case 'center-left':
      return 'text-blue-400';
    case 'center':
      return 'text-gray-500';
    case 'center-right':
      return 'text-red-400';
    case 'right':
      return 'text-red-600';
    default:
      return 'text-gray-500';
  }
}

/**
 * Get background color for bias direction
 */
export function getBiasBgColor(direction: BiasDirection): string {
  switch (direction) {
    case 'left':
      return 'bg-blue-100 dark:bg-blue-900/30';
    case 'center-left':
      return 'bg-blue-50 dark:bg-blue-900/20';
    case 'center':
      return 'bg-gray-100 dark:bg-gray-800';
    case 'center-right':
      return 'bg-red-50 dark:bg-red-900/20';
    case 'right':
      return 'bg-red-100 dark:bg-red-900/30';
    default:
      return 'bg-gray-100 dark:bg-gray-800';
  }
}

/**
 * Get display color for narrative type
 */
export function getNarrativeColor(type: NarrativeType): string {
  switch (type) {
    case 'conflict':
      return 'text-red-500';
    case 'cooperation':
      return 'text-green-500';
    case 'crisis':
      return 'text-orange-500';
    case 'progress':
      return 'text-blue-500';
    case 'decline':
      return 'text-yellow-600';
    case 'neutral':
      return 'text-gray-500';
    default:
      return 'text-gray-500';
  }
}

/**
 * Get background color for narrative type
 */
export function getNarrativeBgColor(type: NarrativeType): string {
  switch (type) {
    case 'conflict':
      return 'bg-red-100 dark:bg-red-900/30';
    case 'cooperation':
      return 'bg-green-100 dark:bg-green-900/30';
    case 'crisis':
      return 'bg-orange-100 dark:bg-orange-900/30';
    case 'progress':
      return 'bg-blue-100 dark:bg-blue-900/30';
    case 'decline':
      return 'bg-yellow-100 dark:bg-yellow-900/30';
    case 'neutral':
      return 'bg-gray-100 dark:bg-gray-800';
    default:
      return 'bg-gray-100 dark:bg-gray-800';
  }
}

/**
 * Get bias direction label
 */
export function getBiasLabel(score: number): BiasDirection {
  if (score < -0.5) return 'left';
  if (score < -0.2) return 'center-left';
  if (score < 0.2) return 'center';
  if (score < 0.5) return 'center-right';
  return 'right';
}

/**
 * Format cost in USD
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${(cost * 1000).toFixed(2)}m`;
  }
  return `$${cost.toFixed(4)}`;
}

// ==================== Real-time Analysis Types ====================

/**
 * Result from real-time text narrative analysis
 */
export interface RealTimeNarrativeAnalysis {
  frames: {
    type: NarrativeType;
    confidence: number;
    description: string;
  }[];
  bias_score: number;
  bias_direction: 'left' | 'center' | 'right';
  propaganda_signals: string[];
  sentiment: number;
  processing_time_ms: number;
}

// ==================== Knowledge Graph Narrative Types ====================

/**
 * Entity-specific framing analysis from Knowledge Graph
 */
export interface EntityFramingAnalysis {
  entity_name: string;
  entity_id: string;
  frame_distribution: Record<NarrativeType, number>;
  avg_confidence: number;
  total_frames: number;
  bias_score: number;
  first_seen: string;
  last_seen: string;
}

/**
 * High tension narrative from Knowledge Graph
 */
export interface HighTensionNarrative {
  id: string;
  tension_score: number;
  frame_type: NarrativeType;
  entities: string[];
  headline: string;
  source: string;
  created_at: string;
  article_id: string;
}

/**
 * Co-occurrence of entities in narrative frames
 */
export interface NarrativeCooccurrence {
  entity1: string;
  entity1_id: string;
  entity2: string;
  entity2_id: string;
  shared_frame_count: number;
  frame_types: NarrativeType[];
  avg_tension: number;
}

/**
 * Frame distribution from Knowledge Graph
 */
export interface KGFrameDistribution {
  frame_type: NarrativeType;
  count: number;
  percentage: number;
  avg_confidence: number;
  entity_count: number;
}

/**
 * Entity with narrative frame mentions
 */
export interface TopNarrativeEntity {
  entity_name: string;
  entity_id: string;
  entity_type: string;
  frame_mentions: number;
  dominant_frame: NarrativeType;
  avg_tension: number;
  article_count: number;
}

/**
 * Overall narrative statistics from Knowledge Graph
 */
export interface NarrativeStats {
  total_frames: number;
  total_articles_analyzed: number;
  total_entities_involved: number;
  avg_tension_score: number;
  frame_distribution: Record<NarrativeType, number>;
  bias_distribution: Record<BiasDirection, number>;
  time_range: {
    start: string;
    end: string;
  };
  most_active_day: {
    date: string;
    frame_count: number;
  };
}

// ==================== KG API Response Types ====================

export interface KGNarrativeFramesResponse {
  frames: Array<{
    id: string;
    frame_type: NarrativeType;
    confidence: number;
    entity_name: string;
    article_id: string;
    created_at: string;
  }>;
  total: number;
  page: number;
  per_page: number;
}

export interface KGFrameDistributionResponse {
  distribution: KGFrameDistribution[];
  total_frames: number;
  period: {
    start: string;
    end: string;
  };
}

export interface EntityFramingAnalysisResponse {
  analysis: EntityFramingAnalysis;
  related_entities: Array<{
    entity_name: string;
    shared_frames: number;
  }>;
}

export interface NarrativeCooccurrenceResponse {
  cooccurrences: NarrativeCooccurrence[];
  total: number;
}

export interface HighTensionNarrativesResponse {
  narratives: HighTensionNarrative[];
  total: number;
  avg_tension: number;
}

export interface NarrativeStatsResponse {
  stats: NarrativeStats;
  generated_at: string;
}

export interface TopNarrativeEntitiesResponse {
  entities: TopNarrativeEntity[];
  total: number;
  frame_filter?: NarrativeType;
}

// ==================== KG Filter Types ====================

export interface KGNarrativeFilters {
  entity_name?: string;
  entity_id?: string;
  frame_type?: NarrativeType;
  min_confidence?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
  page?: number;
}

export interface TensionFilters {
  min_tension?: number;
  max_tension?: number;
  frame_type?: NarrativeType;
  entity_name?: string;
  limit?: number;
}

export interface CooccurrenceFilters {
  entity_name?: string;
  frame_type?: NarrativeType;
  min_shared_frames?: number;
  limit?: number;
}

// ==================== Tension Utility Functions ====================

/**
 * Get severity level for tension score
 */
export function getTensionSeverity(score: number): 'low' | 'medium' | 'high' | 'critical' {
  if (score < 0.3) return 'low';
  if (score < 0.6) return 'medium';
  if (score < 0.8) return 'high';
  return 'critical';
}

/**
 * Get color for tension severity
 */
export function getTensionColor(score: number): string {
  const severity = getTensionSeverity(score);
  switch (severity) {
    case 'low':
      return 'text-green-500';
    case 'medium':
      return 'text-yellow-500';
    case 'high':
      return 'text-orange-500';
    case 'critical':
      return 'text-red-600';
  }
}

/**
 * Get background color for tension severity
 */
export function getTensionBgColor(score: number): string {
  const severity = getTensionSeverity(score);
  switch (severity) {
    case 'low':
      return 'bg-green-100 dark:bg-green-900/30';
    case 'medium':
      return 'bg-yellow-100 dark:bg-yellow-900/30';
    case 'high':
      return 'bg-orange-100 dark:bg-orange-900/30';
    case 'critical':
      return 'bg-red-100 dark:bg-red-900/30';
  }
}
