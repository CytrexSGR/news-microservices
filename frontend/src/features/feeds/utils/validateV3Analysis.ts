/**
 * Runtime validation for V3 Analysis data structure
 *
 * Purpose: Catch data structure mismatches between backend and frontend at runtime.
 * This prevents display issues like "N/A" scores when data structure changes.
 *
 * Related: POSTMORTEMS.md Incident #23 (2025-11-23)
 */

import type { Tier1Results, Tier1Scores, TriageDecision, Tier2Results } from '../types/analysisV3';

/**
 * Validation error with context
 */
export class V3ValidationError extends Error {
  field: string;
  expected: string;
  received: unknown;

  constructor(
    message: string,
    field: string,
    expected: string,
    received: unknown
  ) {
    super(`V3 Validation Error in '${field}': ${message}\nExpected: ${expected}\nReceived: ${JSON.stringify(received)}`);
    this.name = 'V3ValidationError';
    this.field = field;
    this.expected = expected;
    this.received = received;
  }
}

/**
 * Validate Tier 0 (Triage) structure
 */
export function validateTier0(data: unknown): asserts data is TriageDecision {
  if (!data || typeof data !== 'object') {
    throw new V3ValidationError(
      'Tier0 data must be an object',
      'tier0',
      'object with PriorityScore, category, keep',
      data
    );
  }

  const tier0 = data as Record<string, unknown>;

  // Check PriorityScore (capital P!)
  if (typeof tier0.PriorityScore !== 'number') {
    throw new V3ValidationError(
      'PriorityScore must be a number',
      'tier0.PriorityScore',
      'number (0-10)',
      tier0.PriorityScore
    );
  }

  // Check category
  const validCategories = ['CONFLICT', 'FINANCE', 'POLITICS', 'HUMANITARIAN', 'SECURITY', 'TECHNOLOGY', 'HEALTH', 'OTHER'];
  if (typeof tier0.category !== 'string' || !validCategories.includes(tier0.category)) {
    throw new V3ValidationError(
      'category must be a valid V3Category',
      'tier0.category',
      validCategories.join(' | '),
      tier0.category
    );
  }

  // Check keep
  if (typeof tier0.keep !== 'boolean') {
    throw new V3ValidationError(
      'keep must be a boolean',
      'tier0.keep',
      'boolean',
      tier0.keep
    );
  }
}

/**
 * Validate Tier 1 Scores structure (CRITICAL: Must be nested!)
 */
export function validateTier1Scores(scores: unknown): asserts scores is Tier1Scores {
  if (!scores || typeof scores !== 'object') {
    throw new V3ValidationError(
      'Tier1 scores must be an object',
      'tier1.scores',
      'object with impact_score, credibility_score, urgency_score',
      scores
    );
  }

  const scoresObj = scores as Record<string, unknown>;

  // Check all three required scores
  const requiredScores = ['impact_score', 'credibility_score', 'urgency_score'] as const;
  for (const scoreField of requiredScores) {
    if (typeof scoresObj[scoreField] !== 'number') {
      throw new V3ValidationError(
        `${scoreField} must be a number`,
        `tier1.scores.${scoreField}`,
        'number (0.0-10.0)',
        scoresObj[scoreField]
      );
    }

    // Validate range
    const score = scoresObj[scoreField] as number;
    if (score < 0 || score > 10) {
      throw new V3ValidationError(
        `${scoreField} must be between 0.0 and 10.0`,
        `tier1.scores.${scoreField}`,
        '0.0 <= score <= 10.0',
        score
      );
    }
  }
}

/**
 * Validate Tier 1 (Foundation) structure
 *
 * CRITICAL: Scores MUST be nested in 'scores' object!
 * Common mistake: Accessing tier1.impact_score instead of tier1.scores.impact_score
 */
export function validateTier1(data: unknown): asserts data is Tier1Results {
  if (!data || typeof data !== 'object') {
    throw new V3ValidationError(
      'Tier1 data must be an object',
      'tier1',
      'object with entities, relations, topics, scores',
      data
    );
  }

  const tier1 = data as Record<string, unknown>;

  // Check arrays
  if (!Array.isArray(tier1.entities)) {
    throw new V3ValidationError(
      'entities must be an array',
      'tier1.entities',
      'Entity[]',
      tier1.entities
    );
  }

  if (!Array.isArray(tier1.relations)) {
    throw new V3ValidationError(
      'relations must be an array',
      'tier1.relations',
      'Relation[]',
      tier1.relations
    );
  }

  if (!Array.isArray(tier1.topics)) {
    throw new V3ValidationError(
      'topics must be an array',
      'tier1.topics',
      'Topic[]',
      tier1.topics
    );
  }

  // CRITICAL: Validate nested scores object
  if (!tier1.scores) {
    throw new V3ValidationError(
      'scores object is missing! Backend should transform flat structure to nested.',
      'tier1.scores',
      'object with impact_score, credibility_score, urgency_score',
      undefined
    );
  }

  validateTier1Scores(tier1.scores);
}

/**
 * Validate Tier 2 (Specialists) structure
 */
export function validateTier2(data: unknown): asserts data is Tier2Results {
  if (!data || typeof data !== 'object') {
    throw new V3ValidationError(
      'Tier2 data must be an object',
      'tier2',
      'object with specialist findings',
      data
    );
  }

  const tier2 = data as Record<string, unknown>;

  // Check aggregated metadata
  if (typeof tier2.total_tokens !== 'number') {
    throw new V3ValidationError(
      'total_tokens must be a number',
      'tier2.total_tokens',
      'number',
      tier2.total_tokens
    );
  }

  if (typeof tier2.total_cost_usd !== 'number') {
    throw new V3ValidationError(
      'total_cost_usd must be a number',
      'tier2.total_cost_usd',
      'number',
      tier2.total_cost_usd
    );
  }

  if (typeof tier2.specialists_executed !== 'number') {
    throw new V3ValidationError(
      'specialists_executed must be a number',
      'tier2.specialists_executed',
      'number',
      tier2.specialists_executed
    );
  }
}

/**
 * Validate complete V3 analysis structure
 *
 * Use this before rendering V3 analysis data to catch structure issues early.
 *
 * @param data - V3 analysis data from backend
 * @throws V3ValidationError if structure is invalid
 *
 * @example
 * ```tsx
 * const { data: article } = useArticleV2(itemId);
 * if (article?.v3_analysis) {
 *   try {
 *     validateV3Analysis(article.v3_analysis);
 *     // Safe to render - data structure is correct
 *   } catch (error) {
 *     if (error instanceof V3ValidationError) {
 *       console.error('V3 data structure error:', error);
 *       // Show error to user or log to monitoring
 *     }
 *   }
 * }
 * ```
 */
export function validateV3Analysis(data: unknown): void {
  if (!data || typeof data !== 'object') {
    throw new V3ValidationError(
      'V3 analysis must be an object',
      'v3_analysis',
      'object with tier0, tier1, tier2',
      data
    );
  }

  const v3 = data as Record<string, unknown>;

  // Validate tier0 (always present)
  if (v3.tier0) {
    validateTier0(v3.tier0);
  } else {
    throw new V3ValidationError(
      'tier0 is required',
      'v3_analysis.tier0',
      'TriageDecision object',
      undefined
    );
  }

  // Validate tier1 (optional - only if article was kept)
  if (v3.tier1) {
    validateTier1(v3.tier1);
  }

  // Validate tier2 (optional - only if specialists ran)
  if (v3.tier2) {
    validateTier2(v3.tier2);
  }
}

/**
 * Safe accessor for Tier 1 scores with runtime validation
 *
 * Use this helper to safely access scores with automatic validation.
 * Throws V3ValidationError if structure is invalid.
 *
 * @example
 * ```tsx
 * const scores = getTier1Scores(tier1);
 * return <p>Impact: {scores.impact_score.toFixed(1)}</p>;
 * ```
 */
export function getTier1Scores(tier1: unknown): Tier1Scores {
  if (!tier1 || typeof tier1 !== 'object') {
    throw new V3ValidationError(
      'tier1 must be an object',
      'tier1',
      'Tier1Results object',
      tier1
    );
  }

  const tier1Obj = tier1 as Record<string, unknown>;

  if (!tier1Obj.scores) {
    throw new V3ValidationError(
      'scores object is missing! Use tier1.scores.impact_score, not tier1.impact_score',
      'tier1.scores',
      'Tier1Scores object',
      undefined
    );
  }

  validateTier1Scores(tier1Obj.scores);
  return tier1Obj.scores as Tier1Scores;
}
