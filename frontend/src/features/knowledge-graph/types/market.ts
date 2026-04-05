/**
 * Market Node Types for Knowledge Graph
 *
 * TypeScript type definitions for market data integration with the knowledge graph.
 * Supports stocks, crypto, forex, commodities, and indices.
 *
 * @module features/knowledge-graph/types/market
 */

// ===========================
// Market Node Types
// ===========================

/**
 * Asset type for market nodes
 */
export type AssetType = 'stock' | 'crypto' | 'forex' | 'commodity' | 'index';

/**
 * Market Node in the Knowledge Graph
 *
 * Represents a financial instrument (stock, crypto, etc.) as a node in the graph.
 */
export interface MarketNode {
  /** Trading symbol (e.g., "AAPL", "BTCUSD") */
  symbol: string;
  /** Full name of the instrument (e.g., "Apple Inc.") */
  name: string;
  /** Exchange where traded (e.g., "NASDAQ", "NYSE", "BINANCE") */
  exchange: string;
  /** Type of asset */
  asset_type: AssetType;
  /** Number of connections to other entities in the graph */
  connection_count: number;
  /** Last data update timestamp (ISO 8601) */
  last_updated: string;
}

/**
 * Price data for a market node
 */
export interface MarketPriceData {
  /** Current price */
  current: number;
  /** 24-hour price change (absolute) */
  change_24h: number;
  /** 24-hour price change (percentage) */
  change_percent: number;
}

/**
 * Connected entity summary for market details
 */
export interface MarketConnectedEntity {
  /** Entity name */
  name: string;
  /** Entity type (PERSON, ORGANIZATION, etc.) */
  type: string;
  /** Number of relationships with this market node */
  relationship_count: number;
  /** Average sentiment score for relationships (-1 to 1) */
  sentiment_avg: number;
}

/**
 * Related article summary for market details
 */
export interface MarketRelatedArticle {
  /** Article ID */
  id: string;
  /** Article title */
  title: string;
  /** Publication timestamp (ISO 8601) */
  published_at: string;
  /** Article sentiment score (-1 to 1) */
  sentiment: number;
}

/**
 * Detailed Market Node Information
 *
 * Extended market node data including price, connections, and articles.
 */
export interface MarketNodeDetails {
  /** Trading symbol */
  symbol: string;
  /** Full name */
  name: string;
  /** Exchange */
  exchange: string;
  /** Asset type */
  asset_type: string;
  /** Current price data */
  price_data: MarketPriceData;
  /** Connected entities with relationship info */
  connected_entities: MarketConnectedEntity[];
  /** Related news articles */
  related_articles: MarketRelatedArticle[];
}

/**
 * Market Statistics
 *
 * Aggregate statistics for market nodes in the knowledge graph.
 */
export interface MarketStats {
  /** Total number of market nodes in the graph */
  total_market_nodes: number;
  /** Count by asset type (e.g., { stock: 150, crypto: 50 }) */
  by_asset_type: Record<string, number>;
  /** Total connections between market nodes and entities */
  total_connections: number;
  /** Average connections per market node */
  avg_connections_per_market: number;
  /** Most connected market nodes */
  most_connected: MarketMostConnected[];
}

/**
 * Most connected market node entry
 */
export interface MarketMostConnected {
  /** Trading symbol */
  symbol: string;
  /** Connection count */
  connections: number;
}

/**
 * Market History Entry
 *
 * Historical data point for a market node.
 */
export interface MarketHistoryEntry {
  /** Timestamp (ISO 8601) */
  timestamp: string;
  /** Connection count at this point in time */
  connection_count: number;
  /** Number of related articles */
  article_count: number;
  /** Average sentiment */
  avg_sentiment: number;
}

/**
 * Market History Response
 */
export interface MarketHistoryResponse {
  /** Trading symbol */
  symbol: string;
  /** Historical data points */
  history: MarketHistoryEntry[];
  /** Time range start (ISO 8601) */
  start_date: string;
  /** Time range end (ISO 8601) */
  end_date: string;
}

// ===========================
// API Request Types
// ===========================

/**
 * Query parameters for listing market nodes
 */
export interface MarketNodesQueryParams {
  /** Filter by asset type */
  asset_type?: AssetType;
  /** Filter by exchange */
  exchange?: string;
  /** Search by symbol or name */
  search?: string;
  /** Minimum connection count */
  min_connections?: number;
  /** Sort field */
  sort_by?: 'symbol' | 'name' | 'connection_count' | 'last_updated';
  /** Sort direction */
  sort_order?: 'asc' | 'desc';
  /** Pagination limit */
  limit?: number;
  /** Pagination offset */
  offset?: number;
}

/**
 * Query parameters for market history
 */
export interface MarketHistoryQueryParams {
  /** Start date (ISO 8601) */
  start_date?: string;
  /** End date (ISO 8601) */
  end_date?: string;
  /** Granularity (hour, day, week) */
  granularity?: 'hour' | 'day' | 'week';
}

// ===========================
// Color Scheme Extensions
// ===========================

/**
 * Asset type color mapping for graph visualization
 */
export const ASSET_TYPE_COLORS: Record<AssetType | 'DEFAULT', string> = {
  stock: '#22C55E',      // Green-500 - Traditional stocks
  crypto: '#F59E0B',     // Amber-500 - Cryptocurrency
  forex: '#3B82F6',      // Blue-500 - Forex pairs
  commodity: '#A855F7',  // Purple-500 - Commodities
  index: '#EF4444',      // Red-500 - Market indices
  DEFAULT: '#6B7280',    // Gray-500 - Default
};

/**
 * Asset type icon mapping
 */
export const ASSET_TYPE_ICONS: Record<AssetType | 'DEFAULT', string> = {
  stock: '📈',
  crypto: '₿',
  forex: '💱',
  commodity: '🛢️',
  index: '📊',
  DEFAULT: '💹',
};
