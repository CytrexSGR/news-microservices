/**
 * JobsTable Component
 *
 * Displays all scheduled jobs with:
 * - Job name and schedule (cron expression + human readable)
 * - Last run time and status
 * - Next run time
 * - Average duration
 * - Actions (run now, view history)
 */

import { useState, useMemo } from 'react';
import {
  Clock,
  Play,
  History,
  ChevronUp,
  ChevronDown,
  Search,
  Filter,
  RefreshCw,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { RunJobButton } from './RunJobButton';
import type { CronJob } from '../types';
import { cronToHumanReadable } from '../types';

interface JobsTableProps {
  jobs: CronJob[];
  isLoading?: boolean;
  onJobSelect?: (job: CronJob) => void;
  onRefresh?: () => void;
}

type SortField = 'name' | 'next_run_time' | 'trigger';
type SortOrder = 'asc' | 'desc';

export function JobsTable({
  jobs,
  isLoading = false,
  onJobSelect,
  onRefresh,
}: JobsTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('next_run_time');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Filter and sort jobs
  const filteredJobs = useMemo(() => {
    let result = [...jobs];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (job) =>
          job.name.toLowerCase().includes(query) ||
          job.id.toLowerCase().includes(query) ||
          job.trigger.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter((job) => {
        if (statusFilter === 'pending') return job.pending;
        if (statusFilter === 'scheduled') return !job.pending && job.next_run_time;
        if (statusFilter === 'paused') return !job.next_run_time;
        return true;
      });
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'next_run_time':
          if (!a.next_run_time && !b.next_run_time) comparison = 0;
          else if (!a.next_run_time) comparison = 1;
          else if (!b.next_run_time) comparison = -1;
          else comparison = new Date(a.next_run_time).getTime() - new Date(b.next_run_time).getTime();
          break;
        case 'trigger':
          comparison = a.trigger.localeCompare(b.trigger);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [jobs, searchQuery, statusFilter, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-3 w-3" />
    ) : (
      <ChevronDown className="h-3 w-3" />
    );
  };

  const formatNextRun = (nextRunTime: string | null): string => {
    if (!nextRunTime) return 'Not scheduled';

    const date = new Date(nextRunTime);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 0) return 'Overdue';
    if (diffMins < 1) return 'Less than a minute';
    if (diffMins < 60) return `In ${diffMins} min`;
    if (diffHours < 24) return `In ${diffHours}h ${diffMins % 60}m`;
    return `In ${diffDays}d ${diffHours % 24}h`;
  };

  const handleRunJob = async (job: CronJob) => {
    // This would trigger the job manually
    console.log('Running job manually:', job.id);
    // The actual implementation would call an API endpoint
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Scheduled Jobs
            </CardTitle>
            <CardDescription>
              {jobs.length} jobs registered | {filteredJobs.length} shown
            </CardDescription>
          </div>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search jobs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Filter status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="scheduled">Scheduled</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center gap-1">
                    Job Name
                    <SortIcon field="name" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted"
                  onClick={() => handleSort('trigger')}
                >
                  <div className="flex items-center gap-1">
                    Schedule
                    <SortIcon field="trigger" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted"
                  onClick={() => handleSort('next_run_time')}
                >
                  <div className="flex items-center gap-1">
                    Next Run
                    <SortIcon field="next_run_time" />
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    {isLoading ? 'Loading jobs...' : 'No jobs found'}
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => (
                  <tr
                    key={job.id}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => onJobSelect?.(job)}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-sm">{job.name}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {job.id}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="text-sm">{cronToHumanReadable(job.trigger)}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {job.trigger.length > 50
                            ? job.trigger.substring(0, 50) + '...'
                            : job.trigger}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm">{formatNextRun(job.next_run_time)}</div>
                      {job.next_run_time && (
                        <div className="text-xs text-muted-foreground">
                          {new Date(job.next_run_time).toLocaleString()}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {job.pending ? (
                        <Badge className="bg-blue-500/10 text-blue-500">Pending</Badge>
                      ) : job.next_run_time ? (
                        <Badge className="bg-green-500/10 text-green-500">Scheduled</Badge>
                      ) : (
                        <Badge className="bg-gray-500/10 text-gray-500">Paused</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <RunJobButton
                          jobName={job.name}
                          onRun={() => handleRunJob(job)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onJobSelect?.(job);
                          }}
                        >
                          <History className="h-3 w-3 mr-1" />
                          Details
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
