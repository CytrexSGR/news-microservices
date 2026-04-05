/**
 * Entity Canonicalization Feature Module
 *
 * Provides entity canonicalization capabilities including:
 * - Single entity canonicalization
 * - Batch entity processing with CSV support
 * - Entity cluster browsing
 * - Canonicalization statistics and metrics
 * - Entity alias management
 * - Merge history tracking
 *
 * API Hooks:
 * - useCanonicalizeEntity - Canonicalize a single entity
 * - useEntityClusters - Fetch entity clusters by type
 * - useBatchCanonicalize - Batch entity canonicalization
 * - useCanonStats - Canonicalization statistics
 * - useAsyncJobStatus - Poll async job status
 * - useAsyncJobResult - Fetch completed job results
 * - useEntityAliases - Get entity aliases
 * - useEntityHistory - Fetch merge history
 *
 * Components:
 * - EntityCanonForm - Single entity form
 * - EntityClustersTable - Clusters display table
 * - BatchCanonForm - Batch upload form
 * - CanonStatsCard - Statistics card
 * - AsyncJobStatusView - Job progress view
 * - AsyncJobResultView - Job results display
 * - EntityAliasesTable - Aliases table
 * - EntityHistoryTimeline - Merge history timeline
 *
 * Pages:
 * - EntitiesPage - Main canonicalization page
 * - EntityClustersPage - Browse clusters by type
 * - BatchCanonPage - Batch processing page
 * - EntityDashboardPage - Stats dashboard
 * - EntityDetailsPage - Entity detail view
 */

// Types
export * from './types';

// API hooks
export * from './api';

// Components
export * from './components';

// Pages
export * from './pages';
