/**
 * Content Analysis Types
 * Types for article analysis, entity extraction, and sentiment analysis
 */

/**
 * Entity types supported by the analysis service
 */
export type EntityType =
  | 'PERSON'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'EVENT'
  | 'TOPIC'
  | 'PRODUCT'
  | 'MONEY'
  | 'DATE'
  | 'PERCENT'
  | 'QUANTITY'
  | 'ORDINAL'
  | 'CARDINAL'
  | 'LAW'
  | 'WORK_OF_ART';

/**
 * Extracted entity from content analysis
 */
export interface AnalysisEntity {
  name: string;
  type: EntityType;
  confidence: number;
  start_offset?: number;
  end_offset?: number;
  wikidata_id?: string;
}

/**
 * Sentiment analysis result
 */
export interface SentimentResult {
  /** Score from -1 (negative) to 1 (positive) */
  score: number;
  label: 'negative' | 'neutral' | 'positive';
  confidence: number;
}

/**
 * Complete analysis result for an article
 */
export interface AnalysisResult {
  article_id: string;
  entities: AnalysisEntity[];
  sentiment: SentimentResult;
  topics: string[];
  narrative_frames: string[];
  analysis_timestamp: string;
  cost_usd: number;
  latency_ms: number;
}

/**
 * Analysis processing status
 */
export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Status response for analysis job
 */
export interface AnalysisStatusResponse {
  article_id: string;
  status: AnalysisStatus;
  progress_percent?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

/**
 * Request payload for triggering analysis
 */
export interface AnalyzeArticleRequest {
  article_id: string;
  force_reanalyze?: boolean;
  include_entities?: boolean;
  include_sentiment?: boolean;
  include_topics?: boolean;
  include_narrative_frames?: boolean;
}

/**
 * Response from analyze endpoint
 */
export interface AnalyzeArticleResponse {
  job_id: string;
  article_id: string;
  status: AnalysisStatus;
  message: string;
  estimated_time_seconds?: number;
}

/**
 * Response from entities endpoint
 */
export interface EntitiesResponse {
  article_id: string;
  entities: AnalysisEntity[];
  extracted_at: string;
  entity_count: number;
}

/**
 * Entity type display configuration
 */
export interface EntityTypeConfig {
  label: string;
  color: string;
  bgColor: string;
  icon: string;
}

/**
 * Get display configuration for entity type
 */
export function getEntityTypeConfig(type: EntityType): EntityTypeConfig {
  const configs: Record<EntityType, EntityTypeConfig> = {
    PERSON: {
      label: 'Person',
      color: 'text-blue-700 dark:text-blue-300',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      icon: 'User',
    },
    ORGANIZATION: {
      label: 'Organization',
      color: 'text-purple-700 dark:text-purple-300',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
      icon: 'Building2',
    },
    LOCATION: {
      label: 'Location',
      color: 'text-green-700 dark:text-green-300',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      icon: 'MapPin',
    },
    EVENT: {
      label: 'Event',
      color: 'text-orange-700 dark:text-orange-300',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
      icon: 'Calendar',
    },
    TOPIC: {
      label: 'Topic',
      color: 'text-teal-700 dark:text-teal-300',
      bgColor: 'bg-teal-100 dark:bg-teal-900/30',
      icon: 'Hash',
    },
    PRODUCT: {
      label: 'Product',
      color: 'text-pink-700 dark:text-pink-300',
      bgColor: 'bg-pink-100 dark:bg-pink-900/30',
      icon: 'Package',
    },
    MONEY: {
      label: 'Money',
      color: 'text-emerald-700 dark:text-emerald-300',
      bgColor: 'bg-emerald-100 dark:bg-emerald-900/30',
      icon: 'DollarSign',
    },
    DATE: {
      label: 'Date',
      color: 'text-cyan-700 dark:text-cyan-300',
      bgColor: 'bg-cyan-100 dark:bg-cyan-900/30',
      icon: 'CalendarDays',
    },
    PERCENT: {
      label: 'Percent',
      color: 'text-indigo-700 dark:text-indigo-300',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
      icon: 'Percent',
    },
    QUANTITY: {
      label: 'Quantity',
      color: 'text-amber-700 dark:text-amber-300',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      icon: 'Hash',
    },
    ORDINAL: {
      label: 'Ordinal',
      color: 'text-slate-700 dark:text-slate-300',
      bgColor: 'bg-slate-100 dark:bg-slate-900/30',
      icon: 'ListOrdered',
    },
    CARDINAL: {
      label: 'Cardinal',
      color: 'text-gray-700 dark:text-gray-300',
      bgColor: 'bg-gray-100 dark:bg-gray-900/30',
      icon: 'Hash',
    },
    LAW: {
      label: 'Law',
      color: 'text-red-700 dark:text-red-300',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      icon: 'Scale',
    },
    WORK_OF_ART: {
      label: 'Work of Art',
      color: 'text-rose-700 dark:text-rose-300',
      bgColor: 'bg-rose-100 dark:bg-rose-900/30',
      icon: 'Palette',
    },
  };

  return configs[type] || {
    label: type,
    color: 'text-gray-700 dark:text-gray-300',
    bgColor: 'bg-gray-100 dark:bg-gray-900/30',
    icon: 'Tag',
  };
}

/**
 * Get sentiment display configuration
 */
export function getSentimentConfig(label: SentimentResult['label']) {
  const configs = {
    positive: {
      color: 'text-green-700 dark:text-green-300',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      icon: 'TrendingUp',
    },
    neutral: {
      color: 'text-gray-700 dark:text-gray-300',
      bgColor: 'bg-gray-100 dark:bg-gray-900/30',
      icon: 'Minus',
    },
    negative: {
      color: 'text-red-700 dark:text-red-300',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      icon: 'TrendingDown',
    },
  };

  return configs[label];
}

/**
 * Get status display configuration
 */
export function getStatusConfig(status: AnalysisStatus) {
  const configs = {
    pending: {
      color: 'text-gray-700 dark:text-gray-300',
      bgColor: 'bg-gray-100 dark:bg-gray-800',
      icon: 'Clock',
      label: 'Pending',
    },
    processing: {
      color: 'text-blue-700 dark:text-blue-300',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      icon: 'Loader2',
      label: 'Processing',
    },
    completed: {
      color: 'text-green-700 dark:text-green-300',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      icon: 'CheckCircle',
      label: 'Completed',
    },
    failed: {
      color: 'text-red-700 dark:text-red-300',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      icon: 'XCircle',
      label: 'Failed',
    },
  };

  return configs[status];
}
