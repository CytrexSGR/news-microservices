/**
 * Narrative Analysis API Hooks
 *
 * Re-exports all API hooks for narrative analysis functionality.
 */

// ==================== Analysis Mutations ====================

// Original analysis mutation
export { useAnalyzeNarrative, NARRATIVE_ANALYSIS_COST_USD } from './useAnalyzeNarrative';

// Real-time text analysis mutation (NEW)
export {
  useAnalyzeTextNarrative,
  REALTIME_ANALYSIS_COST_USD,
  type AnalyzeTextNarrativeParams,
} from './useAnalyzeTextNarrative';

// ==================== Intelligence Server Query Hooks ====================

// Enhanced with full MCP parameters
export {
  useNarrativeFrames,
  useNarrativeFrame,
  type NarrativeFramesParams,
} from './useNarrativeFrames';

export {
  useBiasAnalysis,
  useBiasStats,
  type BiasAnalysisParams,
} from './useBiasAnalysis';

export {
  useNarrativeOverview,
  useFrameDistribution,
  useNarrativeCosts,
  type NarrativeOverviewParams,
} from './useNarrativeOverview';

export {
  useNarrativeClusters,
  useNarrativeCluster,
  useClusterStats,
  type NarrativeClustersParams,
} from './useNarrativeClusters';

// ==================== Knowledge Graph Narrative Hooks (NEW) ====================

// Re-export all KG hooks
export * from './kg';
