/**
 * Earnings Transcript Hook
 * Fetches earnings call transcripts for analysis
 */

import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { EarningsTranscript } from '../types/earnings.types';

/**
 * Fetch earnings transcript for a specific quarter
 */
export const useEarningsTranscript = (
  symbol: string,
  quarter: string,
  year: number
) => {
  return useQuery({
    queryKey: ['market', 'earnings-transcript', symbol, quarter, year],
    queryFn: () =>
      mcpClient.callTool<EarningsTranscript>('fmp_earnings_transcript', {
        symbol,
        quarter,
        year,
      }),
    enabled: !!symbol && !!quarter && !!year,
    staleTime: Infinity, // Transcripts never change
  });
};

/**
 * Fetch available transcripts for a symbol
 */
export const useAvailableTranscripts = (symbol: string) => {
  return useQuery({
    queryKey: ['market', 'earnings-transcripts', 'available', symbol],
    queryFn: () =>
      mcpClient.callTool<Array<{ quarter: string; year: number; date: string }>>(
        'fmp_available_transcripts',
        { symbol }
      ),
    enabled: !!symbol,
    staleTime: 86400000, // 24 hours
  });
};

/**
 * Fetch most recent transcript for a symbol
 */
export const useLatestTranscript = (symbol: string) => {
  return useQuery({
    queryKey: ['market', 'earnings-transcript', 'latest', symbol],
    queryFn: () =>
      mcpClient.callTool<EarningsTranscript>('fmp_latest_transcript', { symbol }),
    enabled: !!symbol,
    staleTime: 86400000, // 24 hours
  });
};

/**
 * Search within transcript content
 */
export interface TranscriptSearchResult {
  paragraph: string;
  speaker?: string;
  matchCount: number;
}

export function searchTranscript(
  transcript: EarningsTranscript,
  query: string
): TranscriptSearchResult[] {
  if (!query.trim()) return [];

  const searchTerms = query.toLowerCase().split(/\s+/);
  const paragraphs = transcript.content.split(/\n\n+/);
  const results: TranscriptSearchResult[] = [];

  paragraphs.forEach((paragraph) => {
    const lowerPara = paragraph.toLowerCase();
    let matchCount = 0;

    searchTerms.forEach((term) => {
      const regex = new RegExp(term, 'gi');
      const matches = lowerPara.match(regex);
      if (matches) matchCount += matches.length;
    });

    if (matchCount > 0) {
      // Try to extract speaker name (format: "Name: speech")
      const speakerMatch = paragraph.match(/^([^:]+):/);
      results.push({
        paragraph,
        speaker: speakerMatch ? speakerMatch[1].trim() : undefined,
        matchCount,
      });
    }
  });

  // Sort by match count descending
  return results.sort((a, b) => b.matchCount - a.matchCount);
}

/**
 * Extract key metrics mentioned in transcript
 */
export interface MentionedMetric {
  type: 'revenue' | 'earnings' | 'growth' | 'margin' | 'guidance' | 'other';
  text: string;
  value?: string;
}

const metricPatterns = [
  { type: 'revenue', pattern: /revenue[s]?\s+(?:of|was|reached|totaled)?\s*\$?[\d.,]+\s*(?:billion|million|B|M)?/gi },
  { type: 'earnings', pattern: /(?:eps|earnings per share)\s+(?:of|was)?\s*\$?[\d.]+/gi },
  { type: 'growth', pattern: /(?:growth|grew|increased)\s+(?:by|of)?\s*[\d.]+%/gi },
  { type: 'margin', pattern: /margin[s]?\s+(?:of|at|was)?\s*[\d.]+%/gi },
  { type: 'guidance', pattern: /(?:expect|anticipate|guide|outlook)[^\n.]*[\d.]+/gi },
] as const;

export function extractMentionedMetrics(transcript: EarningsTranscript): MentionedMetric[] {
  const metrics: MentionedMetric[] = [];
  const seen = new Set<string>();

  metricPatterns.forEach(({ type, pattern }) => {
    const matches = transcript.content.matchAll(pattern);
    for (const match of matches) {
      const text = match[0].trim();
      if (!seen.has(text.toLowerCase())) {
        seen.add(text.toLowerCase());
        metrics.push({
          type: type as MentionedMetric['type'],
          text,
        });
      }
    }
  });

  return metrics;
}

/**
 * Get executive summary from key points
 */
export function getExecutiveSummary(transcript: EarningsTranscript): string[] {
  if (transcript.key_points.length > 0) {
    return transcript.key_points.slice(0, 5);
  }

  // Fallback: Extract first sentence from first 5 paragraphs
  const paragraphs = transcript.content.split(/\n\n+/).slice(0, 10);
  const sentences: string[] = [];

  paragraphs.forEach((p) => {
    const firstSentence = p.match(/^[^.!?]+[.!?]/);
    if (firstSentence && firstSentence[0].length > 50) {
      sentences.push(firstSentence[0]);
    }
  });

  return sentences.slice(0, 5);
}
