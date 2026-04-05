/**
 * Search Service Feature Module
 *
 * Exports all hooks, components, pages, and types for the Search Service integration.
 *
 * @example
 * ```tsx
 * // Import hooks
 * import {
 *   useSavedSearches,
 *   useSavedSearch,
 *   useExecuteSavedSearch,
 *   useScheduledSearches,
 *   useSearchAlerts
 * } from '@/features/search';
 *
 * // Import components
 * import {
 *   SearchDashboard,
 *   SavedSearchesSidebar,
 *   SearchResultCard,
 *   SearchFiltersPanel
 * } from '@/features/search';
 *
 * // Import pages
 * import { SearchPage, SavedSearchesPage, SearchAlertsPage } from '@/features/search';
 * ```
 */

// =============================================================================
// Admin Hooks (Search Service Statistics)
// =============================================================================
export {
  useCacheStats,
  useIndexStats,
  useQueryStats,
  usePerformanceStats,
} from './hooks';

// =============================================================================
// Saved Searches API
// =============================================================================
export {
  // Legacy hooks (backward compatibility)
  useSavedSearches,
  useCreateSavedSearch,
  useUpdateSavedSearch,
  useDeleteSavedSearch,
  useRunSavedSearch,
  savedSearchKeys,

  // Single saved search
  useSavedSearch,
  useSavedSearchWithHistory,

  // Enhanced mutations
  useSaveSearch,
  useUpdateSearch,
  useRemoveSavedSearch,
  useToggleSearchSchedule,
  useToggleSearchAlert,

  // Search execution
  useExecuteSavedSearch,
  useQuickSearch,
  useLiveSearch,
  useSearchSuggestions,
  searchExecutionKeys,

  // Scheduled searches
  useScheduledSearches,
  useUpcomingScheduledSearches,
  useScheduleSearch,
  useUnscheduleSearch,
  useRunScheduledSearchNow,
  cronToConfig,
  configToCron,
  describeSchedule,
  scheduledSearchKeys,

  // Search alerts
  useSearchAlerts,
  useSearchAlertConfig,
  useSearchAlertHistory,
  useConfigureSearchAlert,
  useToggleAlert,
  useTestSearchAlert,
  useAcknowledgeAlert,
  searchAlertKeys,
} from './api';

// =============================================================================
// Components
// =============================================================================
export {
  // Admin/Dashboard
  CacheStatsCard,
  SearchDashboard,

  // Legacy (backward compatibility)
  SaveSearchDialog,
  SavedSearchCard,
  SavedSearchesList,

  // Enhanced saved searches
  SavedSearchesSidebar,
  EnhancedSaveSearchDialog,

  // Search filters
  SearchFiltersPanel,

  // Scheduled searches
  ScheduledSearchesPanel,

  // Alerts
  SearchAlertConfigPanel,

  // Search results
  SearchResultCard,
  SearchResultListItem,
} from './components';

// =============================================================================
// Pages
// =============================================================================
export {
  SearchPage,
  SavedSearchesPage,
  SearchAlertsPage,
} from './pages';

// =============================================================================
// Types - Admin Statistics (from shared types)
// =============================================================================
export type {
  CacheStatistics,
  IndexStatistics,
  QueryStatistics,
  PerformanceStatistics,
} from '@/types/search';

// =============================================================================
// Types - Search Feature
// =============================================================================
export type {
  // Core Types
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchListResponse,

  // Legacy types (backward compatibility)
  SavedSearchFilters,
  RunSavedSearchResponse,

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
} from './types';
