/**
 * Narrative Feature Module
 *
 * Provides narrative analysis capabilities including:
 * - Frame detection (victim, hero, threat, solution, conflict, economic)
 * - Bias analysis across the political spectrum
 * - Narrative clustering and grouping
 * - Text analysis for one-off content
 *
 * @module features/narrative
 *
 * @example
 * ```typescript
 * import {
 *   getNarrativeOverview,
 *   listFrames,
 *   analyzeText,
 *   type NarrativeOverview
 * } from '@/features/narrative';
 *
 * // Get overview statistics
 * const { data: overview } = await getNarrativeOverview({ days: 7 });
 *
 * // List frames with filters
 * const { data: frames } = await listFrames({
 *   frame_type: 'victim',
 *   min_confidence: 0.7
 * });
 *
 * // Analyze text
 * const { data: analysis } = await analyzeText({
 *   text: 'Breaking news content...',
 *   source: 'cnn'
 * });
 * ```
 */

// API exports
export * from './api';

// Type exports (for explicit imports)
export * from './types';

// Components
export { TextAnalyzer } from './components/TextAnalyzer';

// Hooks
export { useTextAnalyzer } from './hooks/useTextAnalyzer';
