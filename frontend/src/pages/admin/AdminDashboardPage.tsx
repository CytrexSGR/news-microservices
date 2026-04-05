/**
 * Admin Dashboard Page
 *
 * System Health Dashboard for monitoring all services.
 * Provides a comprehensive overview of:
 * - Overall system health percentage
 * - Service status grid with health indicators
 * - Container resource usage
 * - Recent health alerts
 *
 * Features:
 * - Auto-refresh every 30 seconds
 * - Color-coded health indicators (green/yellow/red)
 * - Real-time container metrics (CPU, memory, PIDs)
 * - Alert timeline with severity levels
 */

import { useState, useEffect } from 'react';
import { Activity, RefreshCw, Clock, Settings } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  useSystemHealth,
  HealthSummaryCard,
  ServiceHealthGrid,
  ContainerStatusList,
  HealthAlertsList,
} from '@/features/admin/health';

type ViewMode = 'grid' | 'list';

export function AdminDashboardPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const {
    summary,
    containers,
    alerts,
    isLoading,
    isFetching,
    refetch,
  } = useSystemHealth({
    autoRefresh,
    refetchInterval: 30000, // 30 seconds
    alertLimit: 20,
  });

  // Track last update time
  useEffect(() => {
    if (!isFetching && summary) {
      setLastUpdated(new Date());
    }
  }, [isFetching, summary]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Activity className={`h-6 w-6 text-primary ${isFetching ? 'animate-spin' : ''}`} />
            System Health Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Real-time monitoring of all services and containers
          </p>
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex rounded-lg border border-border overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 text-sm ${
                viewMode === 'grid'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 text-sm ${
                viewMode === 'list'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              List
            </button>
          </div>

          {/* Auto-refresh Toggle */}
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${autoRefresh && isFetching ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto (30s)' : 'Paused'}
          </Button>

          {/* Manual Refresh */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <HealthSummaryCard summary={summary} isLoading={isLoading} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Services / Containers - 2 columns */}
        <div className="lg:col-span-2">
          {viewMode === 'grid' ? (
            <ServiceHealthGrid containers={containers} isLoading={isLoading} />
          ) : (
            <ContainerStatusList containers={containers} isLoading={isLoading} />
          )}
        </div>

        {/* Alerts - 1 column */}
        <div className="lg:col-span-1">
          <HealthAlertsList alerts={alerts} isLoading={isLoading} limit={10} />
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-xs text-muted-foreground text-center py-4 border-t border-border">
        <p>
          Monitoring {containers.length} containers via analytics-service (port 8107)
          {autoRefresh && ' • Auto-refreshing every 30 seconds'}
        </p>
      </div>
    </div>
  );
}
