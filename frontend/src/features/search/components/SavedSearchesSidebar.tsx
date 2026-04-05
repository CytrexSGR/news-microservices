/**
 * SavedSearchesSidebar Component
 *
 * Sidebar displaying list of saved searches with quick actions.
 * Shows scheduled searches with clock icon and notification status.
 */

import * as React from 'react';
import { useState } from 'react';
import { format, parseISO } from 'date-fns';
import {
  Search,
  Clock,
  Bell,
  Play,
  MoreHorizontal,
  Trash2,
  Edit,
  Calendar,
  Loader2,
  Star,
  StarOff,
  ChevronRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useSavedSearches, useDeleteSavedSearch } from '../api/useSavedSearches';
import { useExecuteSavedSearch } from '../api/useExecuteSavedSearch';
import type { SavedSearch } from '../types/search.types';

interface SavedSearchesSidebarProps {
  /** Currently selected search ID */
  selectedId?: string;
  /** Called when a search is selected */
  onSelect?: (search: SavedSearch) => void;
  /** Called when edit is clicked */
  onEdit?: (search: SavedSearch) => void;
  /** Called when create new is clicked */
  onCreate?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Single saved search item in the sidebar
 */
function SavedSearchItem({
  search,
  isSelected,
  onSelect,
  onEdit,
  onRun,
  onDelete,
  isRunning,
  isDeleting,
}: {
  search: SavedSearch;
  isSelected: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onRun: () => void;
  onDelete: () => void;
  isRunning: boolean;
  isDeleting: boolean;
}) {
  const [showActions, setShowActions] = useState(false);

  const lastRun = search.last_run
    ? format(parseISO(search.last_run), 'MMM d, HH:mm')
    : 'Never run';

  return (
    <div
      className={cn(
        'group relative flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors',
        isSelected
          ? 'bg-primary/10 text-primary'
          : 'hover:bg-muted/50'
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      onClick={onSelect}
    >
      {/* Icon */}
      <div className="shrink-0">
        {search.is_scheduled ? (
          <Clock className="h-4 w-4 text-primary" />
        ) : (
          <Search className="h-4 w-4 text-muted-foreground" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate text-sm">{search.name}</span>
          {search.alert_enabled && (
            <Bell className="h-3 w-3 text-amber-500 shrink-0" />
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="truncate">
            {search.query || 'No query'}
          </span>
          {search.result_count !== undefined && (
            <>
              <span>-</span>
              <span>{search.result_count} results</span>
            </>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div
        className={cn(
          'flex items-center gap-1 shrink-0 transition-opacity',
          showActions ? 'opacity-100' : 'opacity-0'
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Run Button */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onRun}
                disabled={isRunning}
              >
                {isRunning ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">Run search</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* More Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={onRun} disabled={isRunning}>
              <Play className="mr-2 h-4 w-4" />
              Run Now
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onEdit}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={onDelete}
              disabled={isDeleting}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Selected indicator */}
      {isSelected && (
        <ChevronRight className="h-4 w-4 text-primary shrink-0" />
      )}
    </div>
  );
}

/**
 * Loading skeleton for sidebar
 */
function SidebarSkeleton() {
  return (
    <div className="space-y-2 p-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-2">
          <Skeleton className="h-4 w-4 rounded" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SavedSearchesSidebar({
  selectedId,
  onSelect,
  onEdit,
  onCreate,
  className,
}: SavedSearchesSidebarProps) {
  const { data, isLoading, error } = useSavedSearches();
  const { mutate: executeSearch, isPending: isExecuting } = useExecuteSavedSearch();
  const { mutate: deleteSearch, isPending: isDeleting } = useDeleteSavedSearch();

  const [runningId, setRunningId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleRun = (search: SavedSearch) => {
    setRunningId(search.id);
    executeSearch(
      { id: search.id },
      {
        onSettled: () => setRunningId(null),
      }
    );
  };

  const handleDelete = (search: SavedSearch) => {
    if (!window.confirm(`Delete "${search.name}"?`)) return;
    setDeletingId(search.id);
    deleteSearch(Number(search.id), {
      onSettled: () => setDeletingId(null),
    });
  };

  // Separate scheduled and regular searches
  const scheduledSearches = data?.items.filter((s) => s.is_scheduled) || [];
  const regularSearches = data?.items.filter((s) => !s.is_scheduled) || [];

  if (isLoading) {
    return (
      <div className={cn('w-72 border-r bg-background', className)}>
        <div className="p-4 border-b">
          <h2 className="font-semibold flex items-center gap-2">
            <Search className="h-4 w-4" />
            Saved Searches
          </h2>
        </div>
        <SidebarSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('w-72 border-r bg-background', className)}>
        <div className="p-4 border-b">
          <h2 className="font-semibold flex items-center gap-2">
            <Search className="h-4 w-4" />
            Saved Searches
          </h2>
        </div>
        <div className="p-4 text-sm text-destructive">
          Failed to load saved searches
        </div>
      </div>
    );
  }

  const totalCount = data?.total || 0;

  return (
    <div className={cn('w-72 border-r bg-background flex flex-col', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold flex items-center gap-2">
            <Search className="h-4 w-4" />
            Saved Searches
            <Badge variant="secondary" className="text-xs">
              {totalCount}
            </Badge>
          </h2>
          {onCreate && (
            <Button variant="ghost" size="sm" onClick={onCreate}>
              + New
            </Button>
          )}
        </div>
      </div>

      {/* Scrollable list */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {totalCount === 0 ? (
            <div className="text-center py-8 px-4">
              <Search className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground mb-3">
                No saved searches yet
              </p>
              {onCreate && (
                <Button variant="outline" size="sm" onClick={onCreate}>
                  Create your first search
                </Button>
              )}
            </div>
          ) : (
            <>
              {/* Scheduled Searches */}
              {scheduledSearches.length > 0 && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Clock className="h-3 w-3" />
                    Scheduled ({scheduledSearches.length})
                  </div>
                  <div className="space-y-1">
                    {scheduledSearches.map((search) => (
                      <SavedSearchItem
                        key={search.id}
                        search={search}
                        isSelected={selectedId === search.id}
                        onSelect={() => onSelect?.(search)}
                        onEdit={() => onEdit?.(search)}
                        onRun={() => handleRun(search)}
                        onDelete={() => handleDelete(search)}
                        isRunning={runningId === search.id}
                        isDeleting={deletingId === search.id}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Regular Searches */}
              {regularSearches.length > 0 && (
                <div>
                  {scheduledSearches.length > 0 && (
                    <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      <Search className="h-3 w-3" />
                      Saved ({regularSearches.length})
                    </div>
                  )}
                  <div className="space-y-1">
                    {regularSearches.map((search) => (
                      <SavedSearchItem
                        key={search.id}
                        search={search}
                        isSelected={selectedId === search.id}
                        onSelect={() => onSelect?.(search)}
                        onEdit={() => onEdit?.(search)}
                        onRun={() => handleRun(search)}
                        onDelete={() => handleDelete(search)}
                        isRunning={runningId === search.id}
                        isDeleting={deletingId === search.id}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
