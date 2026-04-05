/**
 * ResearchSourcesList Component
 *
 * Displays a list of sources for a research task with:
 * - Source links with domain and title
 * - Relevance scores
 * - Snippets preview
 * - Published dates
 */

import {
  ExternalLink,
  Globe,
  BarChart2,
  Calendar,
  Loader2,
  AlertCircle,
  Link2,
} from 'lucide-react';
import { useResearchSources } from '../api';
import type { ResearchSource } from '../types';

interface ResearchSourcesListProps {
  taskId: number;
  sources?: ResearchSource[];
  showLoadingState?: boolean;
}

function SourceCard({ source }: { source: ResearchSource }) {
  const relevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500 bg-green-500/10';
    if (score >= 0.5) return 'text-yellow-500 bg-yellow-500/10';
    return 'text-red-500 bg-red-500/10';
  };

  return (
    <div className="border border-border rounded-lg p-4 bg-card hover:border-primary/50 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-foreground hover:text-primary transition-colors flex items-center gap-2 group"
          >
            <span className="truncate">{source.title || 'Untitled Source'}</span>
            <ExternalLink className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
          </a>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <Globe className="h-3 w-3" />
            <span className="truncate">{source.domain}</span>
          </div>
        </div>

        {/* Relevance Score */}
        <div
          className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${relevanceColor(
            source.relevance_score
          )}`}
        >
          <BarChart2 className="h-3 w-3" />
          {Math.round(source.relevance_score * 100)}%
        </div>
      </div>

      {/* Snippet */}
      {source.snippet && (
        <p className="mt-3 text-sm text-muted-foreground line-clamp-3">
          {source.snippet}
        </p>
      )}

      {/* Footer */}
      {source.published_date && (
        <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
          <Calendar className="h-3 w-3" />
          {new Date(source.published_date).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

export function ResearchSourcesList({
  taskId,
  sources: providedSources,
  showLoadingState = true,
}: ResearchSourcesListProps) {
  // Only fetch if sources not provided
  const { data, isLoading, isError } = useResearchSources(
    providedSources ? undefined : taskId
  );

  const sources = providedSources || data?.sources || [];

  if (showLoadingState && isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading sources...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center py-8 text-destructive">
        <AlertCircle className="h-5 w-5 mr-2" />
        Failed to load sources
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <Link2 className="h-8 w-8 mb-2 opacity-50" />
        <p className="text-sm">No sources available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
          <Link2 className="h-4 w-4 text-primary" />
          Sources ({sources.length})
        </h4>
      </div>

      <div className="space-y-3">
        {sources.map((source, index) => (
          <SourceCard key={`${source.url}-${index}`} source={source} />
        ))}
      </div>
    </div>
  );
}
