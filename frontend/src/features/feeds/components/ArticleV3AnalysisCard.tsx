/**
 * ArticleV3AnalysisCard Component
 *
 * Displays Content-Analysis-V3 results for an article.
 *
 * V3 Pipeline:
 * - Tier 0: Triage decision (keep/discard, priority score, category)
 * - Tier 1: Foundation extraction (entities, relations, topics, scores)
 * - Tier 2: Specialist analysis (optional, 6 specialized modules including Bias Scorer)
 *
 * Compared to V2:
 * - 96.7% cost reduction ($0.0085 → $0.00028)
 * - Simpler architecture (4 tiers vs V2's complex agent ecosystem)
 * - Added: Simplified Political Bias Scorer (7-level scale, minimal overhead)
 * - Missing: Conflict Analysis, Intelligence Synthesis
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type {
  TriageDecision,
  Tier1Results,
  Tier2Results,
  V3Category,
} from '@/features/feeds/types/analysisV3';

interface ArticleV3AnalysisCardProps {
  /** Tier0 triage decision (always present) */
  tier0: TriageDecision;

  /** Tier1 foundation extraction (null if discarded by Tier0) */
  tier1?: Tier1Results | null;

  /** Tier2 specialist analysis (null if not run) */
  tier2?: Tier2Results | null;

  /** Optional CSS classes */
  className?: string;

  /** Compact mode for list view */
  compact?: boolean;
}

/**
 * Get color for priority score (0-10)
 */
const getPriorityColor = (score: number): string => {
  if (score >= 8) return 'bg-red-100 text-red-800 border-red-200';
  if (score >= 5) return 'bg-orange-100 text-orange-800 border-orange-200';
  if (score >= 3) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  return 'bg-gray-100 text-gray-800 border-gray-200';
};

/**
 * Get color for category
 */
const getCategoryColor = (category: V3Category): string => {
  const colors: Record<V3Category, string> = {
    CONFLICT: 'bg-red-100 text-red-800',
    FINANCE: 'bg-blue-100 text-blue-800',
    POLITICS: 'bg-purple-100 text-purple-800',
    HUMANITARIAN: 'bg-green-100 text-green-800',
    SECURITY: 'bg-orange-100 text-orange-800',
    TECHNOLOGY: 'bg-cyan-100 text-cyan-800',
    OTHER: 'bg-gray-100 text-gray-800',
  };
  return colors[category] || colors.OTHER;
};

/**
 * Get color for score (0.0-10.0)
 */
const getScoreColor = (score: number): string => {
  if (score >= 7.0) return 'text-green-600 font-semibold';
  if (score >= 4.0) return 'text-yellow-600';
  return 'text-red-600';
};

export function ArticleV3AnalysisCard({
  tier0,
  tier1,
  tier2,
  className = '',
  compact = false,
}: ArticleV3AnalysisCardProps) {
  // Determine if article was discarded
  const discarded = !tier0.keep;

  if (compact) {
    // Compact view for article list
    return (
      <div className={`flex items-center gap-2 flex-wrap ${className}`}>
        {/* Priority Score */}
        <Badge className={getPriorityColor(tier0.PriorityScore)}>
          P{tier0.PriorityScore}
        </Badge>

        {/* Category */}
        <Badge className={getCategoryColor(tier0.category)}>
          {tier0.category}
        </Badge>

        {/* Discarded indicator */}
        {discarded && (
          <Badge variant="outline" className="bg-gray-50 text-gray-600">
            Discarded
          </Badge>
        )}

        {/* Entity count (if available) */}
        {tier1 && tier1.entities.length > 0 && (
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            {tier1.entities.length} entities
          </Badge>
        )}

        {/* Specialist count (if available) */}
        {tier2 && tier2.specialists_executed > 0 && (
          <Badge variant="outline" className="bg-purple-50 text-purple-700">
            {tier2.specialists_executed} specialists
          </Badge>
        )}

        {/* Cost (tiny badge) */}
        <span className="text-xs text-gray-500">
          ${(tier0.cost_usd + (tier1?.cost_usd || 0) + (tier2?.total_cost_usd || 0)).toFixed(5)}
        </span>
      </div>
    );
  }

  // Full card view
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span>V3 Analysis</span>
          <Badge variant="outline" className="bg-green-50 text-green-700">
            Cost: ${(tier0.cost_usd + (tier1?.cost_usd || 0) + (tier2?.total_cost_usd || 0)).toFixed(5)}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Tier 0: Triage */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-600 uppercase">
            Tier 0: Triage
          </h4>
          <div className="flex flex-wrap gap-2">
            <Badge className={getPriorityColor(tier0.PriorityScore)}>
              Priority: {tier0.PriorityScore}/10
            </Badge>
            <Badge className={getCategoryColor(tier0.category)}>
              {tier0.category}
            </Badge>
            <Badge variant={tier0.keep ? 'default' : 'outline'}>
              {tier0.keep ? 'Keep' : 'Discard'}
            </Badge>
          </div>
        </div>

        {/* Tier 1: Foundation */}
        {tier1 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-600 uppercase">
              Tier 1: Foundation Extraction
            </h4>

            {/* Scores */}
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Impact:</span>{' '}
                <span className={getScoreColor(tier1.scores.impact_score)}>
                  {tier1.scores.impact_score.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Credibility:</span>{' '}
                <span className={getScoreColor(tier1.scores.credibility_score)}>
                  {tier1.scores.credibility_score.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Urgency:</span>{' '}
                <span className={getScoreColor(tier1.scores.urgency_score)}>
                  {tier1.scores.urgency_score.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Entities, Relations, Topics counts */}
            <div className="flex flex-wrap gap-2 text-xs">
              {tier1.entities.length > 0 && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  {tier1.entities.length} entities
                </Badge>
              )}
              {tier1.relations.length > 0 && (
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  {tier1.relations.length} relations
                </Badge>
              )}
              {tier1.topics.length > 0 && (
                <Badge variant="outline" className="bg-purple-50 text-purple-700">
                  {tier1.topics.length} topics
                </Badge>
              )}
            </div>

            {/* Top entities (max 3) */}
            {tier1.entities.length > 0 && (
              <div className="text-xs text-gray-600">
                <span className="font-medium">Top entities:</span>{' '}
                {tier1.entities
                  .slice(0, 3)
                  .map((e) => e.name)
                  .join(', ')}
                {tier1.entities.length > 3 && ` +${tier1.entities.length - 3} more`}
              </div>
            )}
          </div>
        )}

        {/* Tier 2: Specialists */}
        {tier2 && tier2.specialists_executed > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-gray-600 uppercase">
              Tier 2: Specialist Analysis
            </h4>
            <div className="flex flex-wrap gap-2 text-xs">
              {tier2.TOPIC_CLASSIFIER && (
                <Badge variant="outline" className="bg-indigo-50 text-indigo-700">
                  Topic Classifier
                </Badge>
              )}
              {tier2.ENTITY_EXTRACTOR && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  Entity Extractor
                </Badge>
              )}
              {tier2.FINANCIAL_ANALYST && (
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  Financial Analyst
                </Badge>
              )}
              {tier2.GEOPOLITICAL_ANALYST && (
                <Badge variant="outline" className="bg-red-50 text-red-700">
                  Geopolitical Analyst
                </Badge>
              )}
              {tier2.SENTIMENT_ANALYZER && (
                <Badge variant="outline" className="bg-purple-50 text-purple-700">
                  Sentiment Analyzer
                </Badge>
              )}
              {tier2.BIAS_SCORER && (
                <Badge variant="outline" className="bg-amber-50 text-amber-700">
                  Bias Scorer
                </Badge>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {tier2.specialists_executed} specialist{tier2.specialists_executed !== 1 ? 's' : ''} executed
              • ${tier2.total_cost_usd.toFixed(5)} • {tier2.total_tokens} tokens
            </div>

            {/* Political Bias Display */}
            {tier2.BIAS_SCORER?.political_bias && (
              <div className="mt-3 text-xs">
                <div className="font-medium text-gray-600 mb-2">
                  ⚖️ Political Bias:
                  <span className="font-semibold text-gray-800 ml-1">
                    {tier2.BIAS_SCORER.political_bias.political_direction.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className="mx-1">•</span>
                  <span className="font-semibold" style={{
                    color: tier2.BIAS_SCORER.political_bias.bias_score < -0.15 ? '#b91c1c' :
                           tier2.BIAS_SCORER.political_bias.bias_score > 0.15 ? '#1d4ed8' :
                           '#374151'
                  }}>
                    {tier2.BIAS_SCORER.political_bias.bias_score.toFixed(2)}
                  </span>
                  <span className="mx-1">•</span>
                  <span className="text-gray-700 capitalize">
                    {tier2.BIAS_SCORER.political_bias.bias_strength}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Discarded message */}
        {discarded && (
          <div className="bg-gray-50 border border-gray-200 rounded p-2 text-xs text-gray-600">
            Article discarded by Tier 0 triage. No further analysis performed.
          </div>
        )}

        {/* Model info */}
        <div className="text-xs text-gray-400 border-t pt-2">
          Model: {tier0.model} • Tokens: {tier0.tokens_used + (tier1?.tokens_used || 0) + (tier2?.total_tokens || 0)}
        </div>
      </CardContent>
    </Card>
  );
}
