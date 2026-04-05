/**
 * Hooks - Main Export
 *
 * Provides React Query hooks for various API integrations.
 */

// Strategy Evaluation hook
export {
  useStrategyEvaluation,
  useRegimeEvaluation,
  calculateEntryScoreDisplay,
  isExitTriggered,
  getRegimeName,
  getRegimeColor,
  strategyEvaluationKeys,
  type UseStrategyEvaluationOptions,
  type UseStrategyEvaluationResult,
} from './useStrategyEvaluation';

// Strategy Evaluation types
export type {
  StrategyEvaluationResponse,
  RegimeEvaluation,
  EntryEvaluation,
  ExitEvaluation,
  ConditionEvaluation,
  ExitRuleEvaluation,
  ExitRuleType,
  HypotheticalLevels,
  ConditionDisplayState,
  ConditionStatus,
} from '../types/strategy-evaluation';
