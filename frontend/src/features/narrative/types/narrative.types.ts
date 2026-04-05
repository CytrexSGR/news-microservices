/**
 * Narrative Service Types
 *
 * Based on narrative-service/app/schemas/narrative.py
 * Port: 8119
 *
 * @module features/narrative/types
 */

// ============================================================================
// Enums and Literals
// ============================================================================

/**
 * Available frame types for narrative analysis
 *
 * - victim: Entity portrayed as victim/suffering
 * - hero: Entity portrayed as hero/savior
 * - threat: Entity portrayed as threat/danger
 * - solution: Entity/action portrayed as solution
 * - conflict: Conflict/opposition framing
 * - economic: Economic impact framing
 */
export type FrameType =
  | 'victim'
  | 'hero'
  | 'threat'
  | 'solution'
  | 'conflict'
  | 'economic';

/**
 * Bias spectrum labels
 */
export type BiasLabel =
  | 'left'
  | 'center-left'
  | 'center'
  | 'center-right'
  | 'right';

/**
 * Perspective types for bias analysis
 */
export type Perspective =
  | 'progressive'
  | 'moderate'
  | 'conservative'
  | 'neutral';

// ============================================================================
// Core Entity Types
// ============================================================================

/**
 * Narrative frame detected in text
 */
export interface NarrativeFrame {
  id: string;
  event_id: string;
  frame_type: FrameType;
  confidence: number;
  text_excerpt?: string;
  entities?: FrameEntities;
  frame_metadata?: Record<string, unknown>;
  created_at: string;
}

/**
 * Entities detected within a frame
 */
export interface FrameEntities {
  persons: string[];
  organizations: string[];
  locations: string[];
}

/**
 * Narrative cluster grouping similar frames
 */
export interface NarrativeCluster {
  id: string;
  name: string;
  dominant_frame: FrameType;
  frame_count: number;
  bias_score?: number;
  keywords?: string[];
  entities?: Record<string, unknown>;
  sentiment?: number;
  perspectives?: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Bias analysis result for a piece of content
 */
export interface BiasAnalysis {
  id: string;
  event_id: string;
  source?: string;
  bias_score: number;
  bias_label?: BiasLabel;
  sentiment: number;
  language_indicators?: LanguageIndicators;
  perspective?: Perspective;
  created_at: string;
}

/**
 * Language indicators for bias detection
 */
export interface LanguageIndicators {
  left_markers: number;
  right_markers: number;
  emotional_positive: number;
  emotional_negative: number;
}

/**
 * Top narrative summary for overview
 */
export interface TopNarrative {
  cluster_id: string;
  name: string;
  dominant_frame: FrameType;
  frame_count: number;
  bias_score: number;
}

// ============================================================================
// Request DTOs
// ============================================================================

/**
 * Create a new narrative frame
 */
export interface NarrativeFrameCreate {
  event_id: string;
  frame_type: FrameType;
  confidence: number;
  text_excerpt?: string;
  entities?: FrameEntities;
  frame_metadata?: Record<string, unknown>;
}

/**
 * Text analysis request options
 */
export interface TextAnalyzerOptions {
  analyze_entities?: boolean;
  analyze_sentiment?: boolean;
  analyze_frames?: boolean;
}

/**
 * Input for text analysis endpoint
 */
export interface TextAnalyzerInput {
  text: string;
  source?: string;
  options?: TextAnalyzerOptions;
}

// ============================================================================
// Query Parameters
// ============================================================================

/**
 * Parameters for listing frames
 */
export interface FramesListParams {
  page?: number;
  per_page?: number;
  frame_type?: FrameType;
  event_id?: string;
  min_confidence?: number;
}

/**
 * Parameters for listing clusters
 */
export interface ClustersListParams {
  active_only?: boolean;
  min_frame_count?: number;
  limit?: number;
}

/**
 * Parameters for bias comparison
 */
export interface BiasComparisonParams {
  event_id?: string;
  days?: number;
}

/**
 * Parameters for overview
 */
export interface OverviewParams {
  days?: number;
}

// ============================================================================
// Response DTOs
// ============================================================================

/**
 * Narrative overview statistics
 */
export interface NarrativeOverview {
  total_frames: number;
  total_clusters: number;
  frame_distribution: Record<FrameType, number>;
  bias_distribution: Record<BiasLabel, number>;
  avg_bias_score: number;
  avg_sentiment: number;
  top_narratives: TopNarrative[];
  timestamp?: string;
}

/**
 * Paginated frames list response
 */
export interface FramesListResponse {
  frames: NarrativeFrame[];
  total: number;
  page: number;
  per_page: number;
}

/**
 * Bias comparison response
 */
export interface BiasComparisonResponse {
  source_count: number;
  spectrum_distribution: Record<BiasLabel, number>;
  avg_bias_score: number;
  avg_sentiment: number;
  sources: BiasAnalysis[];
}

/**
 * Cluster update response
 */
export interface ClusterUpdateResponse {
  message: string;
  clusters_updated: number;
}

/**
 * Detected frame from text analysis
 */
export interface DetectedFrame {
  frame_type: FrameType;
  confidence: number;
  text_excerpt: string;
  entities: FrameEntities;
  match_count: number;
}

/**
 * Bias result from text analysis
 */
export interface BiasResult {
  bias_score: number;
  bias_label: BiasLabel;
  sentiment: number;
  language_indicators: LanguageIndicators;
  perspective: Perspective;
  source: string | null;
}

/**
 * Full text analysis result
 */
export interface TextAnalysisResult {
  frames: DetectedFrame[];
  bias: BiasResult;
  text_length: number;
  analyzed_at: string;
  from_cache: boolean;
}

/**
 * Cache statistics response
 */
export interface CacheStatsResponse {
  cache_enabled: boolean;
  hits?: number;
  misses?: number;
  hit_rate?: number;
  total_cached?: number;
  message?: string;
  error?: string;
}

/**
 * Cache clear response
 */
export interface CacheClearResponse {
  success: boolean;
  message: string;
}
