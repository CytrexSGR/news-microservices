/**
 * Ontology Proposals API Client
 *
 * API client for OSS (Ontology Suggestion System) proposals management.
 * Handles proposal listing, details, acceptance/rejection, and history tracking.
 */

import axios from 'axios';

// API Configuration - Updated for CORS compatibility
const API_BASE_URL = import.meta.env.VITE_ONTOLOGY_PROPOSALS_API_URL || 'http://localhost:8109';

// =============================================================================
// Types
// =============================================================================

export type ChangeType =
  | 'NEW_ENTITY_TYPE'
  | 'NEW_RELATIONSHIP_TYPE'
  | 'MODIFY_ENTITY_TYPE'
  | 'MODIFY_RELATIONSHIP_TYPE'
  | 'FLAG_INCONSISTENCY';

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type ProposalStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'IMPLEMENTED';

export interface Evidence {
  example_id: string;
  example_type: string;
  properties?: Record<string, any>;
  context?: string;
  frequency?: number;
}

export interface ImpactAnalysis {
  affected_entities_count?: number;
  affected_relationships_count?: number;
  breaking_change: boolean;
  migration_complexity: string;
  estimated_effort_hours: number;
  benefits: string[];
  risks: string[];
}

export interface OntologyProposal {
  id: number;
  proposal_id: string;
  change_type: ChangeType;
  severity: Severity;
  title: string;
  description: string;
  definition?: string | null;
  evidence: Evidence[];
  pattern_query?: string;
  occurrence_count: number;
  confidence: number;
  confidence_factors?: Record<string, number> | null;
  validation_checks?: string[] | null;
  impact_analysis: ImpactAnalysis;
  oss_version: string;
  related_proposals?: string[] | null;
  tags?: string[] | null;
  status: ProposalStatus;
  created_at: string;
  updated_at: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  implementation_notes?: string | null;
}

export interface ProposalsListResponse {
  proposals: OntologyProposal[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProposalDetailResponse {
  proposal: OntologyProposal;
}

export interface UpdateProposalRequest {
  status?: ProposalStatus;
  reviewed_by?: string;
  rejection_reason?: string;
  implementation_notes?: string;
}

export interface ProposalStatistics {
  total_proposals: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
  implemented_count: number;
  by_severity: Record<Severity, number>;
  by_change_type: Record<ChangeType, number>;
  avg_confidence: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get list of all proposals with optional filtering
 */
export async function getProposals(params?: {
  status?: ProposalStatus;
  severity?: Severity;
  change_type?: ChangeType;
  page?: number;
  page_size?: number;
}): Promise<ProposalsListResponse> {
  const response = await axios.get(`${API_BASE_URL}/api/v1/ontology/proposals`, { params });
  return response.data;
}

/**
 * Get single proposal by ID
 */
export async function getProposal(id: number): Promise<OntologyProposal> {
  const response = await axios.get(`${API_BASE_URL}/api/v1/ontology/proposals/${id}`);
  return response.data;
}

/**
 * Update proposal (accept, reject, or implement)
 */
export async function updateProposal(
  id: number,
  data: UpdateProposalRequest
): Promise<OntologyProposal> {
  // Backend expects query parameters, not JSON body
  const response = await axios.put(
    `${API_BASE_URL}/api/v1/ontology/proposals/${id}`,
    null,
    { params: data }
  );
  return response.data;
}

/**
 * Accept a proposal
 */
export async function acceptProposal(
  id: number,
  reviewed_by: string,
  implementation_notes?: string
): Promise<OntologyProposal> {
  return updateProposal(id, {
    status: 'ACCEPTED',
    reviewed_by,
    implementation_notes,
  });
}

/**
 * Reject a proposal
 */
export async function rejectProposal(
  id: number,
  reviewed_by: string,
  rejection_reason: string
): Promise<OntologyProposal> {
  return updateProposal(id, {
    status: 'REJECTED',
    reviewed_by,
    rejection_reason,
  });
}

/**
 * Mark proposal as implemented
 */
export async function markProposalImplemented(
  id: number,
  implementation_notes: string
): Promise<ProposalDetailResponse> {
  return updateProposal(id, {
    status: 'IMPLEMENTED',
    implementation_notes,
  });
}

/**
 * Get proposal statistics
 */
export async function getProposalStatistics(): Promise<ProposalStatistics> {
  const response = await axios.get(`${API_BASE_URL}/api/v1/ontology/proposals/statistics`);
  return response.data;
}

/**
 * Implement an accepted proposal (execute Cypher scripts)
 */
export async function implementProposal(id: number): Promise<{
  success: boolean;
  proposal_id: string;
  results: any;
  message: string;
}> {
  const response = await axios.post(`${API_BASE_URL}/api/v1/ontology/proposals/${id}/implement`);
  return response.data;
}

/**
 * Delete a proposal
 */
export async function deleteProposal(id: number): Promise<void> {
  await axios.delete(`${API_BASE_URL}/api/v1/ontology/proposals/${id}`);
}
