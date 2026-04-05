/**
 * SavedSearchesPage Component
 *
 * Full saved searches management page with table view,
 * bulk actions, and scheduling controls.
 */

import * as React from 'react';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { format, parseISO } from 'date-fns';
import {
  Search,
  Bookmark,
  Clock,
  Bell,
  Play,
  Trash2,
  Edit,
  MoreVertical,
  RefreshCw,
  Plus,
  Filter,
  AlertCircle,
  Loader2,
  CheckSquare,
  Square,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { useSavedSearches, useDeleteSavedSearch } from '../api/useSavedSearches';
import { useExecuteSavedSearch } from '../api/useExecuteSavedSearch';
import { ScheduledSearchesPanel } from '../components/ScheduledSearchesPanel';
import { EnhancedSaveSearchDialog } from '../components/EnhancedSaveSearchDialog';
import type { SavedSearch } from '../types/search.types';

export function SavedSearchesPage() {
  const navigate = useNavigate();

  // State
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Data
  const { data, isLoading, error, refetch, isRefetching } = useSavedSearches();
  const { mutate: executeSearch, isPending: isExecuting } = useExecuteSavedSearch();
  const { mutate: deleteSearch, isPending: isDeleting } = useDeleteSavedSearch();

  const [executingId, setExecutingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Select all handler
  const handleSelectAll = useCallback(() => {
    if (!data?.items) return;
    if (selectedIds.length === data.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(data.items.map((s) => s.id));
    }
  }, [data?.items, selectedIds.length]);

  // Toggle single selection
  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  }, []);

  // Run search
  const handleRun = useCallback(
    (search: SavedSearch) => {
      setExecutingId(search.id);
      executeSearch(
        { id: search.id },
        {
          onSuccess: (results) => {
            navigate(`/search?q=${encodeURIComponent(search.query || '')}`);
          },
          onSettled: () => setExecutingId(null),
        }
      );
    },
    [executeSearch, navigate]
  );

  // Delete single
  const handleDelete = useCallback(
    (id: string) => {
      setDeletingId(id);
      deleteSearch(Number(id), {
        onSuccess: () => {
          setDeleteConfirmId(null);
          setSelectedIds((prev) => prev.filter((i) => i !== id));
        },
        onSettled: () => setDeletingId(null),
      });
    },
    [deleteSearch]
  );

  // Bulk delete
  const handleBulkDelete = useCallback(() => {
    // Delete one by one (could be optimized with batch endpoint)
    const deleteNext = (ids: string[]) => {
      if (ids.length === 0) {
        setShowBulkDeleteConfirm(false);
        setSelectedIds([]);
        return;
      }
      const [first, ...rest] = ids;
      deleteSearch(Number(first), {
        onSuccess: () => deleteNext(rest),
        onError: () => {
          toast.error('Some items could not be deleted');
          setShowBulkDeleteConfirm(false);
          setSelectedIds([]);
        },
      });
    };
    deleteNext(selectedIds);
  }, [selectedIds, deleteSearch]);

  // Filter counts
  const scheduledCount = data?.items.filter((s) => s.is_scheduled).length || 0;
  const alertCount = data?.items.filter((s) => s.alert_enabled).length || 0;

  if (error) {
    return (
      <div className="container py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Failed to Load Saved Searches</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error.message}</span>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bookmark className="h-6 w-6" />
            Saved Searches
            {data?.total !== undefined && (
              <Badge variant="secondary">{data.total}</Badge>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your saved searches, schedules, and alerts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isRefetching && 'animate-spin')} />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Search
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-6">
        <TabsList>
          <TabsTrigger value="all">
            All Searches
            {data?.total !== undefined && (
              <span className="ml-1.5 text-xs text-muted-foreground">
                ({data.total})
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="scheduled">
            <Clock className="h-4 w-4 mr-1.5" />
            Scheduled
            {scheduledCount > 0 && (
              <span className="ml-1.5 text-xs text-muted-foreground">
                ({scheduledCount})
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="h-4 w-4 mr-1.5" />
            With Alerts
            {alertCount > 0 && (
              <span className="ml-1.5 text-xs text-muted-foreground">
                ({alertCount})
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* All Searches Tab */}
        <TabsContent value="all" className="space-y-4">
          {/* Bulk Actions */}
          {selectedIds.length > 0 && (
            <Card className="border-primary/50 bg-primary/5">
              <CardContent className="py-3 flex items-center justify-between">
                <span className="text-sm font-medium">
                  {selectedIds.length} selected
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedIds([])}
                  >
                    Clear
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setShowBulkDeleteConfirm(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Table */}
          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-4 space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : !data?.items.length ? (
                <div className="text-center py-16">
                  <Bookmark className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-semibold mb-1">No Saved Searches</h3>
                  <p className="text-muted-foreground text-sm max-w-sm mx-auto mb-4">
                    Save your frequently used searches to quickly access them later.
                  </p>
                  <Button onClick={() => navigate('/search')}>
                    <Search className="h-4 w-4 mr-2" />
                    Start Searching
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox
                          checked={selectedIds.length === data.items.length}
                          onCheckedChange={handleSelectAll}
                        />
                      </TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Query</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Run</TableHead>
                      <TableHead>Results</TableHead>
                      <TableHead className="w-24">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.map((search) => (
                      <SavedSearchRow
                        key={search.id}
                        search={search}
                        isSelected={selectedIds.includes(search.id)}
                        onSelect={() => handleToggleSelect(search.id)}
                        onRun={() => handleRun(search)}
                        onEdit={() => {
                          // TODO: Implement edit
                          toast('Edit functionality coming soon');
                        }}
                        onDelete={() => setDeleteConfirmId(search.id)}
                        isRunning={executingId === search.id}
                      />
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scheduled Searches Tab */}
        <TabsContent value="scheduled">
          <ScheduledSearchesPanel />
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Searches with Alerts
              </CardTitle>
              <CardDescription>
                Searches configured to send alerts when new results are found
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-48 w-full" />
              ) : alertCount === 0 ? (
                <div className="text-center py-12">
                  <Bell className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                  <p className="text-muted-foreground">
                    No searches with alerts configured
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Query</TableHead>
                      <TableHead>Threshold</TableHead>
                      <TableHead>Last Alert</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data?.items
                      .filter((s) => s.alert_enabled)
                      .map((search) => (
                        <TableRow key={search.id}>
                          <TableCell className="font-medium">
                            {search.name}
                          </TableCell>
                          <TableCell className="font-mono text-sm text-muted-foreground">
                            {search.query || '-'}
                          </TableCell>
                          <TableCell>
                            {search.alert_threshold || 1} results
                          </TableCell>
                          <TableCell>-</TableCell>
                          <TableCell>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                navigate(`/search/alerts/${search.id}`)
                              }
                            >
                              Configure
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation */}
      <AlertDialog
        open={!!deleteConfirmId}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Saved Search?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The saved search and any associated
              schedules or alerts will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
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

      {/* Bulk Delete Confirmation */}
      <AlertDialog
        open={showBulkDeleteConfirm}
        onOpenChange={setShowBulkDeleteConfirm}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedIds.length} Saved Searches?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. All selected searches and their
              associated schedules and alerts will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete All
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Create Dialog */}
      <EnhancedSaveSearchDialog
        query=""
        filters={{}}
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSaved={() => refetch()}
      />
    </div>
  );
}

/**
 * Table row for a single saved search
 */
function SavedSearchRow({
  search,
  isSelected,
  onSelect,
  onRun,
  onEdit,
  onDelete,
  isRunning,
}: {
  search: SavedSearch;
  isSelected: boolean;
  onSelect: () => void;
  onRun: () => void;
  onEdit: () => void;
  onDelete: () => void;
  isRunning: boolean;
}) {
  const lastRun = search.last_run
    ? format(parseISO(search.last_run), 'MMM d, HH:mm')
    : 'Never';

  return (
    <TableRow>
      <TableCell>
        <Checkbox checked={isSelected} onCheckedChange={onSelect} />
      </TableCell>
      <TableCell>
        <div className="font-medium">{search.name}</div>
      </TableCell>
      <TableCell>
        <code className="text-sm text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
          {search.query || 'No query'}
        </code>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          {search.is_scheduled && (
            <Badge variant="outline" className="gap-1">
              <Clock className="h-3 w-3" />
              Scheduled
            </Badge>
          )}
          {search.alert_enabled && (
            <Badge variant="outline" className="gap-1">
              <Bell className="h-3 w-3" />
              Alerts
            </Badge>
          )}
          {!search.is_scheduled && !search.alert_enabled && (
            <span className="text-muted-foreground text-sm">-</span>
          )}
        </div>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">{lastRun}</TableCell>
      <TableCell>
        {search.result_count !== undefined ? (
          <span className="font-medium">{search.result_count}</span>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onRun}
            disabled={isRunning}
            className="h-8 w-8"
          >
            {isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
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
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  );
}
