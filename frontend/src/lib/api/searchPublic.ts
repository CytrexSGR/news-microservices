/**
 * API client for Search Service - Public Endpoints
 *
 * Note: Search endpoint requires authentication via searchApi
 * Autocomplete and popular queries endpoints are public
 *
 * Base URL: http://localhost:8106/api/v1
 * Pattern: Follows searchServiceAdmin.ts structure
 */

import { searchApi } from '@/api/axios'
import type {
  SearchParams,
  SearchResponse,
  AutocompleteResponse,
  PopularQueriesResponse,
  RelatedSearchesResponse,
  FacetsResponse,
} from '@/features/search-ui/types/search.types'

// ===========================
// Search Endpoints
// ===========================

/**
 * Search articles using full-text search
 *
 * Requires authentication via JWT token (automatically added by searchApi interceptor)
 *
 * @param params - Search parameters
 * @returns Search results with pagination
 *
 * @example
 * ```ts
 * const results = await searchArticles({
 *   query: 'artificial intelligence',
 *   page: 1,
 *   page_size: 20,
 *   sentiment: 'positive',
 *   date_from: '2024-01-01'
 * })
 * ```
 */
export const searchArticles = async (params: SearchParams): Promise<SearchResponse> => {
  const { data } = await searchApi.get<SearchResponse>('/search', { params })
  return data
}

/**
 * Advanced search with semantic capabilities
 *
 * @param params - Advanced search parameters including semantic options
 * @returns Search results with enhanced relevance scoring
 *
 * @example
 * ```ts
 * const results = await advancedSearch({
 *   query: 'AI breakthrough',
 *   semantic: true,
 *   title_boost: 2.0,
 *   include_facets: true
 * })
 * ```
 */
export const advancedSearch = async (params: SearchParams): Promise<SearchResponse> => {
  const { data } = await searchApi.get<SearchResponse>('/search/advanced', { params })
  return data
}

// ===========================
// Autocomplete Endpoints
// ===========================

/**
 * Get autocomplete suggestions based on partial query
 *
 * Provides suggestions from:
 * - Popular searches
 * - Article titles
 * - Search history
 *
 * No authentication required
 *
 * @param query - Partial query string (1-100 characters)
 * @param limit - Maximum number of suggestions (1-20, default: 10)
 * @returns List of suggestions
 *
 * @example
 * ```ts
 * const suggestions = await getAutocomplete('artificial int', 5)
 * // Returns: { query: 'artificial int', suggestions: ['artificial intelligence', ...] }
 * ```
 */
export const getAutocomplete = async (
  query: string,
  limit: number = 10
): Promise<AutocompleteResponse> => {
  const { data } = await searchApi.get<AutocompleteResponse>('/search/suggest', {
    params: { query, limit },
  })
  return data
}

// ===========================
// Popular & Trending Endpoints
// ===========================

/**
 * Get most popular search queries
 *
 * No authentication required
 *
 * @param limit - Maximum number of queries (1-50, default: 10)
 * @returns List of popular queries with hit counts
 *
 * @example
 * ```ts
 * const popular = await getPopularQueries(10)
 * // Returns: { popular_queries: [{ query: 'AI', hit_count: 150 }, ...], total: 10 }
 * ```
 */
export const getPopularQueries = async (limit: number = 10): Promise<PopularQueriesResponse> => {
  const { data } = await searchApi.get<PopularQueriesResponse>('/search/popular', {
    params: { limit },
  })
  return data
}

/**
 * Get related search queries for a given query
 *
 * No authentication required
 *
 * @param query - Current search query (1-500 characters)
 * @param limit - Maximum number of related queries (1-20, default: 5)
 * @returns List of related queries
 *
 * @example
 * ```ts
 * const related = await getRelatedSearches('machine learning', 5)
 * // Returns: { query: 'machine learning', related: ['deep learning', 'neural networks', ...] }
 * ```
 */
export const getRelatedSearches = async (
  query: string,
  limit: number = 5
): Promise<RelatedSearchesResponse> => {
  const { data } = await searchApi.get<RelatedSearchesResponse>('/search/related', {
    params: { query, limit },
  })
  return data
}

/**
 * Get all available filter options (facets)
 *
 * Returns all unique sources and categories from the search index.
 * Used to dynamically populate filter dropdowns with actual data.
 *
 * No authentication required
 *
 * @returns Available sources and categories
 *
 * @example
 * ```ts
 * const facets = await getFacets()
 * // Returns: { sources: ['BBC News', 'Reuters', ...], categories: ['economy_markets', ...] }
 * ```
 */
export const getFacets = async (): Promise<FacetsResponse> => {
  const { data } = await searchApi.get<FacetsResponse>('/search/facets')
  return data
}

// ===========================
// Search History Endpoints
// ===========================

/**
 * Get user's search history
 *
 * Requires authentication
 *
 * @param limit - Maximum number of history items
 * @returns List of recent searches
 *
 * @example
 * ```ts
 * const history = await getSearchHistory(20)
 * ```
 */
export const getSearchHistory = async (limit: number = 20) => {
  const { data } = await searchApi.get('/search/history', {
    params: { limit },
  })
  return data
}

// ===========================
// Saved Searches Endpoints
// ===========================

/**
 * Get user's saved searches
 *
 * Requires authentication
 *
 * @returns List of saved searches
 *
 * @example
 * ```ts
 * const saved = await getSavedSearches()
 * ```
 */
export const getSavedSearches = async () => {
  const { data } = await searchApi.get('/search/saved')
  return data
}

/**
 * Save a search query
 *
 * Requires authentication
 *
 * @param searchParams - Search parameters to save
 * @param name - Optional name for the saved search
 * @returns Saved search details
 *
 * @example
 * ```ts
 * const saved = await saveSearch(
 *   { query: 'AI news', sentiment: 'positive' },
 *   'Positive AI News'
 * )
 * ```
 */
export const saveSearch = async (searchParams: SearchParams, name?: string) => {
  const { data } = await searchApi.post('/search/saved', {
    ...searchParams,
    name,
  })
  return data
}

/**
 * Delete a saved search
 *
 * Requires authentication
 *
 * @param searchId - ID of the saved search to delete
 * @returns Deletion confirmation
 *
 * @example
 * ```ts
 * await deleteSavedSearch('123e4567-e89b-12d3-a456-426614174000')
 * ```
 */
export const deleteSavedSearch = async (searchId: string) => {
  const { data } = await searchApi.delete(`/search/saved/${searchId}`)
  return data
}
