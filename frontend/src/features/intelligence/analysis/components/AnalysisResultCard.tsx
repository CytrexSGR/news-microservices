/**
 * AnalysisResultCard - Full result display for article analysis
 *
 * Displays complete analysis results including entities, sentiment,
 * topics, and narrative frames.
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Hash,
  BookOpen,
  Users,
  Clock,
  DollarSign,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AnalysisResult, EntityType } from '../types/analysis.types';
import { getSentimentConfig, getEntityTypeConfig } from '../types/analysis.types';
import { EntityExtractionView } from './EntityExtractionView';
import { AnalysisStatusBadge } from './AnalysisStatusBadge';

interface AnalysisResultCardProps {
  result?: AnalysisResult | null;
  isLoading?: boolean;
  error?: Error | null;
  showTabs?: boolean;
  className?: string;
}

export function AnalysisResultCard({
  result,
  isLoading = false,
  error = null,
  showTabs = true,
  className,
}: AnalysisResultCardProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
          <Skeleton className="h-48" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Analysis Result</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            <p>Failed to load analysis result</p>
            <p className="text-sm text-muted-foreground mt-2">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Analysis Result</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No analysis result available. Submit an article for analysis.
          </div>
        </CardContent>
      </Card>
    );
  }

  const sentimentConfig = getSentimentConfig(result.sentiment.label);
  const SentimentIcon = result.sentiment.label === 'positive'
    ? TrendingUp
    : result.sentiment.label === 'negative'
    ? TrendingDown
    : Minus;

  // Group entities by type for summary
  const entitySummary = result.entities.reduce(
    (acc, entity) => {
      acc[entity.type] = (acc[entity.type] || 0) + 1;
      return acc;
    },
    {} as Record<EntityType, number>
  );

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Analysis Result
              <AnalysisStatusBadge status="completed" size="sm" />
            </CardTitle>
            <CardDescription>
              Article ID: {result.article_id}
            </CardDescription>
          </div>
          <div className="text-right text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{new Date(result.analysis_timestamp).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Summary metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Sentiment */}
          <div className={cn('p-4 rounded-lg', sentimentConfig.bgColor)}>
            <div className="flex items-center gap-2 mb-2">
              <SentimentIcon className={cn('h-5 w-5', sentimentConfig.color)} />
              <span className="text-sm font-medium">Sentiment</span>
            </div>
            <div className={cn('text-2xl font-bold', sentimentConfig.color)}>
              {result.sentiment.label.charAt(0).toUpperCase() + result.sentiment.label.slice(1)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Score: {result.sentiment.score.toFixed(2)} ({(result.sentiment.confidence * 100).toFixed(0)}%)
            </div>
          </div>

          {/* Entities */}
          <div className="p-4 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-5 w-5 text-blue-700 dark:text-blue-300" />
              <span className="text-sm font-medium">Entities</span>
            </div>
            <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
              {result.entities.length}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {Object.keys(entitySummary).length} types
            </div>
          </div>

          {/* Topics */}
          <div className="p-4 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <div className="flex items-center gap-2 mb-2">
              <Hash className="h-5 w-5 text-purple-700 dark:text-purple-300" />
              <span className="text-sm font-medium">Topics</span>
            </div>
            <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
              {result.topics.length}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              classified topics
            </div>
          </div>

          {/* Performance */}
          <div className="p-4 rounded-lg bg-amber-100 dark:bg-amber-900/30">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-5 w-5 text-amber-700 dark:text-amber-300" />
              <span className="text-sm font-medium">Performance</span>
            </div>
            <div className="text-2xl font-bold text-amber-700 dark:text-amber-300">
              {(result.latency_ms / 1000).toFixed(1)}s
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              ${result.cost_usd.toFixed(4)} cost
            </div>
          </div>
        </div>

        {/* Topics */}
        {result.topics.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <Hash className="h-4 w-4" />
              Topics
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.topics.map((topic, idx) => (
                <Badge key={idx} variant="secondary">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Narrative Frames */}
        {result.narrative_frames.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Narrative Frames
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.narrative_frames.map((frame, idx) => (
                <Badge key={idx} variant="outline" className="bg-teal-100 dark:bg-teal-900/30">
                  {frame}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Entities (detailed or in tab) */}
        {showTabs ? (
          <Tabs defaultValue="entities" className="space-y-4">
            <TabsList>
              <TabsTrigger value="entities">
                Entities ({result.entities.length})
              </TabsTrigger>
              <TabsTrigger value="summary">
                Entity Summary
              </TabsTrigger>
            </TabsList>

            <TabsContent value="entities">
              <EntityExtractionView
                entities={result.entities}
                showFilters={true}
                maxInitialItems={15}
              />
            </TabsContent>

            <TabsContent value="summary">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(entitySummary)
                  .sort(([, a], [, b]) => b - a)
                  .map(([type, count]) => {
                    const config = getEntityTypeConfig(type as EntityType);
                    return (
                      <div
                        key={type}
                        className={cn('p-3 rounded-lg', config.bgColor)}
                      >
                        <div className={cn('font-medium', config.color)}>
                          {config.label}
                        </div>
                        <div className="text-2xl font-bold">{count}</div>
                      </div>
                    );
                  })}
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <EntityExtractionView
            entities={result.entities}
            showFilters={true}
            maxInitialItems={10}
          />
        )}
      </CardContent>
    </Card>
  );
}
