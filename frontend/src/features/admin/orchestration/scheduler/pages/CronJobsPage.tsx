import React from 'react';
import { CronJobsTable } from '../components/CronJobsTable';
import { useCronJobsList } from '../api';

/**
 * Cron Jobs Management Page
 *
 * Dedicated page for managing scheduled cron jobs.
 */
export const CronJobsPage: React.FC = () => {
  const { data } = useCronJobsList();

  const enabledCount = data?.cron_jobs.filter((j) => j.enabled).length || 0;
  const disabledCount = data?.cron_jobs.filter((j) => !j.enabled).length || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Scheduled Tasks</h1>
          <p className="text-gray-600">
            Manage recurring cron jobs and schedules
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Total Jobs</p>
          <p className="text-2xl font-bold">{data?.total || 0}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Active</p>
          <p className="text-2xl font-bold text-green-600">{enabledCount}</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Disabled</p>
          <p className="text-2xl font-bold text-gray-500">{disabledCount}</p>
        </div>
      </div>

      {/* Cron Jobs Table */}
      <CronJobsTable />

      {/* Cron Expression Help */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">Cron Expression Reference</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm text-blue-700">
          <div>
            <p className="font-medium">Field</p>
            <p>minute</p>
            <p>hour</p>
            <p>day (month)</p>
            <p>month</p>
            <p>day (week)</p>
          </div>
          <div>
            <p className="font-medium">Values</p>
            <p>0-59</p>
            <p>0-23</p>
            <p>1-31</p>
            <p>1-12</p>
            <p>0-6 (Sun-Sat)</p>
          </div>
          <div className="col-span-3">
            <p className="font-medium">Examples</p>
            <p><code className="bg-blue-100 px-1 rounded">*/5 * * * *</code> Every 5 minutes</p>
            <p><code className="bg-blue-100 px-1 rounded">0 * * * *</code> Every hour</p>
            <p><code className="bg-blue-100 px-1 rounded">0 0 * * *</code> Daily at midnight</p>
            <p><code className="bg-blue-100 px-1 rounded">0 0 * * 0</code> Weekly on Sunday</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CronJobsPage;
