/**
 * useStrategyEdit Hook
 *
 * Manages edit mode state and provides helper functions for updating
 * specific parts of a strategy definition.
 */

import { useState, useCallback } from 'react';
import { useUpdateStrategy, type UpdateStrategyParams } from './useUpdateStrategy';
import type { Strategy, StrategyDefinition, IndicatorConfig, RegimeLogic } from '../types';
import toast from 'react-hot-toast';

// ============================================================================
// Types
// ============================================================================

export interface UseStrategyEditOptions {
  strategy: Strategy;
  onSuccess?: () => void;
}

export interface UseStrategyEditResult {
  /** Whether edit mode is active */
  isEditMode: boolean;
  /** Set edit mode state */
  setEditMode: (enabled: boolean) => void;
  /** Toggle edit mode */
  toggleEditMode: () => void;
  /** Whether a mutation is pending */
  isPending: boolean;

  // Update helpers
  /** Update an indicator at a specific index */
  updateIndicator: (index: number, updates: Partial<IndicatorConfig>) => Promise<void>;
  /** Update a specific parameter of an indicator */
  updateIndicatorParam: (index: number, paramKey: string, value: number) => Promise<void>;
  /** Update regime logic (entry, exit, risk) */
  updateRegimeLogic: (regime: string, updates: Partial<RegimeLogic>) => Promise<void>;
  /** Update a specific risk setting */
  updateRiskSetting: (
    regime: string,
    field: 'stopLoss' | 'positionSize' | 'leverage',
    key: string,
    value: number
  ) => Promise<void>;
  /** Update execution settings */
  updateExecution: (key: string, value: string | number | boolean) => Promise<void>;
  /** Update strategy metadata (name, version, description) */
  updateMetadata: (updates: Partial<Strategy>) => Promise<void>;
  /** Update the entire definition (batch update) */
  updateDefinition: (updates: Partial<StrategyDefinition>) => Promise<void>;
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Manage strategy edit mode and updates
 *
 * @param options - Strategy and callbacks
 * @returns Edit state and update functions
 *
 * @example
 * ```tsx
 * const {
 *   isEditMode,
 *   toggleEditMode,
 *   updateIndicatorParam,
 *   isPending,
 * } = useStrategyEdit({ strategy });
 *
 * // Toggle edit mode
 * <Button onClick={toggleEditMode}>
 *   {isEditMode ? 'View Mode' : 'Edit Mode'}
 * </Button>
 *
 * // Update indicator parameter
 * await updateIndicatorParam(0, 'period', 20);
 * ```
 */
export function useStrategyEdit({
  strategy,
  onSuccess,
}: UseStrategyEditOptions): UseStrategyEditResult {
  const [isEditMode, setEditMode] = useState(false);
  const updateMutation = useUpdateStrategy();

  const toggleEditMode = useCallback(() => {
    setEditMode((prev) => !prev);
  }, []);

  const handleUpdate = useCallback(
    async (updates: UpdateStrategyParams['updates']) => {
      try {
        await updateMutation.mutateAsync({
          strategyId: strategy.id,
          updates,
        });
        toast.success('Strategy updated');
        onSuccess?.();
      } catch (error) {
        toast.error('Failed to update strategy');
        throw error;
      }
    },
    [strategy.id, updateMutation, onSuccess]
  );

  // ============================================================================
  // Update Helpers
  // ============================================================================

  const updateIndicator = useCallback(
    async (index: number, updates: Partial<IndicatorConfig>) => {
      const newIndicators = [...strategy.definition.indicators];
      newIndicators[index] = { ...newIndicators[index], ...updates };
      await handleUpdate({
        definition: { indicators: newIndicators } as Partial<StrategyDefinition>,
      });
    },
    [strategy.definition.indicators, handleUpdate]
  );

  const updateIndicatorParam = useCallback(
    async (index: number, paramKey: string, value: number) => {
      const newIndicators = [...strategy.definition.indicators];
      newIndicators[index] = {
        ...newIndicators[index],
        params: {
          ...newIndicators[index].params,
          [paramKey]: value,
        },
      };
      await handleUpdate({
        definition: { indicators: newIndicators } as Partial<StrategyDefinition>,
      });
    },
    [strategy.definition.indicators, handleUpdate]
  );

  const updateRegimeLogic = useCallback(
    async (regime: string, updates: Partial<RegimeLogic>) => {
      const newLogic = {
        ...strategy.definition.logic,
        [regime]: {
          ...strategy.definition.logic[regime],
          ...updates,
        },
      };
      await handleUpdate({
        definition: { logic: newLogic } as Partial<StrategyDefinition>,
      });
    },
    [strategy.definition.logic, handleUpdate]
  );

  const updateRiskSetting = useCallback(
    async (
      regime: string,
      field: 'stopLoss' | 'positionSize' | 'leverage',
      key: string,
      value: number
    ) => {
      const currentRisk = strategy.definition.logic[regime]?.risk || {};
      const currentField = currentRisk[field] || {};
      const newRisk = {
        ...currentRisk,
        [field]: {
          ...currentField,
          [key]: value,
        },
      };
      await updateRegimeLogic(regime, { risk: newRisk });
    },
    [strategy.definition.logic, updateRegimeLogic]
  );

  const updateExecution = useCallback(
    async (key: string, value: string | number | boolean) => {
      const newExecution = {
        ...strategy.definition.execution,
        [key]: value,
      };
      await handleUpdate({
        definition: { execution: newExecution } as Partial<StrategyDefinition>,
      });
    },
    [strategy.definition.execution, handleUpdate]
  );

  const updateMetadata = useCallback(
    async (updates: Partial<Strategy>) => {
      await handleUpdate(updates);
    },
    [handleUpdate]
  );

  const updateDefinition = useCallback(
    async (updates: Partial<StrategyDefinition>) => {
      await handleUpdate({ definition: updates });
    },
    [handleUpdate]
  );

  return {
    isEditMode,
    setEditMode,
    toggleEditMode,
    isPending: updateMutation.isPending,
    updateIndicator,
    updateIndicatorParam,
    updateRegimeLogic,
    updateRiskSetting,
    updateExecution,
    updateMetadata,
    updateDefinition,
  };
}
