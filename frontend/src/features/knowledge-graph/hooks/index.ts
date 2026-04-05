/**
 * Knowledge Graph Hooks
 *
 * Custom React Query hooks for knowledge graph data fetching and state management.
 *
 * ## Entity Hooks (Legacy - REST API based):
 * - `useEntityConnections` - Fetch entity graph with nodes and edges
 * - `useEntitySearch` - Search entities with debounced input
 * - `useFindPath` - Find shortest paths between entities
 * - `useArticleEntities` - Get entities from specific article
 * - `useTopEntities` - Get trending/top entities (admin API)
 *
 * ## Market & Quality Hooks (MCP-based):
 * See `@/features/knowledge-graph/api` for:
 * - `useMarketNodes` - Query market nodes with filters
 * - `useMarketDetails` - Get single market node details
 * - `useMarketHistory` - Get historical data for market
 * - `useMarketStats` - Get aggregate market statistics
 * - `useGraphIntegrity` - Get graph health metrics
 * - `useDisambiguationQuality` - Get disambiguation metrics
 *
 * ## Usage Examples:
 *
 * ```tsx
 * // Entity connections for graph visualization
 * const { data, isLoading } = useEntityConnections('Tesla', {
 *   relationshipType: 'WORKS_FOR',
 *   limit: 50
 * })
 *
 * // Debounced entity search
 * const [query, setQuery] = useState('')
 * const { data: results } = useEntitySearch(query, {
 *   limit: 10,
 *   debounceMs: 300
 * })
 *
 * // Pathfinding between entities
 * const { data: paths } = useFindPath('Elon Musk', 'Tesla', {
 *   maxDepth: 3,
 *   minConfidence: 0.7
 * })
 *
 * // Article entities
 * const { data: entities } = useArticleEntities(articleId, {
 *   entityType: 'PERSON'
 * })
 *
 * // Trending entities
 * const { data: trending } = useTopEntities({
 *   limit: 10,
 *   refetchInterval: 5 * 60 * 1000 // Auto-refresh
 * })
 * ```
 *
 * ## Features:
 * - TypeScript support with full type inference
 * - Automatic caching and deduplication
 * - Error handling via React Query
 * - Loading states
 * - Stale-while-revalidate pattern
 * - Optional auto-refresh
 * - Query key management
 *
 * @module features/knowledge-graph/hooks
 */

export { useEntityConnections } from './useEntityConnections';
export type { UseEntityConnectionsOptions } from './useEntityConnections';

export { useEntitySearch } from './useEntitySearch';
export type { UseEntitySearchOptions } from './useEntitySearch';

export { useFindPath } from './useFindPath';
export type { UseFindPathOptions } from './useFindPath';

export { useArticleEntities } from './useArticleEntities';
export type { UseArticleEntitiesOptions } from './useArticleEntities';

export { useTopEntities } from './useTopEntities';
export type { UseTopEntitiesOptions } from './useTopEntities';
