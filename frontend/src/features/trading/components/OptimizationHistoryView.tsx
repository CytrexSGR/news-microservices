/**
 * Optimization History View
 *
 * Comprehensive view of all optimization jobs with search, filter, and comparison.
 *
 * Features:
 * - Searchable and sortable table
 * - Filter by strategy, status, metric
 * - View detailed results
 * - Compare multiple runs
 * - Pagination support
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  History,
  Search,
  Filter,
  ChevronUp,
  ChevronDown,
  Eye,
  RefreshCw,
  Loader2,
} from 'lucide-react';

import type { OptimizationJob, OptimizationResult } from '../types/optimization';
import { OptimizationResultsView } from './OptimizationResultsView';
import { predictionClient } from '@/lib/api-client';

type SortField = 'started_at' | 'best_score' | 'duration_seconds' | 'strategy_id';
type SortDirection = 'asc' | 'desc';

export function OptimizationHistoryView() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all');
  const [sortField, setSortField] = useState<SortField>('started_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Fetch all optimization jobs
  const { data: jobs, isLoading, isRefetching, refetch } = useQuery<OptimizationJob[]>({
    queryKey: ['optimization-history', statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = { limit: '100' };
      if (statusFilter !== 'all') params.status = statusFilter;

      const response = await predictionClient.get<OptimizationJob[]>(
        '/optimization/jobs',
        params
      );

      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch job results when viewing details
  const { data: jobResults } = useQuery<OptimizationResult | null>({
    queryKey: ['optimization-results', selectedJobId],
    queryFn: async () => {
      if (!selectedJobId) return null;

      try {
        const response = await predictionClient.get<OptimizationResult>(
          `/optimization/jobs/${selectedJobId}/results`
        );
        return response.data;
      } catch (error) {
        return null;
      }
    },
    enabled: !!selectedJobId,
  });

  // Filter and sort jobs
  const filteredAndSortedJobs = useMemo(() => {
    if (!jobs) return [];

    // Filter by search query
    const filtered = jobs.filter((job) => {
      const searchLower = searchQuery.toLowerCase();
      return (
        job.strategy_id.toLowerCase().includes(searchLower) ||
        job.objective_metric.toLowerCase().includes(searchLower) ||
        job.id.toLowerCase().includes(searchLower)
      );
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle null values
      if (aValue === null) return 1;
      if (bValue === null) return -1;

      // Convert to numbers for numeric fields
      if (sortField === 'best_score' || sortField === 'duration_seconds') {
        aValue = parseFloat(aValue);
        bValue = parseFloat(bValue);
      }

      // Date comparison
      if (sortField === 'started_at') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [jobs, searchQuery, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? (
      <ChevronUp className="h-4 w-4 inline ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 inline ml-1" />
    );
  };

  const getStatusBadgeVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // If viewing results, show OptimizationResultsView
  if (selectedJobId && jobResults) {
    return (
      <OptimizationResultsView
        result={jobResults}
        jobId={selectedJobId}
        onClose={() => setSelectedJobId(null)}
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Optimization History
            {isRefetching && (
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </CardTitle>

          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {/* Search and Filters */}
        <div className="flex gap-4 mb-6">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by strategy, metric, or job ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <div className="flex gap-1">
              {(['all', 'completed', 'failed'] as const).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                  className="capitalize"
                >
                  {status}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Table */}
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : !filteredAndSortedJobs || filteredAndSortedJobs.length === 0 ? (
          <div className="text-center p-8 text-muted-foreground">
            No optimization jobs found
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('strategy_id')}
                  >
                    Strategy {getSortIcon('strategy_id')}
                  </TableHead>
                  <TableHead>Objective</TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('best_score')}
                  >
                    Best Score {getSortIcon('best_score')}
                  </TableHead>
                  <TableHead>Trials</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('started_at')}
                  >
                    Started At {getSortIcon('started_at')}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort('duration_seconds')}
                  >
                    Duration {getSortIcon('duration_seconds')}
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedJobs.map((job) => (
                  <TableRow
                    key={job.id}
                    className="hover:bg-muted/50 cursor-pointer"
                    onClick={() => job.status === 'completed' && setSelectedJobId(job.id)}
                  >
                    <TableCell className="font-medium">{job.strategy_id}</TableCell>
                    <TableCell className="capitalize">
                      {job.objective_metric.replace('_', ' ')}
                    </TableCell>
                    <TableCell>
                      {job.best_score ? parseFloat(job.best_score).toFixed(4) : '-'}
                    </TableCell>
                    <TableCell>
                      {job.trials_completed} / {job.trials_total}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(job.status)}>
                        {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(job.started_at)}
                    </TableCell>
                    <TableCell>
                      {job.duration_seconds > 0 ? formatDuration(job.duration_seconds) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {job.status === 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedJobId(job.id);
                          }}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Summary Stats */}
        {filteredAndSortedJobs && filteredAndSortedJobs.length > 0 && (
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredAndSortedJobs.length} job{filteredAndSortedJobs.length !== 1 ? 's' : ''}
            {searchQuery && ` matching "${searchQuery}"`}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
