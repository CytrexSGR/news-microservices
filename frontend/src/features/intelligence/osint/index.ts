/**
 * OSINT Feature - Main Export
 *
 * Open Source Intelligence monitoring and analysis feature
 *
 * This feature provides:
 * - Pattern detection across entities and relationships
 * - Graph quality analysis and recommendations
 * - OSINT template management
 * - Instance lifecycle management (create, read, update, delete)
 * - Execution and result tracking
 * - Alert monitoring and acknowledgement
 *
 * @example
 * ```tsx
 * // Import pages for routing
 * import { OsintDashboardPage, TemplatesPage, AlertsPage } from '@/features/intelligence/osint';
 *
 * // Import hooks for custom components
 * import { useOsintTemplates, useAlertStats } from '@/features/intelligence/osint/api';
 *
 * // Import components for composition
 * import { PatternDetectionPanel, AlertStatsCard } from '@/features/intelligence/osint/components';
 *
 * // Import types for type-safety
 * import type { OsintTemplate, AlertSeverity } from '@/features/intelligence/osint/types/osint.types';
 * ```
 */

// Re-export everything from sub-modules
export * from './types/osint.types';
export * from './api';
export * from './components';
export * from './pages';
