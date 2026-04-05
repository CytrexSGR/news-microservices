/**
 * OSINT API Hooks - Barrel Export
 *
 * All API hooks for OSINT (Open Source Intelligence) feature
 */

// Pattern Detection & Graph Quality
export { useDetectPatterns } from './useDetectPatterns';
export { useGraphQuality } from './useGraphQuality';

// Templates
export { useOsintTemplates, useOsintTemplatesByCategory } from './useOsintTemplates';
export { useOsintTemplate } from './useOsintTemplate';

// Instances (CRUD)
export { useOsintInstances, useOsintInstance } from './useOsintInstances';
export { useCreateOsintInstance } from './useCreateOsintInstance';
export { useUpdateOsintInstance } from './useUpdateOsintInstance';
export { useDeleteOsintInstance } from './useDeleteOsintInstance';

// Execution
export { useExecuteOsint } from './useExecuteOsint';
export { useOsintExecution, useOsintExecutionPolling } from './useOsintExecution';

// Alerts
export { useOsintAlerts, useUnacknowledgedAlertsCount } from './useOsintAlerts';
export { useAlertStats } from './useAlertStats';
export { useAcknowledgeAlert } from './useAcknowledgeAlert';
