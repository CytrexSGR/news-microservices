/**
 * Market Feature API Hooks
 * Centralized exports for all market data hooks
 */

// Earnings Calendar
export {
  useEarningsCalendar,
  useWeeklyEarnings,
  useTodayEarnings,
  useUpcomingEarnings,
  useSymbolEarnings,
  useEarningsGroupedByDate,
  groupEarningsByDate,
} from './useEarningsCalendar';

// Earnings Surprises
export {
  useEarningsSurprises,
  useRecentSurprises,
  useEarningsSurpriseStats,
  calculateSurpriseStats,
  filterSurprises,
  getTopSurprises,
  type SurpriseStats,
  type TopSurprises,
} from './useEarningsSurprises';

// Earnings Transcripts
export {
  useEarningsTranscript,
  useAvailableTranscripts,
  useLatestTranscript,
  searchTranscript,
  extractMentionedMetrics,
  getExecutiveSummary,
  type TranscriptSearchResult,
  type MentionedMetric,
} from './useEarningsTranscript';
