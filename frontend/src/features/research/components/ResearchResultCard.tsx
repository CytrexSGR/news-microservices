/**
 * ResearchResultCard Component
 *
 * Displays a single research task with:
 * - Status indicator (pending, processing, completed, failed)
 * - Query preview
 * - Result preview (if completed)
 * - Metadata (model, depth, cost, tokens)
 */

import { useState } from 'react';
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Coins,
  Zap,
  Calendar,
} from 'lucide-react';
import type { ResearchTaskResponse } from '../types';

interface ResearchResultCardProps {
  task: ResearchTaskResponse;
  onSelect?: (taskId: number) => void;
  isSelected?: boolean;
}

const STATUS_CONFIG = {
  pending: {
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Pending',
  },
  processing: {
    icon: Loader2,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    label: 'Processing',
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Completed',
  },
  failed: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Failed',
  },
};

export function ResearchResultCard({
  task,
  onSelect,
  isSelected = false,
}: ResearchResultCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusConfig = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;
  const StatusIcon = statusConfig.icon;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const truncateQuery = (query: string, maxLength = 100) => {
    if (query.length <= maxLength) return query;
    return query.slice(0, maxLength) + '...';
  };

  const getResultPreview = () => {
    if (!task.result) return null;

    // Handle different result formats
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
    return JSON.stringify(task.result).slice(0, 200);
  };

  return (
    <div
      className={`border rounded-lg transition-all ${
        isSelected
          ? 'border-primary bg-primary/5'
          : 'border-border bg-card hover:border-primary/50'
      }`}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer"
        onClick={() => onSelect?.(task.id)}
      >
        <div className="flex items-start justify-between gap-4">
          {/* Status Badge */}
          <div
            className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
          >
            <StatusIcon
              className={`h-3.5 w-3.5 ${statusConfig.animate ? 'animate-spin' : ''}`}
            />
            {statusConfig.label}
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {task.model_name}
            </span>
            <span className="flex items-center gap-1">
              <Coins className="h-3 w-3" />
              ${task.cost.toFixed(4)}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(task.created_at)}
            </span>
          </div>
        </div>

        {/* Query */}
        <p className="mt-3 text-sm text-foreground">
          {truncateQuery(task.query)}
        </p>

        {/* Error Message */}
        {task.status === 'failed' && task.error_message && (
          <div className="mt-2 p-2 bg-destructive/10 rounded text-xs text-destructive">
            {task.error_message}
          </div>
        )}

        {/* Result Preview */}
        {task.status === 'completed' && getResultPreview() && (
          <div className="mt-3 p-3 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground line-clamp-2">
              {getResultPreview()}
            </p>
          </div>
        )}

        {/* Expand Button */}
        {task.status === 'completed' && task.result && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3 w-3" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" />
                Show full result
              </>
            )}
          </button>
        )}
      </div>

      {/* Expanded Content */}
      {expanded && task.status === 'completed' && task.result && (
        <div className="px-4 pb-4 border-t border-border">
          <div className="mt-4 space-y-4">
            {/* Full Result */}
            <div className="p-4 bg-muted/30 rounded-lg">
              <pre className="text-sm text-foreground whitespace-pre-wrap overflow-x-auto">
                {JSON.stringify(task.result, null, 2)}
              </pre>
            </div>

            {/* Structured Data */}
            {task.structured_data && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">
                  Structured Data
                </h4>
                <pre className="p-4 bg-muted/30 rounded-lg text-sm text-foreground whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(task.structured_data, null, 2)}
                </pre>
              </div>
            )}

            {/* Citations */}
            {task.result &&
              typeof task.result === 'object' &&
              'citations' in task.result &&
              Array.isArray(task.result.citations) && (
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-2">
                    Citations ({(task.result.citations as Array<{ url?: string; title?: string }>).length})
                  </h4>
                  <ul className="space-y-1">
                    {(task.result.citations as Array<{ url?: string; title?: string }>).map((citation, idx) => (
                      <li key={idx} className="text-sm">
                        <a
                          href={citation.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1"
                        >
                          {citation.title || citation.url}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* Token Usage */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t border-border">
              <span>Tokens: {task.tokens_used.toLocaleString()}</span>
              <span>Depth: {task.depth}</span>
              {task.completed_at && (
                <span>
                  Completed: {new Date(task.completed_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
