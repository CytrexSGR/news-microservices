/**
 * TypeScript type definitions for Content-Analysis-V3 API
 *
 * Based on: services/content-analysis-v3/app/models/schemas.py
 *
 * V3 Pipeline Architecture:
 * - Tier 0: Fast triage (keep/discard decision)
 * - Tier 1: Foundation extraction (entities, relations, topics, scores)
 * - Tier 2: Specialist analysis (5 specialized modules)
 * - Tier 3: Intelligence modules (planned, not implemented)
 *
 * Cost Optimization: 96.7% reduction vs V2 ($0.0085 → $0.00028 per article)
 */

// ============================================================================
// TIER 0: TRIAGE
// ============================================================================

export type V3Category =
  | "CONFLICT"
  | "FINANCE"
  | "POLITICS"
  | "HUMANITARIAN"
  | "SECURITY"
  | "TECHNOLOGY"
  | "HEALTH"
  | "OTHER";

export interface TriageDecision {
  /** Urgency score 0-10 */
  PriorityScore: number;

  /** Article category */
  category: V3Category;

  /** True = process further, False = discard */
  keep: boolean;

  // Metadata
  tokens_used: number;
  cost_usd: number;
  model: string;
}

// ============================================================================
// TIER 1: FOUNDATION EXTRACTION
// ============================================================================

export type EntityType = "PERSON" | "ORGANIZATION" | "LOCATION" | "EVENT";

export interface Entity {
  name: string;
  type: EntityType;
  confidence: number; // 0.0-1.0
  mentions: number;

  // Optional enrichment
  aliases?: string[];
  role?: string; // e.g., "CEO", "Minister"
}

export interface Relation {
  /** Entity name */
  subject: string;

  /** Relation type (WORKS_FOR, LOCATED_IN, etc.) */
  predicate: string;

  /** Target entity name */
  object: string;

  confidence: number; // 0.0-1.0
}

export interface Topic {
  /** Router keyword (FINANCE, CONFLICT, etc.) */
  keyword: string;

  confidence: number; // 0.0-1.0

  /** TOPIC_CLASSIFIER parent topic */
  parent_category: string;
}

/**
 * Tier 1 Foundation Scores
 *
 * NOTE: Backend transformation (analysis_loader.py:233-250) nests scores.
 * Database stores scores at top level, but frontend receives nested structure.
 *
 * Database: { impact_score: 7.0, credibility_score: 8.0, urgency_score: 4.0 }
 * Frontend: { scores: { impact_score: 7.0, credibility_score: 8.0, urgency_score: 4.0 } }
 *
 * Always access as: tier1.scores.impact_score (NOT tier1.impact_score)
 * See: POSTMORTEMS.md Incident #23 (2025-11-23)
 */
export interface Tier1Scores {
  impact_score: number; // 0.0-10.0
  credibility_score: number; // 0.0-10.0
  urgency_score: number; // 0.0-10.0
}

/**
 * Tier 1 Foundation Results
 *
 * Contains entities, relations, topics, and scores extracted by Tier 1 agent.
 * Scores are nested in a separate 'scores' object (see Tier1Scores for details).
 */
export interface Tier1Results {
  entities: Entity[];
  relations: Relation[];
  topics: Topic[];

  scores: Tier1Scores;  // ← Always nested (backend transformation)

  // Metadata
  tokens_used: number;
  cost_usd: number;
  model: string;
}

// ============================================================================
// TIER 2: SPECIALIST ANALYSIS
// ============================================================================

export type SpecialistName =
  | "TOPIC_CLASSIFIER"
  | "ENTITY_EXTRACTOR"
  | "FINANCIAL_ANALYST"
  | "GEOPOLITICAL_ANALYST"
  | "SENTIMENT_ANALYZER"
  | "BIAS_SCORER"
  | "NARRATIVE_ANALYST";

export interface SpecialistFindings {
  specialist_name: SpecialistName;

  // Structured findings (only one populated based on specialist_name)
  entities: Entity[];
  relations: Relation[];
  metrics: Record<string, number>;
  political_bias?: PoliticalBias;  // Only for BIAS_SCORER

  // Metadata
  tokens_used: number;
  cost_usd: number;
  model: string;
  execution_time_ms: number;
}

export type PoliticalDirection =
  | "far_left"
  | "left"
  | "center_left"
  | "center"
  | "center_right"
  | "right"
  | "far_right";

export type BiasStrength = "minimal" | "weak" | "moderate" | "strong" | "extreme";

export interface PoliticalBias {
  political_direction: PoliticalDirection;
  bias_score: number; // -1.0 to +1.0
  bias_strength: BiasStrength;
  confidence: number; // 0.0 to 1.0
}

export type FrameType =
  | "victim"
  | "hero"
  | "threat"
  | "solution"
  | "conflict"
  | "economic"
  | "moral"
  | "attribution";

export interface NarrativeFrame {
  frame_type: FrameType;
  confidence: number; // 0.0 to 1.0
  entities: string[];
  text_excerpt: string;
  role_mapping: Record<string, string>;
}

export interface NarrativeFrameMetrics {
  frames: NarrativeFrame[];
  dominant_frame: FrameType | null;
  entity_portrayals: Record<string, string[]>;
  narrative_tension: number; // 0.0 to 1.0
  propaganda_indicators: string[];
}

export interface Tier2Results {
  TOPIC_CLASSIFIER?: SpecialistFindings;
  ENTITY_EXTRACTOR?: SpecialistFindings;
  FINANCIAL_ANALYST?: SpecialistFindings;
  GEOPOLITICAL_ANALYST?: SpecialistFindings;
  SENTIMENT_ANALYZER?: SpecialistFindings;
  BIAS_SCORER?: SpecialistFindings;  // Uses political_bias field
  NARRATIVE_ANALYST?: SpecialistFindings & {
    narrative_frame_metrics?: NarrativeFrameMetrics;
  };

  // Aggregated metadata
  total_tokens: number;
  total_cost_usd: number;
  specialists_executed: number;
}

// ============================================================================
// TIER 3: INTELLIGENCE MODULES (Planned)
// ============================================================================

export type FindingType =
  | "ENTITY_CLUSTER"
  | "CAUSAL_CHAIN"
  | "TEMPORAL_SEQUENCE"
  | "CONFLICT_PATTERN"
  | "INFLUENCE_NETWORK";

export interface SymbolicFinding {
  finding_type: FindingType;

  // Graph-ready structure
  nodes: Record<string, any>[];
  edges: Record<string, any>[];

  confidence: number; // 0.0-1.0
}

export type IntelligenceModuleName =
  | "EVENT_INTELLIGENCE"
  | "SECURITY_INTELLIGENCE"
  | "HUMANITARIAN_INTELLIGENCE"
  | "GEOPOLITICAL_INTELLIGENCE"
  | "FINANCIAL_INTELLIGENCE"
  | "REGIONAL_INTELLIGENCE";

export interface IntelligenceModuleOutput {
  module_name: IntelligenceModuleName;
  symbolic_findings: SymbolicFinding[];

  // Numerical metrics only (for PostgreSQL)
  metrics: Record<string, number>;

  // Metadata
  tokens_used: number;
  cost_usd: number;
  model: string;
  execution_time_ms: number;
}

export interface RouterDecision {
  modules_to_run: string[];
  skipped_modules: string[];
  decision_time_ms: number;
}

export interface Tier3Results {
  // Modules (0-6 can be triggered)
  EVENT_INTELLIGENCE?: IntelligenceModuleOutput;
  SECURITY_INTELLIGENCE?: IntelligenceModuleOutput;
  HUMANITARIAN_INTELLIGENCE?: IntelligenceModuleOutput;
  GEOPOLITICAL_INTELLIGENCE?: IntelligenceModuleOutput;
  FINANCIAL_INTELLIGENCE?: IntelligenceModuleOutput;
  REGIONAL_INTELLIGENCE?: IntelligenceModuleOutput;

  // Router decision
  router_decision: RouterDecision;

  // Aggregated metadata
  modules_executed: number;
  total_tokens: number;
  total_cost_usd: number;
}

// ============================================================================
// COMPLETE V3 ARTICLE ANALYSIS
// ============================================================================

export interface V3ArticleAnalysis {
  article_id: string;
  version: "v3";

  // Tier results
  tier0: TriageDecision;
  tier1: Tier1Results;
  tier2: Tier2Results;
  tier3?: Tier3Results; // Optional, not yet implemented

  // Aggregated statistics
  total_cost_usd: number;
  total_tokens: number;
  processing_time_ms: number;

  // Provider breakdown
  providers_used: Record<string, number>; // e.g., {"gemini-flash": 11800, "gpt-4o-mini": 3000}

  created_at: string; // ISO timestamp
}

// ============================================================================
// API RESPONSE MODELS (from app/api/analysis.py)
// ============================================================================

export type AnalysisStatus =
  | "pending"
  | "processing"
  | "tier0_complete"
  | "tier1_complete"
  | "tier2_complete"
  | "already_analyzed"
  | "failed";

export interface AnalysisStatusResponse {
  article_id: string;
  status: AnalysisStatus;
  tier0_complete: boolean;
  tier1_complete: boolean;
  tier2_complete: boolean;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface AnalyzeArticleRequest {
  article_id: string; // UUID
  title: string;
  url: string;
  content: string;
  run_tier2?: boolean; // Default: true
}

export interface AnalyzeArticleResponse {
  article_id: string;
  status: AnalysisStatus;
  message: string;
  tier0_complete: boolean;
  tier1_complete: boolean;
  tier2_complete: boolean;
}

export interface AnalysisResultsResponse {
  article_id: string;
  tier0: TriageDecision | null;
  tier1: Tier1Results | null;
  tier2: Tier2Results | null;
}

// ============================================================================
// DATABASE ROW TYPES (for raw API responses)
// ============================================================================

/**
 * Raw tier0 database row as returned by GET /results/{article_id}/tier0
 */
export interface Tier0DatabaseRow {
  article_id: string;
  priority_score: number;
  category: V3Category;
  keep: boolean;
  tokens_used: number;
  cost_usd: number;
  model: string;
  created_at: string;
}

/**
 * Raw tier1 scores database row
 */
export interface Tier1ScoresDatabaseRow {
  article_id: string;
  impact_score: number;
  credibility_score: number;
  urgency_score: number;
  tokens_used: number;
  cost_usd: number;
  model: string;
  created_at: string;
}

/**
 * Raw tier1 entity database row
 */
export interface Tier1EntityDatabaseRow {
  id: number;
  article_id: string;
  name: string;
  type: EntityType;
  confidence: number;
  mentions: number;
  aliases: string[] | null;
  role: string | null;
  created_at: string;
}

/**
 * Raw tier1 relation database row
 */
export interface Tier1RelationDatabaseRow {
  id: number;
  article_id: string;
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  created_at: string;
}

/**
 * Raw tier1 topic database row
 */
export interface Tier1TopicDatabaseRow {
  id: number;
  article_id: string;
  keyword: string;
  confidence: number;
  parent_category: string;
  created_at: string;
}

/**
 * Raw tier2 specialist result database row
 */
export interface Tier2SpecialistDatabaseRow {
  id: number;
  article_id: string;
  specialist_name: SpecialistName;
  findings: any; // JSON field containing entities, relations, metrics
  tokens_used: number;
  cost_usd: number;
  model: string;
  execution_time_ms: number;
  created_at: string;
}

/**
 * Raw tier1 results as returned by GET /results/{article_id}/tier1
 */
export interface Tier1ResultsDatabaseResponse {
  scores: Tier1ScoresDatabaseRow;
  entities: Tier1EntityDatabaseRow[];
  relations: Tier1RelationDatabaseRow[];
  topics: Tier1TopicDatabaseRow[];
}

/**
 * Raw tier2 results as returned by GET /results/{article_id}/tier2
 */
export interface Tier2ResultsDatabaseResponse {
  specialists: Tier2SpecialistDatabaseRow[];
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Convert raw database tier0 row to TriageDecision
 */
export function mapTier0Row(row: Tier0DatabaseRow): TriageDecision {
  return {
    PriorityScore: row.priority_score,
    category: row.category,
    keep: row.keep,
    tokens_used: row.tokens_used,
    cost_usd: row.cost_usd,
    model: row.model,
  };
}

/**
 * Convert raw database tier1 response to Tier1Results
 */
export function mapTier1Results(data: Tier1ResultsDatabaseResponse): Tier1Results {
  return {
    entities: data.entities.map(e => ({
      name: e.name,
      type: e.type,
      confidence: e.confidence,
      mentions: e.mentions,
      aliases: e.aliases || undefined,
      role: e.role || undefined,
    })),
    relations: data.relations.map(r => ({
      subject: r.subject,
      predicate: r.predicate,
      object: r.object,
      confidence: r.confidence,
    })),
    topics: data.topics.map(t => ({
      keyword: t.keyword,
      confidence: t.confidence,
      parent_category: t.parent_category,
    })),
    scores: {
      impact_score: data.scores.impact_score,
      credibility_score: data.scores.credibility_score,
      urgency_score: data.scores.urgency_score,
    },
    tokens_used: data.scores.tokens_used,
    cost_usd: data.scores.cost_usd,
    model: data.scores.model,
  };
}

/**
 * Convert raw database tier2 response to Tier2Results
 */
export function mapTier2Results(data: Tier2ResultsDatabaseResponse): Tier2Results {
  const result: Tier2Results = {
    total_tokens: 0,
    total_cost_usd: 0,
    specialists_executed: data.specialists.length,
  };

  for (const specialist of data.specialists) {
    const findings: SpecialistFindings = {
      specialist_name: specialist.specialist_name,
      entities: specialist.findings?.entities || [],
      relations: specialist.findings?.relations || [],
      metrics: specialist.findings?.metrics || {},
      tokens_used: specialist.tokens_used,
      cost_usd: specialist.cost_usd,
      model: specialist.model,
      execution_time_ms: specialist.execution_time_ms,
    };

    result.total_tokens += specialist.tokens_used;
    result.total_cost_usd += specialist.cost_usd;

    // Assign to correct specialist field
    result[specialist.specialist_name] = findings;
  }

  return result;
}
