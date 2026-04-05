/**
 * Earnings Calendar Hook
 * Fetches upcoming and historical earnings events
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EarningsEvent, EarningsCalendarFilters, EarningsByDate } from '../types/earnings.types';

/**
 * Fetch earnings calendar with optional date filters
 */
export const useEarningsCalendar = (filters?: EarningsCalendarFilters) => {
  return useQuery({
    queryKey: ['market', 'earnings-calendar', filters],
    queryFn: () =>
      mcpClient.callTool<EarningsEvent[]>('fmp_earnings_calendar', filters || {}),
    refetchInterval: 3600000, // Refresh hourly
    staleTime: 1800000, // 30 minutes
  });
};

/**
 * Fetch earnings for current week
 */
export const useWeeklyEarnings = () => {
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay());
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);

  return useEarningsCalendar({
    from: startOfWeek.toISOString().split('T')[0],
    to: endOfWeek.toISOString().split('T')[0],
  });
};

/**
 * Fetch earnings for today
 */
export const useTodayEarnings = () => {
  const today = new Date().toISOString().split('T')[0];

  return useEarningsCalendar({
    from: today,
    to: today,
  });
};

/**
 * Fetch upcoming earnings (next 7 days)
 */
export const useUpcomingEarnings = (days: number = 7) => {
  const today = new Date();
  const future = new Date(today);
  future.setDate(today.getDate() + days);

  return useEarningsCalendar({
    from: today.toISOString().split('T')[0],
    to: future.toISOString().split('T')[0],
  });
};

/**
 * Fetch earnings for a specific symbol
 */
export const useSymbolEarnings = (symbol: string) => {
  return useQuery({
    queryKey: ['market', 'earnings-calendar', 'symbol', symbol],
    queryFn: () =>
      mcpClient.callTool<EarningsEvent[]>('fmp_earnings_calendar', { symbol }),
    enabled: !!symbol,
    refetchInterval: 3600000,
  });
};

/**
 * Group earnings by date for calendar display
 */
export function groupEarningsByDate(events: EarningsEvent[]): EarningsByDate[] {
  const grouped = events.reduce(
    (acc, event) => {
      const date = event.date;
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(event);
      return acc;
    },
    {} as Record<string, EarningsEvent[]>
  );

  return Object.entries(grouped)
    .map(([date, events]) => ({ date, events }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/**
 * Hook to get earnings grouped by date
 */
export const useEarningsGroupedByDate = (filters?: EarningsCalendarFilters) => {
  const query = useEarningsCalendar(filters);

  return {
    ...query,
    groupedData: query.data ? groupEarningsByDate(query.data) : [],
  };
};
