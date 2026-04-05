/**
 * Search Results Container Component
 *
 * Container for displaying search results with:
 * - Loading states
 * - Empty states
 * - Error states
 * - Result count display
 * - Grid/List layout
 */

import * as React from 'react'
import { AlertCircle, Search, Grid3x3, List } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/utils'
import type { SearchResultItem } from '../../types/search.types'

interface SearchResultsProps {
  /** Search results array */
  results: SearchResultItem[]
  /** Loading state */
  isLoading?: boolean
  /** Error state */
  error?: Error | null
  /** Total number of results */
  totalResults?: number
  /** Current search query */
  query?: string
  /** Execution time in milliseconds */
  executionTime?: number
  /** View mode: grid or list */
  viewMode?: 'grid' | 'list'
  /** Callback to change view mode */
  onViewModeChange?: (mode: 'grid' | 'list') => void
  /** Custom class name */
  className?: string
  /** Children (ArticleCard components) */
  children?: React.ReactNode
}

/**
 * Loading skeleton for search results
 */
function SearchResultsSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <Skeleton className="mb-2 h-6 w-3/4" />
          <Skeleton className="mb-4 h-4 w-full" />
          <Skeleton className="mb-2 h-4 w-full" />
          <Skeleton className="mb-4 h-4 w-2/3" />
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-5 w-16" />
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Empty state for no results
 */
function EmptyState({ query }: { query?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-muted p-6 mb-4">
        <Search className="h-12 w-12 text-muted-foreground" />
      </div>
      <h3 className="text-xl font-semibold mb-2">No results found</h3>
      {query ? (
        <p className="text-muted-foreground max-w-md">
          No articles found matching <span className="font-medium">"{query}"</span>.
          Try adjusting your search terms or filters.
        </p>
      ) : (
        <p className="text-muted-foreground max-w-md">
          Start by entering a search query to find articles.
        </p>
      )}
    </div>
  )
}

/**
 * Error state for search failures
 */
function ErrorState({ error }: { error: Error }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Search Error</AlertTitle>
      <AlertDescription>
        {error.message || 'An error occurred while searching. Please try again.'}
      </AlertDescription>
    </Alert>
  )
}

/**
 * Results header with count and view toggle
 */
function ResultsHeader({
  totalResults,
  executionTime,
  viewMode = 'list',
  onViewModeChange,
}: {
  totalResults: number
  executionTime?: number
  viewMode?: 'grid' | 'list'
  onViewModeChange?: (mode: 'grid' | 'list') => void
}) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">
          {totalResults.toLocaleString()}
        </span>
        {totalResults === 1 ? 'result' : 'results'}
        {executionTime !== undefined && (
          <span className="text-xs">
            ({executionTime.toFixed(0)}ms)
          </span>
        )}
      </div>

      {onViewModeChange && (
        <div className="flex items-center gap-1 border border-border rounded-md p-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onViewModeChange('list')}
            className={cn(
              'h-7 w-7',
              viewMode === 'list' && 'bg-accent text-accent-foreground'
            )}
            title="List view"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onViewModeChange('grid')}
            className={cn(
              'h-7 w-7',
              viewMode === 'grid' && 'bg-accent text-accent-foreground'
            )}
            title="Grid view"
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

/**
 * Main SearchResults component
 */
export function SearchResults({
  results,
  isLoading = false,
  error = null,
  totalResults = 0,
  query,
  executionTime,
  viewMode = 'list',
  onViewModeChange,
  className,
  children,
}: SearchResultsProps) {
  // Error state
  if (error) {
    return (
      <div className={cn('w-full', className)}>
        <ErrorState error={error} />
      </div>
    )
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('w-full', className)}>
        <SearchResultsSkeleton count={6} />
      </div>
    )
  }

  // Empty state
  if (results.length === 0) {
    return (
      <div className={cn('w-full', className)}>
        <EmptyState query={query} />
      </div>
    )
  }

  // Results display
  return (
    <div className={cn('w-full space-y-4', className)}>
      <ResultsHeader
        totalResults={totalResults}
        executionTime={executionTime}
        viewMode={viewMode}
        onViewModeChange={onViewModeChange}
      />

      <div
        className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
            : 'space-y-4'
        )}
      >
        {children}
      </div>
    </div>
  )
}
