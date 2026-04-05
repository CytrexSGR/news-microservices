/**
 * Search UI Components - Barrel Export
 *
 * All public-facing search components.
 *
 * @example
 * ```tsx
 * import { SearchInput, SearchFilters, SearchResults, ArticleCard } from '@/features/search-ui/components';
 * ```
 */

// Search Bar Components
export { SearchInput } from './search-bar'
export { SearchSuggestions } from './search-bar'
export { SearchFilters, getActiveFilterCount } from './search-bar'

// Result Components
export { SearchResults } from './results'
export { ArticleCard, ArticleCardCompact } from './results'
export { SearchPagination, SearchPaginationCompact } from './results'

// Facet Components (from existing)
export * from './facets'
