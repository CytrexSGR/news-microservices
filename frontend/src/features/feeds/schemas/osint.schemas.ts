/**
 * Zod Runtime Validation Schemas for OSINT Event Data
 *
 * Provides type-safe runtime validation to catch backend data quality issues
 * and prevent frontend crashes from malformed data.
 *
 * Schema matches:
 * - Backend: database/models/event_analysis.py (EventAnalysis model)
 * - Backend validation: services/content-analysis-service/app/services/event_analysis/data_validation.py
 */

import { z } from 'zod';

/**
 * Impact Schema - Structured numeric fields only (no narrative text)
 *
 * Allowed keys (enforced by backend sanitization):
 * - fatalities, injured, displaced, affected: integer counts
 * - buildings_damaged: integer count
 * - infrastructure_damaged: string description
 * - economic_cost_usd: float value
 */
export const ImpactSchema = z.object({
  fatalities: z.number().int().min(0).max(10_000).nullable().optional(),
  injured: z.number().int().min(0).max(50_000).nullable().optional(),
  displaced: z.number().int().min(0).max(1_000_000).nullable().optional(),
  affected: z.number().int().min(0).max(10_000_000).nullable().optional(),
  civilians_affected: z.number().int().min(0).max(10_000_000).nullable().optional(), // Legacy field
  buildings_damaged: z.number().int().min(0).max(100_000).nullable().optional(),
  infrastructure_damaged: z.string().nullable().optional(),
  economic_cost_usd: z.number().min(0).max(1_000_000_000_000).nullable().optional(),
  environmental_damage: z.string().nullable().optional(),
}).strict(); // Reject any additional keys (catches backend errors)

/**
 * Actors Schema - WHO framework
 *
 * Allowed roles:
 * - alleged_attacker: Who carried out the action
 * - victim: Who was targeted/affected
 * - reporting_party: Who is reporting this
 * - witness: Who witnessed the event (optional)
 * - investigator: Who is investigating (optional)
 */
export const ActorsSchema = z.object({
  alleged_attacker: z.string().nullable().optional(),
  victim: z.string().nullable().optional(),
  reporting_party: z.string().nullable().optional(),
  witness: z.string().nullable().optional(),
  investigator: z.string().nullable().optional(),
}).strict();

/**
 * Claim Schema - Evidence-based assertions
 *
 * Each claim has:
 * - statement: The claim being made
 * - confidence: "low" | "medium" | "high"
 * - evidence_ref: Source of evidence (quote, photo, statement)
 * - attribution: Who made this claim
 */
export const ClaimSchema = z.object({
  statement: z.string(),
  confidence: z.enum(['low', 'medium', 'high']),
  evidence_ref: z.string().optional(),
  attribution: z.string().optional(),
});

/**
 * Confidence Dimensions Schema
 *
 * 4-dimension confidence assessment:
 * - source_credibility: How reliable is the source?
 * - specificity: How detailed is the information?
 * - counter_statements: Are there conflicting reports?
 * - corroboration: Is it confirmed by multiple sources?
 * - weighted_score: Overall score (0-1)
 */
export const ConfidenceDimensionsSchema = z.object({
  source_credibility: z.enum(['low', 'medium', 'high']),
  specificity: z.enum(['low', 'medium', 'high']),
  counter_statements: z.enum(['low', 'medium', 'high']),
  corroboration: z.enum(['low', 'medium', 'high']),
  weighted_score: z.number().min(0).max(1).optional(), // Backend doesn't always provide weighted_score
});

/**
 * Evidence Schema - Supporting evidence items
 */
export const EvidenceSchema = z.object({
  type: z.enum(['quote', 'photo', 'video', 'document', 'satellite_imagery', 'social_media']),
  text: z.string().optional(),
  source: z.string().optional(),
  position: z.number().int().optional(),
  claim_ref: z.number().int().optional(),
  url: z.string().url().optional(),
  description: z.string().optional(),
});

/**
 * Publisher Context Schema
 */
export const PublisherContextSchema = z.object({
  publisher_bias: z.string().nullable().optional(),
  source_type: z.string().nullable().optional(),
  reliability_score: z.number().min(0).max(1).nullable().optional(),
  fact_check_rating: z.string().nullable().optional(),
  publisher_type: z.string().nullable().optional(),
  source: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
}).strict();

/**
 * OSINT Event Schema - Complete event structure
 *
 * Main model matching EventAnalysis database model.
 */
export const OsintEventSchema = z.object({
  id: z.string().uuid(),
  article_id: z.string().uuid(),
  headline: z.string(),
  source: z.string(),
  publisher_url: z.string().nullable().optional(),

  // 5W Framework
  primary_event: z.string(),
  location: z.string().nullable().optional(),
  event_date: z.string().nullable().optional(), // Backend returns naive datetime without Z
  actors: ActorsSchema,
  means: z.array(z.string()).nullable().optional(),
  impact: ImpactSchema.nullable().optional(),

  // Claims and evidence
  claims: z.array(ClaimSchema),
  status: z.record(z.string(), z.any()).nullable().optional(),
  evidence: z.array(EvidenceSchema).nullable().optional(),

  // Risk assessment
  risk_tags: z.array(z.string()),
  publisher_context: PublisherContextSchema.nullable().optional(),

  // Analysis metadata
  summary: z.string(),
  confidence_overall: z.enum(['low', 'medium', 'high']),
  confidence_dimensions: ConfidenceDimensionsSchema.nullable().optional(),

  // Computed fields
  claim_count: z.number().int().min(0),
  evidence_count: z.number().int().min(0),
  needs_analyst_review: z.boolean(),

  // Timestamps (backend returns naive datetime without timezone)
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});

/**
 * Type exports for use in components
 */
export type Impact = z.infer<typeof ImpactSchema>;
export type Actors = z.infer<typeof ActorsSchema>;
export type Claim = z.infer<typeof ClaimSchema>;
export type ConfidenceDimensions = z.infer<typeof ConfidenceDimensionsSchema>;
export type Evidence = z.infer<typeof EvidenceSchema>;
export type PublisherContext = z.infer<typeof PublisherContextSchema>;
export type OsintEvent = z.infer<typeof OsintEventSchema>;

/**
 * Validation helper - validates and returns typed data
 *
 * Usage:
 * ```typescript
 * try {
 *   const validEvent = validateOsintEvent(rawData);
 *   // validEvent is now fully typed and validated
 * } catch (error) {
 *   console.error('OSINT data validation failed:', error);
 *   // Handle error (show fallback UI, log to Sentry, etc.)
 * }
 * ```
 */
export function validateOsintEvent(data: unknown): OsintEvent {
  return OsintEventSchema.parse(data);
}

/**
 * Safe validation helper - returns validation result without throwing
 *
 * Usage:
 * ```typescript
 * const result = safeValidateOsintEvent(rawData);
 * if (result.success) {
 *   // result.data is typed OsintEvent
 *   return <OsintEventCard event={result.data} />;
 * } else {
 *   console.error('Validation errors:', result.error.issues);
 *   return <ErrorFallback />;
 * }
 * ```
 */
export function safeValidateOsintEvent(data: unknown) {
  return OsintEventSchema.safeParse(data);
}

/**
 * Array validation helper
 */
export function validateOsintEvents(data: unknown[]): OsintEvent[] {
  return data.map(item => validateOsintEvent(item));
}

/**
 * Safe array validation helper
 */
export function safeValidateOsintEvents(data: unknown[]) {
  return data.map(item => safeValidateOsintEvent(item));
}
