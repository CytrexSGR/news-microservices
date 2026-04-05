/**
 * SavedSearchesList Component
 *
 * Displays a list of saved searches with:
 * - Loading state with skeletons
 * - Empty state with call-to-action
 * - Error state with retry
 * - Grid layout for cards
 */

import * as React from 'react'
import { Bookmark, RefreshCw, SearchX, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { Card, CardContent } from '@/components/ui/Card'
import { useSavedSearches } from '../api/useSavedSearches'
import { SavedSearchCard } from './SavedSearchCard'
import type { SavedSearch } from '../types/savedSearch'

interface SavedSearchesListProps {
  /** Called when a search is run (for navigation) */
  onRunSearch?: (results: { query: string; total: number }) => void
  /** Maximum number of items to show (optional) */
  limit?: number
  /** Show as compact list (for sidebar) */
  compact?: boolean
  /** Optional: Custom class name */
  className?: string
}

/**
 * Loading skeleton for saved search cards
 */
function SavedSearchSkeleton() {
  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <Skeleton className="h-5 w-[200px]" />
            <Skeleton className="h-4 w-[150px]" />
          </div>
          <Skeleton className="h-9 w-20" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-24" />
        </div>
        <div className="flex gap-4 pt-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
    </Card>
  )
}

/**
 * Empty state when no saved searches exist
 */
function EmptyState() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <SearchX className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No Saved Searches</h3>
        <p className="text-muted-foreground text-sm max-w-sm mb-4">
          Save your frequently used searches to quickly access them later. Go to
          the search page and click &ldquo;Save Search&rdquo; to get started.
        </p>
        <Button variant="outline" asChild>
          <a href="/search">
            <Bookmark className="mr-2 h-4 w-4" />
            Go to Search
          </a>
        </Button>
      </CardContent>
    </Card>
  )
}

/**
 * Error state with retry button
 */
function ErrorState({
  error,
  onRetry,
}: {
  error: Error
  onRetry: () => void
}) {
  return (
    <Card className="border-destructive/50">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Failed to Load</h3>
        <p className="text-muted-foreground text-sm max-w-sm mb-4">
          {error.message || 'An error occurred while loading your saved searches.'}
        </p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
      </CardContent>
    </Card>
  )
}

export function SavedSearchesList({
  onRunSearch,
  limit,
  compact = false,
  className,
}: SavedSearchesListProps) {
  const { data, isLoading, error, refetch } = useSavedSearches()

  // Loading state
  if (isLoading) {
    return (
      <div className={compact ? 'space-y-2' : 'grid gap-4 md:grid-cols-2 lg:grid-cols-3'}>
        {Array.from({ length: compact ? 3 : 6 }).map((_, i) => (
          <SavedSearchSkeleton key={i} />
        ))}
      </div>
    )
  }

  // Error state
  if (error) {
    return <ErrorState error={error} onRetry={() => refetch()} />
  }

  // Empty state
  if (!data?.items.length) {
    return <EmptyState />
  }

  // Get items (optionally limited)
  const items = limit ? data.items.slice(0, limit) : data.items

  // Render list
  return (
    <div
      className={
        compact
          ? 'space-y-2'
          : `grid gap-4 md:grid-cols-2 lg:grid-cols-3 ${className || ''}`
      }
    >
      {items.map((savedSearch: SavedSearch) => (
        <SavedSearchCard
          key={savedSearch.id}
          savedSearch={savedSearch}
          onRun={onRunSearch}
        />
      ))}
    </div>
  )
}
