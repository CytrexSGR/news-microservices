/**
 * ErrorLogsPage
 *
 * Displays error logs with filtering capabilities.
 */

import { useState } from 'react';
import {
  AlertCircle,
  RefreshCw,
  Filter,
  Search,
  Calendar,
  Download,
} from 'lucide-react';
import { useErrorLogs } from '../api/useErrorLogs';
import { useServicesList } from '../api/useServicesList';
import { ErrorLogsTable } from '../components';
import type { LogLevel } from '../types';

export function ErrorLogsPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<LogLevel | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [limit, setLimit] = useState(50);

  const { services } = useServicesList({ autoRefresh: false });

  const {
    logs,
    totalLogs,
    hasMore,
    isLoading,
    isFetching,
    invalidate,
    criticalCount,
    errorCount,
    warningCount,
  } = useErrorLogs({
    filters: {
      service: serviceFilter || undefined,
      level: levelFilter || undefined,
      limit,
    },
    autoRefresh,
    refetchInterval: 30000,
  });

  // Filter logs by search query (client-side)
  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      log.message.toLowerCase().includes(query) ||
      log.service.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Error Logs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {totalLogs} total logs | {criticalCount} critical | {errorCount} errors | {warningCount} warnings
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-border"
            />
            Auto-refresh
          </label>
          <button
            onClick={invalidate}
            disabled={isFetching}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Level Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <button
          onClick={() => setLevelFilter(levelFilter === 'critical' ? '' : 'critical')}
          className={`p-4 rounded-lg border transition-all ${
            levelFilter === 'critical'
              ? 'border-red-500 bg-red-50 dark:bg-red-950/30'
              : 'border-border bg-card hover:border-red-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Critical</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            {criticalCount}
          </p>
        </button>

        <button
          onClick={() => setLevelFilter(levelFilter === 'error' ? '' : 'error')}
          className={`p-4 rounded-lg border transition-all ${
            levelFilter === 'error'
              ? 'border-orange-500 bg-orange-50 dark:bg-orange-950/30'
              : 'border-border bg-card hover:border-orange-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Errors</span>
            <AlertCircle className="w-4 h-4 text-orange-500" />
          </div>
          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-1">
            {errorCount}
          </p>
        </button>

        <button
          onClick={() => setLevelFilter(levelFilter === 'warning' ? '' : 'warning')}
          className={`p-4 rounded-lg border transition-all ${
            levelFilter === 'warning'
              ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/30'
              : 'border-border bg-card hover:border-yellow-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Warnings</span>
            <AlertCircle className="w-4 h-4 text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
            {warningCount}
          </p>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 bg-card border border-border rounded-lg">
        {/* Search */}
        <div className="flex-1 min-w-64">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Service Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="bg-muted border border-border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All Services</option>
            {services.map((service) => (
              <option key={service.name} value={service.name}>
                {service.name}
              </option>
            ))}
          </select>
        </div>

        {/* Limit */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Show:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-muted border border-border rounded-lg px-3 py-2 text-sm"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>

        {/* Clear Filters */}
        {(serviceFilter || levelFilter || searchQuery) && (
          <button
            onClick={() => {
              setServiceFilter('');
              setLevelFilter('');
              setSearchQuery('');
            }}
            className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results count */}
      {filteredLogs.length !== logs.length && (
        <p className="text-sm text-muted-foreground">
          Showing {filteredLogs.length} of {logs.length} logs
        </p>
      )}

      {/* Error Logs Table */}
      <ErrorLogsTable logs={filteredLogs} isLoading={isLoading} />

      {/* Load More */}
      {hasMore && (
        <div className="text-center">
          <button
            onClick={() => setLimit((prev) => prev + 50)}
            className="px-4 py-2 text-sm text-primary hover:underline"
          >
            Load more logs...
          </button>
        </div>
      )}
    </div>
  );
}
