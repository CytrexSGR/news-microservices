import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useFeeds } from '@/features/feeds/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Input } from '@/components/ui/Input';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table';
import {
  Rss,
  Plus,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Settings,
  Activity,
  FileText,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { Feed } from '@/features/feeds/types';

export function FeedsPage() {
  const navigate = useNavigate();
  const { data: feeds, isLoading, error } = useFeeds();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter feeds based on search query
  const filteredFeeds = feeds?.filter((feed) =>
    feed.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    feed.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (feed.category && feed.category.toLowerCase().includes(searchQuery.toLowerCase()))
  ) ?? [];

  // Loading state
  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-4 w-64" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <Skeleton className="h-10 w-full max-w-md" />
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6">
        <div
          className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Feeds</h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Failed to load feeds'}
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
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Rss className="h-8 w-8 text-primary" />
            Feeds
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your RSS feed subscriptions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => navigate('/admin/services/feed-service')}
          >
            <Settings className="h-4 w-4 mr-2" />
            Admin
          </Button>
          <Button onClick={() => navigate('/admin/services/feed-service?tab=explorer')}>
            <Plus className="h-4 w-4 mr-2" />
            Add Feed
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Rss className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{feeds?.length ?? 0}</p>
              <p className="text-sm text-muted-foreground">Total Feeds</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {feeds?.filter((f) => f.is_active).length ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">Active</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10">
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {feeds?.filter((f) => !f.is_active).length ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">Inactive</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <FileText className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {feeds?.reduce((sum, f) => sum + (f.total_items ?? 0), 0) ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">Total Articles</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search feeds by name, URL, or category..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Feeds Table */}
      {filteredFeeds.length > 0 ? (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[300px]">Feed</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Health</TableHead>
                <TableHead>Articles</TableHead>
                <TableHead>Last Sync</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFeeds.map((feed) => (
                <FeedRow key={feed.id} feed={feed} navigate={navigate} />
              ))}
            </TableBody>
          </Table>
        </Card>
      ) : (
        <Card className="p-8 text-center">
          <Rss className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">
            {searchQuery ? 'No Feeds Found' : 'No Feeds Yet'}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Add your first RSS feed to start collecting articles'}
          </p>
          {!searchQuery && (
            <Button onClick={() => navigate('/admin/services/feed-service?tab=explorer')}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Feed
            </Button>
          )}
        </Card>
      )}
    </div>
  );
}

// Feed Row Component
function FeedRow({
  feed,
  navigate,
}: {
  feed: Feed;
  navigate: ReturnType<typeof useNavigate>;
}) {
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getHealthBg = (score: number) => {
    if (score >= 80) return 'bg-green-500/10';
    if (score >= 50) return 'bg-yellow-500/10';
    return 'bg-red-500/10';
  };

  return (
    <TableRow className="cursor-pointer" onClick={() => navigate(`/feeds/${feed.id}`)}>
      <TableCell>
        <div className="space-y-1">
          <div className="font-medium flex items-center gap-2">
            {feed.name}
            {feed.admiralty_code && (
              <Badge
                variant="outline"
                className="text-xs"
                style={{ borderColor: feed.admiralty_code.color, color: feed.admiralty_code.color }}
              >
                {feed.admiralty_code.code}
              </Badge>
            )}
          </div>
          <a
            href={feed.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 truncate max-w-[280px]"
          >
            <ExternalLink className="h-3 w-3 shrink-0" />
            <span className="truncate">{feed.url}</span>
          </a>
        </div>
      </TableCell>
      <TableCell>
        <Badge
          variant={feed.is_active ? 'default' : 'secondary'}
          className={feed.is_active ? 'bg-green-500/10 text-green-600 border-green-500/20' : ''}
        >
          {feed.is_active ? (
            <>
              <CheckCircle className="h-3 w-3 mr-1" />
              Active
            </>
          ) : (
            <>
              <XCircle className="h-3 w-3 mr-1" />
              Inactive
            </>
          )}
        </Badge>
      </TableCell>
      <TableCell>
        {feed.category ? (
          <Badge variant="outline">{feed.category}</Badge>
        ) : (
          <span className="text-muted-foreground text-sm">-</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <div className={`p-1 rounded ${getHealthBg(feed.health_score)}`}>
            <Activity className={`h-4 w-4 ${getHealthColor(feed.health_score)}`} />
          </div>
          <span className={`font-medium ${getHealthColor(feed.health_score)}`}>
            {feed.health_score}%
          </span>
        </div>
      </TableCell>
      <TableCell>
        <div className="space-y-0.5">
          <div className="font-medium">{feed.total_items.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground">
            +{feed.items_last_24h} today
          </div>
        </div>
      </TableCell>
      <TableCell>
        {feed.last_fetched_at ? (
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatDistanceToNow(new Date(feed.last_fetched_at), { addSuffix: true })}
          </div>
        ) : (
          <span className="text-muted-foreground text-sm">Never</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/feeds/${feed.id}`);
          }}
        >
          View Details
        </Button>
      </TableCell>
    </TableRow>
  );
}
