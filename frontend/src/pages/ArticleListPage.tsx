import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useArticles } from '@/features/feeds/api/useArticles';
import { ArticleV3AnalysisCard } from '@/features/feeds/components/ArticleV3AnalysisCard';
import { ArticleFilters, type ArticleFilterValues } from '@/features/feeds/components/ArticleFilters';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { FileText, ExternalLink, Calendar, User, ChevronLeft, ChevronRight, File, ChevronDown, ChevronUp, ArrowUp, ArrowDown, Sparkles, BookOpen } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { FeedItemWithFeed } from '@/features/feeds/types';
import { stripHtml, getFirstSentences } from '@/lib/utils/htmlUtils';

type SortField = 'created_at' | 'published_at';
type SortOrder = 'asc' | 'desc';

export function ArticleListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const pageSize = 20;
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [filters, setFilters] = useState<ArticleFilterValues>({
    feedIds: [],
    dateFrom: null,
    dateTo: null,
    sentiment: null,
    category: null,
    sourceType: null,
  });

  const { data: articlesRaw, isLoading, error } = useArticles({
    limit: pageSize,
    offset: page * pageSize,
    feedIds: filters.feedIds.length > 0 ? filters.feedIds : undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined,
    sentiment: filters.sentiment || undefined,
    category: filters.category || undefined,
    sourceType: filters.sourceType || undefined,
    sortBy: sortBy,
    order: sortOrder,
  });

  // Articles now include both v2_analysis (legacy) and v3_analysis (active) directly from feed-service
  const articles = useMemo(() => {
    if (!articlesRaw) return [];
    return articlesRaw;
  }, [articlesRaw]);

  const handleFilterChange = useCallback((newFilters: ArticleFilterValues) => {
    setFilters(newFilters);
    setPage(0); // Reset to first page when filters change
  }, []);

  const handleSortChange = (field: SortField) => {
    if (sortBy === field) {
      // Toggle order if same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to desc
      setSortBy(field);
      setSortOrder('desc');
    }
    setPage(0); // Reset to first page when sort changes
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        {/* Header Skeleton */}
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>

        {/* Filters Skeleton */}
        <div className="flex gap-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>

        {/* Table Skeleton */}
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4 border border-border rounded-lg">
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div
          className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Articles</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Failed to load articles'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Articles</h1>
          <p className="text-muted-foreground mt-1">
            Browse articles from all feeds
          </p>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Sort by:</span>
        <Button
          variant={sortBy === 'created_at' ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleSortChange('created_at')}
          className="gap-2"
        >
          Fetched
          {sortBy === 'created_at' && (
            sortOrder === 'desc' ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />
          )}
        </Button>
        <Button
          variant={sortBy === 'published_at' ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleSortChange('published_at')}
          className="gap-2"
        >
          Published
          {sortBy === 'published_at' && (
            sortOrder === 'desc' ? <ArrowDown className="h-3 w-3" /> : <ArrowUp className="h-3 w-3" />
          )}
        </Button>
      </div>

      {/* Filters */}
      <ArticleFilters
        onFilterChange={handleFilterChange}
        initialFilters={filters}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters(!showFilters)}
      />

      {/* Articles List */}
      <div className="space-y-4">
        {articles && articles.length > 0 ? (
          articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              v3Analysis={article.v3_analysis || null}
              v3Loading={false}
              navigate={navigate}
            />
          ))
        ) : (
          <Card className="p-8 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Articles Found</h3>
            <p className="text-sm text-muted-foreground">
              There are no articles to display. Try adding some feeds first.
            </p>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {articles && articles.length > 0 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page + 1}
          </span>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setPage(page + 1)}
            disabled={!articles || articles.length < pageSize}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

// Article Card Component (inline)
function ArticleCard({
  article,
  v3Analysis,
  v3Loading,
  navigate,
}: {
  article: FeedItemWithFeed;
  v3Analysis: any;
  v3Loading: boolean;
  navigate: any;
}) {
  const [showContent, setShowContent] = useState(false);
  const [showResearch, setShowResearch] = useState(false);

  // Check if this is a research article
  const isResearchArticle = article.source_type === 'perplexity_research';
  // Check if this article has linked research
  const hasResearch = article.research_articles && article.research_articles.length > 0;

  return (
    <Card className="p-6 hover:shadow-md transition-shadow">
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-[320px_1fr]">
        {/* Left Column: V3 Analysis Block - Always shown for consistent layout */}
        <div className="lg:border-r border-border lg:pr-6">
          {v3Loading ? (
            <Skeleton className="h-48 w-full" />
          ) : v3Analysis && v3Analysis.tier0 ? (
            <ArticleV3AnalysisCard
              tier0={v3Analysis.tier0}
              tier1={v3Analysis.tier1}
              tier2={v3Analysis.tier2}
              compact={false}
            />
          ) : (
            <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg">
              {/* Show informative message based on content availability */}
              {/* 300 chars ≈ 50 words - matches scraping-service minimum threshold */}
              {(!article.content || article.content.length < 300) ? (
                <span>Insufficient content for tier analysis</span>
              ) : article.scrape_status === 'error' ? (
                <span>Scraping failed - analysis unavailable</span>
              ) : (
                <span>Analysis pending</span>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Article Info */}
        <div className="space-y-3">
          {/* Header: Feed Badge + Source Type Badge + Title + Original Link */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                {/* Feed Source Badge */}
                <Badge variant="outline">
                  {isResearchArticle ? 'Perplexity Research' : article.feed_name}
                </Badge>
                {/* Research Source Badge - Purple for AI-generated content */}
                {isResearchArticle && (
                  <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                    <Sparkles className="h-3 w-3 mr-1" />
                    AI Research
                  </Badge>
                )}
                {/* Has Research Indicator - Shows when original has linked research */}
                {hasResearch && (
                  <Badge variant="secondary" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    <BookOpen className="h-3 w-3 mr-1" />
                    {article.research_articles!.length} Research
                  </Badge>
                )}
              </div>
              <h3 className="text-xl font-semibold line-clamp-2 mb-2">{article.title}</h3>
              {/* Primary link to original article - prominently displayed */}
              <a
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline inline-flex items-center gap-1"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span className="font-medium">View Original Article</span>
              </a>
            </div>
          </div>

          {/* Meta: Dates, Author, Word Count */}
          <div className="space-y-2">
            {/* Primary Dates Row */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
              {article.published_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span className="font-medium">Published:</span>
                  <span>{formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}</span>
                </div>
              )}
              {article.created_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span className="font-medium">Fetched:</span>
                  <span>{formatDistanceToNow(new Date(article.created_at), { addSuffix: true })}</span>
                </div>
              )}
              {article.scraped_at && (
                <div className="flex items-center gap-1">
                  <File className="h-4 w-4" />
                  <span className="font-medium">Scraped:</span>
                  <span>{formatDistanceToNow(new Date(article.scraped_at), { addSuffix: true })}</span>
                </div>
              )}
            </div>
            {/* Secondary Info Row */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
              {article.author && (
                <div className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  <span>{article.author}</span>
                </div>
              )}
              {article.scrape_word_count && (
                <span>{article.scrape_word_count} words</span>
              )}
            </div>
          </div>

          {/* Content Preview - Auto-extracted first 2-3 sentences */}
          {(article.content || article.description) && (
            <div className="border-l-2 border-primary/20 pl-4 py-2 bg-muted/30 rounded">
              <p className="text-sm text-foreground leading-relaxed">
                {/* Use content if available, fallback to description */}
                {(() => {
                  const sourceText = article.content || article.description || '';
                  const preview = getFirstSentences(sourceText, 3);
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

          {/* Full Scraped Content (Collapsible) */}
          {article.content && (
            <div className="border border-border rounded-lg">
              <button
                className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                onClick={() => setShowContent(!showContent)}
              >
                <div className="flex items-center gap-2 text-sm font-medium">
                  <File className="h-4 w-4 text-green-600" />
                  <span>Scraped Content ({article.scrape_word_count || 0} words)</span>
                </div>
                {showContent ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
              {showContent && (
                <div className="p-3 border-t border-border text-sm text-muted-foreground max-h-96 overflow-y-auto">
                  <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                    {stripHtml(article.content)}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Research Articles (Collapsible) - For original articles with linked research */}
          {hasResearch && (
            <div className="border border-purple-200 dark:border-purple-800 rounded-lg bg-purple-50/50 dark:bg-purple-900/20">
              <button
                className="w-full flex items-center justify-between p-3 hover:bg-purple-100/50 dark:hover:bg-purple-900/30 transition-colors"
                onClick={() => setShowResearch(!showResearch)}
              >
                <div className="flex items-center gap-2 text-sm font-medium text-purple-800 dark:text-purple-200">
                  <Sparkles className="h-4 w-4" />
                  <span>Perplexity Research ({article.research_articles!.length} article{article.research_articles!.length > 1 ? 's' : ''})</span>
                </div>
                {showResearch ? (
                  <ChevronUp className="h-4 w-4 text-purple-600" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-purple-600" />
                )}
              </button>
              {showResearch && (
                <div className="p-3 border-t border-purple-200 dark:border-purple-800 space-y-3">
                  {article.research_articles!.map((research) => (
                    <div
                      key={research.id}
                      className="p-3 rounded-lg bg-white dark:bg-gray-800 border border-purple-100 dark:border-purple-700"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm mb-1">{research.title}</h4>
                          {research.description && (
                            <p className="text-xs text-muted-foreground line-clamp-3">
                              {stripHtml(research.description)}
                            </p>
                          )}
                          {/* Source metadata (model, cost, etc.) */}
                          {research.source_metadata && (
                            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                              {research.source_metadata.model && (
                                <span className="px-1.5 py-0.5 rounded bg-muted">
                                  {research.source_metadata.model}
                                </span>
                              )}
                              {research.created_at && (
                                <span>
                                  {formatDistanceToNow(new Date(research.created_at), { addSuffix: true })}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/articles/${research.id}`)}
                          className="shrink-0"
                        >
                          <BookOpen className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Source Metadata for Research Articles */}
          {isResearchArticle && article.source_metadata && (
            <div className="text-xs text-muted-foreground bg-purple-50 dark:bg-purple-900/20 rounded-lg p-2 flex items-center gap-3">
              <span className="font-medium text-purple-700 dark:text-purple-300">AI Research:</span>
              {article.source_metadata.model && (
                <span>Model: {article.source_metadata.model}</span>
              )}
              {article.source_metadata.query && (
                <span className="truncate max-w-xs">Query: "{article.source_metadata.query}"</span>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2 pt-2">
            {/* Primary action: View detailed analysis */}
            <Button
              variant="default"
              size="sm"
              onClick={() => navigate(`/articles/${article.id}`)}
            >
              View Full Analysis
            </Button>
            {/* Secondary action: Read original article (external link) */}
            <a
              href={article.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground text-sm font-medium transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Read Original
            </a>
          </div>
        </div>
      </div>
    </Card>
  );
}
