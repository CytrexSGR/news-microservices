/**
 * Strategy Feature Module
 *
 * Unified exports for the Strategy Management feature
 */

// Types
export * from './types';

// Hooks
export { useStrategy, useStrategyList, useCloneStrategy, useDeleteStrategy, strategyKeys } from './hooks/useStrategy';
export { useUpdateStrategy, type UpdateStrategyParams } from './hooks/useUpdateStrategy';
export { useStrategyEdit, type UseStrategyEditResult, type UseStrategyEditOptions } from './hooks/useStrategyEdit';
export { useBacktests, useDeleteBacktest, backtestKeys } from './hooks/useBacktests';
export { usePaperTrading, type PaperTradeSession, type UsePaperTradingOptions } from './hooks/usePaperTrading';

// Context
export { StrategyEditProvider, useStrategyEditContext } from './context';

// Components
export * from './components';
