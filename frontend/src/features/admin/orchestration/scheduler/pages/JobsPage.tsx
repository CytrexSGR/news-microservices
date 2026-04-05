import React, { useState } from 'react';
import { JobsListTable } from '../components/JobsListTable';
import { JobsStatsPanel } from '../components/JobsStatsPanel';
import type { JobStatus } from '../types/scheduler.types';

/**
 * Jobs Management Page
 *
 * Full-featured jobs management with filtering, pagination,
 * and bulk actions.
 */
export const JobsPage: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<JobStatus | undefined>();

  const statusFilters: { value: JobStatus | 'all'; label: string; color: string }[] = [
    { value: 'all', label: 'All Jobs', color: 'bg-gray-100 text-gray-800' },
    { value: 'pending', label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'running', label: 'Running', color: 'bg-blue-100 text-blue-800' },
    { value: 'completed', label: 'Completed', color: 'bg-green-100 text-green-800' },
    { value: 'failed', label: 'Failed', color: 'bg-red-100 text-red-800' },
    { value: 'cancelled', label: 'Cancelled', color: 'bg-gray-100 text-gray-600' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Jobs Management</h1>
          <p className="text-gray-600">
            View and manage all background jobs
          </p>
        </div>
      </div>

      {/* Statistics Summary */}
      <JobsStatsPanel />

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        {statusFilters.map((filter) => (
          <button
            key={filter.value}
            onClick={() =>
              setSelectedStatus(filter.value === 'all' ? undefined : filter.value)
            }
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              (filter.value === 'all' && !selectedStatus) ||
              filter.value === selectedStatus
                ? `${filter.color} ring-2 ring-offset-2 ring-blue-500`
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Jobs Table */}
      <JobsListTable initialStatus={selectedStatus} pageSize={50} />
    </div>
  );
};

export default JobsPage;
