/**
 * Search UI Feature - Main Export
 *
 * Public search interface for article discovery.
 *
 * @example
 * ```tsx
 * import { useArticleSearch, SearchInput } from '@/features/search-ui';
 *
 * const { data } = useArticleSearch({ query: 'tesla', page: 1 });
 * ```
 */

// Components
export * from './components';

// Hooks
export * from './hooks';

// Types
export * from './types';

// Re-export commonly used items for convenience
export type { SearchRequest, SearchResponse, SearchFilters } from './types';
export { useArticleSearch, useSuggestions } from './hooks';
