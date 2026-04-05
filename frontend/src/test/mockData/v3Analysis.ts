/**
 * Mock data for V3 Analysis testing
 *
 * Provides realistic test data that matches the V3 API contract.
 * Data structure validated against validateV3Analysis.ts validators.
 */

import type {
  TriageDecision,
  Tier1Results,
  Tier2Results,
  V3AnalysisData,
} from '@/features/feeds/types/analysisV3';

/**
 * Valid Tier0 triage decision (article kept for analysis)
 */
export const mockTier0Kept: TriageDecision = {
  PriorityScore: 8.5,
  category: 'CONFLICT',
  keep: true,
  reasoning: 'High-priority conflict event with significant geopolitical implications',
  cost_usd: 0.00012,
  tokens_used: 450,
  model: 'gpt-4o-mini',
};

/**
 * Valid Tier0 triage decision (article discarded)
 */
export const mockTier0Discarded: TriageDecision = {
  PriorityScore: 2.3,
  category: 'OTHER',
  keep: false,
  reasoning: 'Low relevance, no significant news value',
  cost_usd: 0.00008,
  tokens_used: 320,
  model: 'gpt-4o-mini',
};

/**
 * Valid Tier1 foundation results with nested scores
 * CRITICAL: Scores must be in nested 'scores' object!
 */
export const mockTier1: Tier1Results = {
  entities: [
    {
      name: 'European Central Bank',
      type: 'ORGANIZATION',
      relevance: 0.95,
    },
    {
      name: 'Christine Lagarde',
      type: 'PERSON',
      relevance: 0.88,
    },
    {
      name: 'Frankfurt',
      type: 'LOCATION',
      relevance: 0.72,
    },
  ],
  relations: [
    {
      source: 'Christine Lagarde',
      target: 'European Central Bank',
      type: 'LEADS',
      confidence: 0.98,
    },
    {
      source: 'European Central Bank',
      target: 'Frankfurt',
      type: 'LOCATED_IN',
      confidence: 0.99,
    },
  ],
  topics: [
    {
      name: 'Monetary Policy',
      relevance: 0.92,
    },
    {
      name: 'Interest Rates',
      relevance: 0.87,
    },
  ],
  scores: {
    // ← IMPORTANT: Nested structure as expected by frontend
    impact_score: 7.5,
    credibility_score: 8.2,
    urgency_score: 6.1,
  },
  tokens_used: 1200,
  cost_usd: 0.00045,
  model: 'gpt-4o-mini',
};

/**
 * Tier1 with low scores
 */
export const mockTier1LowScores: Tier1Results = {
  entities: [],
  relations: [],
  topics: [],
  scores: {
    impact_score: 2.5,
    credibility_score: 3.0,
    urgency_score: 1.8,
  },
  tokens_used: 800,
  cost_usd: 0.0003,
  model: 'gpt-4o-mini',
};

/**
 * INVALID Tier1 - flat structure (common mistake)
 * This represents backend data BEFORE transformation
 */
export const mockTier1FlatInvalid = {
  entities: [],
  relations: [],
  topics: [],
  // ❌ WRONG: Scores at top level instead of nested
  impact_score: 7.0,
  credibility_score: 8.0,
  urgency_score: 4.0,
  tokens_used: 900,
  cost_usd: 0.00035,
  model: 'gpt-4o-mini',
};

/**
 * Valid Tier2 specialist results
 */
export const mockTier2: Tier2Results = {
  conflict_analysis: {
    conflict_type: 'ECONOMIC',
    severity: 7.2,
    actors: ['ECB', 'EU Member States'],
    implications: 'Potential impact on EU economic stability',
  },
  bias_analysis: {
    political_bias: 'MODERATE_LEFT',
    bias_score: 0.35,
    indicators: ['pro-regulation language', 'emphasis on social impact'],
  },
  total_tokens: 2500,
  total_cost_usd: 0.00095,
  specialists_executed: 6,
};

/**
 * Complete V3 analysis (all tiers present)
 */
export const mockV3AnalysisComplete: V3AnalysisData = {
  article_id: 'c850f37b-5df1-40ce-b310-908021bc1dac',
  pipeline_version: '3.0',
  success: true,
  tier0: mockTier0Kept,
  tier1: mockTier1,
  tier2: mockTier2,
  relevance_score: 8.1,
  score_breakdown: {
    priority: 8.5,
    impact: 7.5,
    credibility: 8.2,
    urgency: 6.1,
  },
  metrics: {
    total_cost_usd: 0.00152,
    total_time_ms: 1850,
    tier0_cost_usd: 0.00012,
    tier1_cost_usd: 0.00045,
    tier2_cost_usd: 0.00095,
  },
  error_message: null,
  failed_agents: [],
  created_at: '2025-11-23T10:30:00Z',
  updated_at: '2025-11-23T10:30:02Z',
};

/**
 * V3 analysis with discarded article (only tier0)
 */
export const mockV3AnalysisDiscarded: V3AnalysisData = {
  article_id: 'a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6',
  pipeline_version: '3.0',
  success: true,
  tier0: mockTier0Discarded,
  tier1: null, // Not analyzed (discarded)
  tier2: null,
  relevance_score: 2.3,
  score_breakdown: {
    priority: 2.3,
  },
  metrics: {
    total_cost_usd: 0.00008,
    total_time_ms: 320,
    tier0_cost_usd: 0.00008,
  },
  error_message: null,
  failed_agents: [],
  created_at: '2025-11-23T11:00:00Z',
  updated_at: '2025-11-23T11:00:01Z',
};

/**
 * Failed V3 analysis
 */
export const mockV3AnalysisFailed: V3AnalysisData = {
  article_id: 'error-article-id',
  pipeline_version: '3.0',
  success: false,
  tier0: mockTier0Kept,
  tier1: null,
  tier2: null,
  relevance_score: null,
  score_breakdown: {},
  metrics: {
    total_cost_usd: 0.00012,
    total_time_ms: 500,
  },
  error_message: 'Tier 1 analysis failed: API rate limit exceeded',
  failed_agents: ['foundation'],
  created_at: '2025-11-23T12:00:00Z',
  updated_at: '2025-11-23T12:00:01Z',
};

/**
 * INVALID V3 analysis - missing tier0.scores (validation should catch this)
 */
export const mockV3AnalysisInvalidMissingScores = {
  article_id: 'invalid-scores-id',
  pipeline_version: '3.0',
  success: true,
  tier0: mockTier0Kept,
  tier1: mockTier1FlatInvalid, // ❌ Invalid structure
  tier2: null,
  relevance_score: 7.0,
  score_breakdown: {},
  metrics: {},
  error_message: null,
  failed_agents: [],
  created_at: '2025-11-23T13:00:00Z',
  updated_at: '2025-11-23T13:00:01Z',
};
