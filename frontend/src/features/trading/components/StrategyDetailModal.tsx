/**
 * StrategyDetailModal Component
 *
 * Read-only modal view for displaying strategy details.
 * Uses Dialog component for displaying strategy configuration.
 *
 * Sections:
 * - Metadata (name, version, description, dates)
 * - Regime Detection (provider, config)
 * - Indicators (multi-timeframe table)
 * - Logic (per-regime entry/exit with tabs)
 * - Risk Management (position sizing, leverage)
 */

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import type { Strategy } from '@/types/strategy'
import {
  MetadataSection,
  RegimeDetectionSection,
  IndicatorsSection,
  LogicSection,
  MTFASection,
  ProtectionsSection,
  ExecutionSection,
} from './strategy'

interface StrategyDetailModalProps {
  /** Strategy to display (null when modal is closed) */
  strategy: Strategy | null
  /** Whether modal is open */
  open: boolean
  /** Callback when modal should close */
  onClose: () => void
}

export function StrategyDetailModal({ strategy, open, onClose }: StrategyDetailModalProps) {
  // Don't render if no strategy
  if (!strategy) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="mb-6">
          <DialogTitle>Strategy Details</DialogTitle>
          <DialogDescription>
            View complete configuration and logic for this strategy
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 pr-2">
          {/* Metadata Section */}
          <MetadataSection strategy={strategy} />

          {/* Regime Detection Section */}
          <RegimeDetectionSection config={strategy.definition.regimeDetection} />

          {/* Indicators Section */}
          <IndicatorsSection indicators={strategy.definition.indicators} />

          {/* Logic Section (Entry/Exit per Regime) */}
          {/* Note: Risk management is defined per regime, not globally */}
          <LogicSection logic={strategy.definition.logic} />

          {/* Multi-Timeframe Analysis Section */}
          <MTFASection mtfa={strategy.definition.mtfa} />

          {/* Protection Guards Section */}
          <ProtectionsSection protections={strategy.definition.protections || strategy.definition.execution?.protections} />

          {/* Execution Settings Section */}
          <ExecutionSection execution={strategy.definition.execution} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
