/**
 * ServicesPage
 *
 * Displays all services with detailed status information.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Server,
  RefreshCw,
  Filter,
  Search,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { useServicesList } from '../api/useServicesList';
import { ServicesGrid, HealthBadge } from '../components';
import type { HealthStatus, ServiceType } from '../types';

export function ServicesPage() {
  const navigate = useNavigate();
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [statusFilter, setStatusFilter] = useState<HealthStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<ServiceType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const { services, isLoading, isFetching, invalidate } = useServicesList({
    autoRefresh,
    refetchInterval: 30000,
  });

  // Filter services
  const filteredServices = services.filter((service) => {
    if (statusFilter !== 'all' && service.status !== statusFilter) return false;
    if (typeFilter !== 'all' && service.type !== typeFilter) return false;
    if (searchQuery && !service.name.toLowerCase().includes(searchQuery.toLowerCase()))
      return false;
    return true;
  });

  // Count by status
  const statusCounts = {
    healthy: services.filter((s) => s.status === 'healthy').length,
    degraded: services.filter((s) => s.status === 'degraded').length,
    unhealthy: services.filter((s) => s.status === 'unhealthy').length,
    unknown: services.filter((s) => s.status === 'unknown').length,
  };

  const handleServiceClick = (serviceName: string) => {
    navigate(`/admin/monitoring/services/${encodeURIComponent(serviceName)}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Services</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {services.length} services | {statusCounts.healthy} healthy
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

      {/* Status Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button
          onClick={() => setStatusFilter(statusFilter === 'healthy' ? 'all' : 'healthy')}
          className={`p-4 rounded-lg border transition-all ${
            statusFilter === 'healthy'
              ? 'border-green-500 bg-green-50 dark:bg-green-950/30'
              : 'border-border bg-card hover:border-green-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Healthy</span>
            <CheckCircle className="w-4 h-4 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            {statusCounts.healthy}
          </p>
        </button>

        <button
          onClick={() => setStatusFilter(statusFilter === 'degraded' ? 'all' : 'degraded')}
          className={`p-4 rounded-lg border transition-all ${
            statusFilter === 'degraded'
              ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/30'
              : 'border-border bg-card hover:border-yellow-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Degraded</span>
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">
            {statusCounts.degraded}
          </p>
        </button>

        <button
          onClick={() => setStatusFilter(statusFilter === 'unhealthy' ? 'all' : 'unhealthy')}
          className={`p-4 rounded-lg border transition-all ${
            statusFilter === 'unhealthy'
              ? 'border-red-500 bg-red-50 dark:bg-red-950/30'
              : 'border-border bg-card hover:border-red-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Unhealthy</span>
            <XCircle className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            {statusCounts.unhealthy}
          </p>
        </button>

        <button
          onClick={() => setStatusFilter('all')}
          className={`p-4 rounded-lg border transition-all ${
            statusFilter === 'all'
              ? 'border-primary bg-primary/10'
              : 'border-border bg-card hover:border-primary/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Total</span>
            <Server className="w-4 h-4 text-primary" />
          </div>
          <p className="text-2xl font-bold text-foreground mt-1">{services.length}</p>
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
              placeholder="Search services..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ServiceType | 'all')}
            className="bg-muted border border-border rounded-lg px-3 py-2 text-sm"
          >
            <option value="all">All Types</option>
            <option value="api">API</option>
            <option value="worker">Worker</option>
            <option value="database">Database</option>
            <option value="queue">Queue</option>
            <option value="cache">Cache</option>
          </select>
        </div>

        {/* Clear Filters */}
        {(statusFilter !== 'all' || typeFilter !== 'all' || searchQuery) && (
          <button
            onClick={() => {
              setStatusFilter('all');
              setTypeFilter('all');
              setSearchQuery('');
            }}
            className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results count */}
      {filteredServices.length !== services.length && (
        <p className="text-sm text-muted-foreground">
          Showing {filteredServices.length} of {services.length} services
        </p>
      )}

      {/* Services Grid */}
      <ServicesGrid
        services={filteredServices}
        isLoading={isLoading}
        onServiceClick={handleServiceClick}
      />
    </div>
  );
}
