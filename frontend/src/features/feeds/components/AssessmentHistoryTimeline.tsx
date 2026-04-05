import { format, formatDistanceToNow } from 'date-fns';
import { ChevronDown, ChevronUp, Star, Shield, Calendar, TrendingUp, TrendingDown } from 'lucide-react';
import { useState } from 'react';
import type { AssessmentHistoryItem } from '../api/useAssessmentHistory';

interface AssessmentHistoryTimelineProps {
  history: AssessmentHistoryItem[];
  isLoading?: boolean;
}

export function AssessmentHistoryTimeline({ history, isLoading }: AssessmentHistoryTimelineProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Helper functions
  const getCredibilityColor = (tier?: string) => {
    if (!tier) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    const colors = {
      tier_1: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      tier_2: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      tier_3: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    };
    return colors[tier as keyof typeof colors] || colors.tier_2;
  };

  const getPoliticalBiasColor = (bias?: string) => {
    if (!bias) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    const biasLower = bias.toLowerCase();
    if (biasLower.includes('left')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (biasLower.includes('right')) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
  };

  const getScoreTrend = (currentScore?: number, previousScore?: number) => {
    if (!currentScore || !previousScore) return null;
    const diff = currentScore - previousScore;
    if (diff > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (diff < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return null;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-24 bg-muted rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p className="text-base font-medium">No assessment history available</p>
        <p className="text-sm mt-1">Previous assessments will appear here once you run multiple analyses.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {history.map((item, index) => {
        const isExpanded = expandedItems.has(item.id);
        const isLatest = index === 0;
        const previousItem = index < history.length - 1 ? history[index + 1] : null;

        return (
          <div
            key={item.id}
            className={`border rounded-lg transition-all ${
              isLatest
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            }`}
          >
            {/* Header - Always Visible */}
            <button
              onClick={() => toggleExpand(item.id)}
              className="w-full p-4 flex items-center justify-between text-left hover:bg-muted/50 transition-colors rounded-lg"
            >
              <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Date */}
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">
                      {format(new Date(item.assessment_date || item.created_at), 'PPP')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(item.assessment_date || item.created_at), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                </div>

                {/* Credibility Tier */}
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCredibilityColor(item.credibility_tier)}`}>
                    {item.credibility_tier?.replace('_', ' ').toUpperCase() || 'N/A'}
                  </span>
                </div>

                {/* Reputation Score */}
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 text-yellow-500" />
                  <div className="flex items-center gap-1">
                    <span className="text-sm font-semibold">
                      {item.reputation_score || 'N/A'}/100
                    </span>
                    {getScoreTrend(item.reputation_score, previousItem?.reputation_score)}
                  </div>
                </div>

                {/* Status Badge */}
                <div className="flex items-center justify-end">
                  {isLatest && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      Latest
                    </span>
                  )}
                </div>
              </div>

              {/* Expand Icon */}
              <div className="ml-4">
                {isExpanded ? (
                  <ChevronUp className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
            </button>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-4 border-t border-border pt-4">
                {/* Summary */}
                {item.assessment_summary && (
                  <div className="bg-muted/50 p-3 rounded-lg">
                    <p className="text-sm">{item.assessment_summary}</p>
                  </div>
                )}

                {/* Detailed Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Political Bias</p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPoliticalBiasColor(item.political_bias)}`}>
                      {item.political_bias || 'Unknown'}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Organization Type</p>
                    <p className="text-sm">{item.organization_type || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Founded Year</p>
                    <p className="text-sm">{item.founded_year || 'Unknown'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Assessment Status</p>
                    <p className="text-sm">{item.assessment_status || 'N/A'}</p>
                  </div>
                </div>

                {/* Editorial Standards */}
                {item.editorial_standards && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">Editorial Standards</p>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="bg-muted/50 p-2 rounded">
                        <p className="text-muted-foreground mb-1">Fact Checking</p>
                        <p className="font-medium">
                          {item.editorial_standards.fact_checking_level || 'N/A'}
                        </p>
                      </div>
                      <div className="bg-muted/50 p-2 rounded">
                        <p className="text-muted-foreground mb-1">Corrections</p>
                        <p className="font-medium">
                          {item.editorial_standards.corrections_policy || 'N/A'}
                        </p>
                      </div>
                      <div className="bg-muted/50 p-2 rounded">
                        <p className="text-muted-foreground mb-1">Attribution</p>
                        <p className="font-medium">
                          {item.editorial_standards.source_attribution || 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Trust Ratings */}
                {item.trust_ratings && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">Trust Ratings</p>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      {item.trust_ratings.media_bias_fact_check && (
                        <div className="bg-muted/50 p-2 rounded">
                          <p className="text-muted-foreground mb-1">MBFC</p>
                          <p className="font-medium">{item.trust_ratings.media_bias_fact_check}</p>
                        </div>
                      )}
                      {item.trust_ratings.allsides_rating && (
                        <div className="bg-muted/50 p-2 rounded">
                          <p className="text-muted-foreground mb-1">AllSides</p>
                          <p className="font-medium">{item.trust_ratings.allsides_rating}</p>
                        </div>
                      )}
                      {item.trust_ratings.newsguard_score !== undefined && (
                        <div className="bg-muted/50 p-2 rounded">
                          <p className="text-muted-foreground mb-1">NewsGuard</p>
                          <p className="font-medium">{item.trust_ratings.newsguard_score}/100</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {item.recommendation && (
                  <div className="bg-blue-50 dark:bg-blue-950/30 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-2">
                      Recommendations
                    </p>
                    <div className="space-y-1 text-xs text-blue-800 dark:text-blue-200">
                      {item.recommendation.skip_waiting_period && (
                        <p>• Skip waiting period enabled</p>
                      )}
                      {item.recommendation.initial_quality_boost !== undefined && (
                        <p>• Initial quality boost: {item.recommendation.initial_quality_boost}</p>
                      )}
                      {item.recommendation.bot_detection_threshold !== undefined && (
                        <p>• Bot detection threshold: {item.recommendation.bot_detection_threshold}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
