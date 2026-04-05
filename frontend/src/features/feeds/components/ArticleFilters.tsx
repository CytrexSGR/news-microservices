import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Calendar, X, Filter } from 'lucide-react';
import { useFeeds } from '../api/useFeeds';

export interface ArticleFilterValues {
  feedIds: string[];
  dateFrom: string | null;
  dateTo: string | null;
  sentiment: string | null;
  category: string | null;
  sourceType: string | null;
}

interface ArticleFiltersProps {
  onFilterChange: (filters: ArticleFilterValues) => void;
  initialFilters?: Partial<ArticleFilterValues>;
  showFilters: boolean;
  onToggleFilters: () => void;
}

const SENTIMENT_OPTIONS = [
  { value: 'positive', label: 'Positive' },
  { value: 'negative', label: 'Negative' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'mixed', label: 'Mixed' },
];

const CATEGORY_OPTIONS = [
  { value: 'Geopolitics Security', label: 'Geopolitics & Security' },
  { value: 'Politics Society', label: 'Politics & Security' },
  { value: 'Economy Markets', label: 'Economy & Markets' },
  { value: 'Climate Environment Health', label: 'Climate, Environment & Health' },
  { value: 'Panorama', label: 'Panorama' },
  { value: 'Technology Science', label: 'Technology & Science' },
];

const SOURCE_TYPE_OPTIONS = [
  { value: 'rss', label: 'RSS Feeds' },
  { value: 'perplexity_research', label: 'Perplexity Research' },
];

export function ArticleFilters({ onFilterChange, initialFilters = {}, showFilters, onToggleFilters }: ArticleFiltersProps) {
  const { data: feeds, isLoading: feedsLoading } = useFeeds();

  const [filters, setFilters] = useState<ArticleFilterValues>({
    feedIds: initialFilters.feedIds || [],
    dateFrom: initialFilters.dateFrom || null,
    dateTo: initialFilters.dateTo || null,
    sentiment: initialFilters.sentiment || null,
    category: initialFilters.category || null,
    sourceType: initialFilters.sourceType || null,
  });

  const handleFeedToggle = (feedId: string) => {
    const newFilters = {
      ...filters,
      feedIds: filters.feedIds.includes(feedId)
        ? filters.feedIds.filter(id => id !== feedId)
        : [...filters.feedIds, feedId],
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDateFromChange = (value: string) => {
    const newFilters = { ...filters, dateFrom: value || null };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDateToChange = (value: string) => {
    const newFilters = { ...filters, dateTo: value || null };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSentimentChange = (value: string) => {
    const newFilters = { ...filters, sentiment: value || null };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleCategoryChange = (value: string) => {
    const newFilters = { ...filters, category: value || null };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSourceTypeChange = (value: string) => {
    const newFilters = { ...filters, sourceType: value || null };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const newFilters = {
      feedIds: [],
      dateFrom: null,
      dateTo: null,
      sentiment: null,
      category: null,
      sourceType: null,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const activeFilterCount =
    filters.feedIds.length +
    (filters.dateFrom ? 1 : 0) +
    (filters.dateTo ? 1 : 0) +
    (filters.sentiment ? 1 : 0) +
    (filters.category ? 1 : 0) +
    (filters.sourceType ? 1 : 0);

  return (
    <div className="space-y-4">
      {/* Filter Toggle Button */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleFilters}
          className="gap-2"
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <Badge variant="default" className="ml-1 px-1.5 py-0.5 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="gap-1 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
            <span>Clear All</span>
          </Button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="border border-border rounded-lg p-4 space-y-4 bg-card">
          {/* Source Type Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Source Type</label>
            <div className="grid grid-cols-2 gap-2">
              {SOURCE_TYPE_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleSourceTypeChange(
                    filters.sourceType === option.value ? '' : option.value
                  )}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    filters.sourceType === option.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80 text-muted-foreground'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Feed Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Feeds</label>
              {filters.feedIds.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilters(prev => ({ ...prev, feedIds: [] }))}
                  className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
            <div className="space-y-1">
              {feedsLoading ? (
                <p className="text-sm text-muted-foreground">Loading feeds...</p>
              ) : feeds && feeds.length > 0 ? (
                <div className="border border-border rounded-md max-h-[200px] overflow-y-auto">
                  {feeds.map(feed => (
                    <label
                      key={feed.id}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-muted cursor-pointer border-b border-border last:border-b-0"
                    >
                      <input
                        type="checkbox"
                        checked={filters.feedIds.includes(feed.id)}
                        onChange={() => handleFeedToggle(feed.id)}
                        className="h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary cursor-pointer"
                      />
                      <span className="text-sm flex-1">{feed.name}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No feeds available</p>
              )}
              {feeds && feeds.length > 0 && filters.feedIds.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {filters.feedIds.length} feed{filters.feedIds.length !== 1 ? 's' : ''} selected
                </p>
              )}
            </div>
          </div>

          {/* Date Range Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Date Range
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">From</label>
                <input
                  type="date"
                  value={filters.dateFrom || ''}
                  onChange={(e) => handleDateFromChange(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">To</label>
                <input
                  type="date"
                  value={filters.dateTo || ''}
                  onChange={(e) => handleDateToChange(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm"
                />
              </div>
            </div>
          </div>

          {/* Sentiment Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sentiment</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {SENTIMENT_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleSentimentChange(
                    filters.sentiment === option.value ? '' : option.value
                  )}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    filters.sentiment === option.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80 text-muted-foreground'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Category</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {CATEGORY_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleCategoryChange(
                    filters.category === option.value ? '' : option.value
                  )}
                  className={`px-3 py-2 rounded-md text-sm text-left transition-colors ${
                    filters.category === option.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80 text-muted-foreground'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
