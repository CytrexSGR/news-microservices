/**
 * Earnings Calendar Types
 * Integration with FMP service for earnings data
 */

/**
 * Earnings time indicator
 * - bmo: Before Market Open
 * - amc: After Market Close
 * - dmh: During Market Hours
 */
export type EarningsTime = 'bmo' | 'amc' | 'dmh';

/**
 * Earnings Event from calendar
 */
export interface EarningsEvent {
  symbol: string;
  company_name: string;
  date: string;
  time: EarningsTime;
  fiscal_quarter: string;
  fiscal_year: number;
  eps_estimated: number | null;
  eps_actual: number | null;
  revenue_estimated: number | null;
  revenue_actual: number | null;
  surprise_percent?: number;
}

/**
 * Historical earnings surprise data
 */
export interface EarningsSurprise {
  symbol: string;
  date: string;
  fiscal_quarter: string;
  eps_estimated: number;
  eps_actual: number;
  surprise_percent: number;
  revenue_estimated: number;
  revenue_actual: number;
  revenue_surprise_percent: number;
}

/**
 * Earnings call transcript
 */
export interface EarningsTranscript {
  symbol: string;
  quarter: string;
  year: number;
  date: string;
  content: string;
  participants: EarningsParticipant[];
  key_points: string[];
}

/**
 * Participant in earnings call
 */
export interface EarningsParticipant {
  name: string;
  role: string;
}

/**
 * Filters for earnings calendar queries
 */
export interface EarningsCalendarFilters {
  from?: string;
  to?: string;
  symbol?: string;
}

/**
 * Earnings grouped by date for calendar view
 */
export interface EarningsByDate {
  date: string;
  events: EarningsEvent[];
}

/**
 * Surprise classification
 */
export type SurpriseType = 'beat' | 'miss' | 'inline';

/**
 * Get surprise classification based on actual vs estimated
 */
export function getSurpriseType(actual: number | null, estimated: number | null): SurpriseType {
  if (actual === null || estimated === null) return 'inline';
  const diff = actual - estimated;
  const threshold = Math.abs(estimated) * 0.02; // 2% threshold for inline

  if (diff > threshold) return 'beat';
  if (diff < -threshold) return 'miss';
  return 'inline';
}

/**
 * Format earnings time for display
 */
export function formatEarningsTime(time: EarningsTime): string {
  switch (time) {
    case 'bmo':
      return 'Before Open';
    case 'amc':
      return 'After Close';
    case 'dmh':
      return 'Market Hours';
    default:
      return time;
  }
}

/**
 * Get color class for earnings time
 */
export function getEarningsTimeColor(time: EarningsTime): string {
  switch (time) {
    case 'bmo':
      return 'text-green-600 bg-green-100 dark:bg-green-900/30';
    case 'amc':
      return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
    case 'dmh':
      return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
    default:
      return 'text-gray-500';
  }
}

/**
 * Get color class for surprise type
 */
export function getSurpriseColor(type: SurpriseType): string {
  switch (type) {
    case 'beat':
      return 'text-green-600';
    case 'miss':
      return 'text-red-600';
    case 'inline':
      return 'text-gray-500';
  }
}
