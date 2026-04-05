/**
 * Monitoring Routes
 *
 * Route configuration for the monitoring feature.
 * All routes are under /admin/monitoring/* and require admin access.
 */

import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import { MonitoringLayout } from './MonitoringLayout';

// Lazy load pages for code splitting
const MonitoringDashboard = lazy(() =>
  import('./pages/MonitoringDashboard').then((m) => ({ default: m.MonitoringDashboard }))
);
const ServicesPage = lazy(() =>
  import('./pages/ServicesPage').then((m) => ({ default: m.ServicesPage }))
);
const ServiceDetailPage = lazy(() =>
  import('./pages/ServiceDetailPage').then((m) => ({ default: m.ServiceDetailPage }))
);
const ErrorLogsPage = lazy(() =>
  import('./pages/ErrorLogsPage').then((m) => ({ default: m.ErrorLogsPage }))
);
const PerformancePage = lazy(() =>
  import('./pages/PerformancePage').then((m) => ({ default: m.PerformancePage }))
);
const InfrastructurePage = lazy(() =>
  import('./pages/InfrastructurePage').then((m) => ({ default: m.InfrastructurePage }))
);

/**
 * Loading fallback component
 */
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}

/**
 * Wrap page component with Suspense
 */
function withSuspense(Component: React.ComponentType) {
  return (
    <Suspense fallback={<PageLoader />}>
      <Component />
    </Suspense>
  );
}

/**
 * Monitoring feature routes
 *
 * Routes:
 * - /admin/monitoring - Dashboard overview
 * - /admin/monitoring/services - All services list
 * - /admin/monitoring/services/:name - Single service detail
 * - /admin/monitoring/errors - Error logs
 * - /admin/monitoring/performance - Performance metrics
 * - /admin/monitoring/infrastructure - Queues/DB/Cache
 */
export const monitoringRoutes: RouteObject = {
  path: 'monitoring',
  element: <MonitoringLayout />,
  children: [
    {
      index: true,
      element: withSuspense(MonitoringDashboard),
    },
    {
      path: 'services',
      element: withSuspense(ServicesPage),
    },
    {
      path: 'services/:name',
      element: withSuspense(ServiceDetailPage),
    },
    {
      path: 'errors',
      element: withSuspense(ErrorLogsPage),
    },
    {
      path: 'performance',
      element: withSuspense(PerformancePage),
    },
    {
      path: 'infrastructure',
      element: withSuspense(InfrastructurePage),
    },
  ],
};

/**
 * Export route path constants for navigation
 */
export const MONITORING_ROUTES = {
  DASHBOARD: '/admin/monitoring',
  SERVICES: '/admin/monitoring/services',
  SERVICE_DETAIL: (name: string) => `/admin/monitoring/services/${encodeURIComponent(name)}`,
  ERRORS: '/admin/monitoring/errors',
  PERFORMANCE: '/admin/monitoring/performance',
  INFRASTRUCTURE: '/admin/monitoring/infrastructure',
} as const;
