/**
 * Source Management Hooks
 *
 * Re-export all source-related hooks for easy importing.
 */

export { useSources, sourceQueryKeys } from './useSources'
export type { UseSourcesOptions } from './useSources'

export { useSource, useSourceByDomain } from './useSource'
export type { UseSourceOptions } from './useSource'

export { useCreateSource } from './useCreateSource'
export type { UseCreateSourceOptions } from './useCreateSource'

export { useUpdateSource } from './useUpdateSource'
export type { UseUpdateSourceOptions, UpdateSourceParams } from './useUpdateSource'

export { useDeleteSource } from './useDeleteSource'
export type { UseDeleteSourceOptions } from './useDeleteSource'

export { useSourceFeeds, useAddSourceFeed, useRemoveSourceFeed } from './useSourceFeeds'
export type {
  UseSourceFeedsOptions,
  AddFeedParams,
  UseAddSourceFeedOptions,
  RemoveFeedParams,
  UseRemoveSourceFeedOptions,
} from './useSourceFeeds'

export {
  useSourceAssessmentHistory,
  useTriggerSourceAssessment,
} from './useSourceAssessment'
export type {
  UseSourceAssessmentHistoryOptions,
  UseTriggerSourceAssessmentOptions,
} from './useSourceAssessment'
