/**
 * PerformancePage
 *
 * Displays system-wide performance metrics and analysis.
 */

import { useState } from 'react';
import {
  Activity,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  Cpu,
  MemoryStick,
} from 'lucide-react';
import { usePerformanceMetrics } from '../api/usePerformanceMetrics';
import { PerformanceChart, HealthBadge } from '../components';

/**
 * Trend indicator component
 */
function TrendIndicator({ value, invert = false }: { value: number; invert?: boolean }) {
  const isPositive = invert ? value < 0 : value > 0;
  const isNegative = invert ? value > 0 : value < 0;

  if (Math.abs(value) < 0.01) {
    return <span className="text-muted-foreground text-xs">--</span>;
  }

  return (
    <span
      className={`flex items-center gap-1 text-xs ${
        isPositive
          ? 'text-green-600 dark:text-green-400'
          : isNegative
          ? 'text-red-600 dark:text-red-400'
          : 'text-muted-foreground'
      }`}
    >
      {value > 0 ? (
        <TrendingUp className="w-3 h-3" />
      ) : (
        <TrendingDown className="w-3 h-3" />
      )}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}

export function PerformancePage() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { data: metrics, isLoading, isFetching, invalidate } = usePerformanceMetrics({
    autoRefresh,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-muted rounded w-64 animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-64 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Performance</h1>
          <p className="text-sm text-muted-foreground mt-1">
            System-wide performance metrics and analysis
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

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Average Latency */}
        <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="w-4 h-4" />
              <span className="text-sm">Avg Latency</span>
            </div>
            {metrics?.trends && (
              <TrendIndicator value={metrics.trends.latency_trend} invert />
            )}
          </div>
          <p
            className={`text-2xl font-bold ${
              (metrics?.avg_latency_ms ?? 0) > 100
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-foreground'
            }`}
          >
            {metrics?.avg_latency_ms.toFixed(1) ?? '--'} ms
          </p>
        </div>

        {/* Total RPS */}
        <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Activity className="w-4 h-4" />
              <span className="text-sm">Total RPS</span>
            </div>
            {metrics?.trends && <TrendIndicator value={metrics.trends.rps_trend} />}
          </div>
          <p className="text-2xl font-bold text-foreground">
            {metrics?.total_rps.toFixed(1) ?? '--'}
          </p>
        </div>

        {/* Error Rate */}
        <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm">Error Rate</span>
            </div>
            {metrics?.trends && (
              <TrendIndicator value={metrics.trends.error_rate_trend} invert />
            )}
          </div>
          <p
            className={`text-2xl font-bold ${
              (metrics?.total_error_rate_percent ?? 0) > 1
                ? 'text-red-600 dark:text-red-400'
                : 'text-foreground'
            }`}
          >
            {metrics?.total_error_rate_percent.toFixed(2) ?? '--'}%
          </p>
        </div>

        {/* Resource Usage */}
        <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Cpu className="w-4 h-4" />
              <span className="text-sm">Resources</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-xl font-bold text-foreground">
              {metrics?.total_cpu_percent.toFixed(1) ?? '--'}%
            </p>
            <span className="text-xs text-muted-foreground">CPU</span>
            <span className="text-muted-foreground">|</span>
            <p className="text-xl font-bold text-foreground">
              {((metrics?.total_memory_mb ?? 0) / 1024).toFixed(1)}
            </p>
            <span className="text-xs text-muted-foreground">GB</span>
          </div>
        </div>
      </div>

      {/* Service Performance Table */}
      {metrics?.services && metrics.services.length > 0 && (
        <div className="bg-card border border-border rounded-lg shadow-sm">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-foreground">Service Performance</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-3 text-sm font-medium text-muted-foreground">
                    Service
                  </th>
                  <th className="text-left p-3 text-sm font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="text-right p-3 text-sm font-medium text-muted-foreground">
                    Avg Latency
                  </th>
                  <th className="text-right p-3 text-sm font-medium text-muted-foreground">
                    RPS
                  </th>
                  <th className="text-right p-3 text-sm font-medium text-muted-foreground">
                    Error Rate
                  </th>
                </tr>
              </thead>
              <tbody>
                {metrics.services.map((service) => (
                  <tr
                    key={service.name}
                    className="border-b border-border last:border-b-0 hover:bg-muted/30"
                  >
                    <td className="p-3 text-sm font-medium text-foreground">
                      {service.name}
                    </td>
                    <td className="p-3">
                      <HealthBadge status={service.status} size="sm" />
                    </td>
                    <td
                      className={`p-3 text-sm text-right ${
                        service.avg_latency_ms > 100
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-foreground'
                      }`}
                    >
                      {service.avg_latency_ms.toFixed(1)} ms
                    </td>
                    <td className="p-3 text-sm text-right text-foreground">
                      {service.rps.toFixed(2)}
                    </td>
                    <td
                      className={`p-3 text-sm text-right ${
                        service.error_rate_percent > 1
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-foreground'
                      }`}
                    >
                      {service.error_rate_percent.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trend Period Info */}
      {metrics?.trends && (
        <div className="text-center text-xs text-muted-foreground">
          Trends calculated over {metrics.trends.period}
        </div>
      )}
    </div>
  );
}
