import React from 'react';
import { Card } from '@/components/ui/Card';
import { useCronJobsList } from '../api';
import type { CronJob } from '../types/scheduler.types';

interface CronJobsTableProps {
  className?: string;
}

/**
 * Cron Job Row
 */
const CronJobRow: React.FC<{ job: CronJob }> = ({ job }) => {
  const statusColor = job.enabled
    ? 'bg-green-100 text-green-800'
    : 'bg-gray-100 text-gray-600';

  const lastStatusColor =
    job.last_status === 'success'
      ? 'text-green-600'
      : job.last_status === 'failed'
      ? 'text-red-600'
      : 'text-gray-500';

  const formatDate = (dateStr: string | undefined): string => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-3 py-3">
        <div>
          <p className="font-medium">{job.name}</p>
          {job.description && (
            <p className="text-xs text-gray-500">{job.description}</p>
          )}
        </div>
      </td>
      <td className="px-3 py-3 font-mono text-sm">{job.schedule}</td>
      <td className="px-3 py-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor}`}>
          {job.enabled ? 'ENABLED' : 'DISABLED'}
        </span>
      </td>
      <td className="px-3 py-3 text-sm text-gray-600">
        {formatDate(job.last_run)}
        {job.last_status && (
          <span className={`ml-2 text-xs ${lastStatusColor}`}>
            ({job.last_status})
          </span>
        )}
      </td>
      <td className="px-3 py-3 text-sm">
        <span className="text-blue-600 font-medium">
          {formatDate(job.next_run)}
        </span>
      </td>
      <td className="px-3 py-3 text-sm text-gray-600">
        {job.run_count.toLocaleString()}
      </td>
    </tr>
  );
};

/**
 * Cron Jobs Table
 *
 * Displays all scheduled cron jobs with their schedules and status.
 */
export const CronJobsTable: React.FC<CronJobsTableProps> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useCronJobsList();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Cron Jobs</h3>
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Cron Jobs</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load cron jobs: {error.message}
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
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold">Cron Jobs</h3>
            <p className="text-sm text-gray-500">
              {data?.total || 0} scheduled jobs
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {data?.cron_jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No cron jobs configured</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">Name</th>
                  <th className="px-3 py-2 text-left">Schedule</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Last Run</th>
                  <th className="px-3 py-2 text-left">Next Run</th>
                  <th className="px-3 py-2 text-left">Run Count</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data?.cron_jobs.map((job) => (
                  <CronJobRow key={job.name} job={job} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Card>
  );
};
