import { useState } from 'react'
import { Link } from 'react-router-dom'
import { SearchInput } from '@/features/search-ui/components/search-bar/SearchInput'
import { SearchFilters, getActiveFilterCount } from '@/features/search-ui/components/search-bar/SearchFilters'
import { SearchResults, SearchPagination, ArticleCard } from '@/features/search-ui/components/results'
import { useSearch, useSearchParams, useFacets } from '@/features/search-ui/hooks'
import { SaveSearchDialog } from '@/features/search/components'
import { Button } from '@/components/ui/Button'
import { Filter, Bookmark } from 'lucide-react'

/**
 * SearchPage - Public search interface for articles
 *
 * Location: /search
 * Access: Public (no authentication required)
 *
 * Features:
 * - Full-text search with autocomplete
 * - Advanced filters (date range, source, sentiment)
 * - Search result previews with highlights
 * - URL state management (shareable links)
 * - Responsive layout with collapsible filters
 * - Pagination and page size selection
 *
 * @returns {JSX.Element} Public search page
 */
export function SearchPage() {
  const {
    query,
    filters,
    page,
    pageSize,
    setQuery,
    setFilters,
    setPage,
    setPageSize,
    getSearchParams,
  } = useSearchParams()

  // Mobile filter panel state
  const [showFilters, setShowFilters] = useState(false)

  // Get search params for API call
  const searchParams = getSearchParams()

  // Execute search
  const { data, isLoading, error } = useSearch(searchParams)

  // Load available facets (sources and categories)
  const { data: facets } = useFacets()

  // Calculate active filter count
  const activeFilterCount = getActiveFilterCount(filters)

  // Handle search execution
  const handleSearch = (newQuery: string) => {
    setQuery(newQuery)
    setPage(1) // Reset to page 1 on new search
  }

  // Handle filter changes (partial updates)
  const handleFiltersChange = (changedFilters: Partial<typeof filters>) => {
    setFilters(changedFilters)
    setPage(1) // Reset to page 1 when filters change
  }

  // Calculate total pages
  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Search Articles</h1>
          <p className="text-muted-foreground">
            {data?.total
              ? `${data.total.toLocaleString()} ${data.total === 1 ? 'result' : 'results'} found`
              : 'Search our comprehensive article database'}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <SaveSearchDialog
            query={query}
            filters={filters}
          />
          <Button variant="outline" size="sm" asChild>
            <Link to="/search/saved" className="gap-2">
              <Bookmark className="h-4 w-4" />
              Saved Searches
            </Link>
          </Button>
        </div>
      </div>

      {/* Search Input */}
      <SearchInput
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        showSuggestions={true}
        placeholder="Search articles by title, content, or keywords..."
      />

      {/* Mobile Filter Toggle */}
      <div className="md:hidden">
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="w-full gap-2"
        >
          <Filter className="h-4 w-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
          {activeFilterCount > 0 && (
            <span className="ml-auto bg-primary text-primary-foreground rounded-full px-2 py-0.5 text-xs">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <aside className={`md:col-span-1 ${showFilters ? 'block' : 'hidden md:block'}`}>
          <SearchFilters
            filters={filters}
            onFiltersChange={handleFiltersChange}
            activeFilterCount={activeFilterCount}
            availableSources={facets?.sources || []}
            availableCategories={facets?.categories || []}
            collapsed={false}
          />
        </aside>

        {/* Results Area */}
        <main className="md:col-span-3 space-y-4">
          <SearchResults
            results={data?.results || []}
            isLoading={isLoading}
            error={error || null}
            totalResults={data?.total || 0}
            query={query}
            executionTime={data?.execution_time_ms}
          >
            {/* Render ArticleCard for each result */}
            {data?.results.map((article) => (
              <ArticleCard
                key={article.article_id}
                article={article}
                onClick={(article) => {
                  // Open article URL in new tab
                  if (article.url) {
                    window.open(article.url, '_blank', 'noopener,noreferrer')
                  }
                }}
              />
            ))}
          </SearchResults>

          {/* Pagination */}
          {data && data.total > 0 && (
            <SearchPagination
              currentPage={page}
              totalPages={totalPages}
              pageSize={pageSize}
              totalResults={data.total}
              onPageChange={setPage}
              onPageSizeChange={(newPageSize) => {
                setPageSize(newPageSize)
                setPage(1) // Reset to page 1 when page size changes
              }}
              isLoading={isLoading}
            />
          )}
        </main>
      </div>
    </div>
  )
}
