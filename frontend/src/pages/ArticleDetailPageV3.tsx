import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Calendar, User, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { useArticleV2 } from '@/features/feeds/api/useArticleV2';
import { ArticleV3AnalysisCard } from '@/features/feeds/components/ArticleV3AnalysisCard';
import { validateV3Analysis, V3ValidationError } from '@/features/feeds/utils/validateV3Analysis';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

export function ArticleDetailPageV3() {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();

  // Fetch article metadata AND V3 analysis (from feed-service)
  // feed-service now includes v3_analysis field in article response
  const { data: article, isLoading: articleLoading, error: articleError } = useArticleV2(itemId || '');

  // Extract V3 analysis from article response
  const v3Analysis = article?.v3_analysis || null;

  const isLoading = articleLoading;
  const error = articleError;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading article analysis...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="p-6">
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Article</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Article not found'}
          </p>
        </div>
      </div>
    );
  }

  // Validate V3 analysis structure (catches backend/frontend mismatches)
  // See: POSTMORTEMS.md Incident #23 (2025-11-23)
  let v3ValidationError: string | null = null;
  if (v3Analysis) {
    try {
      validateV3Analysis(v3Analysis);
    } catch (error) {
      if (error instanceof V3ValidationError) {
        console.error('V3 Analysis validation error:', error);
        v3ValidationError = error.message;
      }
    }
  }

  const hasV3 = v3Analysis != null;
  const tier0 = v3Analysis?.tier0;
  const tier1 = v3Analysis?.tier1;
  const tier2 = v3Analysis?.tier2;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
          aria-label="Go back"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <span className="font-medium">{article.feed_name}</span>
            {article.published_at && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>
                    {formatDistanceToNow(new Date(article.published_at), {
                      addSuffix: true,
                    })}
                  </span>
                </div>
              </>
            )}
            {article.author && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  <span>{article.author}</span>
                </div>
              </>
            )}
          </div>
          <h1 className="text-3xl font-bold">{article.title}</h1>
        </div>
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          View Original
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>

      {/* V3 Validation Error */}
      {v3ValidationError && (
        <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-800 dark:text-red-200">
                ⚠️ V3 Analysis Data Structure Error
              </p>
              <p className="text-xs text-red-700 dark:text-red-300 mt-1 font-mono whitespace-pre-wrap">
                {v3ValidationError}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                This indicates a mismatch between backend data structure and frontend expectations.
                Please report this issue.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* V3 Analysis Status */}
      {!hasV3 && !v3ValidationError && (
        <div className="bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              {/* 300 chars ≈ 50 words - matches scraping-service minimum threshold */}
              {(!article.content || article.content.length < 300) ? (
                'Insufficient content for tier analysis (minimum ~50 words required)'
              ) : article.scrape_status === 'error' ? (
                'Scraping failed - analysis unavailable'
              ) : (
                '⏳ Analysis pending - will be performed automatically'
              )}
            </p>
          </div>
        </div>
      )}

      {hasV3 && tier0 && (
        <div className={`rounded-lg p-3 flex items-center justify-between ${
          tier0.keep
            ? 'bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800'
            : 'bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800'
        }`}>
          <div className="flex items-center gap-2">
            {tier0.keep ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-gray-500" />
            )}
            <p className={`text-sm ${
              tier0.keep
                ? 'text-green-800 dark:text-green-200'
                : 'text-gray-700 dark:text-gray-300'
            }`}>
              {tier0.keep
                ? `✓ V3 Analysis Complete - ${tier2 ? tier2.specialists_executed : 0} specialists executed`
                : '✗ Article discarded by V3 Triage'}
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            Cost: ${(
              tier0.cost_usd +
              (tier1?.cost_usd || 0) +
              (tier2?.total_cost_usd || 0)
            ).toFixed(5)}
          </div>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="tier0" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="tier0" disabled={!hasV3}>Tier 0: Triage</TabsTrigger>
          <TabsTrigger value="tier1" disabled={!tier1}>Tier 1: Foundation</TabsTrigger>
          <TabsTrigger value="tier2" disabled={!tier2}>Tier 2: Specialists</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
        </TabsList>

        {/* Tier 0: Triage */}
        <TabsContent value="tier0" className="space-y-6">
          {tier0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Tier 0: Triage Decision</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Decision</p>
                    <Badge variant={tier0.keep ? 'default' : 'outline'} className="mt-1">
                      {tier0.keep ? 'KEEP' : 'DISCARD'}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Priority Score</p>
                    <p className="text-lg font-semibold">{tier0.PriorityScore}/10</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Category</p>
                    <Badge className="mt-1">{tier0.category}</Badge>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Cost</p>
                    <p className="text-sm font-medium">${tier0.cost_usd.toFixed(6)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="p-8 text-center text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-4" />
              <p>V3 Triage not available</p>
            </Card>
          )}
        </TabsContent>

        {/* Tier 1: Foundation */}
        <TabsContent value="tier1" className="space-y-6">
          {tier1 ? (
            <>
              {/* Scores */}
              {/*
                Note: Backend transforms tier1_results into nested structure.
                Database stores: { impact_score: 7.0, credibility_score: 8.0, urgency_score: 4.0 }
                Backend transforms to: { scores: { impact_score: 7.0, ... } }
                See: services/feed-service/app/services/analysis_loader.py:233-250
                Fixed: 2025-11-23 (POSTMORTEMS.md Incident #23)
              */}
              <Card>
                <CardHeader>
                  <CardTitle>Foundation Scores</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Impact</p>
                      <p className="text-2xl font-bold">{tier1.scores?.impact_score?.toFixed(1) ?? 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Credibility</p>
                      <p className="text-2xl font-bold">{tier1.scores?.credibility_score?.toFixed(1) ?? 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Urgency</p>
                      <p className="text-2xl font-bold">{tier1.scores?.urgency_score?.toFixed(1) ?? 'N/A'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Entities */}
              {tier1.entities.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Entities ({tier1.entities.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {tier1.entities.map((entity, idx) => (
                        <Badge key={idx} variant="secondary">
                          {entity.name} ({entity.type})
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Topics */}
              {tier1.topics.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Topics ({tier1.topics.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {tier1.topics.map((topic, idx) => (
                        <Badge key={idx} variant="outline">
                          {topic.keyword} ({(topic.confidence * 100).toFixed(0)}%)
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Relations */}
              {tier1.relations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Relations ({tier1.relations.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {tier1.relations.slice(0, 10).map((rel, idx) => (
                        <div key={idx} className="text-sm border-l-2 border-primary/20 pl-3">
                          <span className="font-medium">{rel.subject}</span>
                          {' → '}
                          <span className="text-muted-foreground">{rel.predicate}</span>
                          {' → '}
                          <span className="font-medium">{rel.object}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="p-8 text-center text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-4" />
              <p>Foundation extraction not available (article may have been discarded)</p>
            </Card>
          )}
        </TabsContent>

        {/* Tier 2: Specialists */}
        <TabsContent value="tier2" className="space-y-6">
          {tier2 ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Specialist Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    {tier2.specialists_executed} specialists executed
                  </p>

                  {/* Show specialist findings here */}
                  {/* Entity Enrichment */}
                  {tier2.ENTITY_EXTRACTOR?.entity_enrichment && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">🏷️ Entity Enrichment</h4>
                      <div className="space-y-3">
                        {tier2.ENTITY_EXTRACTOR.entity_enrichment.entities.map((entity: any, idx: number) => (
                          <div key={idx} className="border-l-2 border-primary/20 pl-3">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="secondary">{entity.type}</Badge>
                              <span className="font-medium">{entity.name}</span>
                            </div>
                            {entity.details && typeof entity.details === 'object' && (
                              <div className="text-xs text-muted-foreground space-y-1">
                                {Object.entries(entity.details)
                                  .filter(([_, value]) => value != null)
                                  .map(([key, value]) => (
                                    <div key={key}>
                                      <span className="capitalize">{key.replace(/_/g, ' ')}: </span>
                                      <span>{Array.isArray(value) ? value.join(', ') : String(value)}</span>
                                    </div>
                                  ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Topic Classification */}
                  {tier2.TOPIC_CLASSIFIER?.topic_classification && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">📑 Topic Classification</h4>
                      <div className="flex flex-wrap gap-2">
                        {tier2.TOPIC_CLASSIFIER.topic_classification.topics.map((topic: any, idx: number) => (
                          <Badge key={idx} variant="outline">
                            {topic.topic} ({(topic.confidence * 100).toFixed(0)}%)
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Financial Analysis */}
                  {tier2.FINANCIAL_ANALYST?.financial_metrics && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">💰 Financial Analysis</h4>
                      {tier2.FINANCIAL_ANALYST.financial_metrics.metrics && typeof tier2.FINANCIAL_ANALYST.financial_metrics.metrics === 'object' && (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {Object.entries(tier2.FINANCIAL_ANALYST.financial_metrics.metrics).map(([key, value]) => (
                            <div key={key}>
                              <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}: </span>
                              <span className="font-medium">{value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {tier2.FINANCIAL_ANALYST.financial_metrics.affected_symbols?.length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Affected Symbols:</p>
                          <div className="flex flex-wrap gap-1">
                            {tier2.FINANCIAL_ANALYST.financial_metrics.affected_symbols.map((symbol: string, idx: number) => (
                              <Badge key={idx} variant="outline" className="text-xs">{symbol}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Geopolitical Analysis */}
                  {tier2.GEOPOLITICAL_ANALYST?.geopolitical_metrics && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">🌍 Geopolitical Analysis</h4>
                      {tier2.GEOPOLITICAL_ANALYST.geopolitical_metrics.metrics && typeof tier2.GEOPOLITICAL_ANALYST.geopolitical_metrics.metrics === 'object' && (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {Object.entries(tier2.GEOPOLITICAL_ANALYST.geopolitical_metrics.metrics).map(([key, value]) => (
                            <div key={key}>
                              <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}: </span>
                              <span className="font-medium">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {tier2.GEOPOLITICAL_ANALYST.geopolitical_metrics.regions_affected?.length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Regions Affected:</p>
                          <div className="flex flex-wrap gap-1">
                            {tier2.GEOPOLITICAL_ANALYST.geopolitical_metrics.regions_affected.map((region: string, idx: number) => (
                              <Badge key={idx} variant="outline" className="text-xs">{region}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Sentiment Analysis */}
                  {tier2.SENTIMENT_ANALYZER?.sentiment_metrics && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">😊 Sentiment Analysis</h4>
                      {tier2.SENTIMENT_ANALYZER.sentiment_metrics.sentiment_scores && typeof tier2.SENTIMENT_ANALYZER.sentiment_metrics.sentiment_scores === 'object' && (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {Object.entries(tier2.SENTIMENT_ANALYZER.sentiment_metrics.sentiment_scores).map(([key, value]) => (
                            <div key={key}>
                              <span className="text-muted-foreground capitalize">{key}: </span>
                              <span className="font-medium">{(value as number * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Political Bias Analysis */}
                  {tier2.BIAS_SCORER?.political_bias && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold">⚖️ Political Bias Analysis</h4>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Direction:</span>
                          <div className="font-semibold mt-1">
                            {tier2.BIAS_SCORER.political_bias.political_direction.replace(/_/g, ' ').toUpperCase()}
                          </div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Score:</span>
                          <div className="font-semibold mt-1 text-lg" style={{
                            color: tier2.BIAS_SCORER.political_bias.bias_score < -0.15 ? '#b91c1c' :
                                   tier2.BIAS_SCORER.political_bias.bias_score > 0.15 ? '#1d4ed8' :
                                   '#374151'
                          }}>
                            {tier2.BIAS_SCORER.political_bias.bias_score.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Strength:</span>
                          <div className="font-semibold mt-1 capitalize">
                            {tier2.BIAS_SCORER.political_bias.bias_strength}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        Confidence: {(tier2.BIAS_SCORER.political_bias.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}

                  {/* Narrative Analysis */}
                  {tier2.NARRATIVE_ANALYST?.narrative_frame_metrics && (
                    <div className="space-y-3 mb-4">
                      <h4 className="font-semibold">🎭 Narrative Analysis</h4>

                      {/* Tension Score */}
                      <div className="flex items-center gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground">Narrative Tension:</span>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${(tier2.NARRATIVE_ANALYST.narrative_frame_metrics.narrative_tension || 0) * 100}%`,
                                  backgroundColor: (tier2.NARRATIVE_ANALYST.narrative_frame_metrics.narrative_tension || 0) > 0.7
                                    ? '#dc2626'
                                    : (tier2.NARRATIVE_ANALYST.narrative_frame_metrics.narrative_tension || 0) > 0.4
                                      ? '#f59e0b'
                                      : '#22c55e'
                                }}
                              />
                            </div>
                            <span className="font-bold text-lg">
                              {((tier2.NARRATIVE_ANALYST.narrative_frame_metrics.narrative_tension || 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.dominant_frame && (
                          <div>
                            <span className="text-sm text-muted-foreground">Dominant Frame:</span>
                            <Badge className="mt-1 ml-2 capitalize">
                              {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.dominant_frame}
                            </Badge>
                          </div>
                        )}
                      </div>

                      {/* Detected Frames */}
                      {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.frames?.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground">Detected Frames:</p>
                          <div className="space-y-2">
                            {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.frames.map((frame: any, idx: number) => (
                              <div key={idx} className="border-l-2 border-primary/30 pl-3 py-1">
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className="capitalize">{frame.frame_type}</Badge>
                                  <span className="text-xs text-muted-foreground">
                                    {(frame.confidence * 100).toFixed(0)}% confidence
                                  </span>
                                </div>
                                {frame.entities?.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {frame.entities.map((entity: string, eidx: number) => (
                                      <Badge key={eidx} variant="secondary" className="text-xs">{entity}</Badge>
                                    ))}
                                  </div>
                                )}
                                {frame.text_excerpt && (
                                  <p className="text-xs text-muted-foreground mt-1 italic">
                                    "{frame.text_excerpt.slice(0, 150)}{frame.text_excerpt.length > 150 ? '...' : ''}"
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Entity Portrayals */}
                      {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.entity_portrayals &&
                       Object.keys(tier2.NARRATIVE_ANALYST.narrative_frame_metrics.entity_portrayals).length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground">Entity Portrayals:</p>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(tier2.NARRATIVE_ANALYST.narrative_frame_metrics.entity_portrayals).map(([entity, roles]: [string, any]) => (
                              <div key={entity} className="text-sm">
                                <span className="font-medium">{entity}:</span>
                                <span className="text-muted-foreground ml-1">
                                  {Array.isArray(roles) ? roles.join(', ') : roles}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Propaganda Indicators */}
                      {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.propaganda_indicators?.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs text-muted-foreground">Propaganda Indicators:</p>
                          <div className="flex flex-wrap gap-1">
                            {tier2.NARRATIVE_ANALYST.narrative_frame_metrics.propaganda_indicators.map((indicator: string, idx: number) => (
                              <Badge key={idx} variant="destructive" className="text-xs capitalize">
                                {indicator.replace(/_/g, ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* No findings message */}
                  {!tier2.ENTITY_EXTRACTOR && !tier2.TOPIC_CLASSIFIER && !tier2.FINANCIAL_ANALYST &&
                   !tier2.GEOPOLITICAL_ANALYST && !tier2.SENTIMENT_ANALYZER && !tier2.BIAS_SCORER &&
                   !tier2.NARRATIVE_ANALYST && (
                    <p className="text-sm text-muted-foreground italic">
                      No specialist findings available (specialists may have skipped this article)
                    </p>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="p-8 text-center text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-4" />
              <p>Specialist analysis not performed (low priority or discarded)</p>
            </Card>
          )}
        </TabsContent>

        {/* Content */}
        <TabsContent value="content" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Article Content</CardTitle>
            </CardHeader>
            <CardContent>
              {article.content ? (
                <div className="prose dark:prose-invert max-w-none">
                  <p className="text-sm whitespace-pre-wrap">{article.content}</p>
                </div>
              ) : article.description ? (
                <div className="prose dark:prose-invert max-w-none">
                  <p className="text-sm whitespace-pre-wrap">{article.description}</p>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p className="text-sm">Full content not available</p>
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline text-sm mt-2 inline-flex items-center gap-1"
                  >
                    View original article
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
            </CardContent>
          </Card>

          {article.scrape_word_count && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Word Count</span>
                  <span className="font-medium">{article.scrape_word_count.toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
