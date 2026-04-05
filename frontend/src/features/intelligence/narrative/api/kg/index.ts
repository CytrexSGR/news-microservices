/**
 * Knowledge Graph Narrative API Hooks
 *
 * Hooks for accessing narrative frame data stored in the Knowledge Graph (Neo4j).
 * These provide entity-centric views of narrative analysis data.
 */

// Entity-specific frame hooks
export {
  useKGNarrativeFrames,
  useEntityNarrativeFrames,
} from './useKGNarrativeFrames';

// Frame distribution hooks
export {
  useFrameDistribution,
  useRecentFrameDistribution,
  type FrameDistributionParams,
} from './useFrameDistribution';

// Entity framing analysis hooks
export {
  useEntityFramingAnalysis,
  useEntityFramingByName,
  type EntityFramingParams,
} from './useEntityFramingAnalysis';

// Co-occurrence hooks
export {
  useNarrativeCooccurrence,
  useEntityCooccurrences,
  useHighAffinityPairs,
} from './useNarrativeCooccurrence';

// High tension narrative hooks
export {
  useHighTensionNarratives,
  useCriticalTensionNarratives,
  useEntityTensionNarratives,
  useTensionAlerts,
} from './useHighTensionNarratives';

// Narrative statistics hooks
export {
  useNarrativeStats,
  useRecentNarrativeStats,
  useTodayNarrativeStats,
  type NarrativeStatsParams,
} from './useNarrativeStats';

// Top entities hooks
export {
  useTopNarrativeEntities,
  useTopEntitiesByFrame,
  useMostControversialEntities,
  useTopEntitiesByType,
  type TopNarrativeEntitiesParams,
} from './useTopNarrativeEntities';
