/**
 * SavedSearchCard Component
 *
 * Displays a single saved search with:
 * - Name and query
 * - Active filters as badges
 * - Last updated timestamp
 * - Run, edit, and delete actions
 * - Notification status indicator
 */

import * as React from 'react'
import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import {
  Play,
  Trash2,
  Bell,
  BellOff,
  Calendar,
  Filter,
  MoreVertical,
  Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'
import { useDeleteSavedSearch, useRunSavedSearch } from '../api/useSavedSearches'
import type { SavedSearch } from '../types/savedSearch'

interface SavedSearchCardProps {
  /** Saved search data */
  savedSearch: SavedSearch
  /** Called when running search (navigate to results) */
  onRun?: (results: { query: string; total: number }) => void
  /** Optional: Custom class name */
  className?: string
}

// Category display mapping
const categoryDisplayMap: Record<string, { label: string; color: string }> = {
  economy_markets: { label: 'Economy & Markets', color: 'bg-blue-500' },
  technology_science: { label: 'Technology & Science', color: 'bg-purple-500' },
  geopolitics_security: { label: 'Geopolitics & Security', color: 'bg-red-500' },
  climate_environment_health: {
    label: 'Climate & Environment',
    color: 'bg-green-500',
  },
  politics_society: { label: 'Politics & Society', color: 'bg-orange-500' },
  panorama: { label: 'Panorama', color: 'bg-indigo-500' },
}

export function SavedSearchCard({
  savedSearch,
  onRun,
  className,
}: SavedSearchCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const { mutate: runSearch, isPending: isRunning } = useRunSavedSearch()
  const { mutate: deleteSearch, isPending: isDeleting } = useDeleteSavedSearch()

  const handleRun = () => {
    runSearch(
      { id: savedSearch.id },
      {
        onSuccess: (results) => {
          toast.success(`Found ${results.total} results`)
          onRun?.({ query: results.query, total: results.total })
        },
        onError: (error: Error) => {
          toast.error(error.message || 'Failed to run search')
        },
      }
    )
  }

  const handleDelete = () => {
    deleteSearch(savedSearch.id, {
      onSuccess: () => {
        toast.success(`Deleted "${savedSearch.name}"`)
        setShowDeleteConfirm(false)
      },
      onError: (error: Error) => {
        toast.error(error.message || 'Failed to delete search')
      },
    })
  }

  // Format dates
  const createdDate = format(parseISO(savedSearch.created_at), 'MMM d, yyyy')
  const updatedDate = format(
    parseISO(savedSearch.updated_at),
    'MMM d, yyyy HH:mm'
  )

  // Count filters
  const filterCount =
    (savedSearch.filters?.source?.length ? 1 : 0) +
    (savedSearch.filters?.sentiment?.length ? 1 : 0) +
    (savedSearch.filters?.date_from ? 1 : 0) +
    (savedSearch.filters?.date_to ? 1 : 0)

  return (
    <>
      <Card
        className={cn(
          'group transition-all hover:shadow-md hover:border-primary/30',
          className
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1 flex-1 min-w-0">
              {/* Name */}
              <h3 className="font-semibold text-lg truncate">
                {savedSearch.name}
              </h3>
              {/* Query */}
              {savedSearch.query && (
                <p className="text-sm text-muted-foreground font-mono truncate">
                  &ldquo;{savedSearch.query}&rdquo;
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Notification indicator */}
              {savedSearch.notifications_enabled ? (
                <Bell className="h-4 w-4 text-primary" />
              ) : (
                <BellOff className="h-4 w-4 text-muted-foreground opacity-50" />
              )}

              {/* Run button */}
              <Button
                variant="default"
                size="sm"
                onClick={handleRun}
                disabled={isRunning}
              >
                {isRunning ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Run
                  </>
                )}
              </Button>

              {/* More menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <MoreVertical className="h-4 w-4" />
                    <span className="sr-only">More options</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleRun} disabled={isRunning}>
                    <Play className="mr-2 h-4 w-4" />
                    Run Search
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setShowDeleteConfirm(true)}
                    className="text-destructive focus:text-destructive"
                    disabled={isDeleting}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* Filters */}
          {filterCount > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              {savedSearch.filters?.source?.map((source) => (
                <Badge key={source} variant="secondary" className="text-xs">
                  {source}
                </Badge>
              ))}
              {savedSearch.filters?.sentiment?.map((cat) => {
                const display = categoryDisplayMap[cat] || {
                  label: cat,
                  color: 'bg-gray-500',
                }
                return (
                  <Badge key={cat} variant="secondary" className="text-xs">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${display.color} mr-1.5`}
                    />
                    {display.label}
                  </Badge>
                )
              })}
              {savedSearch.filters?.date_from && (
                <Badge variant="outline" className="text-xs">
                  From: {savedSearch.filters.date_from}
                </Badge>
              )}
              {savedSearch.filters?.date_to && (
                <Badge variant="outline" className="text-xs">
                  To: {savedSearch.filters.date_to}
                </Badge>
              )}
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>Created {createdDate}</span>
            </div>
            <span>|</span>
            <span>Last run: {updatedDate}</span>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Saved Search?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &ldquo;{savedSearch.name}&rdquo;?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
