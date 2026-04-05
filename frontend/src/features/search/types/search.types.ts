/**
 * Search Feature - Complete Type Definitions
 *
 * Comprehensive types for saved searches, scheduling, alerts, and results.
 * Based on search-service API schemas at port 8106.
 */

// =============================================================================
// Search Filters
// =============================================================================

/**
 * Search filter configuration
 */
export interface SearchFilters {
  /** Start date for date range filter (ISO string) */
  date_from?: string;
  /** End date for date range filter (ISO string) */
  date_to?: string;
  /** Filter by source names */
  sources?: string[];
  /** Filter by categories */
  categories?: string[];
  /** Filter by sentiment */
  sentiment?: 'positive' | 'negative' | 'neutral' | 'all';
  /** Only include articles with extracted entities */
  has_entities?: boolean;
  /** Filter by specific entity types */
  entity_types?: EntityType[];
}

/**
 * Entity types for filtering
 */
export type EntityType =
  | 'PERSON'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'GPE'
  | 'EVENT'
  | 'PRODUCT'
  | 'MONEY'
  | 'DATE'
  | 'PERCENT';

// =============================================================================
// Saved Search
// =============================================================================

/**
 * Saved search from API
 */
export interface SavedSearch {
  /** Unique identifier */
  id: string;
  /** User-assigned name */
  name: string;
  /** Search query string */
  query: string;
  /** Applied filters */
  filters: SearchFilters;
  /** Whether search is scheduled to run automatically */
  is_scheduled: boolean;
  /** Cron expression for schedule (if scheduled) */
  schedule_cron?: string;
  /** Whether alerts are enabled for new results */
  alert_enabled: boolean;
  /** Minimum new results to trigger alert */
  alert_threshold?: number;
  /** Creation timestamp (ISO string) */
  created_at: string;
  /** Last update timestamp (ISO string) */
  updated_at: string;
  /** Last execution timestamp (ISO string) */
  last_run?: string;
  /** Result count from last run */
  result_count?: number;
}

/**
 * Request to create a new saved search
 */
export interface SavedSearchCreate {
  /** Name for the saved search */
  name: string;
  /** Search query */
  query: string;
  /** Optional filters */
  filters?: SearchFilters;
  /** Enable scheduled execution */
  is_scheduled?: boolean;
  /** Cron expression for schedule */
  schedule_cron?: string;
  /** Enable alerts for new results */
  alert_enabled?: boolean;
  /** Minimum new results to trigger alert */
  alert_threshold?: number;
}

/**
 * Request to update an existing saved search
 */
export interface SavedSearchUpdate {
  /** Updated name */
  name?: string;
  /** Updated query */
  query?: string;
  /** Updated filters */
  filters?: SearchFilters;
  /** Updated schedule status */
  is_scheduled?: boolean;
  /** Updated cron expression */
  schedule_cron?: string;
  /** Updated alert status */
  alert_enabled?: boolean;
  /** Updated alert threshold */
  alert_threshold?: number;
}

/**
 * Paginated list of saved searches
 */
export interface SavedSearchListResponse {
  /** Total count of saved searches */
  total: number;
  /** List of saved searches */
  items: SavedSearch[];
}

// =============================================================================
// Search Results
// =============================================================================

/**
 * Entity extracted from article
 */
export interface SearchEntity {
  /** Entity name */
  name: string;
  /** Entity type */
  type: EntityType;
  /** Confidence score (0-1) */
  confidence?: number;
}

/**
 * Single search result (article)
 */
export interface SearchResult {
  /** Article ID */
  id: string;
  /** Article title */
  title: string;
  /** Content preview/snippet */
  content_preview: string;
  /** Source name */
  source: string;
  /** Publication date (ISO string) */
  published_at: string;
  /** Sentiment score (-1 to 1) */
  sentiment_score: number;
  /** Sentiment label */
  sentiment_label?: 'positive' | 'negative' | 'neutral';
  /** Extracted entities */
  entities: SearchEntity[];
  /** Search relevance score */
  relevance_score: number;
  /** Article URL */
  url?: string;
  /** Author name */
  author?: string;
  /** Highlighted matches */
  highlights?: Record<string, string[]>;
}

/**
 * Response from executing a search
 */
export interface SearchExecuteResponse {
  /** Query that was executed */
  query: string;
  /** Total number of matching results */
  total: number;
  /** Current page number */
  page: number;
  /** Page size */
  page_size: number;
  /** List of results */
  results: SearchResult[];
  /** Facets for filtering */
  facets?: SearchFacets;
  /** Query execution time in milliseconds */
  execution_time_ms: number;
}

/**
 * Search facets for filtering UI
 */
export interface SearchFacets {
  /** Sources with counts */
  sources?: Array<{ value: string; count: number }>;
  /** Categories with counts */
  categories?: Array<{ value: string; count: number }>;
  /** Sentiment distribution */
  sentiments?: Array<{ value: string; count: number }>;
  /** Entity types with counts */
  entity_types?: Array<{ value: EntityType; count: number }>;
}

// =============================================================================
// Scheduled Searches
// =============================================================================

/**
 * Schedule frequency presets
 */
export type ScheduleFrequency = 'hourly' | 'daily' | 'weekly' | 'custom';

/**
 * Schedule configuration
 */
export interface ScheduleConfig {
  /** Schedule frequency */
  frequency: ScheduleFrequency;
  /** Cron expression (for custom frequency) */
  cron?: string;
  /** Hour to run (0-23, for daily/weekly) */
  hour?: number;
  /** Day of week (0-6, for weekly) */
  day_of_week?: number;
  /** Timezone for schedule */
  timezone?: string;
}

/**
 * Scheduled search with execution details
 */
export interface ScheduledSearch extends SavedSearch {
  /** Next scheduled execution time (ISO string) */
  next_run?: string;
  /** Previous execution times */
  run_history?: Array<{
    executed_at: string;
    result_count: number;
    execution_time_ms: number;
    success: boolean;
    error?: string;
  }>;
}

/**
 * Response for listing scheduled searches
 */
export interface ScheduledSearchListResponse {
  /** Total count */
  total: number;
  /** List of scheduled searches */
  items: ScheduledSearch[];
}

// =============================================================================
// Search Alerts
// =============================================================================

/**
 * Alert delivery channel types
 */
export type AlertChannelType = 'email' | 'webhook' | 'in_app';

/**
 * Alert configuration for a saved search
 */
export interface SearchAlertConfig {
  /** Associated saved search ID */
  saved_search_id: string;
  /** Alert channel type */
  alert_type: AlertChannelType;
  /** Minimum new results to trigger alert */
  threshold: number;
  /** Cooldown period in minutes before next alert */
  cooldown_minutes: number;
  /** Whether alert is currently enabled */
  enabled: boolean;
  /** Webhook URL (if alert_type is webhook) */
  webhook_url?: string;
  /** Email address (if alert_type is email) */
  email?: string;
}

/**
 * Request to create/update alert configuration
 */
export interface SearchAlertConfigRequest {
  /** Alert channel type */
  alert_type: AlertChannelType;
  /** Minimum new results to trigger */
  threshold: number;
  /** Cooldown in minutes */
  cooldown_minutes: number;
  /** Enable/disable alert */
  enabled?: boolean;
  /** Webhook URL */
  webhook_url?: string;
  /** Email override */
  email?: string;
}

/**
 * Alert history entry
 */
export interface SearchAlertHistoryEntry {
  /** Alert ID */
  id: string;
  /** Saved search ID */
  saved_search_id: string;
  /** When alert was triggered */
  triggered_at: string;
  /** Alert channel used */
  channel: AlertChannelType;
  /** Number of new results that triggered alert */
  result_count: number;
  /** Delivery status */
  status: 'sent' | 'failed' | 'pending';
  /** Error message if failed */
  error?: string;
}

/**
 * Response for alert history
 */
export interface SearchAlertHistoryResponse {
  /** Total count */
  total: number;
  /** List of alert history entries */
  items: SearchAlertHistoryEntry[];
}

// =============================================================================
// Quick Search
// =============================================================================

/**
 * Quick search request (not saved)
 */
export interface QuickSearchRequest {
  /** Search query */
  query: string;
  /** Optional filters */
  filters?: SearchFilters;
  /** Page number */
  page?: number;
  /** Page size */
  page_size?: number;
  /** Sort field */
  sort_by?: 'relevance' | 'date' | 'sentiment';
  /** Sort direction */
  sort_order?: 'asc' | 'desc';
}

/**
 * Search suggestions response
 */
export interface SearchSuggestionsResponse {
  /** Query suggestions based on history */
  queries: string[];
  /** Entity suggestions */
  entities: Array<{ name: string; type: EntityType }>;
  /** Recent searches */
  recent: Array<{ query: string; timestamp: string }>;
}

// =============================================================================
// Type Guards
// =============================================================================

/**
 * Type guard to check if search has schedule
 */
export function isScheduledSearch(search: SavedSearch): search is ScheduledSearch {
  return search.is_scheduled && !!search.schedule_cron;
}

/**
 * Type guard to check if sentiment is valid
 */
export function isValidSentiment(
  value: string
): value is 'positive' | 'negative' | 'neutral' {
  return ['positive', 'negative', 'neutral'].includes(value);
}

/**
 * Type guard to check if entity type is valid
 */
export function isValidEntityType(value: string): value is EntityType {
  const validTypes: EntityType[] = [
    'PERSON',
    'ORGANIZATION',
    'LOCATION',
    'GPE',
    'EVENT',
    'PRODUCT',
    'MONEY',
    'DATE',
    'PERCENT',
  ];
  return validTypes.includes(value as EntityType);
}
