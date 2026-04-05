/**
 * EarningsTranscriptViewer Component
 * Full transcript display with search and key points
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  FileText,
  Search,
  Users,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Quote,
  Download,
} from 'lucide-react';
import {
  useEarningsTranscript,
  searchTranscript,
  extractMentionedMetrics,
  getExecutiveSummary,
} from '../../api/useEarningsTranscript';
import type { EarningsTranscript, EarningsParticipant } from '../../types/earnings.types';

interface EarningsTranscriptViewerProps {
  symbol: string;
  quarter: string;
  year: number;
  className?: string;
}

export function EarningsTranscriptViewer({
  symbol,
  quarter,
  year,
  className,
}: EarningsTranscriptViewerProps) {
  const { data: transcript, isLoading, error } = useEarningsTranscript(symbol, quarter, year);
  const [searchQuery, setSearchQuery] = useState('');
  const [showParticipants, setShowParticipants] = useState(false);
  const [showFullContent, setShowFullContent] = useState(false);

  const searchResults = useMemo(() => {
    if (!transcript || !searchQuery.trim()) return [];
    return searchTranscript(transcript, searchQuery);
  }, [transcript, searchQuery]);

  const mentionedMetrics = useMemo(() => {
    if (!transcript) return [];
    return extractMentionedMetrics(transcript);
  }, [transcript]);

  const executiveSummary = useMemo(() => {
    if (!transcript) return [];
    return getExecutiveSummary(transcript);
  }, [transcript]);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load transcript for {symbol} {quarter} {year}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!transcript) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No transcript available for {symbol} {quarter} {year}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {symbol} Earnings Call - {quarter} {year}
          </CardTitle>

          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {new Date(transcript.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search within transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Key Points */}
        {executiveSummary.length > 0 && (
          <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="h-4 w-4 text-primary" />
              <span className="font-semibold text-sm">Key Points</span>
            </div>
            <ul className="space-y-2">
              {executiveSummary.map((point, index) => (
                <li key={index} className="text-sm flex gap-2">
                  <span className="text-primary">-</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Mentioned Metrics */}
        {mentionedMetrics.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-semibold">Mentioned Metrics</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {mentionedMetrics.slice(0, 10).map((metric, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {metric.text}
                </Badge>
              ))}
              {mentionedMetrics.length > 10 && (
                <Badge variant="secondary" className="text-xs">
                  +{mentionedMetrics.length - 10} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Participants */}
        <Collapsible open={showParticipants} onOpenChange={setShowParticipants}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <span>Participants ({transcript.participants.length})</span>
              </div>
              {showParticipants ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 mt-2">
              {transcript.participants.map((participant, index) => (
                <ParticipantCard key={index} participant={participant} />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Search Results or Full Transcript */}
        {searchQuery.trim() ? (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Found {searchResults.length} matches for "{searchQuery}"
            </div>
            {searchResults.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No matches found
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {searchResults.map((result, index) => (
                  <SearchResultItem
                    key={index}
                    result={result}
                    query={searchQuery}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            <Collapsible open={showFullContent} onOpenChange={setShowFullContent}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <div className="flex items-center gap-2">
                    <Quote className="h-4 w-4" />
                    <span>Full Transcript</span>
                  </div>
                  {showFullContent ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-4 p-4 rounded-lg border bg-muted/30 max-h-[600px] overflow-y-auto">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {transcript.content}
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Preview when collapsed */}
            {!showFullContent && (
              <div className="mt-4 p-4 rounded-lg border bg-muted/30">
                <div className="text-sm text-muted-foreground line-clamp-6 leading-relaxed">
                  {transcript.content.slice(0, 500)}...
                </div>
                <Button
                  variant="link"
                  className="mt-2 p-0 h-auto text-primary"
                  onClick={() => setShowFullContent(true)}
                >
                  Read full transcript
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface ParticipantCardProps {
  participant: EarningsParticipant;
}

function ParticipantCard({ participant }: ParticipantCardProps) {
  return (
    <div className="p-3 rounded-lg border bg-muted/30">
      <div className="font-medium text-sm">{participant.name}</div>
      <div className="text-xs text-muted-foreground">{participant.role}</div>
    </div>
  );
}

interface SearchResultItemProps {
  result: {
    paragraph: string;
    speaker?: string;
    matchCount: number;
  };
  query: string;
}

function SearchResultItem({ result, query }: SearchResultItemProps) {
  // Highlight matching terms
  const highlightedText = useMemo(() => {
    const terms = query.toLowerCase().split(/\s+/);
    let text = result.paragraph;

    terms.forEach((term) => {
      const regex = new RegExp(`(${term})`, 'gi');
      text = text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-900">$1</mark>');
    });

    return text;
  }, [result.paragraph, query]);

  return (
    <div className="p-3 rounded-lg border hover:bg-muted/50 transition-colors">
      {result.speaker && (
        <div className="text-xs font-semibold text-primary mb-1">{result.speaker}</div>
      )}
      <div
        className="text-sm leading-relaxed"
        dangerouslySetInnerHTML={{ __html: highlightedText }}
      />
      <div className="mt-2 text-xs text-muted-foreground">
        {result.matchCount} match{result.matchCount > 1 ? 'es' : ''}
      </div>
    </div>
  );
}

export default EarningsTranscriptViewer;
