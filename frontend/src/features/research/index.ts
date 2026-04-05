/**
 * Research Feature Module Export
 *
 * Provides AI-powered research functionality using Perplexity API
 * Backend: research-service (port 8103)
 *
 * Routes:
 * - /research - Dashboard with form
 * - /research/history - Query history table
 * - /research/:id - Single result view
 * - /research/stats - Usage statistics
 */

// Types
export * from './types';

// API & Hooks
export * from './api';

// Components
export * from './components';

// Pages
export * from './pages';

// Routes
export { ResearchRoutes, researchRouteConfig } from './routes';

// Layout
export { ResearchLayout } from './ResearchLayout';
