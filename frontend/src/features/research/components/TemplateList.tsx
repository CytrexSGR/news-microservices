/**
 * TemplateList Component
 *
 * Displays available research templates with:
 * - Template cards with preview
 * - Quick apply functionality
 * - Usage statistics
 */

import { useState } from 'react';
import {
  FileText,
  Play,
  Loader2,
  ChevronDown,
  ChevronUp,
  Star,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useResearchTemplates, useApplyTemplate } from '../api';
import type { TemplateResponse } from '../types';

interface TemplateListProps {
  onTaskCreated?: (taskId: number) => void;
  feedId?: string;
  articleId?: string;
}

export function TemplateList({
  onTaskCreated,
  feedId,
  articleId,
}: TemplateListProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { data: templates, isLoading, isError } = useResearchTemplates();
  const applyTemplate = useApplyTemplate();

  const handleApply = async (template: TemplateResponse) => {
    try {
      const result = await applyTemplate.mutateAsync({
        templateId: template.id,
        applyData: {
          ...(feedId && { feed_id: feedId }),
          ...(articleId && { article_id: articleId }),
        },
      });
      onTaskCreated?.(result.id);
    } catch {
      // Error handled in mutation hook
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-12 text-destructive">
        Failed to load templates
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No templates available</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {templates.map((template) => (
        <div
          key={template.id}
          className="border border-border rounded-lg bg-card overflow-hidden"
        >
          {/* Header */}
          <div className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <h3 className="font-medium text-foreground">{template.name}</h3>
              </div>
              {template.is_public && (
                <span className="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full">
                  Public
                </span>
              )}
            </div>

            {template.description && (
              <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                {template.description}
              </p>
            )}

            {/* Stats */}
            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Star className="h-3 w-3" />
                {template.usage_count} uses
              </span>
              <span>Model: {template.default_model}</span>
              <span>Depth: {template.default_depth}</span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-4">
              <Button
                size="sm"
                onClick={() => handleApply(template)}
                disabled={applyTemplate.isPending}
                className="gap-1"
              >
                {applyTemplate.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                Apply
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  setExpandedId(expandedId === template.id ? null : template.id)
                }
                className="gap-1"
              >
                {expandedId === template.id ? (
                  <>
                    <ChevronUp className="h-3 w-3" />
                    Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" />
                    More
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Expanded Content */}
          {expandedId === template.id && (
            <div className="px-4 pb-4 border-t border-border bg-muted/30">
              <div className="pt-4 space-y-3">
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-1">
                    Query Template
                  </h4>
                  <p className="text-sm text-foreground bg-background p-2 rounded">
                    {template.query_template}
                  </p>
                </div>

                {template.parameters &&
                  Object.keys(template.parameters).length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-muted-foreground mb-1">
                        Parameters
                      </h4>
                      <pre className="text-xs text-foreground bg-background p-2 rounded overflow-x-auto">
                        {JSON.stringify(template.parameters, null, 2)}
                      </pre>
                    </div>
                  )}

                {template.research_function && (
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-1">
                      Research Function
                    </h4>
                    <span className="text-sm font-mono text-primary">
                      {template.research_function}
                    </span>
                  </div>
                )}

                {template.last_used_at && (
                  <p className="text-xs text-muted-foreground">
                    Last used: {new Date(template.last_used_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
