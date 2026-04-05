/**
 * ResearchHistoryTable Component
 *
 * Table view of research history with:
 * - Sortable columns
 * - Status filters
 * - Pagination
 * - Action buttons (view, cancel, retry, export)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Eye,
  RotateCcw,
  Ban,
  Download,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Loader2,
  Zap,
  Coins,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  useResearchHistory,
  useCancelResearch,
  useRetryResearch,
} from '../api';
import { ResearchStatusBadge } from './ResearchStatusBadge';
import { ResearchExportButton } from './ResearchExportButton';
import type { TaskStatus, ResearchTaskResponse } from '../types';

interface ResearchHistoryTableProps {
  feedId?: string;
  onTaskSelect?: (taskId: number) => void;
}

const STATUS_FILTERS: { value: TaskStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'completed', label: 'Completed' },
  { value: 'processing', label: 'Processing' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export function ResearchHistoryTable({
  feedId,
  onTaskSelect,
}: ResearchHistoryTableProps) {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [page, setPage] = useState(1);
  const [days, setDays] = useState(30);
  const pageSize = 15;

  const { data, isLoading, refetch, isFetching } = useResearchHistory({
    days,
    page,
    page_size: pageSize,
  });

  const cancelMutation = useCancelResearch();
  const retryMutation = useRetryResearch();

  // Filter tasks by status
  const filteredTasks =
    statusFilter === 'all'
      ? data?.tasks
      : data?.tasks.filter((t) => t.status === statusFilter);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const truncateQuery = (query: string, maxLength = 60) => {
    if (query.length <= maxLength) return query;
    return query.slice(0, maxLength) + '...';
  };

  const handleView = (task: ResearchTaskResponse) => {
    if (onTaskSelect) {
      onTaskSelect(task.id);
    } else {
      navigate(`/research/${task.id}`);
    }
  };

  const canCancel = (status: TaskStatus) =>
    status === 'pending' || status === 'processing';
  const canRetry = (status: TaskStatus) => status === 'failed';
  const canExport = (status: TaskStatus) => status === 'completed';

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => {
                setStatusFilter(filter.value);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                statusFilter === filter.value
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-card border-border text-muted-foreground hover:border-primary/50'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => {
              setDays(Number(e.target.value));
              setPage(1);
            }}
            className="px-3 py-1.5 text-sm bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw
              className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Query
                </th>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Status
                </th>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Model
                </th>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Cost
                </th>
                <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                  Created
                </th>
                <th className="text-right text-xs font-medium text-muted-foreground px-4 py-3">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-muted-foreground" />
                  </td>
                </tr>
              ) : !filteredTasks || filteredTasks.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    No research tasks found
                  </td>
                </tr>
              ) : (
                filteredTasks.map((task) => (
                  <tr
                    key={task.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleView(task)}
                        className="text-sm text-foreground hover:text-primary transition-colors text-left"
                      >
                        {truncateQuery(task.query)}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <ResearchStatusBadge status={task.status} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Zap className="h-3 w-3" />
                        {task.model_name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Coins className="h-3 w-3" />
                        ${task.cost.toFixed(4)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(task.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleView(task)}
                          className="h-8 w-8 p-0"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>

                        {canCancel(task.status) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => cancelMutation.mutate(task.id)}
                            disabled={cancelMutation.isPending}
                            className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                            title="Cancel"
                          >
                            <Ban className="h-4 w-4" />
                          </Button>
                        )}

                        {canRetry(task.status) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => retryMutation.mutate(task.id)}
                            disabled={retryMutation.isPending}
                            className="h-8 w-8 p-0"
                            title="Retry"
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        )}

                        {canExport(task.status) && (
                          <ResearchExportButton
                            taskId={task.id}
                          />
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, data?.total || 0)} of {data?.total}{' '}
            results
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
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
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
    </div>
  );
}
