/**
 * Search Feature API - Barrel Export
 *
 * Exports all API hooks for the search feature.
 */

// Saved Searches - List and CRUD
export {
  useSavedSearches,
  useCreateSavedSearch,
  useUpdateSavedSearch,
  useDeleteSavedSearch,
  useRunSavedSearch,
  savedSearchKeys,
} from './useSavedSearches';

// Single Saved Search
export {
  useSavedSearch,
  useSavedSearchWithHistory,
} from './useSavedSearch';

// Save Search Mutations
export {
  useSaveSearch,
  useUpdateSavedSearch as useUpdateSearch,
  useDeleteSavedSearch as useRemoveSavedSearch,
  useToggleSearchSchedule,
  useToggleSearchAlert,
} from './useSaveSearch';

// Search Execution
export {
  useExecuteSavedSearch,
  useQuickSearch,
  useLiveSearch,
  useSearchSuggestions,
  searchExecutionKeys,
} from './useExecuteSavedSearch';

// Scheduled Searches
export {
  useScheduledSearches,
  useUpcomingScheduledSearches,
  useScheduleSearch,
  useUnscheduleSearch,
  useRunScheduledSearchNow,
  cronToConfig,
  configToCron,
  describeSchedule,
  scheduledSearchKeys,
} from './useScheduledSearches';

// Search Alerts
export {
  useSearchAlerts,
  useSearchAlertConfig,
  useSearchAlertHistory,
  useConfigureSearchAlert,
  useToggleSearchAlert as useToggleAlert,
  useTestSearchAlert,
  useAcknowledgeAlert,
  searchAlertKeys,
} from './useSearchAlerts';
