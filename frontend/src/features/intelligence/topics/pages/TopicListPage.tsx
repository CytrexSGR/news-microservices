// frontend/src/features/intelligence/topics/pages/TopicListPage.tsx

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Tag, FileText, Hash, RefreshCw, Database, AlertTriangle, Sparkles, TextSearch } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { useTopics, useTopicSearch, useBatches } from '../api/useTopics';
import type { TopicListParams, TopicSummary, TopicSearchResult, TopicSearchParams } from '../types';

export function TopicListPage() {
  const [params, setParams] = useState<TopicListParams>({
    min_size: 5,
    limit: 50,
    offset: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchMode, setSearchMode] = useState<'semantic' | 'keyword'>('semantic');

  // Fetch topics
  const { data, isLoading, error, refetch } = useTopics(params);

  // Search topics (only when searching)
  const searchParams: TopicSearchParams = {
    q: searchQuery,
    mode: searchMode,
    limit: 50,
    min_similarity: 0.3,
  };
  const { data: searchData, isLoading: searchLoading } = useTopicSearch(
    searchParams,
    isSearching && searchQuery.length > 0
  );

  // Fetch latest batch info
  const { data: batchData } = useBatches('completed');
  const latestBatch = batchData?.batches?.[0];

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setIsSearching(true);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearching(false);
  };

  // Display data
  const displayTopics = isSearching && searchData ? searchData.results : data?.topics || [];
  const isLoadingAny = isLoading || searchLoading;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Tag className="h-6 w-6" />
            Topic Browser
          </h1>
          <p className="text-muted-foreground">
            Explore semantic topic clusters from news articles
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Batch Info Card */}
      {latestBatch && (
        <Card className="bg-muted/30">
          <CardContent className="py-3">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Latest Batch:</span>
              </div>
              <Badge variant="outline">{latestBatch.cluster_count} Topics</Badge>
              <Badge variant="outline">{latestBatch.article_count} Articles</Badge>
              {latestBatch.csai_score && (
                <Badge variant="secondary">CSAI: {(latestBatch.csai_score * 100).toFixed(1)}%</Badge>
              )}
              <span className="text-muted-foreground">
                {latestBatch.completed_at && new Date(latestBatch.completed_at).toLocaleString()}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Bar */}
      <Card>
        <CardContent className="py-4 space-y-3">
          {/* Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Search Mode:</span>
            <div className="flex rounded-md border overflow-hidden">
              <button
                type="button"
                onClick={() => setSearchMode('semantic')}
                className={`px-3 py-1.5 text-sm flex items-center gap-1.5 transition-colors ${
                  searchMode === 'semantic'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background hover:bg-muted'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5" />
                Semantic
              </button>
              <button
                type="button"
                onClick={() => setSearchMode('keyword')}
                className={`px-3 py-1.5 text-sm flex items-center gap-1.5 transition-colors ${
                  searchMode === 'keyword'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background hover:bg-muted'
                }`}
              >
                <TextSearch className="h-3.5 w-3.5" />
                Keyword
              </button>
            </div>
            <span className="text-xs text-muted-foreground ml-2">
              {searchMode === 'semantic'
                ? 'Uses AI embeddings for mathematical similarity'
                : 'Simple text matching in titles'}
            </span>
          </div>

          {/* Search Input */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchMode === 'semantic'
                  ? "Describe what you're looking for (e.g., 'military conflict in eastern europe')..."
                  : "Search topics by keyword..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={!searchQuery.trim()}>
              Search
            </Button>
            {isSearching && (
              <Button type="button" variant="outline" onClick={clearSearch}>
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="py-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>Failed to load topics. Please try again.</span>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoadingAny && (
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading topics...</p>
        </div>
      )}

      {/* Results Header */}
      {!isLoadingAny && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {isSearching
              ? <>
                  Found {searchData?.results.length || 0} topics matching "{searchQuery}"
                  {searchData?.mode === 'semantic' && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      <Sparkles className="h-3 w-3 mr-1" />
                      Semantic
                    </Badge>
                  )}
                  {searchData?.mode === 'keyword' && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      <TextSearch className="h-3 w-3 mr-1" />
                      Keyword
                    </Badge>
                  )}
                </>
              : `Showing ${displayTopics.length} of ${data?.total || 0} topics`}
          </p>
          {!isSearching && (
            <select
              className="text-sm border rounded px-2 py-1"
              value={params.min_size}
              onChange={(e) => setParams({ ...params, min_size: Number(e.target.value), offset: 0 })}
            >
              <option value={3}>Min 3 articles</option>
              <option value={5}>Min 5 articles</option>
              <option value={10}>Min 10 articles</option>
              <option value={20}>Min 20 articles</option>
            </select>
          )}
        </div>
      )}

      {/* Topic Grid */}
      {!isLoadingAny && displayTopics.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayTopics.map((topic) => (
            <TopicCard
              key={'cluster_id' in topic ? topic.cluster_id : topic.id}
              topic={topic}
              isSearchResult={'match_count' in topic}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoadingAny && displayTopics.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No Topics Found</h3>
            <p className="text-muted-foreground">
              {isSearching
                ? 'Try different keywords'
                : 'No topic clusters available yet'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {!isSearching && data && data.has_more && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => setParams({ ...params, offset: params.offset! + params.limit! })}
          >
            Load More
          </Button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Topic Card Component
// =============================================================================

interface TopicCardProps {
  topic: TopicSummary | TopicSearchResult;
  isSearchResult?: boolean;
}

function TopicCard({ topic, isSearchResult }: TopicCardProps) {
  const id = 'cluster_id' in topic ? topic.cluster_id : topic.id;
  const keywords = topic.keywords || [];

  return (
    <Link to={`/intelligence/topics/${id}`}>
      <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <CardTitle className="text-base line-clamp-2">
              {topic.label || `Topic #${id}`}
            </CardTitle>
            <Badge variant="secondary" className="shrink-0 ml-2">
              <Hash className="h-3 w-3 mr-1" />
              {topic.article_count}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Keywords */}
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {keywords.slice(0, 5).map((kw, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {kw}
                </Badge>
              ))}
              {keywords.length > 5 && (
                <Badge variant="outline" className="text-xs">
                  +{keywords.length - 5}
                </Badge>
              )}
            </div>
          )}

          {/* Semantic Similarity Score */}
          {isSearchResult && 'similarity' in topic && topic.similarity !== undefined && (
            <div className="flex items-center gap-1 text-xs">
              <Sparkles className="h-3 w-3 text-amber-500" />
              <span className="text-muted-foreground">Similarity:</span>
              <span className={`font-medium ${
                topic.similarity >= 0.7 ? 'text-green-600' :
                topic.similarity >= 0.5 ? 'text-amber-600' :
                'text-muted-foreground'
              }`}>
                {(topic.similarity * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Keyword Match Count */}
          {isSearchResult && 'match_count' in topic && topic.match_count !== undefined && (
            <p className="text-xs text-muted-foreground">
              {topic.match_count} matching articles
            </p>
          )}

          {/* Confidence */}
          {'label_confidence' in topic && topic.label_confidence && (
            <p className="text-xs text-muted-foreground">
              Confidence: {(topic.label_confidence * 100).toFixed(0)}%
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

export default TopicListPage;
