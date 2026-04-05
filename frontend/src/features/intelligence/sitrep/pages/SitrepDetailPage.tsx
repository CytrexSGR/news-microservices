/**
 * SitrepDetailPage - Full SITREP report view
 *
 * Displays complete SITREP with:
 * - Executive summary
 * - Key developments with risk assessment
 * - Top stories
 * - Key entities
 * - Sentiment analysis
 * - Emerging signals
 */

import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  AlertTriangle,
  Loader2,
  FileText,
  TrendingUp,
  Users,
  BarChart3,
  Zap,
  Shield,
  Calendar,
  Trash2,
  ExternalLink,
} from 'lucide-react';
import { useSitrep, useMarkSitrepReviewed, useDeleteSitrep } from '../api/useSitreps';
import { format, formatDistanceToNow } from 'date-fns';
import type { KeyDevelopment, TopStory, KeyEntity, EmergingSignal } from '../types/sitrep.types';

// =============================================================================
// Sub-Components
// =============================================================================

function RiskBadge({ level }: { level: string }) {
  const colors = {
    low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[level as keyof typeof colors] || colors.medium}`}>
      {level.toUpperCase()}
    </span>
  );
}

function KeyDevelopmentCard({ development }: { development: KeyDevelopment }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold">{development.title}</h4>
        {development.risk_assessment && <RiskBadge level={development.risk_assessment.level} />}
      </div>
      <p className="text-sm text-muted-foreground mb-3">{development.summary}</p>
      <div className="space-y-2 text-sm">
        <div>
          <span className="font-medium">Significance: </span>
          <span className="text-muted-foreground">{development.significance}</span>
        </div>
        {development.risk_assessment && (
          <div>
            <span className="font-medium">Risk Category: </span>
            <span className="text-muted-foreground capitalize">{development.risk_assessment.category}</span>
          </div>
        )}
        {development.related_entities && development.related_entities.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {development.related_entities.map((entity, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-secondary rounded-full text-xs">
                {entity}
              </span>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

function TopStoryCard({ story }: { story: TopStory }) {
  // Support both GPT-generated (cluster_id) and n8n-generated (id) SITREPs
  const clusterId = story.cluster_id || story.id;
  const storyTitle = story.title || story.label;

  return (
    <Card className="p-4 hover:bg-muted/50 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {story.is_breaking && (
              <span className="px-2 py-0.5 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full text-xs font-medium flex items-center gap-1">
                <Zap className="h-3 w-3" />
                Breaking
              </span>
            )}
            {story.category && (
              <span className="px-2 py-0.5 bg-secondary rounded-full text-xs capitalize">
                {story.category}
              </span>
            )}
          </div>
          {clusterId ? (
            <Link
              to={`/intelligence/events/clusters/${clusterId}`}
              className="font-semibold line-clamp-2 hover:text-primary hover:underline flex items-center gap-1"
            >
              {storyTitle}
              <ExternalLink className="h-3 w-3 opacity-50" />
            </Link>
          ) : (
            <h4 className="font-semibold line-clamp-2">{storyTitle}</h4>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
        <span>{story.article_count} articles</span>
        {story.tension_score != null && <span>Tension: {story.tension_score.toFixed(1)}/10</span>}
        {story.similarity != null && <span>Match: {Math.round(story.similarity * 100)}%</span>}
      </div>
    </Card>
  );
}

function EntityBadge({ entity }: { entity: KeyEntity }) {
  const typeColors: Record<string, string> = {
    person: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    organization: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    location: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm flex items-center gap-2 ${typeColors[entity.type] || 'bg-secondary'}`}>
      {entity.name}
      <span className="text-xs opacity-75">({entity.mention_count})</span>
    </span>
  );
}

function SentimentChart({ sentiment }: { sentiment: { positive_percent?: number; negative_percent?: number; neutral_percent?: number } }) {
  const positive = sentiment.positive_percent ?? 0;
  const neutral = sentiment.neutral_percent ?? 0;
  const negative = sentiment.negative_percent ?? 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm w-20">Positive</span>
        <div className="flex-1 bg-secondary rounded-full h-3">
          <div
            className="bg-green-500 h-full rounded-full"
            style={{ width: `${positive}%` }}
          />
        </div>
        <span className="text-sm w-12 text-right">{positive.toFixed(0)}%</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm w-20">Neutral</span>
        <div className="flex-1 bg-secondary rounded-full h-3">
          <div
            className="bg-gray-400 h-full rounded-full"
            style={{ width: `${neutral}%` }}
          />
        </div>
        <span className="text-sm w-12 text-right">{neutral.toFixed(0)}%</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm w-20">Negative</span>
        <div className="flex-1 bg-secondary rounded-full h-3">
          <div
            className="bg-red-500 h-full rounded-full"
            style={{ width: `${negative}%` }}
          />
        </div>
        <span className="text-sm w-12 text-right">{negative.toFixed(0)}%</span>
      </div>
    </div>
  );
}

function EmergingSignalCard({ signal }: { signal: EmergingSignal }) {
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <TrendingUp className="h-5 w-5 text-primary mt-0.5" />
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full capitalize">
              {signal.signal_type}
            </span>
            <span className="text-xs text-muted-foreground">
              {Math.round(signal.confidence * 100)}% confidence
            </span>
          </div>
          <p className="text-sm">{signal.description}</p>
          {signal.related_entities.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {signal.related_entities.map((entity, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-secondary rounded-full text-xs">
                  {entity}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export function SitrepDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: sitrep, isLoading, error } = useSitrep(id || '');
  const markReviewedMutation = useMarkSitrepReviewed();
  const deleteMutation = useDeleteSitrep();

  const handleMarkReviewed = async () => {
    if (!id) return;
    await markReviewedMutation.mutateAsync({ id, reviewed: !sitrep?.human_reviewed });
  };

  const handleDelete = async () => {
    if (!id || !confirm('Are you sure you want to delete this SITREP?')) return;
    await deleteMutation.mutateAsync(id);
    navigate('/intelligence/sitrep');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !sitrep) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/intelligence/sitrep')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to SITREPs
        </Button>
        <Card className="p-12">
          <div className="text-center text-muted-foreground">
            <AlertTriangle className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">SITREP Not Found</h3>
            <p>The requested report could not be loaded.</p>
          </div>
        </Card>
      </div>
    );
  }

  const typeColors = {
    daily: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    weekly: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    breaking: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => navigate('/intelligence/sitrep')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to SITREPs
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${typeColors[sitrep.report_type]}`}>
              {sitrep.report_type.toUpperCase()}
            </span>
            {sitrep.human_reviewed && (
              <span className="px-3 py-1 rounded-full text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" />
                Reviewed
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">{sitrep.title}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {format(new Date(sitrep.created_at), 'PPpp')}
            </span>
            <span>{sitrep.articles_analyzed} articles analyzed</span>
            {sitrep.confidence_score != null && <span>{Math.round(sitrep.confidence_score * 100)}% confidence</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkReviewed}
            disabled={markReviewedMutation.isPending}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            {sitrep.human_reviewed ? 'Unmark Reviewed' : 'Mark Reviewed'}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Executive Summary */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Executive Summary
        </h2>
        <p className="text-muted-foreground leading-relaxed">{sitrep.executive_summary}</p>
      </Card>

      {/* Key Developments */}
      {sitrep.key_developments && sitrep.key_developments.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-primary" />
            Key Developments
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sitrep.key_developments.map((dev, idx) => (
              <KeyDevelopmentCard key={idx} development={dev} />
            ))}
          </div>
        </div>
      )}

      {/* Top Stories */}
      {sitrep.top_stories && sitrep.top_stories.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Top Stories ({sitrep.top_stories.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sitrep.top_stories.map((story, idx) => (
              <TopStoryCard key={idx} story={story} />
            ))}
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Entities */}
        {sitrep.key_entities && sitrep.key_entities.length > 0 && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Key Entities
            </h2>
            <div className="flex flex-wrap gap-2">
              {sitrep.key_entities.map((entity, idx) => (
                <EntityBadge key={idx} entity={entity} />
              ))}
            </div>
          </Card>
        )}

        {/* Sentiment Summary */}
        {sitrep.sentiment_summary && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Sentiment Analysis
            </h2>
            <div className="mb-3">
              <span className="text-sm text-muted-foreground">Overall: </span>
              <span className="font-medium capitalize">{sitrep.sentiment_summary.overall}</span>
            </div>
            <SentimentChart sentiment={sitrep.sentiment_summary} />
          </Card>
        )}
      </div>

      {/* Emerging Signals */}
      {sitrep.emerging_signals && sitrep.emerging_signals.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Emerging Signals
          </h2>
          <div className="space-y-3">
            {sitrep.emerging_signals.map((signal, idx) => (
              <EmergingSignalCard key={idx} signal={signal} />
            ))}
          </div>
        </div>
      )}

      {/* Generation Metadata */}
      <Card className="p-4 bg-muted/50">
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span>Model: {sitrep.generation_model}</span>
          <span>Generation time: {(sitrep.generation_time_ms / 1000).toFixed(1)}s</span>
          {sitrep.prompt_tokens && <span>Prompt: {sitrep.prompt_tokens} tokens</span>}
          {sitrep.completion_tokens && <span>Completion: {sitrep.completion_tokens} tokens</span>}
        </div>
      </Card>
    </div>
  );
}

export default SitrepDetailPage;
