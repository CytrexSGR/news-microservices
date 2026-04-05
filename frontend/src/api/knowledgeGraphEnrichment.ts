/**
 * Knowledge Graph Enrichment API Client
 *
 * Provides functions for manual Knowledge Graph enrichment.
 */

import axios from 'axios'

const KG_API_URL = import.meta.env.VITE_KG_API_URL || 'http://localhost:8111'

export interface EnrichmentStats {
  total_not_applicable: number
  total_related_to: number
  enrichment_potential: number
  total_relationships: number
  percentage_needs_enrichment: number
  top_entity_type_patterns: Array<{
    pattern: string
    count: number
  }>
}

export interface EnrichmentCandidate {
  entity1: string
  entity1_type: string
  entity2: string
  entity2_type: string
  current_relationship: string
  occurrence_count: number
  suggested_tools: string[]
  context_samples: string[]
}

export interface EnrichmentAnalysisResult {
  candidates: EnrichmentCandidate[]
  summary: {
    total_candidates: number
    by_entity_type: Record<string, number>
    by_relationship: Record<string, number>
    top_patterns: Array<{
      pattern: string
      count: number
    }>
  }
}

export interface ToolExecutionResult {
  tool: string
  success: boolean
  data?: {
    article_title?: string
    article_url?: string
    extract?: string
    infobox_fields?: number
    categories?: string[]
  }
  suggestions?: Array<{
    relationship_type: string
    confidence: number
    evidence: string
    source: string
  }>
  error?: string
}

export interface ApplyEnrichmentResult {
  updated_count: number
  relationship_exists: boolean
  message: string
  new_relationship_type?: string
  entities?: {
    entity1: string
    entity2: string
  }
}

/**
 * Get enrichment statistics
 */
export const getEnrichmentStats = async (): Promise<EnrichmentStats> => {
  const response = await axios.get(`${KG_API_URL}/api/v1/graph/admin/enrichment/stats`)
  return response.data
}

/**
 * Analyze NOT_APPLICABLE relationships for enrichment opportunities
 */
export const analyzeForEnrichment = async (params: {
  analysis_type?: string
  limit?: number
  min_occurrence?: number
}): Promise<EnrichmentAnalysisResult> => {
  const response = await axios.post(`${KG_API_URL}/api/v1/graph/admin/enrichment/analyze`, {
    analysis_type: params.analysis_type || 'not_applicable_relationships',
    limit: params.limit || 100,
    min_occurrence: params.min_occurrence || 5
  })
  return response.data
}

/**
 * Execute enrichment tool (Wikipedia, Research, Google Deep Research)
 */
export const executeEnrichmentTool = async (params: {
  tool: string
  entity1: string
  entity2: string
  language?: string
}): Promise<ToolExecutionResult> => {
  const response = await axios.post(`${KG_API_URL}/api/v1/graph/admin/enrichment/execute-tool`, {
    tool: params.tool,
    entity1: params.entity1,
    entity2: params.entity2,
    language: params.language || 'de'
  })
  return response.data
}

/**
 * Apply enrichment to Knowledge Graph
 */
export const applyEnrichment = async (params: {
  entity1: string
  entity2: string
  new_relationship_type: string
  confidence: number
  evidence: string
  source?: string
}): Promise<ApplyEnrichmentResult> => {
  const response = await axios.post(`${KG_API_URL}/api/v1/graph/admin/enrichment/apply`, {
    entity1: params.entity1,
    entity2: params.entity2,
    new_relationship_type: params.new_relationship_type,
    confidence: params.confidence,
    evidence: params.evidence,
    source: params.source || 'manual_enrichment'
  })
  return response.data
}
