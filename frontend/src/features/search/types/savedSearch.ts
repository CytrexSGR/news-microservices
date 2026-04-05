/**
 * TypeScript types for Saved Searches
 *
 * Based on search-service API schemas
 */

/**
 * Saved search filters
 */
export interface SavedSearchFilters {
  source?: string[] | null
  sentiment?: string[] | null
  entities?: string[] | null
  date_from?: string | null
  date_to?: string | null
}

/**
 * Create saved search request
 */
export interface SavedSearchCreate {
  /** Name for the saved search */
  name: string
  /** Search query */
  query: string
  /** Optional filters */
  filters?: SavedSearchFilters | null
  /** Enable notifications for new results */
  notifications_enabled?: boolean
}

/**
 * Update saved search request
 */
export interface SavedSearchUpdate {
  name?: string
  query?: string
  filters?: SavedSearchFilters | null
  notifications_enabled?: boolean
}

/**
 * Saved search response from API
 */
export interface SavedSearch {
  id: number
  name: string
  query: string
  filters: SavedSearchFilters | null
  notifications_enabled: boolean
  last_notified_at: string | null
  created_at: string
  updated_at: string
}

/**
 * Saved search list response
 */
export interface SavedSearchListResponse {
  total: number
  items: SavedSearch[]
}

/**
 * Run saved search response (same as SearchResponse)
 */
export interface RunSavedSearchResponse {
  query: string
  total: number
  page: number
  page_size: number
  results: Array<{
    article_id: string
    title: string
    content: string
    author?: string | null
    source?: string | null
    url?: string | null
    published_at?: string | null
    sentiment?: string | null
    entities?: string[] | null
    relevance_score: number
    highlight?: Record<string, string[]> | null
  }>
  facets?: Record<string, unknown> | null
  execution_time_ms: number
}
