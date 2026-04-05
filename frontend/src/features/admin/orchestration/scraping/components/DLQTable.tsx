import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import {
  useDLQEntries,
  useDLQStats,
  useRequeueDLQEntry,
  useBulkRequeueDLQ,
  usePurgeDLQ,
  useUpdateDLQEntry,
} from '../api';
import type { DLQEntry, DLQStatus, DLQFailureReason } from '../types/scraping.types';

interface DLQTableProps {
  className?: string;
  pageSize?: number;
}

/**
 * Status Badge
 */
const StatusBadge: React.FC<{ status: DLQStatus }> = ({ status }) => {
  const colors: Record<DLQStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800',
    abandoned: 'bg-gray-100 text-gray-800',
    manual: 'bg-blue-100 text-blue-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

/**
 * Failure Reason Badge
 */
const FailureReasonBadge: React.FC<{ reason: DLQFailureReason }> = ({ reason }) => {
  const colors: Record<DLQFailureReason, string> = {
    timeout: 'bg-orange-100 text-orange-800',
    rate_limited: 'bg-yellow-100 text-yellow-800',
    blocked: 'bg-red-100 text-red-800',
    paywall: 'bg-purple-100 text-purple-800',
    parse_error: 'bg-pink-100 text-pink-800',
    network_error: 'bg-gray-100 text-gray-800',
    captcha: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[reason]}`}>
      {reason.replace('_', ' ')}
    </span>
  );
};

/**
 * DLQ Table
 *
 * Displays Dead Letter Queue entries with filtering and actions.
 */
export const DLQTable: React.FC<DLQTableProps> = ({ className, pageSize = 20 }) => {
  const [statusFilter, setStatusFilter] = useState<DLQStatus | undefined>();
  const [reasonFilter, setReasonFilter] = useState<DLQFailureReason | undefined>();
  const [page, setPage] = useState(0);

  const { data: stats } = useDLQStats();
  const { data, isLoading, error, refetch, isRefetching } = useDLQEntries({
    status: statusFilter,
    failure_reason: reasonFilter,
    limit: pageSize,
    offset: page * pageSize,
  });

  const requeueEntry = useRequeueDLQEntry();
  const bulkRequeue = useBulkRequeueDLQ();
  const purgeDLQ = usePurgeDLQ();
  const updateEntry = useUpdateDLQEntry();

  const handleRequeue = async (id: number) => {
    try {
      const result = await requeueEntry.mutateAsync(id);
      alert(`Requeued as job ${result.new_job_id}`);
    } catch (err) {
      console.error('Failed to requeue:', err);
    }
  };

  const handleBulkRequeue = async () => {
    if (!confirm('Requeue all pending DLQ entries?')) return;
    try {
      const result = await bulkRequeue.mutateAsync({
        status: 'pending',
        limit: 100,
      });
      alert(`Requeued ${result.requeued_count} entries`);
    } catch (err) {
      console.error('Failed to bulk requeue:', err);
    }
  };

  const handlePurge = async () => {
    if (!confirm('Purge all abandoned DLQ entries?')) return;
    try {
      const result = await purgeDLQ.mutateAsync({ status: 'abandoned' });
      alert(`Purged ${result.purged_count} entries`);
    } catch (err) {
      console.error('Failed to purge:', err);
    }
  };

  const handleAbandon = async (id: number) => {
    try {
      await updateEntry.mutateAsync({
        id,
        status: 'abandoned',
        resolver_notes: 'Manually abandoned',
      });
    } catch (err) {
      console.error('Failed to abandon:', err);
    }
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  const statusOptions: (DLQStatus | 'all')[] = ['all', 'pending', 'resolved', 'abandoned', 'manual'];
  const reasonOptions: (DLQFailureReason | 'all')[] = [
    'all',
    'timeout',
    'rate_limited',
    'blocked',
    'paywall',
    'parse_error',
    'network_error',
    'captcha',
    'unknown',
  ];

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Dead Letter Queue</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load DLQ: {error.message}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="p-6">
        {/* Header with Stats */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold">Dead Letter Queue</h3>
            {stats && (
              <p className="text-sm text-gray-500">
                {stats.total} total | {stats.pending_retry_count} pending retry
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleBulkRequeue}
              disabled={bulkRequeue.isPending || !stats?.pending_retry_count}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              Requeue All Pending
            </button>
            <button
              onClick={handlePurge}
              disabled={purgeDLQ.isPending}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
            >
              Purge Abandoned
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-4">
          <select
            value={statusFilter || 'all'}
            onChange={(e) => {
              const val = e.target.value;
              setStatusFilter(val === 'all' ? undefined : (val as DLQStatus));
              setPage(0);
            }}
            className="px-3 py-1 border rounded text-sm"
          >
            {statusOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'All Status' : opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={reasonFilter || 'all'}
            onChange={(e) => {
              const val = e.target.value;
              setReasonFilter(val === 'all' ? undefined : (val as DLQFailureReason));
              setPage(0);
            }}
            className="px-3 py-1 border rounded text-sm"
          >
            {reasonOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'All Reasons' : opt.replace('_', ' ')}
              </option>
            ))}
          </select>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : data?.entries.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No DLQ entries found</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">URL</th>
                    <th className="px-3 py-2 text-left">Domain</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Reason</th>
                    <th className="px-3 py-2 text-left">Retries</th>
                    <th className="px-3 py-2 text-left">Last Failed</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data?.entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono text-xs">{entry.id}</td>
                      <td className="px-3 py-2 max-w-xs truncate" title={entry.url}>
                        {entry.url}
                      </td>
                      <td className="px-3 py-2 text-gray-600">{entry.domain}</td>
                      <td className="px-3 py-2">
                        <StatusBadge status={entry.status} />
                      </td>
                      <td className="px-3 py-2">
                        <FailureReasonBadge reason={entry.failure_reason} />
                      </td>
                      <td className="px-3 py-2">{entry.retry_count}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">
                        {formatDate(entry.last_failed_at)}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          {entry.status === 'pending' && (
                            <>
                              <button
                                onClick={() => handleRequeue(entry.id)}
                                disabled={requeueEntry.isPending}
                                className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                              >
                                Requeue
                              </button>
                              <button
                                onClick={() => handleAbandon(entry.id)}
                                disabled={updateEntry.isPending}
                                className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                              >
                                Abandon
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t">
              <p className="text-sm text-gray-600">
                Showing {page * pageSize + 1}-
                {Math.min((page + 1) * pageSize, data?.total || 0)} of {data?.total || 0}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data || (page + 1) * pageSize >= data.total}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </Card>
  );
};
