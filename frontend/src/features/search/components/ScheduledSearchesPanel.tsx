/**
 * ScheduledSearchesPanel Component
 *
 * Panel displaying table of scheduled searches with controls
 * for enabling/disabling, running now, and viewing history.
 */

import * as React from 'react';
import { useState } from 'react';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import {
  Clock,
  Play,
  Pause,
  History,
  MoreVertical,
  Trash2,
  Edit,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Loader2,
  CalendarClock,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/Switch';
import { Skeleton } from '@/components/ui/Skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  useScheduledSearches,
  useUnscheduleSearch,
  useRunScheduledSearchNow,
  useScheduleHistory,
  cronToConfig,
  describeSchedule,
} from '../api/useScheduledSearches';
import type { ScheduledSearch } from '../types/search.types';

interface ScheduledSearchesPanelProps {
  /** Called when edit is clicked */
  onEdit?: (search: ScheduledSearch) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Run history dialog
 */
function RunHistoryDialog({
  search,
  open,
  onOpenChange,
}: {
  search: ScheduledSearch | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: history, isLoading } = useScheduleHistory(
    search?.id
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Run History: {search?.name}
          </DialogTitle>
          <DialogDescription>
            Execution history for this scheduled search
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-96">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !history?.length ? (
            <div className="text-center py-8 text-muted-foreground">
              <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No execution history yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Executed At</TableHead>
                  <TableHead>Results</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((run, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-sm">
                      {format(parseISO(run.executed_at), 'MMM d, yyyy HH:mm:ss')}
                    </TableCell>
                    <TableCell>{run.result_count}</TableCell>
                    <TableCell>{run.execution_time_ms}ms</TableCell>
                    <TableCell>
                      {run.success ? (
                        <Badge variant="default" className="bg-green-500">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Success
                        </Badge>
                      ) : (
                        <Badge variant="destructive">
                          <XCircle className="h-3 w-3 mr-1" />
                          Failed
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Single row in the scheduled searches table
 */
function ScheduledSearchRow({
  search,
  onEdit,
  onToggle,
  onRunNow,
  onViewHistory,
  isToggling,
  isRunning,
}: {
  search: ScheduledSearch;
  onEdit: () => void;
  onToggle: (enabled: boolean) => void;
  onRunNow: () => void;
  onViewHistory: () => void;
  isToggling: boolean;
  isRunning: boolean;
}) {
  const scheduleConfig = search.schedule_cron
    ? cronToConfig(search.schedule_cron)
    : null;
  const scheduleDescription = scheduleConfig
    ? describeSchedule(scheduleConfig)
    : 'Not configured';

  const nextRun = search.next_run
    ? formatDistanceToNow(parseISO(search.next_run), { addSuffix: true })
    : 'Not scheduled';

  const lastRun = search.last_run
    ? format(parseISO(search.last_run), 'MMM d, HH:mm')
    : 'Never';

  return (
    <TableRow>
      {/* Name & Query */}
      <TableCell>
        <div className="space-y-0.5">
          <div className="font-medium">{search.name}</div>
          {search.query && (
            <div className="text-xs text-muted-foreground font-mono truncate max-w-48">
              {search.query}
            </div>
          )}
        </div>
      </TableCell>

      {/* Schedule */}
      <TableCell>
        <div className="flex items-center gap-2 text-sm">
          <Clock className="h-4 w-4 text-muted-foreground" />
          {scheduleDescription}
        </div>
      </TableCell>

      {/* Next Run */}
      <TableCell>
        <div className="text-sm">
          {search.is_scheduled ? nextRun : (
            <span className="text-muted-foreground">Disabled</span>
          )}
        </div>
      </TableCell>

      {/* Last Run */}
      <TableCell>
        <div className="space-y-0.5">
          <div className="text-sm">{lastRun}</div>
          {search.result_count !== undefined && (
            <div className="text-xs text-muted-foreground">
              {search.result_count} results
            </div>
          )}
        </div>
      </TableCell>

      {/* Status Toggle */}
      <TableCell>
        <div className="flex items-center gap-2">
          <Switch
            checked={search.is_scheduled}
            onCheckedChange={onToggle}
            disabled={isToggling}
          />
          {isToggling && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
      </TableCell>

      {/* Actions */}
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onRunNow}
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
              <DropdownMenuItem onClick={onRunNow} disabled={isRunning}>
                <Play className="mr-2 h-4 w-4" />
                Run Now
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onViewHistory}>
                <History className="mr-2 h-4 w-4" />
                View History
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onEdit}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Schedule
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  );
}

/**
 * Loading skeleton for table
 */
function TableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Search</TableHead>
          <TableHead>Schedule</TableHead>
          <TableHead>Next Run</TableHead>
          <TableHead>Last Run</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 4 }).map((_, i) => (
          <TableRow key={i}>
            <TableCell><Skeleton className="h-10 w-48" /></TableCell>
            <TableCell><Skeleton className="h-6 w-32" /></TableCell>
            <TableCell><Skeleton className="h-6 w-24" /></TableCell>
            <TableCell><Skeleton className="h-6 w-24" /></TableCell>
            <TableCell><Skeleton className="h-6 w-12" /></TableCell>
            <TableCell><Skeleton className="h-8 w-20" /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function ScheduledSearchesPanel({
  onEdit,
  className,
}: ScheduledSearchesPanelProps) {
  const { data, isLoading, error, refetch, isRefetching } = useScheduledSearches();
  const { mutate: unschedule } = useUnscheduleSearch();
  const { mutate: runNow } = useRunScheduledSearchNow();

  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [historySearch, setHistorySearch] = useState<ScheduledSearch | null>(null);

  const handleToggle = (search: ScheduledSearch, enabled: boolean) => {
    if (!enabled) {
      setTogglingId(search.id);
      unschedule(search.id, {
        onSettled: () => setTogglingId(null),
      });
    }
    // Re-enabling would need schedule dialog
    // For now, just edit
    if (enabled && onEdit) {
      onEdit(search);
    }
  };

  const handleRunNow = (search: ScheduledSearch) => {
    setRunningId(search.id);
    runNow(search.id, {
      onSettled: () => setRunningId(null),
    });
  };

  if (error) {
    return (
      <Card className={cn('border-destructive/50', className)}>
        <CardContent className="py-8 text-center">
          <XCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <p className="text-destructive">Failed to load scheduled searches</p>
          <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarClock className="h-5 w-5" />
              Scheduled Searches
              {data?.total !== undefined && (
                <Badge variant="secondary">{data.total}</Badge>
              )}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refetch()}
              disabled={isRefetching}
            >
              <RefreshCw
                className={cn('h-4 w-4', isRefetching && 'animate-spin')}
              />
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <TableSkeleton />
          ) : !data?.items.length ? (
            <div className="text-center py-12">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <h3 className="font-semibold mb-1">No Scheduled Searches</h3>
              <p className="text-muted-foreground text-sm max-w-sm mx-auto">
                Schedule your saved searches to run automatically and get notified
                about new results.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Search</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-24">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((search) => (
                  <ScheduledSearchRow
                    key={search.id}
                    search={search}
                    onEdit={() => onEdit?.(search)}
                    onToggle={(enabled) => handleToggle(search, enabled)}
                    onRunNow={() => handleRunNow(search)}
                    onViewHistory={() => setHistorySearch(search)}
                    isToggling={togglingId === search.id}
                    isRunning={runningId === search.id}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* History Dialog */}
      <RunHistoryDialog
        search={historySearch}
        open={!!historySearch}
        onOpenChange={(open) => !open && setHistorySearch(null)}
      />
    </>
  );
}
