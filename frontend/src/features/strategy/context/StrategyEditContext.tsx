/**
 * StrategyEditContext
 *
 * Provides edit mode state and update functions to all strategy tabs.
 */

import { createContext, useContext, type ReactNode } from 'react';
import { useStrategyEdit, type UseStrategyEditResult } from '../hooks/useStrategyEdit';
import type { Strategy } from '../types';

// ============================================================================
// Context
// ============================================================================

const StrategyEditContext = createContext<UseStrategyEditResult | null>(null);

// ============================================================================
// Provider
// ============================================================================

export interface StrategyEditProviderProps {
  children: ReactNode;
  strategy: Strategy;
  onSuccess?: () => void;
}

/**
 * Provides edit mode state to all child components
 *
 * @example
 * ```tsx
 * <StrategyEditProvider strategy={strategy}>
 *   <IndicatorsTab />
 *   <RiskManagementTab />
 *   <LogicTab />
 * </StrategyEditProvider>
 * ```
 */
export function StrategyEditProvider({
  children,
  strategy,
  onSuccess,
}: StrategyEditProviderProps) {
  const editState = useStrategyEdit({ strategy, onSuccess });

  return (
    <StrategyEditContext.Provider value={editState}>
      {children}
    </StrategyEditContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Access edit mode state and update functions
 *
 * @throws Error if used outside StrategyEditProvider
 *
 * @example
 * ```tsx
 * function IndicatorParameter({ index, paramKey, value }) {
 *   const { isEditMode, updateIndicatorParam, isPending } = useStrategyEditContext();
 *
 *   return (
 *     <EditableField
 *       value={value}
 *       canEdit={isEditMode}
 *       onSave={(v) => updateIndicatorParam(index, paramKey, v)}
 *       disabled={isPending}
 *     />
 *   );
 * }
 * ```
 */
export function useStrategyEditContext(): UseStrategyEditResult {
  const context = useContext(StrategyEditContext);
  if (!context) {
    throw new Error(
      'useStrategyEditContext must be used within StrategyEditProvider'
    );
  }
  return context;
}
