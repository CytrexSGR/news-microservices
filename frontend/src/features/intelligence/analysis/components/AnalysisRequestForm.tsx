/**
 * AnalysisRequestForm - Form to submit article for analysis
 *
 * Allows users to configure and trigger content analysis for an article.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Play, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAnalyzeArticle } from '../api/useAnalyzeArticle';
import { AnalysisStatusBadge } from './AnalysisStatusBadge';
import type { AnalyzeArticleRequest } from '../types/analysis.types';

interface AnalysisRequestFormProps {
  /** Pre-filled article ID */
  initialArticleId?: string;
  /** Callback when analysis is submitted */
  onSubmit?: (articleId: string) => void;
  /** Callback when analysis completes */
  onSuccess?: (articleId: string, jobId: string) => void;
  /** Show compact version */
  compact?: boolean;
  className?: string;
}

interface AnalysisOptions {
  forceReanalyze: boolean;
  includeEntities: boolean;
  includeSentiment: boolean;
  includeTopics: boolean;
  includeNarrativeFrames: boolean;
}

const defaultOptions: AnalysisOptions = {
  forceReanalyze: false,
  includeEntities: true,
  includeSentiment: true,
  includeTopics: true,
  includeNarrativeFrames: false,
};

export function AnalysisRequestForm({
  initialArticleId = '',
  onSubmit,
  onSuccess,
  compact = false,
  className,
}: AnalysisRequestFormProps) {
  const [articleId, setArticleId] = useState(initialArticleId);
  const [options, setOptions] = useState<AnalysisOptions>(defaultOptions);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { mutate: analyzeArticle, isPending, isSuccess, isError, error, data } = useAnalyzeArticle({
    onSuccess: (result) => {
      onSuccess?.(result.article_id, result.job_id);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!articleId.trim()) return;

    const request: AnalyzeArticleRequest = {
      article_id: articleId.trim(),
      force_reanalyze: options.forceReanalyze,
      include_entities: options.includeEntities,
      include_sentiment: options.includeSentiment,
      include_topics: options.includeTopics,
      include_narrative_frames: options.includeNarrativeFrames,
    };

    onSubmit?.(articleId.trim());
    analyzeArticle(request);
  };

  const handleOptionChange = (key: keyof AnalysisOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (compact) {
    return (
      <form onSubmit={handleSubmit} className={cn('flex gap-2', className)}>
        <Input
          placeholder="Article ID"
          value={articleId}
          onChange={(e) => setArticleId(e.target.value)}
          disabled={isPending}
          className="flex-1"
        />
        <Button type="submit" disabled={!articleId.trim() || isPending}>
          {isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          <span className="ml-2">Analyze</span>
        </Button>
      </form>
    );
  }

  return (
    <Card className={className}>
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <CardTitle>Analyze Article</CardTitle>
          <CardDescription>
            Submit an article for content analysis including entity extraction,
            sentiment analysis, and topic classification.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Article ID input */}
          <div className="space-y-2">
            <Label htmlFor="articleId">Article ID</Label>
            <Input
              id="articleId"
              placeholder="Enter article ID (e.g., uuid or feed-item-id)"
              value={articleId}
              onChange={(e) => setArticleId(e.target.value)}
              disabled={isPending}
            />
          </div>

          {/* Quick options */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="forceReanalyze"
              checked={options.forceReanalyze}
              onCheckedChange={() => handleOptionChange('forceReanalyze')}
              disabled={isPending}
            />
            <Label htmlFor="forceReanalyze" className="text-sm text-muted-foreground">
              Force re-analysis (even if already analyzed)
            </Label>
          </div>

          {/* Advanced options toggle */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </Button>

          {/* Advanced options */}
          {showAdvanced && (
            <div className="space-y-3 p-4 rounded-lg border bg-muted/50">
              <p className="text-sm font-medium">Include in Analysis:</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeEntities"
                    checked={options.includeEntities}
                    onCheckedChange={() => handleOptionChange('includeEntities')}
                    disabled={isPending}
                  />
                  <Label htmlFor="includeEntities" className="text-sm">
                    Entity Extraction
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeSentiment"
                    checked={options.includeSentiment}
                    onCheckedChange={() => handleOptionChange('includeSentiment')}
                    disabled={isPending}
                  />
                  <Label htmlFor="includeSentiment" className="text-sm">
                    Sentiment Analysis
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeTopics"
                    checked={options.includeTopics}
                    onCheckedChange={() => handleOptionChange('includeTopics')}
                    disabled={isPending}
                  />
                  <Label htmlFor="includeTopics" className="text-sm">
                    Topic Classification
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeNarrativeFrames"
                    checked={options.includeNarrativeFrames}
                    onCheckedChange={() => handleOptionChange('includeNarrativeFrames')}
                    disabled={isPending}
                  />
                  <Label htmlFor="includeNarrativeFrames" className="text-sm">
                    Narrative Frames
                  </Label>
                </div>
              </div>
            </div>
          )}

          {/* Success message */}
          {isSuccess && data && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Analysis Started</AlertTitle>
              <AlertDescription className="flex items-center gap-2">
                <span>Job ID: {data.job_id}</span>
                <AnalysisStatusBadge status={data.status} size="sm" />
                {data.estimated_time_seconds && (
                  <span className="text-muted-foreground">
                    (Est. {data.estimated_time_seconds}s)
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Error message */}
          {isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Analysis Failed</AlertTitle>
              <AlertDescription>
                {error?.message || 'An error occurred while submitting the analysis request.'}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>

        <CardFooter>
          <Button
            type="submit"
            disabled={!articleId.trim() || isPending}
            className="w-full"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Start Analysis
              </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
