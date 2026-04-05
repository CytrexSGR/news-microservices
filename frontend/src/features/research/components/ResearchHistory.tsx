/**
 * ResearchHistory Component
 *
 * Displays paginated list of past research tasks with:
 * - Status filter
 * - Timeline grouping (Today, Yesterday, This Week, etc.)
 * - Pagination
 * - Empty state
 */

import { useState } from 'react';
import {
  History,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Inbox,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useResearchHistory } from '../api';
import { ResearchResultCard } from './ResearchResultCard';
import type { TaskStatus, ResearchTaskResponse } from '../types';

interface ResearchHistoryProps {
  onTaskSelect?: (taskId: number) => void;
  selectedTaskId?: number;
  feedId?: string;
}

const STATUS_FILTERS: { value: TaskStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'completed', label: 'Completed' },
  { value: 'processing', label: 'Processing' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
];

const DAYS_OPTIONS = [7, 30, 90, 365];

export function ResearchHistory({
  onTaskSelect,
  selectedTaskId,
  feedId,
}: ResearchHistoryProps) {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [days, setDays] = useState(30);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, isError, refetch, isFetching } = useResearchHistory({
    days,
    page,
    page_size: pageSize,
  });

  // Filter tasks by status
  const filteredTasks =
    statusFilter === 'all'
      ? data?.tasks
      : data?.tasks.filter((t) => t.status === statusFilter);

  // Group tasks by date
  const groupTasksByDate = (tasks: ResearchTaskResponse[] | undefined) => {
    if (!tasks) return {};

    const groups: Record<string, ResearchTaskResponse[]> = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const thisWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    tasks.forEach((task) => {
      const taskDate = new Date(task.created_at);
      let groupKey: string;

      if (taskDate >= today) {
        groupKey = 'Today';
      } else if (taskDate >= yesterday) {
        groupKey = 'Yesterday';
      } else if (taskDate >= thisWeek) {
        groupKey = 'This Week';
      } else {
        groupKey = taskDate.toLocaleDateString('en-US', {
          month: 'long',
          year: 'numeric',
        });
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(task);
    });

    return groups;
  };

  const groupedTasks = groupTasksByDate(filteredTasks);
  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-4">
      {/* Header with Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-medium text-foreground">Research History</h3>
          {data && (
            <span className="text-sm text-muted-foreground">
              ({data.total} total)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center gap-1 bg-muted/50 rounded-lg p-1">
            <Filter className="h-4 w-4 text-muted-foreground ml-2" />
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.value}
                onClick={() => {
                  setStatusFilter(filter.value);
                  setPage(1);
                }}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  statusFilter === filter.value
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          {/* Days Filter */}
          <select
            value={days}
            onChange={(e) => {
              setDays(Number(e.target.value));
              setPage(1);
            }}
            className="px-2 py-1 text-xs bg-muted/50 border-0 rounded-lg text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {DAYS_OPTIONS.map((d) => (
              <option key={d} value={d}>
                Last {d} days
              </option>
            ))}
          </select>

          {/* Refresh Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => refetch()}
            disabled={isFetching}
            className="h-8 w-8"
          >
            <RefreshCw
              className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : isError ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-destructive mb-2">Failed to load history</p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Try Again
          </Button>
        </div>
      ) : !filteredTasks || filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-1">No research tasks found</p>
          <p className="text-sm text-muted-foreground">
            {statusFilter !== 'all'
              ? `No ${statusFilter} tasks in the last ${days} days`
              : `Start a new research to see it here`}
          </p>
        </div>
      ) : (
        <>
          {/* Grouped Tasks */}
          <div className="space-y-6">
            {Object.entries(groupedTasks).map(([group, tasks]) => (
              <div key={group}>
                <h4 className="text-sm font-medium text-muted-foreground mb-3 sticky top-0 bg-background py-1">
                  {group}
                </h4>
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <ResearchResultCard
                      key={task.id}
                      task={task}
                      onSelect={onTaskSelect}
                      isSelected={selectedTaskId === task.id}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-border">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
