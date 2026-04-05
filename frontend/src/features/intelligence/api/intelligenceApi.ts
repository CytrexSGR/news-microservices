/**
 * Intelligence Service API Client
 *
 * Provides access to intelligence analysis endpoints for event clustering,
 * risk scoring, trend analysis, and entity detection.
 *
 * Base URL: http://localhost:8118/api/v1/intelligence
 *
 * @module features/intelligence/api
 */

import { createApiClient } from '@/shared/api';
import type {
  OverviewResponse,
  ClustersResponse,
  ClusterDetail,
  ClusterEventsResponse,
  LatestEventsResponse,
  SubcategoriesResponse,
  RiskHistoryResponse,
} from '../types/intelligence.types';

// =============================================================================
// Configuration
// =============================================================================

/**
 * Intelligence Service base URL
 * Note: VITE_INTELLIGENCE_API_URL should contain the full path including /api/v1/intelligence
 * Fallback provides full path for localhost development
 */
const INTELLIGENCE_BASE_URL =
  import.meta.env.VITE_INTELLIGENCE_API_URL || 'http://localhost:8118/api/v1/intelligence';

/**
 * Intelligence API client instance
 * Pre-configured with auth interceptor and error handling
 */
export const intelligenceApi = createApiClient(INTELLIGENCE_BASE_URL);

// =============================================================================
// Request Parameter Types
// =============================================================================

/**
 * Parameters for listing clusters
 */
export interface ClustersParams {
  /** Minimum number of events in cluster */
  min_events?: number;
  /** Time range in days (default: 7) */
  time_range?: number;
  /** Filter by time window */
  time_window?: '1h' | '6h' | '12h' | '24h' | 'week' | 'month';
  /** Sort field */
  sort_by?: 'risk_score' | 'event_count' | 'last_updated';
  /** Page number (1-indexed) */
  page?: number;
  /** Items per page (max 100) */
  per_page?: number;
}

/**
 * Parameters for getting cluster events
 */
export interface ClusterEventsParams {
  /** Page number (1-indexed) */
  page?: number;
  /** Items per page (max 100) */
  per_page?: number;
}

/**
 * Parameters for getting latest events
 */
export interface LatestEventsParams {
  /** Hours to look back (1-48, default: 4) */
  hours?: number;
  /** Maximum events to return (1-100, default: 20) */
  limit?: number;
}

/**
 * Parameters for risk history
 */
export interface RiskHistoryParams {
  /** Days to look back (1-30, default: 7) */
  days?: number;
}

/**
 * Parameters for trending entities
 */
export interface TrendingEntitiesParams {
  /** Entity type filter */
  entity_type?: 'person' | 'organization' | 'location' | 'all';
  /** Hours to look back */
  hours?: number;
  /** Maximum entities to return */
  limit?: number;
}

// =============================================================================
// Request Body Types (for POST endpoints)
// =============================================================================

/**
 * Request body for event detection
 */
export interface EventDetectRequest {
  /** Text content to analyze (min 10, max 50000 chars) */
  text: string;
  /** Include keyword extraction (default: true) */
  include_keywords?: boolean;
  /** Maximum keywords to extract (1-50, default: 10) */
  max_keywords?: number;
}

/**
 * Response from event detection
 */
export interface EventDetectResponse {
  /** Extracted entities by type */
  entities: {
    persons: string[];
    organizations: string[];
    locations: string[];
  };
  /** Extracted keywords */
  keywords: string[];
  /** Total number of unique entities */
  entity_count: number;
  /** Input text length */
  text_length: number;
  /** Processing time in milliseconds */
  processing_time_ms: number;
}

/**
 * Request body for risk calculation
 *
 * Supports three modes:
 * 1. Cluster mode: Provide cluster_id
 * 2. Entity mode: Provide entities (array of names)
 * 3. Text mode: Provide text content
 */
export interface RiskCalculateRequest {
  /** Cluster ID to calculate risk for */
  cluster_id?: string;
  /** Entity names to analyze */
  entities?: string[];
  /** Text to analyze for risk (max 50000 chars) */
  text?: string;
  /** Include risk factor breakdown (default: true) */
  include_factors?: boolean;
}

/**
 * Individual risk factor
 */
export interface RiskFactor {
  /** Factor name */
  name: string;
  /** Raw value */
  value: number;
  /** Weight in calculation */
  weight: number;
  /** Contribution to final score */
  contribution: number;
}

/**
 * Response from risk calculation
 */
export interface RiskCalculateResponse {
  /** Calculated risk score (0-100) */
  risk_score: number;
  /** Risk level category */
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  /** Change from previous calculation */
  risk_delta?: number | null;
  /** Risk factor breakdown */
  factors: RiskFactor[];
  /** Associated cluster if any */
  cluster_id?: string | null;
  /** Timestamp of calculation */
  timestamp: string;
}

/**
 * Response for trending entities
 */
export interface TrendingEntitiesResponse {
  entities: Array<{
    name: string;
    type: 'person' | 'organization' | 'location';
    mention_count: number;
    trend_direction: 'up' | 'down' | 'stable';
    trend_percentage: number;
    clusters: string[];
    avg_risk_score: number;
  }>;
  period_hours: number;
  timestamp: string;
}

// =============================================================================
// API Endpoint Functions
// =============================================================================

/**
 * Intelligence Service API Endpoints
 *
 * All endpoints are accessible via this namespace for clean imports:
 * @example
 * ```ts
 * import { intelligenceEndpoints } from '@/features/intelligence/api/intelligenceApi';
 *
 * const overview = await intelligenceEndpoints.getOverview();
 * const clusters = await intelligenceEndpoints.getClusters({ min_events: 5 });
 * ```
 */
export const intelligenceEndpoints = {
  // ===========================================================================
  // Overview & Dashboard
  // ===========================================================================

  /**
   * Get intelligence overview with top clusters and risk metrics
   *
   * Returns:
   * - global_risk_index: Average risk score of top 5 clusters
   * - top_clusters: Top 5 clusters by risk score
   * - geo_risk: Average risk for geopolitical category
   * - finance_risk: Average risk for financial category
   * - top_regions: Top 5 regions by event activity
   * - total_clusters: Total active clusters
   * - total_events: Total events in last 7 days
   */
  getOverview: async (): Promise<OverviewResponse> => {
    const response = await intelligenceApi.get<OverviewResponse>('/overview');
    return response.data;
  },

  // ===========================================================================
  // Clusters
  // ===========================================================================

  /**
   * Get list of intelligence clusters with filtering and pagination
   *
   * @param params - Filtering and pagination parameters
   */
  getClusters: async (params?: ClustersParams): Promise<ClustersResponse> => {
    const response = await intelligenceApi.get<ClustersResponse>('/clusters', {
      params,
    });
    return response.data;
  },

  /**
   * Get detailed information for a specific cluster
   *
   * @param clusterId - UUID of the cluster
   */
  getClusterById: async (clusterId: string): Promise<ClusterDetail> => {
    const response = await intelligenceApi.get<ClusterDetail>(
      `/clusters/${clusterId}`
    );
    return response.data;
  },

  /**
   * Get all events for a specific cluster with pagination
   *
   * @param clusterId - UUID of the cluster
   * @param params - Pagination parameters
   */
  getClusterEvents: async (
    clusterId: string,
    params?: ClusterEventsParams
  ): Promise<ClusterEventsResponse> => {
    const response = await intelligenceApi.get<ClusterEventsResponse>(
      `/clusters/${clusterId}/events`,
      { params }
    );
    return response.data;
  },

  // ===========================================================================
  // Events
  // ===========================================================================

  /**
   * Get latest events across all clusters
   *
   * @param params - Query parameters for filtering
   */
  getLatestEvents: async (
    params?: LatestEventsParams
  ): Promise<LatestEventsResponse> => {
    const response = await intelligenceApi.get<LatestEventsResponse>(
      '/events/latest',
      { params }
    );
    return response.data;
  },

  /**
   * Detect and classify an event from content
   *
   * Analyzes provided text content to:
   * - Detect if it represents a significant event
   * - Extract entities (persons, organizations, locations)
   * - Extract keywords
   * - Match to existing clusters if applicable
   * - Calculate initial risk score
   *
   * @param data - Event detection request
   */
  detectEvents: async (
    data: EventDetectRequest
  ): Promise<EventDetectResponse> => {
    const response = await intelligenceApi.post<EventDetectResponse>(
      '/events/detect',
      data
    );
    return response.data;
  },

  // ===========================================================================
  // Entities
  // ===========================================================================

  /**
   * Get trending entities based on recent mentions and activity
   *
   * Returns entities that have seen increased mention frequency
   * or significant risk score changes.
   *
   * @param params - Query parameters for filtering
   */
  getTrendingEntities: async (
    params?: TrendingEntitiesParams
  ): Promise<TrendingEntitiesResponse> => {
    const response = await intelligenceApi.get<TrendingEntitiesResponse>(
      '/entities/trending',
      { params }
    );
    return response.data;
  },

  // ===========================================================================
  // Categories & Subcategories
  // ===========================================================================

  /**
   * Get top subcategories per category
   *
   * Returns dynamic sub-categories extracted from current news data:
   * - Geo: Top 2 countries/regions
   * - Finance: Top 2 economic topics
   * - Tech: Top 2 tech topics
   */
  getSubcategories: async (): Promise<SubcategoriesResponse> => {
    const response =
      await intelligenceApi.get<SubcategoriesResponse>('/subcategories');
    return response.data;
  },

  // ===========================================================================
  // Risk Analysis
  // ===========================================================================

  /**
   * Get historical risk scores for trend visualization
   *
   * Returns daily risk score history for:
   * - Global risk index
   * - Geo risk
   * - Finance risk
   *
   * @param params - Query parameters
   */
  getRiskHistory: async (
    params?: RiskHistoryParams
  ): Promise<RiskHistoryResponse> => {
    const response = await intelligenceApi.get<RiskHistoryResponse>(
      '/risk-history',
      { params }
    );
    return response.data;
  },

  /**
   * Calculate risk score for a cluster or set of entities
   *
   * Performs risk calculation considering:
   * - Event frequency and recency
   * - Entity relationships
   * - Historical patterns
   * - Cross-cluster correlations
   *
   * @param data - Risk calculation request
   */
  calculateRisk: async (
    data: RiskCalculateRequest
  ): Promise<RiskCalculateResponse> => {
    const response = await intelligenceApi.post<RiskCalculateResponse>(
      '/risk/calculate',
      data
    );
    return response.data;
  },
};

// =============================================================================
// Legacy Exports (for backward compatibility)
// =============================================================================

/**
 * @deprecated Use intelligenceEndpoints.getOverview() instead
 */
export const getIntelligenceOverview = intelligenceEndpoints.getOverview;

/**
 * @deprecated Use intelligenceEndpoints.getClusters() instead
 */
export const getClusters = intelligenceEndpoints.getClusters;

/**
 * @deprecated Use intelligenceEndpoints.getClusterById() instead
 */
export const getClusterDetail = intelligenceEndpoints.getClusterById;

/**
 * @deprecated Use intelligenceEndpoints.getClusterEvents() instead
 */
export const getClusterEvents = intelligenceEndpoints.getClusterEvents;

/**
 * @deprecated Use intelligenceEndpoints.getLatestEvents() instead
 */
export const getLatestEvents = intelligenceEndpoints.getLatestEvents;

/**
 * @deprecated Use intelligenceEndpoints.getSubcategories() instead
 */
export const getSubcategories = intelligenceEndpoints.getSubcategories;

/**
 * @deprecated Use intelligenceEndpoints.getRiskHistory() instead
 */
export const getRiskHistory = (days: number = 7): Promise<RiskHistoryResponse> =>
  intelligenceEndpoints.getRiskHistory({ days });
