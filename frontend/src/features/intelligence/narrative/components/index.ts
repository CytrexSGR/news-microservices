/**
 * Narrative Analysis Components
 *
 * Re-exports all components for the narrative analysis feature.
 */

// ==================== Form Components ====================

export { NarrativeAnalysisForm, QuickAnalysisForm } from './NarrativeAnalysisForm';

// ==================== Table/List Components ====================

export { FramesTable } from './FramesTable';
export { DetectedFrameCard, DetectedFramesList } from './DetectedFrameCard';
export { BiasIndicatorList, BiasIndicatorCard, BiasTypeSummary } from './BiasIndicatorList';
export {
  PropagandaWarnings,
  PropagandaIndicatorCard,
  PropagandaSummaryBadge,
} from './PropagandaWarnings';

// ==================== Chart Components ====================

export {
  BiasRadarChart,
  BiasBarChart,
  BiasGauge,
  BiasComparisonChart,
  BiasChartSkeleton,
} from './BiasChart';

// ==================== Result Views ====================

export { NarrativeResultView, CompactResultView } from './NarrativeResultView';

// ==================== Cost Components ====================

export { CostWarningBadge, InlineCost, CostSummary } from './CostWarningBadge';

// ==================== Dashboard Components ====================

export { NarrativeDashboard } from './NarrativeDashboard';
export {
  NarrativeClustersGrid,
  ClusterStatsSummary,
} from './NarrativeClustersGrid';

// ==================== NEW: Enhanced Narrative Components ====================

// Real-time text analysis panel
export {
  TextAnalyzerPanel,
  CompactTextAnalyzer,
  TextAnalyzerPanelSkeleton,
} from './TextAnalyzerPanel';

// Entity-centric narrative analysis
export {
  EntityNarrativePanel,
  CompactEntityNarrativePanel,
} from './EntityNarrativePanel';

// Tension monitoring
export {
  TensionMonitorPanel,
  TensionWidget,
} from './TensionMonitorPanel';

// Top entities by narrative involvement
export {
  TopNarrativeEntitiesWidget,
  CompactTopEntities,
  ControversialEntitiesWidget,
} from './TopNarrativeEntitiesWidget';

// Advanced frame distribution with KG data
export {
  FrameDistributionAdvanced,
  CompactFrameDistribution,
} from './FrameDistributionAdvanced';

// Overall narrative statistics
export {
  NarrativeStatsWidget,
  CompactNarrativeStats,
  NarrativeStatsSummaryBar,
} from './NarrativeStatsWidget';
