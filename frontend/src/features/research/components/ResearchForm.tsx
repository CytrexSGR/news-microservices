/**
 * ResearchForm Component
 *
 * Form to create new research tasks with:
 * - Query input
 * - Model selection (sonar, sonar-pro, sonar-reasoning-pro)
 * - Depth selection (quick, standard, deep)
 * - Optional template quick-select
 */

import { useState } from 'react';
import { Search, Loader2, Zap, Sparkles, Brain, Info } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useCreateResearchTask, useResearchTemplates } from '../api';
import type { ResearchModel, ResearchDepth, ResearchTaskCreate } from '../types';

interface ResearchFormProps {
  onTaskCreated?: (taskId: number) => void;
  feedId?: string;
  articleId?: string;
  initialQuery?: string;
}

const MODEL_OPTIONS: { value: ResearchModel; label: string; icon: React.ReactNode; description: string }[] = [
  {
    value: 'sonar',
    label: 'Sonar',
    icon: <Zap className="h-4 w-4" />,
    description: 'Fast, cost-effective research',
  },
  {
    value: 'sonar-pro',
    label: 'Sonar Pro',
    icon: <Sparkles className="h-4 w-4" />,
    description: 'Enhanced accuracy and depth',
  },
  {
    value: 'sonar-reasoning-pro',
    label: 'Reasoning Pro',
    icon: <Brain className="h-4 w-4" />,
    description: 'Complex reasoning tasks',
  },
];

const DEPTH_OPTIONS: { value: ResearchDepth; label: string; description: string }[] = [
  { value: 'quick', label: 'Quick', description: 'Fast overview (1-2 sources)' },
  { value: 'standard', label: 'Standard', description: 'Balanced research (3-5 sources)' },
  { value: 'deep', label: 'Deep', description: 'Comprehensive analysis (5+ sources)' },
];

export function ResearchForm({
  onTaskCreated,
  feedId,
  articleId,
  initialQuery = '',
}: ResearchFormProps) {
  const [query, setQuery] = useState(initialQuery);
  const [model, setModel] = useState<ResearchModel>('sonar');
  const [depth, setDepth] = useState<ResearchDepth>('standard');
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

  const { data: templates, isLoading: templatesLoading } = useResearchTemplates();
  const createTask = useCreateResearchTask();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() || query.length < 10) {
      return;
    }

    const taskData: ResearchTaskCreate = {
      query: query.trim(),
      model_name: model,
      depth,
      ...(feedId && { feed_id: feedId }),
      ...(articleId && { article_id: articleId }),
    };

    try {
      const result = await createTask.mutateAsync(taskData);
      setQuery('');
      onTaskCreated?.(result.id);
    } catch {
      // Error handled in mutation hook
    }
  };

  const handleTemplateSelect = (templateId: number) => {
    setSelectedTemplateId(templateId);
    const template = templates?.find((t) => t.id === templateId);
    if (template) {
      // Pre-fill form with template defaults
      setQuery(template.query_template);
      setModel(template.default_model as ResearchModel);
      setDepth(template.default_depth as ResearchDepth);
    }
  };

  const estimatedCost = () => {
    const baseCost = { sonar: 0.005, 'sonar-pro': 0.01, 'sonar-reasoning-pro': 0.02 };
    const depthMultiplier = { quick: 0.5, standard: 1, deep: 2 };
    return (baseCost[model] * depthMultiplier[depth]).toFixed(3);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Quick Template Select */}
      {templates && templates.length > 0 && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Quick Start Templates
          </label>
          <div className="flex flex-wrap gap-2">
            {templates.slice(0, 5).map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => handleTemplateSelect(template.id)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  selectedTemplateId === template.id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-card border-border text-muted-foreground hover:border-primary hover:text-foreground'
                }`}
              >
                {template.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Query Input */}
      <div className="space-y-2">
        <label htmlFor="research-query" className="text-sm font-medium text-foreground">
          Research Query
        </label>
        <div className="relative">
          <textarea
            id="research-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your research question (min. 10 characters)..."
            rows={4}
            className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
            required
            minLength={10}
            maxLength={2000}
          />
          <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
            {query.length}/2000
          </div>
        </div>
        {query.length > 0 && query.length < 10 && (
          <p className="text-sm text-destructive">
            Query must be at least 10 characters
          </p>
        )}
      </div>

      {/* Model Selection */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Research Model</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {MODEL_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setModel(option.value)}
              className={`p-3 rounded-lg border transition-all text-left ${
                model === option.value
                  ? 'bg-primary/10 border-primary text-foreground'
                  : 'bg-card border-border text-muted-foreground hover:border-primary/50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {option.icon}
                <span className="font-medium">{option.label}</span>
              </div>
              <p className="text-xs opacity-70">{option.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Depth Selection */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Research Depth</label>
        <div className="flex gap-2">
          {DEPTH_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setDepth(option.value)}
              className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                depth === option.value
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-card border-border text-muted-foreground hover:border-primary/50'
              }`}
              title={option.description}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Context Info */}
      {(feedId || articleId) && (
        <div className="flex items-start gap-2 p-3 bg-muted/50 rounded-lg">
          <Info className="h-4 w-4 mt-0.5 text-muted-foreground" />
          <div className="text-sm text-muted-foreground">
            This research will be linked to{' '}
            {feedId && <span className="font-medium">Feed #{feedId}</span>}
            {feedId && articleId && ' and '}
            {articleId && <span className="font-medium">Article #{articleId}</span>}
          </div>
        </div>
      )}

      {/* Cost Estimate & Submit */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="text-sm text-muted-foreground">
          Estimated cost: <span className="font-medium text-foreground">${estimatedCost()}</span>
        </div>
        <Button
          type="submit"
          disabled={createTask.isPending || query.length < 10}
          className="gap-2"
        >
          {createTask.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Start Research
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
