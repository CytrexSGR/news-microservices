import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useFeed, useFeedHealth, useAssessFeed, useAssessmentHistory, useFeedItems, useUpdateFeed } from '@/features/feeds/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Collapsible } from '@/components/ui/collapsible';
import { StatCard } from '@/components/shared/StatCard';
import { TimeSeriesChart } from '@/components/shared/TimeSeriesChart';
import { AssessmentHistoryTimeline } from '@/features/feeds/components/AssessmentHistoryTimeline';
import { ScrapingSettings } from '@/features/feeds/components/ScrapingSettings';
import { FetchSettings } from '@/features/feeds/components/FetchSettings';
import { formatDistanceToNow, format } from 'date-fns';
import { stripHtml, getFirstSentences } from '@/lib/utils/htmlUtils';
import {
  ArrowLeft,
  ExternalLink,
  CheckCircle,
  XCircle,
  Check,
  X,
  Shield,
  Star,
  Info,
  RefreshCw,
  FileText,
  Calendar
} from 'lucide-react';

export function FeedDetailPage() {
  const { feedId } = useParams<{ feedId: string }>();
  const navigate = useNavigate();

  const { data: feed, isLoading: feedLoading, error: feedError } = useFeed(feedId!);
  const { data: health, isLoading: healthLoading, error: healthError } = useFeedHealth(feedId!);
  const { data: assessmentHistory, isLoading: historyLoading } = useAssessmentHistory(feedId!);
  const { data: feedItems, isLoading: itemsLoading } = useFeedItems({ feedId: feedId!, limit: 20 });
  const { mutate: assessFeed, isPending: isAssessing } = useAssessFeed();
  const { mutate: updateFeed, isPending: isUpdatingFeed } = useUpdateFeed();

  // Local state for V2 analysis toggle
  const [isAnalysisV2Enabled, setIsAnalysisV2Enabled] = useState(feed?.enable_analysis_v2 ?? false);

  // Local state for feed active toggle (controls fetching)
  const [isFeedActive, setIsFeedActive] = useState(feed?.is_active ?? true);

  // Sync state when feed data loads
  useEffect(() => {
    if (feed) {
      setIsAnalysisV2Enabled(feed.enable_analysis_v2 ?? false);
      setIsFeedActive(feed.is_active ?? true);
    }
  }, [feed]);

  // Handler for toggling analysis V2
  const handleAnalysisV2Toggle = () => {
    const newValue = !isAnalysisV2Enabled;
    setIsAnalysisV2Enabled(newValue);

    updateFeed(
      { feedId: feedId!, updates: { enable_analysis_v2: newValue } },
      {
        onError: () => {
          // Revert on error
          setIsAnalysisV2Enabled(!newValue);
        },
      }
    );
  };

  // Handler for toggling feed active status (fetching)
  const handleFeedActiveToggle = () => {
    const newValue = !isFeedActive;
    setIsFeedActive(newValue);

    updateFeed(
      { feedId: feedId!, updates: { is_active: newValue } },
      {
        onError: () => {
          // Revert on error
          setIsFeedActive(!newValue);
        },
      }
    );
  };

  const isLoading = feedLoading || healthLoading;
  const error = feedError || healthError;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading feed details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !feed) {
    return (
      <div className="p-6">
        <div
          className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Feed</h3>
          <p className="text-sm text-muted-foreground">
            {error ? (error as Error).message : 'Feed not found'}
          </p>
        </div>
      </div>
    );
  }

  // Prepare chart data from health history
  const chartData = health?.history?.map((point) => ({
    timestamp: new Date(point.timestamp).toISOString(),
    value: point.health_score,
  })) || [];

  // Political bias color helper
  const getPoliticalBiasColor = (bias?: string) => {
    if (!bias) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    const biasLower = bias.toLowerCase();
    if (biasLower.includes('left')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (biasLower.includes('right')) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
  };

  // Credibility tier badge
  const getCredibilityBadge = (tier?: string) => {
    if (!tier) return null;
    const colors = {
      tier_1: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      tier_2: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      tier_3: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[tier as keyof typeof colors] || ''}`}>
        {tier.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/feeds')}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Feeds
        </button>

        <div className="flex items-start justify-between">
          <div className="flex-1 max-w-4xl">
            <h1 className="text-3xl font-bold">{feed.name}</h1>
            <div className="flex items-center gap-4 mt-2 flex-wrap">
              <a
                href={feed.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-primary hover:underline break-all"
              >
                {feed.url}
                <ExternalLink className="h-3 w-3 flex-shrink-0" />
              </a>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  feed.is_active
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                {feed.is_active ? 'Active' : 'Paused'}
              </span>
            </div>
            {feed.description && (
              <div className="mt-4 p-4 bg-muted/30 rounded-lg border border-border">
                <p className="text-sm leading-relaxed whitespace-pre-line">{feed.description}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Feed Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Feed Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Category</p>
              <div className="mt-1">
                {feed.category ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                    {feed.category}
                  </span>
                ) : (
                  <p className="text-base text-muted-foreground">Uncategorized</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Scrape Method</p>
              <p className="text-base mt-1 capitalize">{feed.scrape_method || 'newspaper4k'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Full Content Scraping</p>
              <p className="text-base mt-1 flex items-center gap-1">
                {feed.scrape_full_content ? (
                  <>
                    <Check className="h-4 w-4 text-green-500" />
                    Enabled
                  </>
                ) : (
                  <>
                    <X className="h-4 w-4 text-muted-foreground" />
                    Disabled
                    {feed.scrape_disabled_reason === 'auto_threshold' && (
                      <span className="text-xs text-red-500 ml-2">(Auto-disabled after {feed.scrape_failure_threshold || 5} failures)</span>
                    )}
                    {feed.scrape_disabled_reason === 'manual' && (
                      <span className="text-xs text-muted-foreground ml-2">(Manually disabled)</span>
                    )}
                  </>
                )}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Content Analysis V2</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleAnalysisV2Toggle}
                  disabled={isUpdatingFeed}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${isAnalysisV2Enabled ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'}
                    ${isUpdatingFeed ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:opacity-90'}
                  `}
                  aria-label="Toggle content analysis V2"
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${isAnalysisV2Enabled ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
                <div className="flex items-center gap-1.5">
                  {isAnalysisV2Enabled ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-700 dark:text-green-400 font-medium">Enabled</span>
                    </>
                  ) : (
                    <>
                      <X className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">Disabled</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Feed Fetching</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleFeedActiveToggle}
                  disabled={isUpdatingFeed}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${isFeedActive ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'}
                    ${isUpdatingFeed ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:opacity-90'}
                  `}
                  aria-label="Toggle feed fetching"
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${isFeedActive ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
                <div className="flex items-center gap-1.5">
                  {isFeedActive ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-700 dark:text-green-400 font-medium">Active</span>
                    </>
                  ) : (
                    <>
                      <X className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">Paused</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Scraping Failures</p>
              <p className="text-base mt-1 flex items-center gap-2">
                {(() => {
                  const threshold = feed.scrape_failure_threshold || 5;
                  const count = feed.scrape_failure_count ?? 0;
                  const percentage = (count / threshold) * 100;

                  return count > 0 ? (
                    <>
                      <span className={`font-semibold ${
                        percentage >= 80 ? 'text-red-500' :
                        percentage >= 60 ? 'text-orange-500' :
                        'text-yellow-500'
                      }`}>
                        {count}/{threshold}
                      </span>
                      {feed.scrape_last_failure_at && (
                        <span className="text-xs text-muted-foreground">
                          (Last: {format(new Date(feed.scrape_last_failure_at), 'PPp')})
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-green-500">0/{threshold}</span>
                  );
                })()}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Created</p>
              <p className="text-base mt-1">
                {format(new Date(feed.created_at), 'PPP')}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
              <p className="text-base mt-1">
                {feed.updated_at
                  ? format(new Date(feed.updated_at), 'PPP')
                  : 'Never'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Fetch Configuration */}
      <Collapsible title="Fetch Configuration" defaultOpen={false}>
        <FetchSettings
          feedId={feedId!}
          currentSettings={{
            fetch_interval: feed.fetch_interval,
          }}
        />
      </Collapsible>

      {/* Scraping Configuration */}
      <Collapsible title="Scraping Configuration" defaultOpen={false}>
        <ScrapingSettings
          feedId={feedId!}
          currentSettings={{
            scrape_method: feed.scrape_method || 'newspaper4k',
            scrape_failure_threshold: feed.scrape_failure_threshold || 5,
            scrape_full_content: feed.scrape_full_content ?? false,
          }}
        />
      </Collapsible>

      {/* Feed Source Assessment */}
      <Collapsible title="Feed Source Assessment" defaultOpen={false}>
        <div className="space-y-6 pt-4">
          {/* Assessment Button - Always visible */}
          <div className="flex items-center gap-3 pb-4 border-b border-border">
            <button
              onClick={() => assessFeed(feedId!)}
              disabled={isAssessing || feed.assessment?.assessment_status === 'pending'}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${isAssessing ? 'animate-spin' : ''}`} />
              {isAssessing ? 'Running Assessment...' : 'Run New Assessment'}
            </button>
            {feed.assessment?.assessment_status === 'pending' && (
              <span className="text-sm text-muted-foreground">
                Assessment in progress...
              </span>
            )}
            {feed.assessment?.assessment_date && (
              <span className="text-sm text-muted-foreground">
                Last assessed: {formatDistanceToNow(new Date(feed.assessment.assessment_date), { addSuffix: true })}
              </span>
            )}
          </div>

          {/* Assessment Data - Conditional rendering */}
          {feed.assessment ? (
            <>
              {/* Summary */}
              {feed.assessment.assessment_summary && (
                <div className="bg-muted/50 p-4 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Info className="h-5 w-5 text-primary mt-0.5" />
                    <p className="text-sm">{feed.assessment.assessment_summary}</p>
                  </div>
                </div>
              )}

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Credibility Tier</p>
                  {getCredibilityBadge(feed.assessment.credibility_tier)}
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Reputation Score</p>
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span className="text-base font-semibold">
                      {feed.assessment.reputation_score || 'N/A'}/100
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Political Bias</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPoliticalBiasColor(feed.assessment.political_bias)}`}>
                    {feed.assessment.political_bias || 'Unknown'}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Founded</p>
                  <p className="text-base">{feed.assessment.founded_year || 'Unknown'}</p>
                </div>
              </div>

              {/* Organization Details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Organization Type</p>
                  <p className="text-base mt-1">{feed.assessment.organization_type || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Assessment Date</p>
                  <p className="text-base mt-1">
                    {feed.assessment.assessment_date
                      ? format(new Date(feed.assessment.assessment_date), 'PPP')
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Editorial Standards */}
              {feed.assessment.editorial_standards && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Editorial Standards</p>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Fact Checking</p>
                      <p className="text-sm mt-1">
                        {feed.assessment.editorial_standards.fact_checking_level || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Corrections Policy</p>
                      <p className="text-sm mt-1">
                        {feed.assessment.editorial_standards.corrections_policy || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Source Attribution</p>
                      <p className="text-sm mt-1">
                        {feed.assessment.editorial_standards.source_attribution || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Trust Ratings */}
              {feed.assessment.trust_ratings && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Trust Ratings</p>
                  <div className="grid grid-cols-3 gap-4">
                    {feed.assessment.trust_ratings.media_bias_fact_check && (
                      <div>
                        <p className="text-xs text-muted-foreground">Media Bias Fact Check</p>
                        <p className="text-sm mt-1">
                          {feed.assessment.trust_ratings.media_bias_fact_check}
                        </p>
                      </div>
                    )}
                    {feed.assessment.trust_ratings.allsides_rating && (
                      <div>
                        <p className="text-xs text-muted-foreground">AllSides Rating</p>
                        <p className="text-sm mt-1">
                          {feed.assessment.trust_ratings.allsides_rating}
                        </p>
                      </div>
                    )}
                    {feed.assessment.trust_ratings.newsguard_score !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">NewsGuard Score</p>
                        <p className="text-sm mt-1">
                          {feed.assessment.trust_ratings.newsguard_score}/100
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {feed.assessment.recommendation && (
                <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex items-start gap-2">
                    <Shield className="h-5 w-5 text-blue-500 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                        Recommendations
                      </p>
                      <div className="space-y-1 text-xs text-blue-800 dark:text-blue-200">
                        {feed.assessment.recommendation.skip_waiting_period && (
                          <p>• Skip waiting period enabled</p>
                        )}
                        {feed.assessment.recommendation.initial_quality_boost !== undefined && (
                          <p>• Initial quality boost: {feed.assessment.recommendation.initial_quality_boost}</p>
                        )}
                        {feed.assessment.recommendation.bot_detection_threshold !== undefined && (
                          <p>• Bot detection threshold: {feed.assessment.recommendation.bot_detection_threshold}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Info className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-base font-medium">No assessment data available yet</p>
              <p className="text-sm mt-1">Click "Run New Assessment" to analyze this feed source's credibility and reliability.</p>
            </div>
          )}
        </div>
      </Collapsible>

      {/* Assessment History */}
      <Collapsible title="Assessment History" defaultOpen={false}>
        <div className="pt-4">
          <AssessmentHistoryTimeline
            history={assessmentHistory || []}
            isLoading={historyLoading}
          />
        </div>
      </Collapsible>

      {/* Recent Articles */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">Recent Articles</CardTitle>
            <span className="text-sm text-muted-foreground">
              {feedItems?.length || 0} articles
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {itemsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="mt-2 text-sm text-muted-foreground">Loading articles...</p>
            </div>
          ) : feedItems && feedItems.length > 0 ? (
            <div className="space-y-3">
              {feedItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/articles/${item.id}`)}
                  className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors cursor-pointer group"
                >
                  <div className="flex-shrink-0 mt-1">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm group-hover:text-primary transition-colors line-clamp-2">
                      {item.title}
                    </h3>

                    {/* Content Preview */}
                    {(item.content || item.description) && (
                      <div className="border-l-2 border-primary/20 pl-3 py-1.5 mt-2 bg-muted/20 rounded">
                        <p className="text-xs text-foreground leading-relaxed line-clamp-2">
                          {(() => {
                            const sourceText = item.content || item.description || '';
                            const preview = getFirstSentences(sourceText, 2);
                            const fullText = stripHtml(sourceText);
                            return (
                              <>
                                {preview}
                                {fullText.length > preview.length && (
                                  <span className="text-muted-foreground ml-1">...</span>
                                )}
                              </>
                            );
                          })()}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      {item.published_at && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDistanceToNow(new Date(item.published_at), { addSuffix: true })}
                        </span>
                      )}
                      {item.author && (
                        <span>by {item.author}</span>
                      )}
                      {item.scrape_word_count && (
                        <span>{item.scrape_word_count} words</span>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-base font-medium">No articles yet</p>
              <p className="text-sm mt-1">Articles will appear here once the feed is fetched.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Health Overview */}
      {health && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Health Score"
              value={health.health_score.toFixed(1)}
              icon={<Shield className="h-4 w-4" />}
              change={
                health.health_score >= 80
                  ? '+Good'
                  : health.health_score >= 60
                  ? 'Neutral'
                  : '-Poor'
              }
            />
            <StatCard
              title="Success Rate"
              value={`${health.success_rate.toFixed(1)}%`}
              icon={<CheckCircle className="h-4 w-4" />}
              change={
                health.success_rate >= 90
                  ? '+Excellent'
                  : health.success_rate >= 70
                  ? 'Neutral'
                  : '-Poor'
              }
            />
            <StatCard
              title="Total Fetches"
              value={health.total_fetches}
              icon={<RefreshCw className="h-4 w-4" />}
            />
            <StatCard
              title="Consecutive Failures"
              value={health.consecutive_failures}
              icon={<XCircle className="h-4 w-4" />}
              change={health.consecutive_failures === 0 ? '+None' : `-${health.consecutive_failures}`}
            />
          </div>

          {/* Health Score Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Health Score History</CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <TimeSeriesChart
                  data={chartData}
                  dataKey="value"
                  title="Health Score History"
                  xAxisKey="timestamp"
                />
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No history data available
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Fetch Logs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Recent Fetch Attempts</CardTitle>
            </CardHeader>
            <CardContent>
              {health.history && health.history.length > 0 ? (
                <div className="space-y-3">
                  {health.history.slice(0, 10).map((log, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-4 p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex-shrink-0 mt-1">
                        {log.success ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">
                            {log.success ? 'Success' : 'Failed'}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(log.timestamp), {
                              addSuffix: true,
                            })}
                          </span>
                          {log.duration && (
                            <span className="text-xs text-muted-foreground">
                              • {log.duration}ms
                            </span>
                          )}
                        </div>
                        {log.error && (
                          <p className="text-xs text-destructive mt-1">{log.error}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No fetch logs available
                </p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
