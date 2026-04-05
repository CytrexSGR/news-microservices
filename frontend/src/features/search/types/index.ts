/**
 * Search Feature Types - Barrel Export
 *
 * Exports all type definitions for the search feature.
 */

// Re-export all types from search.types
export type {
  // Core Types
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchListResponse,

  // Search Filters
  SearchFilters,
  SortOption,

  // Search Execution
  SearchExecuteRequest,
  SearchExecuteResponse,
  SearchResult,
  EntityType,
  Entity,

  // Scheduled Searches
  ScheduledSearch,
  ScheduleFrequency,
  ScheduleConfig,
  ScheduledSearchListResponse,

  // Search Alerts
  SearchAlertConfig,
  AlertChannelType,
  SearchAlertHistoryEntry,
  SearchAlertHistoryResponse,

  // Search Suggestions
  SearchSuggestion,
  SearchSuggestionsResponse,
} from './search.types';

// Re-export from legacy savedSearch types for backward compatibility
export type {
  SavedSearchFilters,
  RunSavedSearchResponse,
} from './savedSearch';
