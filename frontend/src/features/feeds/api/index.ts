export { useFeeds } from './useFeeds';
export { useFeed } from './useFeed';
export { useFeedHealth } from './useFeedHealth';
export { useAssessFeed } from './useAssessFeed';
export { useAssessmentHistory } from './useAssessmentHistory';
export { useArticleV2 } from './useArticleV2'; // Article data via feed-service
export { useFeedItems } from './useFeedItems';
export { useUpdateFeed } from './useUpdateFeed';

// Feed Creation
export { useCreateFeed } from './useCreateFeed';
export { usePreAssessFeed } from './usePreAssessFeed';

// Admiralty Code Configuration
export {
  useAdmiraltyThresholds,
  useAdmiraltyThreshold,
  useUpdateAdmiraltyThreshold,
  useResetAdmiraltyThresholds,
} from './useAdmiraltyThresholds';

export {
  useQualityWeights,
  useQualityWeight,
  useUpdateQualityWeight,
  useResetQualityWeights,
  useValidateWeights,
  useConfigurationStatus,
} from './useQualityWeights';

// Knowledge Graph Quality Monitoring
export {
  useGraphIntegrity,
  useRefreshGraphIntegrity,
  graphIntegrityQueryKey,
  type GraphIntegrityResult,
  type GraphIntegrityIssue,
} from './useGraphIntegrity';

export {
  useDisambiguationQuality,
  useRefreshDisambiguationQuality,
  disambiguationQualityQueryKey,
  getDisambiguationStatus,
  type DisambiguationQualityResult,
  type DisambiguationTypeMetrics,
} from './useDisambiguationQuality';
