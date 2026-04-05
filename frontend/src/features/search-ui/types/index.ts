/**
 * Search UI Types - Barrel Export
 *
 * Centralizes all search-related type exports
 */

export type {
  // Request Types
  SearchParams,
  SearchFilters,
  AdvancedSearchParams,

  // Response Types
  SearchResponse,
  SearchResultItem,
  AutocompleteResponse,
  PopularQueriesResponse,
  PopularQuery,
  RelatedSearchesResponse,
  RelatedQuery,

  // Error Types
  SearchError,
  ValidationError,
} from './search.types'
