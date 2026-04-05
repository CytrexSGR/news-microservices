/**
 * EntitiesPage - Entity extraction results page
 *
 * Displays extracted entities with filtering and detailed views.
 */
import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  ArrowLeft,
  Search,
  RefreshCw,
  Download,
  AlertCircle,
  Users,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { EntityExtractionView } from '../components/EntityExtractionView';
import { AnalysisStatusBadge } from '../components/AnalysisStatusBadge';
import { useExtractEntities } from '../api/useExtractEntities';
import type { EntityType } from '../types/analysis.types';
import { getEntityTypeConfig } from '../types/analysis.types';

export function EntitiesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [articleId, setArticleId] = useState(searchParams.get('articleId') || '');
  const [searchQuery, setSearchQuery] = useState('');

  const {
    entities,
    entitiesByType,
    entityTypes,
    entityCounts,
    totalEntities,
    extractedAt,
    isLoading,
    isError,
    error,
    refetch,
  } = useExtractEntities({
    articleId,
    enabled: !!articleId,
  });

  // Update URL when article ID changes
  useEffect(() => {
    if (articleId) {
      setSearchParams({ articleId });
    }
  }, [articleId, setSearchParams]);

  // Filter entities by search query
  const filteredEntities = searchQuery
    ? entities.filter(
        (entity) =>
          entity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          entity.type.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : entities;

  const handleArticleIdSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  const handleExportJSON = () => {
    const data = {
      article_id: articleId,
      extracted_at: extractedAt,
      total_entities: totalEntities,
      entities_by_type: entityCounts,
      entities,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `entities-${articleId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/intelligence/analysis">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Analysis
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Entity Extraction</h1>
            <p className="text-sm text-muted-foreground">
              View and filter extracted entities from analyzed articles
            </p>
          </div>
        </div>

        {articleId && entities.length > 0 && (
          <Button variant="outline" size="sm" onClick={handleExportJSON}>
            <Download className="h-4 w-4 mr-2" />
            Export JSON
          </Button>
        )}
      </div>

      {/* Article ID input */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleArticleIdSubmit} className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Enter Article ID to view entities"
                value={articleId}
                onChange={(e) => setArticleId(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={!articleId || isLoading}>
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="ml-2">Load Entities</span>
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Content */}
      {!articleId ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
              <Users className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium mb-2">Enter Article ID</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Enter an article ID above to view extracted entities.
              You can also navigate here from the analysis page after completing an analysis.
            </p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </CardContent>
            </Card>
          </div>
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
              </CardHeader>
              <CardContent className="space-y-3">
                {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : isError ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Failed to Load Entities</AlertTitle>
          <AlertDescription>
            {error?.message || 'An error occurred while fetching entities.'}
            <Button variant="link" className="px-0 ml-2" onClick={() => refetch()}>
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      ) : entities.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
              <AlertCircle className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium mb-2">No Entities Found</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              No entities were extracted for this article. The article may not have been analyzed yet,
              or it may not contain any recognizable entities.
            </p>
            <Button variant="outline" className="mt-4" asChild>
              <Link to={`/intelligence/analysis?articleId=${articleId}`}>
                Run Analysis
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left sidebar: Summary */}
          <div className="lg:col-span-1 space-y-6">
            {/* Overview card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Overview
                </CardTitle>
                {extractedAt && (
                  <CardDescription>
                    Extracted {new Date(extractedAt).toLocaleString()}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center p-4 bg-primary/10 rounded-lg">
                  <div className="text-3xl font-bold text-primary">{totalEntities}</div>
                  <div className="text-sm text-muted-foreground">Total Entities</div>
                </div>

                <div className="text-center p-4 bg-secondary rounded-lg">
                  <div className="text-2xl font-bold">{entityTypes.length}</div>
                  <div className="text-sm text-muted-foreground">Entity Types</div>
                </div>
              </CardContent>
            </Card>

            {/* Entity type breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">By Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(entityCounts)
                    .sort(([, a], [, b]) => b - a)
                    .map(([type, count]) => {
                      const config = getEntityTypeConfig(type as EntityType);
                      const percentage = (count / totalEntities) * 100;

                      return (
                        <div key={type} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className={config.color}>{config.label}</span>
                            <span className="font-mono">{count}</span>
                          </div>
                          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                            <div
                              className={cn('h-full rounded-full', config.bgColor.replace('/30', ''))}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right content: Entity list */}
          <div className="lg:col-span-2 space-y-4">
            {/* Search */}
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search entities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button variant="ghost" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>

            {/* Entity list */}
            <EntityExtractionView
              entities={filteredEntities}
              extractedAt={extractedAt}
              showFilters={true}
              showConfidence={true}
              maxInitialItems={30}
            />

            {/* Search results info */}
            {searchQuery && (
              <p className="text-sm text-muted-foreground text-center">
                Showing {filteredEntities.length} of {entities.length} entities matching "{searchQuery}"
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
