/**
 * SearchPage Component
 *
 * Main search interface with saved searches sidebar,
 * search input, filters, and results display.
 */

import * as React from 'react';
import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  Grid,
  List,
  Loader2,
  RefreshCw,
  X,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { SavedSearchesSidebar } from '../components/SavedSearchesSidebar';
import { SearchFiltersPanel } from '../components/SearchFiltersPanel';
import { SearchResultCard, SearchResultListItem } from '../components/SearchResultCard';
import { EnhancedSaveSearchDialog } from '../components/EnhancedSaveSearchDialog';
import { useLiveSearch, useSearchSuggestions } from '../api/useExecuteSavedSearch';
import type { SearchFilters, SavedSearch, SearchResult } from '../types/search.types';

type ViewMode = 'grid' | 'list';

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [page, setPage] = useState(1);
  const [selectedSearchId, setSelectedSearchId] = useState<string | undefined>();
  const [showFilters, setShowFilters] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Debounce query
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
      if (query) {
        setSearchParams({ q: query });
      } else {
        setSearchParams({});
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query, setSearchParams]);

  // Live search query
  const {
    data: searchResults,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useLiveSearch(
    {
      query: debouncedQuery,
      filters,
      page,
      page_size: 20,
    },
    debouncedQuery.length >= 2
  );

  // Suggestions
  const { data: suggestions } = useSearchSuggestions(query);

  // Count active filters
  const activeFilterCount = Object.values(filters).filter(
    (v) => v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0 : true)
  ).length;

  // Handle saved search selection
  const handleSavedSearchSelect = useCallback((search: SavedSearch) => {
    setSelectedSearchId(search.id);
    setQuery(search.query || '');
    setFilters(search.filters || {});
    setPage(1);
  }, []);

  // Handle filter change
  const handleFilterChange = useCallback((newFilters: SearchFilters) => {
    setFilters(newFilters);
    setPage(1);
  }, []);

  // Clear search
  const handleClearSearch = useCallback(() => {
    setQuery('');
    setDebouncedQuery('');
    setFilters({});
    setSelectedSearchId(undefined);
    setPage(1);
    setSearchParams({});
  }, [setSearchParams]);

  // Handle result click
  const handleResultClick = useCallback((result: SearchResult) => {
    if (result.url) {
      window.open(result.url, '_blank');
    }
  }, []);

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <SavedSearchesSidebar
        selectedId={selectedSearchId}
        onSelect={handleSavedSearchSelect}
        onCreate={() => setShowSaveDialog(true)}
        className="hidden lg:flex"
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Search Header */}
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container py-4 space-y-4">
            {/* Search Bar */}
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search articles..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-10 pr-10"
                />
                {query && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                    onClick={handleClearSearch}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>

              {/* Filters Toggle */}
              <Sheet open={showFilters} onOpenChange={setShowFilters}>
                <SheetTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <SlidersHorizontal className="h-4 w-4" />
                    Filters
                    {activeFilterCount > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {activeFilterCount}
                      </Badge>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-80">
                  <SheetHeader>
                    <SheetTitle>Search Filters</SheetTitle>
                    <SheetDescription>
                      Refine your search results
                    </SheetDescription>
                  </SheetHeader>
                  <div className="mt-6">
                    <SearchFiltersPanel
                      filters={filters}
                      onChange={handleFilterChange}
                    />
                  </div>
                </SheetContent>
              </Sheet>

              {/* Save Search */}
              <EnhancedSaveSearchDialog
                query={query}
                filters={filters}
                open={showSaveDialog}
                onOpenChange={setShowSaveDialog}
                onSaved={(id) => setSelectedSearchId(id)}
              />

              {/* View Toggle */}
              <div className="hidden sm:flex items-center border rounded-lg">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="icon"
                  onClick={() => setViewMode('grid')}
                  className="rounded-r-none"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="icon"
                  onClick={() => setViewMode('list')}
                  className="rounded-l-none"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Search Suggestions */}
            {suggestions && query.length >= 2 && query.length < 5 && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Try:</span>
                {suggestions.queries.slice(0, 3).map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuery(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            )}

            {/* Active Filters Preview */}
            {activeFilterCount > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-muted-foreground">Active filters:</span>
                {filters.sentiment && filters.sentiment !== 'all' && (
                  <Badge variant="secondary">
                    Sentiment: {filters.sentiment}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-1 p-0"
                      onClick={() =>
                        handleFilterChange({ ...filters, sentiment: undefined })
                      }
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {filters.date_from && (
                  <Badge variant="secondary">
                    From: {filters.date_from}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-1 p-0"
                      onClick={() =>
                        handleFilterChange({ ...filters, date_from: undefined })
                      }
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {filters.categories?.map((cat) => (
                  <Badge key={cat} variant="secondary">
                    {cat}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-1 p-0"
                      onClick={() =>
                        handleFilterChange({
                          ...filters,
                          categories: filters.categories?.filter((c) => c !== cat),
                        })
                      }
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFilterChange({})}
                >
                  Clear all
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-auto">
          <div className="container py-6">
            {/* Initial State */}
            {!debouncedQuery && activeFilterCount === 0 && (
              <div className="text-center py-16">
                <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Search Articles</h2>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Enter a search query or select a saved search from the sidebar
                  to find articles.
                </p>
              </div>
            )}

            {/* Loading */}
            {isLoading && (
              <div className={cn(
                'gap-4',
                viewMode === 'grid'
                  ? 'grid md:grid-cols-2 lg:grid-cols-3'
                  : 'space-y-2'
              )}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className={viewMode === 'grid' ? 'h-64' : 'h-24'} />
                ))}
              </div>
            )}

            {/* Error */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Search Failed</AlertTitle>
                <AlertDescription className="flex items-center justify-between">
                  <span>{error.message}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => refetch()}
                    disabled={isRefetching}
                  >
                    <RefreshCw className={cn('h-4 w-4 mr-2', isRefetching && 'animate-spin')} />
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {/* Results */}
            {searchResults && !isLoading && (
              <div className="space-y-4">
                {/* Results Header */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Found <strong>{searchResults.total.toLocaleString()}</strong> results
                    in {searchResults.execution_time_ms}ms
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => refetch()}
                    disabled={isRefetching}
                  >
                    <RefreshCw className={cn('h-4 w-4 mr-2', isRefetching && 'animate-spin')} />
                    Refresh
                  </Button>
                </div>

                {/* Results Grid/List */}
                {searchResults.results.length > 0 ? (
                  viewMode === 'grid' ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {searchResults.results.map((result) => (
                        <SearchResultCard
                          key={result.id}
                          result={result}
                          onClick={handleResultClick}
                          highlightTerms={debouncedQuery.split(' ').filter(Boolean)}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2 divide-y">
                      {searchResults.results.map((result) => (
                        <SearchResultListItem
                          key={result.id}
                          result={result}
                          onClick={handleResultClick}
                          highlightTerms={debouncedQuery.split(' ').filter(Boolean)}
                        />
                      ))}
                    </div>
                  )
                ) : (
                  <div className="text-center py-12">
                    <Search className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">
                      No results found for your search
                    </p>
                  </div>
                )}

                {/* Pagination */}
                {searchResults.total > searchResults.page_size && (
                  <div className="flex items-center justify-center gap-2 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground px-4">
                      Page {page} of {Math.ceil(searchResults.total / searchResults.page_size)}
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page * searchResults.page_size >= searchResults.total}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
