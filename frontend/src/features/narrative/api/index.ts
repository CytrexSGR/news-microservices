/**
 * Narrative Feature API Export
 *
 * This module exports all narrative-related API functions and types.
 *
 * @module features/narrative/api
 *
 * @example
 * ```typescript
 * import {
 *   getNarrativeOverview,
 *   listFrames,
 *   analyzeText,
 *   useTextAnalysis,
 *   type NarrativeOverview,
 *   type TextAnalysisResult
 * } from '@/features/narrative/api';
 *
 * // Get overview
 * const { data: overview } = await getNarrativeOverview({ days: 7 });
 *
 * // Analyze text with hook
 * const { mutate, data } = useTextAnalysis();
 * mutate({ text: 'News article content...', source: 'reuters' });
 * ```
 */

// API Functions
export {
  getNarrativeOverview,
  listFrames,
  createFrame,
  listClusters,
  updateClusters,
  getBiasComparison,
  analyzeText,
  getCacheStats,
  clearCache,
  narrativeEndpoints,
  type ApiResponse,
} from './narrativeApi';

// React Query Hooks
export { useTextAnalysis } from './useTextAnalysis';

// Types re-export for convenience
export type {
  // Core Types
  FrameType,
  BiasLabel,
  Perspective,
  NarrativeFrame,
  FrameEntities,
  NarrativeCluster,
  BiasAnalysis,
  LanguageIndicators,
  TopNarrative,

  // Request DTOs
  NarrativeFrameCreate,
  TextAnalyzerOptions,
  TextAnalyzerInput,

  // Query Parameters
  FramesListParams,
  ClustersListParams,
  BiasComparisonParams,
  OverviewParams,

  // Response DTOs
  NarrativeOverview,
  FramesListResponse,
  BiasComparisonResponse,
  ClusterUpdateResponse,
  DetectedFrame,
  BiasResult,
  TextAnalysisResult,
  CacheStatsResponse,
  CacheClearResponse,
} from '../types';
