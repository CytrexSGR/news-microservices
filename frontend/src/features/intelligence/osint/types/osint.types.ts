/**
 * OSINT (Open Source Intelligence) Types
 * Based on osint-service API schemas
 */

// ============================================================================
// Enums and Category Types
// ============================================================================

export type OsintCategory =
  | 'social_media'
  | 'domain_analysis'
  | 'threat_intelligence'
  | 'network_analysis'
  | 'financial'
  | 'person'
  | 'organization';

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

export type ParameterType = 'string' | 'number' | 'boolean' | 'array';

// ============================================================================
// Template Types
// ============================================================================

export interface TemplateParameter {
  name: string;
  type: ParameterType;
  required: boolean;
  description: string;
  default?: unknown;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    enum?: string[];
  };
}

export interface OsintTemplate {
  name: string;
  category: OsintCategory;
  description: string;
  parameters: TemplateParameter[];
  output_schema: Record<string, unknown>;
  estimated_runtime_seconds: number;
  icon?: string;
  tags?: string[];
}

export interface OsintTemplatesResponse {
  templates: OsintTemplate[];
  total: number;
  timestamp: string;
}

// ============================================================================
// Instance Types
// ============================================================================

export interface OsintInstance {
  id: string;
  template_name: string;
  name: string;
  description?: string;
  parameters: Record<string, unknown>;
  schedule?: string;
  enabled: boolean;
  created_at: string;
  updated_at?: string;
  last_run?: string;
  next_run?: string;
  run_count?: number;
  last_status?: ExecutionStatus;
}

export interface OsintInstanceCreateRequest {
  template_name: string;
  name: string;
  description?: string;
  parameters: Record<string, unknown>;
  schedule?: string;
  enabled?: boolean;
}

export interface OsintInstanceUpdateRequest {
  name?: string;
  description?: string;
  parameters?: Record<string, unknown>;
  schedule?: string;
  enabled?: boolean;
}

export interface OsintInstancesResponse {
  instances: OsintInstance[];
  total: number;
  page: number;
  per_page: number;
  timestamp: string;
}

// ============================================================================
// Execution Types
// ============================================================================

export interface OsintExecution {
  id: string;
  instance_id: string;
  instance_name?: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  results?: Record<string, unknown>;
  error_message?: string;
  metadata?: {
    triggered_by?: 'manual' | 'schedule';
    retry_count?: number;
  };
}

export interface ExecuteOsintRequest {
  instance_id: string;
  parameters?: Record<string, unknown>;
}

export interface OsintExecutionResponse {
  execution: OsintExecution;
  timestamp: string;
}

// ============================================================================
// Alert Types
// ============================================================================

export interface OsintAlert {
  id: string;
  instance_id: string;
  instance_name?: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  created_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  metadata?: Record<string, unknown>;
}

export interface OsintAlertsResponse {
  alerts: OsintAlert[];
  total: number;
  page: number;
  per_page: number;
  timestamp: string;
}

export interface AlertStats {
  total: number;
  by_severity: Record<AlertSeverity, number>;
  unacknowledged: number;
  last_24h: number;
  last_7d: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface AcknowledgeAlertRequest {
  alert_id: string;
  comment?: string;
}

export interface AcknowledgeAlertResponse {
  success: boolean;
  alert_id: string;
  acknowledged_at: string;
  acknowledged_by: string;
}

// ============================================================================
// Pattern Detection Types
// ============================================================================

export interface PatternDetectionRequest {
  entity_ids?: string[];
  timeframe_days?: number;
  pattern_types?: string[];
  min_confidence?: number;
}

export interface DetectedPattern {
  type: string;
  confidence: number;
  entities: string[];
  description: string;
  evidence: PatternEvidence[];
  detected_at: string;
  risk_score?: number;
}

export interface PatternEvidence {
  source: string;
  content: string;
  timestamp: string;
  relevance: number;
}

export interface PatternDetectionResponse {
  patterns: DetectedPattern[];
  total: number;
  analysis_time_ms: number;
  timestamp: string;
}

// ============================================================================
// Graph Quality Types
// ============================================================================

export interface GraphQualityReport {
  total_nodes: number;
  total_edges: number;
  connectivity_score: number;
  orphan_nodes: number;
  duplicate_rate: number;
  completeness_score: number;
  freshness_score: number;
  recommendations: string[];
  breakdown: {
    by_entity_type: Record<string, number>;
    by_relationship_type: Record<string, number>;
  };
  last_updated: string;
}

// ============================================================================
// Utility Functions
// ============================================================================

export function getSeverityColor(severity: AlertSeverity): string {
  switch (severity) {
    case 'low':
      return 'text-green-500';
    case 'medium':
      return 'text-yellow-500';
    case 'high':
      return 'text-orange-500';
    case 'critical':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

export function getSeverityBgColor(severity: AlertSeverity): string {
  switch (severity) {
    case 'low':
      return 'bg-green-500/10';
    case 'medium':
      return 'bg-yellow-500/10';
    case 'high':
      return 'bg-orange-500/10';
    case 'critical':
      return 'bg-red-500/10';
    default:
      return 'bg-gray-500/10';
  }
}

export function getStatusColor(status: ExecutionStatus): string {
  switch (status) {
    case 'pending':
      return 'text-gray-500';
    case 'running':
      return 'text-blue-500';
    case 'completed':
      return 'text-green-500';
    case 'failed':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

export function getStatusBgColor(status: ExecutionStatus): string {
  switch (status) {
    case 'pending':
      return 'bg-gray-500/10';
    case 'running':
      return 'bg-blue-500/10';
    case 'completed':
      return 'bg-green-500/10';
    case 'failed':
      return 'bg-red-500/10';
    default:
      return 'bg-gray-500/10';
  }
}

export function getCategoryLabel(category: OsintCategory): string {
  const labels: Record<OsintCategory, string> = {
    social_media: 'Social Media',
    domain_analysis: 'Domain Analysis',
    threat_intelligence: 'Threat Intelligence',
    network_analysis: 'Network Analysis',
    financial: 'Financial',
    person: 'Person',
    organization: 'Organization',
  };
  return labels[category] || category;
}

export function getCategoryIcon(category: OsintCategory): string {
  const icons: Record<OsintCategory, string> = {
    social_media: 'Share2',
    domain_analysis: 'Globe',
    threat_intelligence: 'Shield',
    network_analysis: 'Network',
    financial: 'DollarSign',
    person: 'User',
    organization: 'Building',
  };
  return icons[category] || 'FileSearch';
}
