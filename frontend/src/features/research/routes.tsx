/**
 * Research Feature Routes
 *
 * Route configuration for the research feature:
 * - /research - Dashboard with form
 * - /research/history - Query history table
 * - /research/:id - Single result view
 * - /research/stats - Usage statistics
 */

import { lazy } from 'react';
import { Route, Routes } from 'react-router-dom';
import { ResearchLayout } from './ResearchLayout';

// Lazy load pages for code splitting
const ResearchDashboard = lazy(() =>
  import('./pages/ResearchDashboard').then((m) => ({
    default: m.ResearchDashboard,
  }))
);

const ResearchHistoryPage = lazy(() =>
  import('./pages/ResearchHistoryPage').then((m) => ({
    default: m.ResearchHistoryPage,
  }))
);

const ResearchResultPage = lazy(() =>
  import('./pages/ResearchResultPage').then((m) => ({
    default: m.ResearchResultPage,
  }))
);

const ResearchStatsPage = lazy(() =>
  import('./pages/ResearchStatsPage').then((m) => ({
    default: m.ResearchStatsPage,
  }))
);

/**
 * Research Routes Component
 *
 * Use this component to render research routes within the app:
 *
 * ```tsx
 * <Route path="/research/*" element={<ResearchRoutes />} />
 * ```
 */
export function ResearchRoutes() {
  return (
    <Routes>
      <Route element={<ResearchLayout />}>
        <Route index element={<ResearchDashboard />} />
        <Route path="history" element={<ResearchHistoryPage />} />
        <Route path="stats" element={<ResearchStatsPage />} />
        <Route path=":id" element={<ResearchResultPage />} />
      </Route>
    </Routes>
  );
}

/**
 * Route definitions for external use (e.g., App.tsx)
 */
export const researchRouteConfig = [
  { path: '/research', element: ResearchDashboard },
  { path: '/research/history', element: ResearchHistoryPage },
  { path: '/research/stats', element: ResearchStatsPage },
  { path: '/research/:id', element: ResearchResultPage },
];
