/**
 * ServicesGrid Component
 *
 * Displays a grid of all services with their status.
 */

import { Server, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { ServiceStatusCard } from './ServiceStatusCard';
import type { ServicesGridProps, ServiceStatus } from '../types';

/**
 * Sort services by health status (unhealthy first, then degraded, then healthy)
 */
function sortServices(services: ServiceStatus[]): ServiceStatus[] {
  return [...services].sort((a, b) => {
    const getPriority = (status: string) => {
      switch (status) {
        case 'unhealthy':
          return 1;
        case 'degraded':
          return 2;
        case 'unknown':
          return 3;
        case 'healthy':
          return 4;
        default:
          return 5;
      }
    };
    return getPriority(a.status) - getPriority(b.status);
  });
}

export function ServicesGrid({
  services,
  isLoading,
  onServiceClick,
}: ServicesGridProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 bg-muted rounded w-32 animate-pulse" />
          <div className="h-4 bg-muted rounded w-48 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="h-32 bg-muted rounded-lg animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  const sortedServices = sortServices(services);

  // Count by status
  const healthyCount = services.filter((s) => s.status === 'healthy').length;
  const degradedCount = services.filter((s) => s.status === 'degraded').length;
  const unhealthyCount = services.filter((s) => s.status === 'unhealthy').length;

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Services</h3>
          <span className="text-sm text-muted-foreground">
            ({services.length} total)
          </span>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle className="w-3 h-3" />
            {healthyCount} healthy
          </span>
          {degradedCount > 0 && (
            <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
              <AlertTriangle className="w-3 h-3" />
              {degradedCount} degraded
            </span>
          )}
          {unhealthyCount > 0 && (
            <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
              <XCircle className="w-3 h-3" />
              {unhealthyCount} unhealthy
            </span>
          )}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {sortedServices.map((service) => (
          <ServiceStatusCard
            key={service.name}
            service={service}
            onClick={onServiceClick ? () => onServiceClick(service.name) : undefined}
          />
        ))}
      </div>

      {/* Empty State */}
      {services.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Server className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No services found</p>
        </div>
      )}
    </div>
  );
}
