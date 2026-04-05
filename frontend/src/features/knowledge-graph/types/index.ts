/**
 * Knowledge Graph Types
 *
 * TypeScript type definitions for entities, relationships, graph state, and API contracts.
 *
 * Key Types:
 * - Entity - Graph node representing a named entity
 * - Relationship - Graph edge representing entity relationship
 * - GraphNode - React Flow node format
 * - GraphEdge - React Flow edge format
 * - FilterState - Active filters state
 * - MarketNode - Market data integration types
 * - GraphIntegrity - Quality assessment types
 *
 * @module features/knowledge-graph/types
 */

// ===========================
// Market Types
// ===========================

export type {
  AssetType,
  MarketNode,
  MarketPriceData,
  MarketConnectedEntity,
  MarketRelatedArticle,
  MarketNodeDetails,
  MarketStats,
  MarketMostConnected,
  MarketHistoryEntry,
  MarketHistoryResponse,
  MarketNodesQueryParams,
  MarketHistoryQueryParams,
} from './market';

export { ASSET_TYPE_COLORS, ASSET_TYPE_ICONS } from './market';

// ===========================
// Quality Types
// ===========================

export type {
  IssueSeverity,
  IssueType,
  QualityIssue,
  GraphIntegrity,
  EntityTypeDisambiguationStats,
  DisambiguationQuality,
  DataFreshness,
  QualityTrendPoint,
  QualityTrends,
  QualityTrendsQueryParams,
} from './quality';

export {
  QUALITY_THRESHOLDS,
  getQualityLevel,
  QUALITY_LEVEL_COLORS,
  SEVERITY_COLORS,
  SEVERITY_ICONS,
} from './quality';
