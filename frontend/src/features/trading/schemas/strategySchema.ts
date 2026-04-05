/**
 * Zod Schema for Strategy Definition
 *
 * Validates all nested configuration:
 * - Metadata
 * - Regime Detection
 * - Entry Logic
 * - Exit Logic
 * - Risk Management
 * - MTFA
 * - Protections
 */

import { z } from 'zod'

// Regime types
export const RegimeSchema = z.enum(['TREND', 'CONSOLIDATION', 'HIGH_VOLATILITY'])

// Regime Detection Schemas
const RuleBasedConfigSchema = z.object({
  adx_threshold: z.number().min(0).max(100),
  bbw_threshold: z.number().min(0).max(0.1),
  atr_threshold: z.number().min(0).max(10),
})

const MLBasedConfigSchema = z.object({
  model_path: z.string(),
  feature_columns: z.array(z.string()),
  confidence_threshold: z.number().min(0).max(1),
})

const HybridConfigSchema = z.object({
  rule_weight: z.number().min(0).max(1),
  ml_weight: z.number().min(0).max(1),
  combine_method: z.enum(['weighted_avg', 'voting', 'sequential']),
})

export const RegimeDetectionSchema = z.object({
  provider: z.enum(['rule_based', 'ml_based', 'hybrid']),
  config: z.union([RuleBasedConfigSchema, MLBasedConfigSchema, HybridConfigSchema]),
})

// MTFA Schema
export const MTFASchema = z.object({
  timeframes: z.array(
    z.object({
      id: z.string(),
      weight: z.number().min(0).max(1),
      divergence_threshold: z.number().min(0).max(0.5),
    })
  ),
})

// Protection Schemas
export const ProtectionSchema = z.object({
  id: z.string(),
  type: z.enum(['StoplossGuard', 'MaxDrawdown', 'LowProfitPairs', 'CooldownPeriod']),
  enabled: z.boolean(),
  config: z.record(z.any()),
})

// Entry Logic Schemas
export const EntryConditionSchema = z.object({
  id: z.string(),
  expression: z.string().min(1),
  description: z.string(),
  confidence: z.number().min(0).max(1).optional(),
})

export const EntryLogicSchema = z.object({
  regime: RegimeSchema,
  aggregation_mode: z.enum(['ALL', 'ANY', 'WEIGHTED', 'CONFIDENCE_VOTING']),
  conditions: z.array(EntryConditionSchema),
})

// Exit Logic Schemas
export const ExitRuleSchema = z.object({
  id: z.string(),
  type: z.enum(['take_profit', 'trailing_stop', 'stop_loss', 'time_based', 'regime_change', 'indicator_signal']),
  enabled: z.boolean(),
  config: z.record(z.any()),
})

export const ExitLogicSchema = z.object({
  regime: RegimeSchema,
  rules: z.array(ExitRuleSchema),
})

// Risk Management Schemas
export const StopLossConfigSchema = z.object({
  method: z.enum(['fixed', 'atr_based', 'trailing', 'formula']),
  fixed_ratio: z.number().optional(),
  atr_multiplier: z.number().optional(),
  trailing_offset: z.number().optional(),
  formula: z.string().optional(),
})

export const PositionSizingConfigSchema = z.object({
  method: z.enum(['percent_risk', 'kelly', 'volatility_adjusted', 'formula']),
  percent_risk: z.number().optional(),
  kelly_fraction: z.number().optional(),
  volatility_window: z.number().optional(),
  formula: z.string().optional(),
})

export const LeverageConfigSchema = z.object({
  max_leverage: z.number().min(1).max(5),
  adaptive: z.boolean(),
  formula: z.string().optional(),
})

export const RiskManagementSchema = z.object({
  regime: RegimeSchema,
  stop_loss: StopLossConfigSchema,
  position_sizing: PositionSizingConfigSchema,
  leverage: LeverageConfigSchema,
})

// Complete Strategy Definition Schema
export const StrategyDefinitionSchema = z.object({
  regimeDetection: RegimeDetectionSchema.optional(),
  mtfa: MTFASchema.optional(),
  protections: z.array(ProtectionSchema).optional(),
  entryLogic: z.record(z.string(), EntryLogicSchema).optional(),
  exitLogic: z.record(z.string(), ExitLogicSchema).optional(),
  riskManagement: z.record(z.string(), RiskManagementSchema).optional(),
})

// Complete Strategy Schema (including metadata)
export const StrategyFormSchema = z.object({
  // Metadata
  name: z.string().min(1, 'Strategy name is required'),
  version: z.string().regex(/^\d+\.\d+\.\d+$/, 'Version must be in format X.Y.Z'),
  description: z.string().optional(),
  author: z.string().optional(),
  tags: z.array(z.string()).optional(),
  is_public: z.boolean(),

  // Strategy Definition - Use passthrough to allow any valid structure
  // Backend (Pydantic) handles detailed validation
  definition: z.any().optional(),
})

export type StrategyFormValues = z.infer<typeof StrategyFormSchema>
