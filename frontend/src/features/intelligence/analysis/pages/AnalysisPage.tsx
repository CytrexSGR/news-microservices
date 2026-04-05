/**
 * AnalysisPage - Main analysis request page
 *
 * Allows users to submit articles for analysis and monitor progress.
 */
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/Button';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { RefreshCw, ArrowRight, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AnalysisRequestForm } from '../components/AnalysisRequestForm';
import { AnalysisStatusBadge } from '../components/AnalysisStatusBadge';
import { AnalysisResultCard } from '../components/AnalysisResultCard';
import { useAnalysisStatus } from '../api/useAnalysisStatus';
import { useAnalysisResult } from '../api/useAnalysisResult';

export function AnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeArticleId, setActiveArticleId] = useState<string | null>(
    searchParams.get('articleId')
  );

  // Status polling
  const {
    data: statusData,
    isLoading: isLoadingStatus,
    status,
    progressPercent,
    errorMessage,
    isPolling,
    isCompleted,
    isFailed,
    refetch: refetchStatus,
  } = useAnalysisStatus({
    articleId: activeArticleId || '',
    enabled: !!activeArticleId,
    pollingInterval: 2000,
  });

  // Fetch result when completed
  const {
    result,
    isLoading: isLoadingResult,
    error: resultError,
  } = useAnalysisResult({
    articleId: activeArticleId || '',
    enabled: !!activeArticleId && isCompleted,
  });

  // Update URL when article ID changes
  useEffect(() => {
    if (activeArticleId) {
      setSearchParams({ articleId: activeArticleId });
    } else {
      setSearchParams({});
    }
  }, [activeArticleId, setSearchParams]);

  const handleAnalysisSubmit = (articleId: string) => {
    setActiveArticleId(articleId);
  };

  const handleAnalysisSuccess = (articleId: string, _jobId: string) => {
    setActiveArticleId(articleId);
  };

  const handleClearArticle = () => {
    setActiveArticleId(null);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Content Analysis</h1>
        <p className="text-muted-foreground mt-2">
          Analyze articles to extract entities, sentiment, topics, and narrative frames.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left column: Analysis form */}
        <div className="space-y-6">
          <AnalysisRequestForm
            initialArticleId={activeArticleId || ''}
            onSubmit={handleAnalysisSubmit}
            onSuccess={handleAnalysisSuccess}
          />

          {/* Quick tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Tips</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Article ID:</strong> Enter the UUID or feed-item-id of the article you want to analyze.
              </p>
              <p>
                <strong>Force re-analysis:</strong> Check this option if you want to re-run analysis on an article that was already processed.
              </p>
              <p>
                <strong>Narrative Frames:</strong> This is an experimental feature that identifies rhetorical patterns in the text.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right column: Status and results */}
        <div className="space-y-6">
          {activeArticleId ? (
            <>
              {/* Status card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-sm">Analysis Status</CardTitle>
                    <CardDescription className="font-mono text-xs">
                      {activeArticleId}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {status && <AnalysisStatusBadge status={status} progressPercent={progressPercent} />}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => refetchStatus()}
                      disabled={isLoadingStatus}
                    >
                      <RefreshCw className={cn('h-4 w-4', isLoadingStatus && 'animate-spin')} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Progress bar for processing */}
                  {isPolling && progressPercent !== undefined && (
                    <div className="space-y-2">
                      <Progress value={progressPercent} className="h-2" />
                      <p className="text-xs text-muted-foreground text-center">
                        Processing... {progressPercent}%
                      </p>
                    </div>
                  )}

                  {/* Timing info */}
                  {statusData && (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {statusData.started_at && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Clock className="h-4 w-4" />
                          <span>Started: {new Date(statusData.started_at).toLocaleTimeString()}</span>
                        </div>
                      )}
                      {statusData.completed_at && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span>Completed: {new Date(statusData.completed_at).toLocaleTimeString()}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Error message */}
                  {isFailed && errorMessage && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Analysis Failed</AlertTitle>
                      <AlertDescription>{errorMessage}</AlertDescription>
                    </Alert>
                  )}

                  {/* Navigation to results */}
                  {isCompleted && (
                    <div className="flex justify-end">
                      <Button variant="outline" size="sm" asChild>
                        <a href={`/intelligence/analysis/entities?articleId=${activeArticleId}`}>
                          View Entity Details
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </a>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Clear button */}
              <div className="flex justify-end">
                <Button variant="ghost" size="sm" onClick={handleClearArticle}>
                  Clear & Start New
                </Button>
              </div>

              <Separator />

              {/* Results */}
              {isCompleted && (
                <AnalysisResultCard
                  result={result}
                  isLoading={isLoadingResult}
                  error={resultError}
                  showTabs={true}
                />
              )}
            </>
          ) : (
            /* Empty state */
            <Card>
              <CardContent className="py-12 text-center">
                <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                  <AlertCircle className="h-6 w-6 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium mb-2">No Article Selected</h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Enter an article ID in the form to start content analysis.
                  Results will appear here once processing is complete.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
