/**
 * ResearchResultPage
 *
 * Detailed view of a single research result:
 * - Full result content
 * - Sources list
 * - Key points extraction
 * - Export options
 * - Cancel/Retry actions
 */

import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Clock,
  Zap,
  Coins,
  Calendar,
  RotateCcw,
  Ban,
  Copy,
  Check,
  FileText,
} from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import {
  useResearchTask,
  useCancelResearch,
  useRetryResearch,
} from '../api';
import { ResearchStatusBadge } from '../components/ResearchStatusBadge';
import { ResearchExportButton } from '../components/ResearchExportButton';
import { ResearchSourcesList } from '../components/ResearchSourcesList';
import { KeyPointsList } from '../components/KeyPointsList';
import type { ResearchSource } from '../types';

export function ResearchResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const taskId = id ? parseInt(id, 10) : undefined;

  const { data: task, isLoading, isError } = useResearchTask(taskId);
  const cancelMutation = useCancelResearch();
  const retryMutation = useRetryResearch();

  const [copied, setCopied] = useState(false);

  if (!taskId) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-lg font-medium">Invalid research ID</p>
        <Button variant="link" asChild className="mt-2">
          <Link to="/research">Back to Research</Link>
        </Button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isError || !task) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-lg font-medium">Failed to load research</p>
        <Button variant="link" asChild className="mt-2">
          <Link to="/research">Back to Research</Link>
        </Button>
      </div>
    );
  }

  const canCancel = task.status === 'pending' || task.status === 'processing';
  const canRetry = task.status === 'failed';
  const canExport = task.status === 'completed';

  // Extract result content
  const getResultContent = () => {
    if (!task.result) return null;

    if (typeof task.result === 'object') {
      if ('answer' in task.result && typeof task.result.answer === 'string') {
        return task.result.answer;
      }
      if ('content' in task.result && typeof task.result.content === 'string') {
        return task.result.content;
      }
      if ('summary' in task.result && typeof task.result.summary === 'string') {
        return task.result.summary;
      }
    }
    return null;
  };

  // Extract key points
  const getKeyPoints = (): string[] => {
    if (!task.result || typeof task.result !== 'object') return [];

    if ('key_points' in task.result && Array.isArray(task.result.key_points)) {
      return task.result.key_points as string[];
    }
    if ('bullets' in task.result && Array.isArray(task.result.bullets)) {
      return task.result.bullets as string[];
    }
    return [];
  };

  // Extract sources
  const getSources = (): ResearchSource[] => {
    if (!task.result || typeof task.result !== 'object') return [];

    if ('citations' in task.result && Array.isArray(task.result.citations)) {
      return (task.result.citations as Array<{
        url?: string;
        title?: string;
        snippet?: string;
        domain?: string;
      }>).map((c) => ({
        url: c.url || '',
        title: c.title || 'Untitled',
        snippet: c.snippet || '',
        relevance_score: 0.5,
        domain: c.domain || new URL(c.url || 'https://unknown.com').hostname,
      }));
    }
    return [];
  };

  const resultContent = getResultContent();
  const keyPoints = getKeyPoints();
  const sources = getSources();

  const handleCopyResult = async () => {
    if (resultContent) {
      await navigator.clipboard.writeText(resultContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/research')}
            className="mt-1"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>

          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-xl font-semibold text-foreground">
                Research #{task.id}
              </h1>
              <ResearchStatusBadge status={task.status} />
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Zap className="h-3.5 w-3.5" />
                {task.model_name}
              </span>
              <span className="flex items-center gap-1">
                <Coins className="h-3.5 w-3.5" />
                ${task.cost.toFixed(4)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {task.tokens_used.toLocaleString()} tokens
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {formatDate(task.created_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {canCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelMutation.mutate(task.id)}
              disabled={cancelMutation.isPending}
              className="gap-1"
            >
              <Ban className="h-4 w-4" />
              Cancel
            </Button>
          )}
          {canRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => retryMutation.mutate(task.id)}
              disabled={retryMutation.isPending}
              className="gap-1"
            >
              <RotateCcw className="h-4 w-4" />
              Retry
            </Button>
          )}
          {canExport && <ResearchExportButton taskId={task.id} />}
        </div>
      </div>

      {/* Query */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-2">
          Query
        </h2>
        <p className="text-foreground">{task.query}</p>
      </div>

      {/* Error Message */}
      {task.status === 'failed' && task.error_message && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h2 className="text-sm font-medium text-destructive mb-2 flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            Error
          </h2>
          <p className="text-destructive">{task.error_message}</p>
        </div>
      )}

      {/* Processing State */}
      {(task.status === 'pending' || task.status === 'processing') && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-8 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-blue-500 font-medium">
            {task.status === 'pending' ? 'Queued for processing...' : 'Processing your research...'}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            This page will update automatically when complete
          </p>
        </div>
      )}

      {/* Result Content */}
      {task.status === 'completed' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Result */}
            {resultContent && (
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-medium text-foreground flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    Result
                  </h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyResult}
                    className="gap-1"
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="whitespace-pre-wrap">{resultContent}</p>
                </div>
              </div>
            )}

            {/* Key Points */}
            {keyPoints.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-6">
                <KeyPointsList points={keyPoints} />
              </div>
            )}

            {/* Raw Result (fallback) */}
            {!resultContent && task.result && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="font-medium text-foreground mb-4">Raw Result</h2>
                <pre className="text-sm text-foreground whitespace-pre-wrap overflow-x-auto bg-muted p-4 rounded-lg">
                  {JSON.stringify(task.result, null, 2)}
                </pre>
              </div>
            )}

            {/* Structured Data */}
            {task.structured_data && (
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="font-medium text-foreground mb-4">
                  Structured Data
                </h2>
                <pre className="text-sm text-foreground whitespace-pre-wrap overflow-x-auto bg-muted p-4 rounded-lg">
                  {JSON.stringify(task.structured_data, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Sources */}
            {sources.length > 0 ? (
              <div className="bg-card border border-border rounded-lg p-6">
                <ResearchSourcesList taskId={task.id} sources={sources} />
              </div>
            ) : (
              <div className="bg-card border border-border rounded-lg p-6">
                <ResearchSourcesList taskId={task.id} />
              </div>
            )}

            {/* Task Details */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="font-medium text-foreground mb-4">Details</h3>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Task ID</dt>
                  <dd className="text-foreground font-mono">#{task.id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Depth</dt>
                  <dd className="text-foreground capitalize">{task.depth}</dd>
                </div>
                {task.feed_id && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Feed</dt>
                    <dd className="text-foreground">{task.feed_id}</dd>
                  </div>
                )}
                {task.article_id && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Article</dt>
                    <dd className="text-foreground">{task.article_id}</dd>
                  </div>
                )}
                {task.completed_at && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Completed</dt>
                    <dd className="text-foreground">
                      {formatDate(task.completed_at)}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
