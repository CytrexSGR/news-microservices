/**
 * Knowledge Graph API Hooks
 *
 * MCP-based React Query hooks for knowledge graph data fetching.
 *
 * ## Market Data Hooks:
 * - `useMarketNodes` - Query market nodes with filters
 * - `useMarketDetails` - Get single market node details
 * - `useMarketHistory` - Get historical data for market
 * - `useMarketStats` - Get aggregate market statistics
 *
 * ## Quality Hooks:
 * - `useGraphIntegrity` - Get graph health metrics
 * - `useDisambiguationQuality` - Get disambiguation metrics
 *
 * @module features/knowledge-graph/api
 */

// ===========================
// Market Data Hooks
// ===========================

export {
  useMarketNodes,
  useMarketNodesByType,
  useMarketSearch,
  marketNodesKeys,
} from './useMarketNodes';
export type { UseMarketNodesOptions } from './useMarketNodes';

export {
  useMarketDetails,
  prefetchMarketDetails,
  marketDetailsKeys,
} from './useMarketDetails';
export type { UseMarketDetailsOptions } from './useMarketDetails';

export {
  useMarketHistory,
  useMarketWeeklyHistory,
  useMarketDailyHistory,
  marketHistoryKeys,
} from './useMarketHistory';
export type { UseMarketHistoryOptions } from './useMarketHistory';

export {
  useMarketStats,
  useAssetTypeDistribution,
  useTopConnectedMarkets,
  marketStatsKeys,
} from './useMarketStats';
export type { UseMarketStatsOptions } from './useMarketStats';

// ===========================
// Quality Hooks
// ===========================

export {
  useGraphIntegrity,
  useQualityScore,
  useCriticalIssues,
  useIntegritySummary,
  graphIntegrityKeys,
} from './useGraphIntegrity';
export type { UseGraphIntegrityOptions } from './useGraphIntegrity';

export {
  useDisambiguationQuality,
  useDisambiguationRate,
  useAmbiguousEntities,
  useDisambiguationByType,
  useDisambiguationSummary,
  disambiguationQualityKeys,
} from './useDisambiguationQuality';
export type { UseDisambiguationQualityOptions } from './useDisambiguationQuality';
