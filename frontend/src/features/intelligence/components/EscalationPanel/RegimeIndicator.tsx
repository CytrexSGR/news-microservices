/**
 * RegimeIndicator Component
 *
 * Displays the current market regime status from FMP service.
 * Shows regime type (Risk On/Off/Transitional), confidence score,
 * description, and duration since regime started.
 *
 * @module features/intelligence/components/EscalationPanel/RegimeIndicator
 */

import type { RegimeStatus } from '../../types/escalation';
import { getRegimeInfo } from '../../types/escalation';

interface RegimeIndicatorProps {
  /** Current market regime status from FMP */
  regime: RegimeStatus;
}

/**
 * Market regime indicator component
 *
 * @example
 * ```tsx
 * <RegimeIndicator
 *   regime={{
 *     type: 'RISK_OFF',
 *     score: 0.75,
 *     since: '2026-01-15T10:00:00Z'
 *   }}
 * />
 * ```
 */
export function RegimeIndicator({ regime }: RegimeIndicatorProps) {
  const regimeInfo = getRegimeInfo(regime.type);

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-muted-foreground">Market Regime</h3>
        <div className={`w-3 h-3 rounded-full ${regimeInfo.color}`} />
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-foreground">
          {regimeInfo.label}
        </span>
        <span className="text-sm text-muted-foreground">
          ({regime.score > 0 ? '+' : ''}
          {(regime.score * 100).toFixed(0)}%)
        </span>
      </div>

      <p className="mt-2 text-sm text-muted-foreground">{regimeInfo.description}</p>

      {regime.since && (
        <p className="mt-2 text-xs text-muted-foreground/70">
          Since {new Date(regime.since).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}
