/**
 * Unit tests for V3 Analysis validation utilities
 *
 * Tests runtime validation that catches data structure mismatches
 * between backend and frontend at runtime.
 *
 * Related: POSTMORTEMS.md Incident #23 (2025-11-23)
 */

import { describe, it, expect } from 'vitest';
import {
  V3ValidationError,
  validateTier0,
  validateTier1,
  validateTier1Scores,
  validateTier2,
  validateV3Analysis,
  getTier1Scores,
} from '../validateV3Analysis';
import {
  mockTier0Kept,
  mockTier0Discarded,
  mockTier1,
  mockTier1LowScores,
  mockTier1FlatInvalid,
  mockTier2,
  mockV3AnalysisComplete,
  mockV3AnalysisDiscarded,
  mockV3AnalysisFailed,
} from '@/test/mockData/v3Analysis';

describe('V3ValidationError', () => {
  it('should create error with context', () => {
    const error = new V3ValidationError(
      'Field is invalid',
      'tier1.scores',
      'object',
      undefined
    );

    expect(error.name).toBe('V3ValidationError');
    expect(error.field).toBe('tier1.scores');
    expect(error.expected).toBe('object');
    expect(error.received).toBeUndefined();
    expect(error.message).toContain('tier1.scores');
    expect(error.message).toContain('Field is invalid');
  });
});

describe('validateTier0', () => {
  it('should validate valid tier0 (kept)', () => {
    expect(() => validateTier0(mockTier0Kept)).not.toThrow();
  });

  it('should validate valid tier0 (discarded)', () => {
    expect(() => validateTier0(mockTier0Discarded)).not.toThrow();
  });

  it('should reject null/undefined', () => {
    expect(() => validateTier0(null)).toThrow(V3ValidationError);
    expect(() => validateTier0(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object', () => {
    expect(() => validateTier0('string')).toThrow(V3ValidationError);
    expect(() => validateTier0(123)).toThrow(V3ValidationError);
  });

  it('should reject missing PriorityScore', () => {
    const invalid = { ...mockTier0Kept, PriorityScore: undefined };
    expect(() => validateTier0(invalid)).toThrow(V3ValidationError);
  });

  it('should reject invalid PriorityScore type', () => {
    const invalid = { ...mockTier0Kept, PriorityScore: 'high' };
    expect(() => validateTier0(invalid)).toThrow(V3ValidationError);
  });

  it('should reject invalid category', () => {
    const invalid = { ...mockTier0Kept, category: 'INVALID_CATEGORY' };
    expect(() => validateTier0(invalid)).toThrow(V3ValidationError);
  });

  it('should reject invalid keep type', () => {
    const invalid = { ...mockTier0Kept, keep: 'yes' };
    expect(() => validateTier0(invalid)).toThrow(V3ValidationError);
  });

  it('should accept all valid categories', () => {
    const categories = ['CONFLICT', 'FINANCE', 'POLITICS', 'HUMANITARIAN', 'SECURITY', 'TECHNOLOGY', 'HEALTH', 'OTHER'];

    categories.forEach((category) => {
      const data = { ...mockTier0Kept, category };
      expect(() => validateTier0(data)).not.toThrow();
    });
  });
});

describe('validateTier1Scores', () => {
  it('should validate valid scores', () => {
    expect(() => validateTier1Scores(mockTier1.scores)).not.toThrow();
  });

  it('should reject null/undefined', () => {
    expect(() => validateTier1Scores(null)).toThrow(V3ValidationError);
    expect(() => validateTier1Scores(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object', () => {
    expect(() => validateTier1Scores('string')).toThrow(V3ValidationError);
  });

  it('should reject missing impact_score', () => {
    const invalid = {
      credibility_score: 8.0,
      urgency_score: 4.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing credibility_score', () => {
    const invalid = {
      impact_score: 7.0,
      urgency_score: 4.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing urgency_score', () => {
    const invalid = {
      impact_score: 7.0,
      credibility_score: 8.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should reject invalid score types', () => {
    const invalid = {
      impact_score: 'high',
      credibility_score: 8.0,
      urgency_score: 4.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should reject scores out of range (< 0)', () => {
    const invalid = {
      impact_score: -1.0,
      credibility_score: 8.0,
      urgency_score: 4.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should reject scores out of range (> 10)', () => {
    const invalid = {
      impact_score: 7.0,
      credibility_score: 11.5,
      urgency_score: 4.0,
    };
    expect(() => validateTier1Scores(invalid)).toThrow(V3ValidationError);
  });

  it('should accept boundary values (0 and 10)', () => {
    const boundary = {
      impact_score: 0.0,
      credibility_score: 10.0,
      urgency_score: 5.0,
    };
    expect(() => validateTier1Scores(boundary)).not.toThrow();
  });
});

describe('validateTier1', () => {
  it('should validate valid tier1', () => {
    expect(() => validateTier1(mockTier1)).not.toThrow();
  });

  it('should validate tier1 with low scores', () => {
    expect(() => validateTier1(mockTier1LowScores)).not.toThrow();
  });

  it('should reject null/undefined', () => {
    expect(() => validateTier1(null)).toThrow(V3ValidationError);
    expect(() => validateTier1(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object', () => {
    expect(() => validateTier1('string')).toThrow(V3ValidationError);
  });

  it('should reject missing entities array', () => {
    const invalid = { ...mockTier1, entities: undefined };
    expect(() => validateTier1(invalid)).toThrow(V3ValidationError);
  });

  it('should reject non-array entities', () => {
    const invalid = { ...mockTier1, entities: 'not an array' };
    expect(() => validateTier1(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing relations array', () => {
    const invalid = { ...mockTier1, relations: undefined };
    expect(() => validateTier1(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing topics array', () => {
    const invalid = { ...mockTier1, topics: undefined };
    expect(() => validateTier1(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing scores object (CRITICAL)', () => {
    // This is the bug from POSTMORTEMS.md Incident #23
    const invalid = { ...mockTier1, scores: undefined };
    expect(() => validateTier1(invalid)).toThrow(V3ValidationError);
    expect(() => validateTier1(invalid)).toThrow(/scores object is missing/);
  });

  it('should reject flat structure (common mistake)', () => {
    // This represents backend data BEFORE transformation
    expect(() => validateTier1(mockTier1FlatInvalid)).toThrow(V3ValidationError);
    expect(() => validateTier1(mockTier1FlatInvalid)).toThrow(/scores object is missing/);
  });
});

describe('validateTier2', () => {
  it('should validate valid tier2', () => {
    expect(() => validateTier2(mockTier2)).not.toThrow();
  });

  it('should reject null/undefined', () => {
    expect(() => validateTier2(null)).toThrow(V3ValidationError);
    expect(() => validateTier2(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object', () => {
    expect(() => validateTier2('string')).toThrow(V3ValidationError);
  });

  it('should reject missing total_tokens', () => {
    const invalid = { ...mockTier2, total_tokens: undefined };
    expect(() => validateTier2(invalid)).toThrow(V3ValidationError);
  });

  it('should reject invalid total_tokens type', () => {
    const invalid = { ...mockTier2, total_tokens: 'many' };
    expect(() => validateTier2(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing total_cost_usd', () => {
    const invalid = { ...mockTier2, total_cost_usd: undefined };
    expect(() => validateTier2(invalid)).toThrow(V3ValidationError);
  });

  it('should reject missing specialists_executed', () => {
    const invalid = { ...mockTier2, specialists_executed: undefined };
    expect(() => validateTier2(invalid)).toThrow(V3ValidationError);
  });
});

describe('validateV3Analysis', () => {
  it('should validate complete V3 analysis (all tiers)', () => {
    expect(() => validateV3Analysis(mockV3AnalysisComplete)).not.toThrow();
  });

  it('should validate discarded analysis (tier0 only)', () => {
    expect(() => validateV3Analysis(mockV3AnalysisDiscarded)).not.toThrow();
  });

  it('should reject null/undefined', () => {
    expect(() => validateV3Analysis(null)).toThrow(V3ValidationError);
    expect(() => validateV3Analysis(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object', () => {
    expect(() => validateV3Analysis('string')).toThrow(V3ValidationError);
  });

  it('should reject missing tier0', () => {
    const invalid = { ...mockV3AnalysisComplete, tier0: undefined };
    expect(() => validateV3Analysis(invalid)).toThrow(V3ValidationError);
    expect(() => validateV3Analysis(invalid)).toThrow(/tier0 is required/);
  });

  it('should validate V3 with optional tier1 missing', () => {
    const data = { ...mockV3AnalysisComplete, tier1: null };
    expect(() => validateV3Analysis(data)).not.toThrow();
  });

  it('should validate V3 with optional tier2 missing', () => {
    const data = { ...mockV3AnalysisComplete, tier2: null };
    expect(() => validateV3Analysis(data)).not.toThrow();
  });

  it('should reject invalid tier1 when present', () => {
    const invalid = {
      ...mockV3AnalysisComplete,
      tier1: mockTier1FlatInvalid, // Flat structure
    };
    expect(() => validateV3Analysis(invalid)).toThrow(V3ValidationError);
  });

  it('should handle failed analysis gracefully', () => {
    // Failed analyses may have tier0 but missing tier1/tier2
    expect(() => validateV3Analysis(mockV3AnalysisFailed)).not.toThrow();
  });
});

describe('getTier1Scores', () => {
  it('should extract scores from valid tier1', () => {
    const scores = getTier1Scores(mockTier1);

    expect(scores.impact_score).toBe(7.5);
    expect(scores.credibility_score).toBe(8.2);
    expect(scores.urgency_score).toBe(6.1);
  });

  it('should reject null/undefined tier1', () => {
    expect(() => getTier1Scores(null)).toThrow(V3ValidationError);
    expect(() => getTier1Scores(undefined)).toThrow(V3ValidationError);
  });

  it('should reject non-object tier1', () => {
    expect(() => getTier1Scores('string')).toThrow(V3ValidationError);
  });

  it('should reject tier1 without scores object', () => {
    const invalid = { ...mockTier1, scores: undefined };
    expect(() => getTier1Scores(invalid)).toThrow(V3ValidationError);
    expect(() => getTier1Scores(invalid)).toThrow(/Use tier1.scores.impact_score, not tier1.impact_score/);
  });

  it('should reject flat structure (common mistake)', () => {
    expect(() => getTier1Scores(mockTier1FlatInvalid)).toThrow(V3ValidationError);
  });

  it('should validate extracted scores', () => {
    // getTier1Scores should validate the scores object
    const invalidScores = {
      ...mockTier1,
      scores: {
        impact_score: 'high', // Invalid type
        credibility_score: 8.0,
        urgency_score: 4.0,
      },
    };

    expect(() => getTier1Scores(invalidScores)).toThrow(V3ValidationError);
  });
});
