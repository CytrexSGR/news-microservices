/**
 * ServiceDetailPage
 *
 * Displays detailed information about a single service.
 */

import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Server,
  RefreshCw,
  Clock,
  Cpu,
  MemoryStick,
  Activity,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { useServiceStatus } from '../api/useServiceStatus';
import { useServiceMetrics } from '../api/useServiceMetrics';
import { HealthBadge, PerformanceChart, MetricsSparkline } from '../components';

/**
 * Format uptime seconds
 */
function formatUptime(seconds?: number): string {
  if (!seconds) return '--';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);

  return parts.join(' ');
}

export function ServiceDetailPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();

  const serviceName = decodeURIComponent(name || '');

  const { data: service, isLoading, isFetching, invalidate } = useServiceStatus({
    serviceName,
    autoRefresh: true,
    refetchInterval: 30000,
  });

  const {
    data: metrics,
    isLoading: metricsLoading,
  } = useServiceMetrics({
    serviceName,
    autoRefresh: true,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-muted rounded w-64 animate-pulse" />
        <div className="h-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!service) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
        <h2 className="text-xl font-semibold text-foreground mb-2">Service Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The service "{serviceName}" could not be found.
        </p>
        <Link
          to="/admin/monitoring/services"
          className="text-primary hover:underline"
        >
          Back to Services
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{serviceName}</h1>
              <HealthBadge status={service.status} />
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {service.description || `${service.type} service`}
              {service.port && ` on port ${service.port}`}
            </p>
          </div>
        </div>
        <button
          onClick={invalidate}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Status Card */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-primary/10">
            <Server className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Service Status</h3>
            <p className="text-xs text-muted-foreground">
              Last check: {new Date(service.last_check).toLocaleString('de-DE')}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Clock className="w-4 h-4" />
              <span className="text-sm">Uptime</span>
            </div>
            <p className="text-xl font-bold text-foreground">
              {formatUptime(service.uptime_seconds)}
            </p>
          </div>

          <div className="p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Cpu className="w-4 h-4" />
              <span className="text-sm">CPU</span>
            </div>
            <p className="text-xl font-bold text-foreground">
              {service.metrics?.cpu_percent.toFixed(1) ?? '--'}%
            </p>
          </div>

          <div className="p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <MemoryStick className="w-4 h-4" />
              <span className="text-sm">Memory</span>
            </div>
            <p className="text-xl font-bold text-foreground">
              {service.metrics?.memory_mb.toFixed(0) ?? '--'} MB
            </p>
          </div>

          <div className="p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Activity className="w-4 h-4" />
              <span className="text-sm">Requests/min</span>
            </div>
            <p className="text-xl font-bold text-foreground">
              {service.metrics?.requests_per_minute ?? '--'}
            </p>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      {metrics && (
        <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
          <h3 className="font-semibold text-foreground mb-6">Performance Metrics</h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">Avg Response Time</p>
              <p className="text-xl font-bold text-foreground">
                {metrics.avg_response_time_ms.toFixed(1)} ms
              </p>
            </div>

            <div className="p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">Error Rate</p>
              <p
                className={`text-xl font-bold ${
                  metrics.error_rate_percent > 1
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-foreground'
                }`}
              >
                {metrics.error_rate_percent.toFixed(2)}%
              </p>
            </div>

            <div className="p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">P95 Latency</p>
              <p className="text-xl font-bold text-foreground">
                {metrics.p95_latency_ms?.toFixed(1) ?? '--'} ms
              </p>
            </div>

            <div className="p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground mb-1">P99 Latency</p>
              <p className="text-xl font-bold text-foreground">
                {metrics.p99_latency_ms?.toFixed(1) ?? '--'} ms
              </p>
            </div>
          </div>

          {/* Charts */}
          {metrics.requests_over_time && metrics.requests_over_time.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <PerformanceChart
                data={metrics.requests_over_time}
                title="Requests Over Time"
                color="#3b82f6"
                unit="req"
              />
              {metrics.errors_over_time && (
                <PerformanceChart
                  data={metrics.errors_over_time}
                  title="Errors Over Time"
                  color="#ef4444"
                  unit="err"
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Service Info */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <h3 className="font-semibold text-foreground mb-4">Service Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Name:</span>{' '}
            <span className="text-foreground font-medium">{service.name}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Type:</span>{' '}
            <span className="text-foreground font-medium capitalize">{service.type}</span>
          </div>
          {service.port && (
            <div>
              <span className="text-muted-foreground">Port:</span>{' '}
              <span className="text-foreground font-medium">{service.port}</span>
            </div>
          )}
          {service.version && (
            <div>
              <span className="text-muted-foreground">Version:</span>{' '}
              <span className="text-foreground font-medium">{service.version}</span>
            </div>
          )}
          {service.container_name && (
            <div>
              <span className="text-muted-foreground">Container:</span>{' '}
              <span className="text-foreground font-medium font-mono text-xs">
                {service.container_name}
              </span>
            </div>
          )}
          {service.endpoint && (
            <div className="col-span-2">
              <span className="text-muted-foreground">Endpoint:</span>{' '}
              <a
                href={service.endpoint}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-1"
              >
                {service.endpoint}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
