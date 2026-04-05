/**
 * EscalationPanel Container Component
 *
 * Main container for the Intelligence Interpretation Layer.
 * Combines RegimeIndicator, FinancePanel, EscalationHeatmap, and CorrelationAlerts
 * into a cohesive dashboard view with loading, error, and empty states.
 *
 * @module features/intelligence/components/EscalationPanel
 */

import { useEscalationSummary } from '../../api/escalation';
import { RegimeIndicator } from './RegimeIndicator';
import { FinancePanel } from './FinancePanel';
import { EscalationHeatmap } from './EscalationHeatmap';
import { CorrelationAlerts } from './CorrelationAlerts';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';

// =============================================================================
// Props Interface
// =============================================================================

interface EscalationPanelProps {
  /**
   * Callback when a cluster link is clicked in CorrelationAlerts
   * Use this to navigate to cluster detail view or open a modal
   */
  onClusterClick?: (clusterId: string) => void;
}

// =============================================================================
// Component
// =============================================================================

/**
 * Escalation Panel container component
 *
 * Fetches escalation summary data and renders a dashboard with:
 * - Market regime indicator (Risk On/Off/Transitional)
 * - Financial indicators (VIX, DXY, Yield Spread, Carry Trade)
 * - Regional escalation heatmap (Geo/Military/Economic by region)
 * - Correlation alerts (Confirmation/Divergence/Early Warning)
 *
 * @example
 * ```tsx
 * function IntelligencePage() {
 *   const navigate = useNavigate();
 *
 *   return (
 *     <EscalationPanel
 *       onClusterClick={(clusterId) => navigate(`/clusters/${clusterId}`)}
 *     />
 *   );
 * }
 * ```
 */
export function EscalationPanel({ onClusterClick }: EscalationPanelProps) {
  const { data, isLoading, error, refetch } = useEscalationSummary();

  // ---------------------------------------------------------------------------
  // Loading State
  // ---------------------------------------------------------------------------

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading escalation data...</span>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Error State
  // ---------------------------------------------------------------------------

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load escalation data</span>
        </div>
        <p className="mt-1 text-sm text-red-500 dark:text-red-400/80">
          {error instanceof Error ? error.message : 'Unknown error occurred'}
        </p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 flex items-center gap-1"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Empty State
  // ---------------------------------------------------------------------------

  if (!data) {
    return null;
  }

  // ---------------------------------------------------------------------------
  // Main Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">
          Intelligence Interpretation
        </h2>
        <button
          onClick={() => refetch()}
          className="text-muted-foreground hover:text-foreground transition-colors"
          title="Refresh data"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Top row: Regime + Finance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RegimeIndicator regime={data.regime} />
        <FinancePanel finance={data.finance} />
      </div>

      {/* Middle: Heatmap */}
      <EscalationHeatmap heatmap={data.heatmap} />

      {/* Bottom: Alerts */}
      <CorrelationAlerts
        alerts={data.alerts}
        onClusterClick={onClusterClick}
      />
    </div>
  );
}

// =============================================================================
// Re-exports
// =============================================================================

// Re-export all sub-components for convenient imports
export { RegimeIndicator } from './RegimeIndicator';
export { FinancePanel } from './FinancePanel';
export { EscalationHeatmap } from './EscalationHeatmap';
export { CorrelationAlerts } from './CorrelationAlerts';
