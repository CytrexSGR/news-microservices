import React from 'react';
import { SchedulerStatusCard } from '../components/SchedulerStatusCard';
import { SchedulerHealthCard } from '../components/SchedulerHealthCard';
import { JobsStatsPanel } from '../components/JobsStatsPanel';
import { JobsListTable } from '../components/JobsListTable';
import { CronJobsTable } from '../components/CronJobsTable';

/**
 * Scheduler Dashboard
 *
 * Main overview page for the scheduler/orchestration system.
 * Displays status, health, statistics, and recent jobs.
 */
export const SchedulerDashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Scheduler Dashboard</h1>
          <p className="text-gray-600">
            Monitor and manage background jobs and scheduled tasks
          </p>
        </div>
      </div>

      {/* Status and Health Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SchedulerStatusCard />
        <SchedulerHealthCard />
      </div>

      {/* Statistics */}
      <JobsStatsPanel />

      {/* Cron Jobs */}
      <CronJobsTable />

      {/* Recent Jobs (limited view) */}
      <JobsListTable pageSize={10} />
    </div>
  );
};

export default SchedulerDashboard;
