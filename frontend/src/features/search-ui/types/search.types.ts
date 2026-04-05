/**
 * TypeScript types for Search Service API
 *
 * Based on OpenAPI schema from http://localhost:8106/openapi.json
 */

// ===========================
// Search Request Types
// ===========================

/**
 * Search parameters for basic search
 */
export interface SearchParams {
  /** Search query (1-500 characters) */
  query: string
  /** Page number (min: 1, default: 1) */
  page?: number
  /** Results per page (min: 1, max: 100, default: 20) */
  page_size?: number
  /** Filter by source */
  source?: string | null
  /** Filter by sentiment */
  sentiment?: string | null
  /** Filter by date from (ISO format) */
  date_from?: string | null
  /** Filter by date to (ISO format) */
  date_to?: string | null
}

/**
 * Search filters for advanced search
 */
export interface SearchFilters {
  source?: string | null
  sentiment?: string | null
  date_from?: string | null
  date_to?: string | null
  entities?: string[]
}

// ===========================
// Search Response Types
// ===========================

/**
 * Single search result item
 */
export interface SearchResultItem {
  /** Article ID */
  article_id: string
  /** Article title */
  title: string
  /** Article content */
  content: string
  /** Article author */
  author?: string | null
  /** Article source */
  source?: string | null
  /** Article URL */
  url?: string | null
  /** Publication date/time */
  published_at?: string | null
  /** Sentiment analysis result */
  sentiment?: string | null
  /** Extracted entities */
  entities?: string[] | null
  /** Search relevance score */
  relevance_score: number
  /** Search term highlights */
  highlight?: Record<string, string[]> | null
}

/**
 * Paginated search response
 */
export interface SearchResponse {
  /** Original search query */
  query: string
  /** Total number of results */
  total: number
  /** Current page number */
  page: number
  /** Results per page */
  page_size: number
  /** Array of search results */
  results: SearchResultItem[]
  /** Search facets (aggregations) */
  facets?: Record<string, unknown> | null
  /** Query execution time in milliseconds */
  execution_time_ms: number
}

// ===========================
// Autocomplete Types
// ===========================

/**
 * Autocomplete suggestion response
 */
export interface AutocompleteResponse {
  /** Original query */
  query: string
  /** Array of suggestions */
  suggestions: string[]
}

// ===========================
// Popular Queries Types
// ===========================

/**
 * Popular query item
 */
export interface PopularQuery {
  /** Query text */
  query: string
  /** Number of times searched */
  hit_count: number
}

/**
 * Popular queries response
 */
export interface PopularQueriesResponse {
  /** Array of popular queries */
  popular_queries: PopularQuery[]
  /** Total count */
  total: number
}

// ===========================
// Related Searches Types
// ===========================

/**
 * Related search query
 */
export interface RelatedQuery {
  /** Related query text */
  query: string
  /** Relevance score */
  score?: number
}

/**
 * Related searches response
 */
export interface RelatedSearchesResponse {
  /** Original query */
  query: string
  /** Array of related query strings */
  related: string[]
}

// ===========================
// Facets Types
// ===========================

/**
 * Available filter options (facets) from search index
 */
export interface FacetsResponse {
  /** Available article sources */
  sources: string[]
  /** Available article categories */
  categories: string[]
}

// ===========================
// Advanced Search Types
// ===========================

/**
 * Advanced search parameters
 */
export interface AdvancedSearchParams extends SearchParams {
  /** Semantic search mode */
  semantic?: boolean
  /** Boost factor for title matches */
  title_boost?: number
  /** Boost factor for content matches */
  content_boost?: number
  /** Include facets in response */
  include_facets?: boolean
}

// ===========================
// Error Types
// ===========================

/**
 * API error response
 */
export interface SearchError {
  detail: string
  code?: string
}

/**
 * Validation error
 */
export interface ValidationError {
  detail: Array<{
    loc: string[]
    msg: string
    type: string
  }>
}
