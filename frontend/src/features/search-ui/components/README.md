# Search UI Components

Complete set of search interface components for the News Microservices application.

## Overview

All components are production-ready and fully typed with TypeScript. They follow the existing design patterns from the admin pages and use Shadcn UI components.

## Components

### Search Bar Components

#### SearchInput
- **Location:** `search-bar/SearchInput.tsx`
- **Purpose:** Search input with autocomplete suggestions
- **Features:**
  - Real-time autocomplete from Search API
  - Keyboard navigation (Arrow keys, Enter, Escape)
  - Debounced API calls (2s stale time)
  - Clear button
  - Loading indicator
  - Click outside to close suggestions

**Usage:**
```tsx
import { SearchInput } from '@/features/search-ui/components'

<SearchInput
  value={query}
  onChange={setQuery}
  onSearch={handleSearch}
  placeholder="Search articles..."
  showSuggestions={true}
/>
```

#### SearchFilters
- **Location:** `search-bar/SearchFilters.tsx`
- **Purpose:** Filter sidebar for advanced search refinement
- **Features:**
  - Date range picker (from/to with validation)
  - Sentiment filter (positive/neutral/negative)
  - Source filter (placeholder - will be populated in Day 5)
  - Entity filter (disabled - future feature)
  - Active filter count badge
  - Clear all filters button
  - Collapsible mode support

**Usage:**
```tsx
import { SearchFilters, getActiveFilterCount } from '@/features/search-ui/components'

const activeCount = getActiveFilterCount(filters)

<SearchFilters
  filters={filters}
  onFiltersChange={setFilters}
  activeFilterCount={activeCount}
  collapsible={false}
  defaultOpen={true}
/>
```

### Results Components

#### SearchResults
- **Location:** `results/SearchResults.tsx`
- **Purpose:** Container for search results with state management
- **Features:**
  - Loading state with skeleton loaders
  - Empty state with search query display
  - Error state with alert message
  - Result count display
  - Execution time display
  - Grid/List view toggle
  - Responsive layout

**Usage:**
```tsx
import { SearchResults, ArticleCard } from '@/features/search-ui/components'

<SearchResults
  results={results}
  isLoading={isLoading}
  error={error}
  totalResults={total}
  query={query}
  executionTime={42}
  viewMode="list"
>
  {results.map(article => (
    <ArticleCard key={article.article_id} article={article} />
  ))}
</SearchResults>
```

#### ArticleCard
- **Location:** `results/ArticleCard.tsx`
- **Purpose:** Display single search result
- **Features:**
  - Title with highlight support (Phase 1 Day 5)
  - Content preview (truncated to 200 chars)
  - Metadata display (source, author, date)
  - Sentiment badge with color coding
  - Relevance score indicator
  - Entity tags (max 5 visible)
  - Click to open article in new tab
  - Hover effects and focus states
  - Keyboard navigation (Enter/Space)
  - Compact variant available

**Usage:**
```tsx
import { ArticleCard } from '@/features/search-ui/components'

<ArticleCard
  article={result}
  onClick={(article) => console.log('Clicked:', article)}
  showFullContent={false}
/>
```

#### SearchPagination
- **Location:** `results/SearchPagination.tsx`
- **Purpose:** Pagination controls for result navigation
- **Features:**
  - Page number buttons (smart range calculation)
  - Previous/Next navigation
  - First/Last page buttons
  - Jump to page input
  - Results per page selector (20/50/100)
  - Result range display
  - Mobile-optimized simplified view
  - Loading state support
  - Compact variant available

**Usage:**
```tsx
import { SearchPagination } from '@/features/search-ui/components'

<SearchPagination
  currentPage={page}
  totalPages={Math.ceil(total / pageSize)}
  pageSize={pageSize}
  totalResults={total}
  onPageChange={setPage}
  onPageSizeChange={setPageSize}
  isLoading={isLoading}
/>
```

## Component States

### Loading States
All components handle loading states gracefully:
- **SearchInput:** Spinner next to search button
- **SearchResults:** Skeleton loaders (6 items)
- **ArticleCard:** Part of SearchResults skeleton
- **SearchPagination:** Disabled controls

### Empty States
- **SearchResults:** Shows search icon + message
- **SearchPagination:** Hidden when no results

### Error States
- **SearchResults:** Red alert with error message
- **SearchFilters:** Individual field validation

## Styling

All components use:
- Tailwind CSS for styling
- Shadcn UI component variants
- Responsive breakpoints (sm/md/lg)
- Dark mode support (via CSS variables)
- Consistent spacing (gap-2/4/6)

## Accessibility

All components are accessible:
- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus visible indicators
- Screen reader friendly

## Future Enhancements (Phase 1 Day 5)

1. **SearchInput:** Add search history dropdown
2. **SearchFilters:** Populate sources from API
3. **ArticleCard:** Implement search term highlighting
4. **SearchResults:** Add sorting options
5. **Facets:** Create faceted search components

## Testing

See `test/TestSearchInput.tsx` for component usage examples.

## Dependencies

- React 18+
- @tanstack/react-query (for API calls)
- date-fns (for date formatting)
- lucide-react (for icons)
- Shadcn UI components

## File Structure

```
components/
├── index.ts                      # Barrel export
├── README.md                     # This file
├── search-bar/
│   ├── SearchInput.tsx          # Search input with autocomplete
│   ├── SearchFilters.tsx        # Filter sidebar
│   ├── SearchSuggestions.tsx    # Suggestion dropdown (unused)
│   └── index.ts                 # Barrel export
├── results/
│   ├── SearchResults.tsx        # Results container
│   ├── ArticleCard.tsx          # Single result card
│   ├── SearchPagination.tsx     # Pagination controls
│   └── index.ts                 # Barrel export
└── facets/
    └── index.ts                 # Placeholder for future facets
```

## Integration Example

Complete search page integration:

```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  SearchInput,
  SearchFilters,
  SearchResults,
  ArticleCard,
  SearchPagination,
  getActiveFilterCount,
} from '@/features/search-ui/components'
import { searchArticles } from '@/lib/api/searchPublic'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({})
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query, filters, page, pageSize],
    queryFn: () => searchArticles({ query, ...filters, page, page_size: pageSize }),
    enabled: query.length >= 2,
  })

  return (
    <div className="container mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <aside className="lg:col-span-1">
          <SearchFilters
            filters={filters}
            onFiltersChange={setFilters}
            activeFilterCount={getActiveFilterCount(filters)}
          />
        </aside>

        {/* Main Content */}
        <main className="lg:col-span-3 space-y-6">
          {/* Search Input */}
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={() => setPage(1)}
          />

          {/* Results */}
          <SearchResults
            results={data?.results || []}
            isLoading={isLoading}
            error={error}
            totalResults={data?.total || 0}
            query={query}
            executionTime={data?.execution_time_ms}
          >
            {data?.results.map(article => (
              <ArticleCard key={article.article_id} article={article} />
            ))}
          </SearchResults>

          {/* Pagination */}
          <SearchPagination
            currentPage={page}
            totalPages={Math.ceil((data?.total || 0) / pageSize)}
            pageSize={pageSize}
            totalResults={data?.total || 0}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        </main>
      </div>
    </div>
  )
}
```

---

**Status:** ✅ Complete (Phase 1 Day 4)  
**Next:** Integrate into main search page (Phase 1 Day 5)
