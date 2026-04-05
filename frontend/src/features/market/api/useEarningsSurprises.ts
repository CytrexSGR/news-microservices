/**
 * Earnings Surprises Hook
 * Fetches historical earnings surprises (beat/miss) for symbols
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EarningsSurprise, SurpriseType } from '../types/earnings.types';
import { getSurpriseType } from '../types/earnings.types';

/**
 * Fetch earnings surprises for a specific symbol
 */
export const useEarningsSurprises = (symbol: string) => {
  return useQuery({
    queryKey: ['market', 'earnings-surprises', symbol],
    queryFn: () =>
      mcpClient.callTool<EarningsSurprise[]>('fmp_earnings_surprises', { symbol }),
    enabled: !!symbol,
    staleTime: 86400000, // 24 hours - historical data doesn't change often
  });
};

/**
 * Fetch recent earnings surprises across all tracked symbols
 */
export const useRecentSurprises = (limit: number = 20) => {
  return useQuery({
    queryKey: ['market', 'earnings-surprises', 'recent', limit],
    queryFn: () =>
      mcpClient.callTool<EarningsSurprise[]>('fmp_recent_earnings_surprises', { limit }),
    refetchInterval: 3600000, // Hourly
    staleTime: 1800000, // 30 minutes
  });
};

/**
 * Surprise statistics for a symbol
 */
export interface SurpriseStats {
  totalReports: number;
  beats: number;
  misses: number;
  inline: number;
  beatRate: number;
  avgSurprisePercent: number;
  avgRevenueSurprisePercent: number;
  streak: {
    type: SurpriseType;
    count: number;
  };
}

/**
 * Calculate surprise statistics from history
 */
export function calculateSurpriseStats(surprises: EarningsSurprise[]): SurpriseStats {
  if (surprises.length === 0) {
    return {
      totalReports: 0,
      beats: 0,
      misses: 0,
      inline: 0,
      beatRate: 0,
      avgSurprisePercent: 0,
      avgRevenueSurprisePercent: 0,
      streak: { type: 'inline', count: 0 },
    };
  }

  let beats = 0;
  let misses = 0;
  let inline = 0;
  let totalSurprise = 0;
  let totalRevenueSurprise = 0;

  surprises.forEach((s) => {
    const type = getSurpriseType(s.eps_actual, s.eps_estimated);
    if (type === 'beat') beats++;
    else if (type === 'miss') misses++;
    else inline++;

    totalSurprise += s.surprise_percent;
    totalRevenueSurprise += s.revenue_surprise_percent;
  });

  // Calculate streak (sorted by date, most recent first)
  const sorted = [...surprises].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
  let streakType = getSurpriseType(sorted[0].eps_actual, sorted[0].eps_estimated);
  let streakCount = 0;

  for (const s of sorted) {
    const type = getSurpriseType(s.eps_actual, s.eps_estimated);
    if (type === streakType) {
      streakCount++;
    } else {
      break;
    }
  }

  return {
    totalReports: surprises.length,
    beats,
    misses,
    inline,
    beatRate: (beats / surprises.length) * 100,
    avgSurprisePercent: totalSurprise / surprises.length,
    avgRevenueSurprisePercent: totalRevenueSurprise / surprises.length,
    streak: {
      type: streakType,
      count: streakCount,
    },
  };
}

/**
 * Hook to get surprise statistics for a symbol
 */
export const useEarningsSurpriseStats = (symbol: string) => {
  const query = useEarningsSurprises(symbol);

  return {
    ...query,
    stats: query.data ? calculateSurpriseStats(query.data) : null,
  };
};

/**
 * Filter surprises by type
 */
export function filterSurprises(
  surprises: EarningsSurprise[],
  type: SurpriseType | 'all'
): EarningsSurprise[] {
  if (type === 'all') return surprises;

  return surprises.filter((s) => {
    return getSurpriseType(s.eps_actual, s.eps_estimated) === type;
  });
}

/**
 * Get top beats and misses from recent surprises
 */
export interface TopSurprises {
  topBeats: EarningsSurprise[];
  topMisses: EarningsSurprise[];
}

export function getTopSurprises(surprises: EarningsSurprise[], limit: number = 5): TopSurprises {
  const sorted = [...surprises].sort(
    (a, b) => b.surprise_percent - a.surprise_percent
  );

  const topBeats = sorted.filter((s) => s.surprise_percent > 0).slice(0, limit);
  const topMisses = sorted.filter((s) => s.surprise_percent < 0).slice(-limit).reverse();

  return { topBeats, topMisses };
}
