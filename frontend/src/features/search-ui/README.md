# Search UI Feature

**Public article search interface for end users.**

## 📋 Overview

The Search UI feature provides a comprehensive, user-friendly search interface for discovering articles across the entire news database. Unlike the admin search feature (`/features/search`), this is a **public-facing** interface designed for end-user article discovery.

### Key Characteristics

- **Access:** Public (no authentication required, uses `get_optional_user`)
- **Purpose:** User-facing article search and discovery
- **Location:** `/search` route
- **Status:** 🚧 **In Development** (placeholder page exists)

### Related Features

```
/features/
├── search/           # Admin statistics dashboard (DONE)
│   ├── components/   # CacheStatsCard, SearchDashboard
│   └── hooks/        # useCacheStats, useIndexStats, etc.
│
└── search-ui/        # Public search interface (THIS FEATURE)
    ├── components/   # SearchBar, ResultList, FilterPanel
    ├── hooks/        # useArticleSearch, useSuggestions
    └── types/        # SearchRequest, SearchResult, etc.
```

---

## 🏗️ Architecture

### Component Organization

```
features/search-ui/
├── README.md                    # This file
├── COMPONENT_TEMPLATE.md        # Component creation guide
│
├── components/                  # React components
│   ├── search-bar/
│   │   ├── SearchInput.tsx      # Main search input with autocomplete
│   │   ├── SearchFilters.tsx    # Advanced filter panel
│   │   └── SearchSuggestions.tsx # Autocomplete dropdown
│   │
│   ├── results/
│   │   ├── ResultList.tsx       # Paginated result list
│   │   ├── ResultCard.tsx       # Individual result card
│   │   ├── ResultPagination.tsx # Pagination controls
│   │   └── ResultStats.tsx      # "Found X results in Y ms"
│   │
│   ├── facets/
│   │   ├── SourceFacet.tsx      # Filter by source
│   │   ├── SentimentFacet.tsx   # Filter by sentiment
│   │   └── DateRangeFacet.tsx   # Date range selector
│   │
│   └── index.ts                 # Barrel export
│
├── hooks/                       # React Query hooks
│   ├── useArticleSearch.ts      # Main search hook
│   ├── useSuggestions.ts        # Autocomplete suggestions
│   ├── usePopularQueries.ts     # Popular search queries
│   ├── useRelatedSearches.ts    # Related queries
│   └── index.ts                 # Barrel export
│
├── types/                       # TypeScript definitions
│   ├── search.ts                # SearchRequest, SearchResponse
│   ├── filters.ts               # SearchFilters, Facets
│   └── index.ts                 # Barrel export
│
├── utils/                       # Utility functions
│   ├── queryBuilder.ts          # Build search queries
│   ├── highlighter.ts           # Highlight search terms
│   └── formatters.ts            # Format dates, numbers
│
└── index.ts                     # Main barrel export
```

---

## 🔌 API Integration

### Backend Endpoints

The search-ui feature connects to the **Search Service** (port 8106):

#### 1. Basic Search
```http
GET /api/v1/search?query={query}&page={page}&page_size={size}
```

**Query Parameters:**
- `query` (required): Search query (1-500 chars)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (1-100, default: 20)
- `source` (optional): Filter by source(s), comma-separated
- `sentiment` (optional): Filter by sentiment(s), comma-separated
- `date_from` (optional): Filter by date from (ISO 8601)
- `date_to` (optional): Filter by date to (ISO 8601)

**Example:**
```bash
GET /api/v1/search?query=tesla&page=1&page_size=20&source=reuters,bloomberg&sentiment=positive
```

#### 2. Advanced Search
```http
POST /api/v1/search/advanced
```

**Request Body:**
```typescript
{
  query: string;
  page: number;
  page_size: number;
  filters?: {
    source?: string[];
    sentiment?: string[];
    date_from?: string;
    date_to?: string;
  };
  options?: {
    fuzzy?: boolean;          // Enable fuzzy matching
    highlight?: boolean;      // Highlight search terms
    facets?: boolean;         // Return faceted results
  };
}
```

**Response:**
```typescript
{
  results: Article[];
  total: number;
  page: number;
  page_size: number;
  execution_time_ms: number;
  facets?: {
    sources: { source: string; count: number }[];
    sentiments: { sentiment: string; count: number }[];
  };
}
```

#### 3. Autocomplete Suggestions
```http
GET /api/v1/search/suggest?query={partial}&limit={limit}
```

**Response:**
```typescript
{
  query: string;
  suggestions: string[];
}
```

#### 4. Popular Queries
```http
GET /api/v1/search/popular?limit={limit}
```

**Response:**
```typescript
{
  popular_queries: {
    query: string;
    hits: number;
  }[];
  total: number;
}
```

#### 5. Related Searches
```http
GET /api/v1/search/related?query={query}&limit={limit}
```

**Response:**
```typescript
{
  query: string;
  related: string[];
}
```

---

## 🎨 Component Examples

### SearchBar Component

**File:** `components/search-bar/SearchInput.tsx`

```tsx
import { useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { useSuggestions } from '@/features/search-ui/hooks';

interface SearchInputProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  className?: string;
}

export function SearchInput({ onSearch, placeholder, className }: SearchInputProps) {
  const [query, setQuery] = useState('');
  const { data: suggestions, isLoading } = useSuggestions(query);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div className="relative">
        <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder || "Search articles..."}
          className="pl-10"
        />
        {isLoading && <div className="absolute right-3 top-3">Loading...</div>}
      </div>

      {suggestions && suggestions.length > 0 && (
        <div className="absolute mt-1 w-full bg-white rounded-md shadow-lg">
          {suggestions.map((suggestion, i) => (
            <div
              key={i}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
              onClick={() => {
                setQuery(suggestion);
                onSearch(suggestion);
              }}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </form>
  );
}
```

### ResultCard Component

**File:** `components/results/ResultCard.tsx`

```tsx
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatDistanceToNow } from 'date-fns';
import type { Article } from '@/types/article';

interface ResultCardProps {
  article: Article;
  highlight?: string;
}

export function ResultCard({ article, highlight }: ResultCardProps) {
  const highlightText = (text: string) => {
    if (!highlight) return text;

    const regex = new RegExp(`(${highlight})`, 'gi');
    return text.split(regex).map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200">{part}</mark>
      ) : (
        part
      )
    );
  };

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-2">
        {/* Title */}
        <h3 className="text-lg font-semibold">
          <a href={`/articles/${article.id}`} className="hover:text-primary">
            {highlightText(article.title)}
          </a>
        </h3>

        {/* Metadata */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{article.source}</span>
          <span>•</span>
          <span>{formatDistanceToNow(new Date(article.published_at))} ago</span>
          {article.sentiment && (
            <>
              <span>•</span>
              <Badge variant={article.sentiment === 'positive' ? 'success' : 'default'}>
                {article.sentiment}
              </Badge>
            </>
          )}
        </div>

        {/* Summary */}
        {article.summary && (
          <p className="text-sm line-clamp-2">
            {highlightText(article.summary)}
          </p>
        )}
      </div>
    </Card>
  );
}
```

---

## 🪝 React Query Hooks

### useArticleSearch Hook

**File:** `hooks/useArticleSearch.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import type { SearchRequest, SearchResponse } from '../types';

/**
 * Search articles with advanced filtering
 *
 * @param request - Search request parameters
 * @param enabled - Whether to execute the query
 * @returns React Query result
 */
export function useArticleSearch(
  request: SearchRequest,
  enabled = true
) {
  return useQuery({
    queryKey: ['search', 'articles', request],
    queryFn: async (): Promise<SearchResponse> => {
      const params = new URLSearchParams({
        query: request.query,
        page: request.page.toString(),
        page_size: request.page_size.toString(),
      });

      if (request.filters?.source) {
        params.append('source', request.filters.source.join(','));
      }
      if (request.filters?.sentiment) {
        params.append('sentiment', request.filters.sentiment.join(','));
      }
      if (request.filters?.date_from) {
        params.append('date_from', request.filters.date_from);
      }
      if (request.filters?.date_to) {
        params.append('date_to', request.filters.date_to);
      }

      const { data } = await searchApi.get(`/api/v1/search?${params}`);
      return data;
    },
    enabled: enabled && request.query.length > 0,
    staleTime: 30000, // 30 seconds
    gcTime: 300000,   // 5 minutes cache
  });
}
```

### useSuggestions Hook

**File:** `hooks/useSuggestions.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';

/**
 * Get autocomplete suggestions for search query
 *
 * @param query - Partial query string
 * @param limit - Maximum suggestions
 * @returns React Query result
 */
export function useSuggestions(
  query: string,
  limit = 10
) {
  return useQuery({
    queryKey: ['search', 'suggestions', query, limit],
    queryFn: async () => {
      const { data } = await searchApi.get('/api/v1/search/suggest', {
        params: { query, limit }
      });
      return data.suggestions as string[];
    },
    enabled: query.length >= 2, // Only fetch for 2+ chars
    staleTime: 60000,           // 60 seconds
  });
}
```

---

## 📘 Type Definitions

### Core Types

**File:** `types/search.ts`

```typescript
/**
 * Search request parameters
 */
export interface SearchRequest {
  query: string;
  page: number;
  page_size: number;
  filters?: SearchFilters;
}

/**
 * Search filters
 */
export interface SearchFilters {
  source?: string[];
  sentiment?: string[];
  date_from?: string;
  date_to?: string;
}

/**
 * Search response
 */
export interface SearchResponse {
  results: Article[];
  total: number;
  page: number;
  page_size: number;
  execution_time_ms: number;
  facets?: SearchFacets;
}

/**
 * Search facets for filtering
 */
export interface SearchFacets {
  sources: { source: string; count: number }[];
  sentiments: { sentiment: string; count: number }[];
}

/**
 * Article in search results
 */
export interface Article {
  id: string;
  title: string;
  summary?: string;
  source: string;
  published_at: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  url: string;
}
```

---

## 🎯 Usage Examples

### Basic Search Page

```tsx
import { useState } from 'react';
import { SearchInput, ResultList } from '@/features/search-ui/components';
import { useArticleSearch } from '@/features/search-ui/hooks';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useArticleSearch({
    query,
    page,
    page_size: 20,
  });

  return (
    <div className="space-y-6">
      <SearchInput onSearch={setQuery} />

      {isLoading && <div>Searching...</div>}
      {error && <div>Error: {error.message}</div>}

      {data && (
        <>
          <div className="text-sm text-muted-foreground">
            Found {data.total} results in {data.execution_time_ms}ms
          </div>

          <ResultList
            results={data.results}
            highlight={query}
          />

          <Pagination
            currentPage={page}
            totalPages={Math.ceil(data.total / data.page_size)}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
```

### Advanced Search with Filters

```tsx
import { useState } from 'react';
import { useArticleSearch } from '@/features/search-ui/hooks';

export function AdvancedSearch() {
  const [filters, setFilters] = useState<SearchFilters>({});

  const { data } = useArticleSearch({
    query: 'tesla',
    page: 1,
    page_size: 20,
    filters,
  });

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Sidebar Filters */}
      <aside className="col-span-3">
        <FilterPanel
          filters={filters}
          onChange={setFilters}
          facets={data?.facets}
        />
      </aside>

      {/* Results */}
      <main className="col-span-9">
        <ResultList results={data?.results || []} />
      </main>
    </div>
  );
}
```

---

## 🚀 Development Guidelines

### 1. Component Creation

When creating new components, follow this structure:

```tsx
/**
 * ComponentName - Brief description
 *
 * @component
 * @example
 * <ComponentName prop1="value" />
 */

interface ComponentNameProps {
  // Props with JSDoc comments
}

export function ComponentName({ ...props }: ComponentNameProps) {
  // Component implementation
}
```

See [COMPONENT_TEMPLATE.md](./COMPONENT_TEMPLATE.md) for full template.

### 2. Hook Creation

All hooks should:
- Use React Query for data fetching
- Include TypeScript types
- Provide loading/error states
- Use appropriate cache strategies

```typescript
/**
 * Hook description
 *
 * @param params - Parameter description
 * @returns React Query result
 */
export function useCustomHook(params: Params) {
  return useQuery({
    queryKey: ['namespace', ...params],
    queryFn: async () => { /* fetch */ },
    staleTime: 30000,
    enabled: /* condition */,
  });
}
```

### 3. Performance Optimization

**Debounce Search Input:**
```typescript
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

const [query, setQuery] = useState('');
const debouncedQuery = useDebouncedValue(query, 300);

const { data } = useArticleSearch({ query: debouncedQuery });
```

**Lazy Load Results:**
```typescript
// Use infinite query for scroll loading
import { useInfiniteQuery } from '@tanstack/react-query';

const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['search', query],
  queryFn: ({ pageParam = 1 }) => fetchArticles(query, pageParam),
  getNextPageParam: (lastPage) => lastPage.nextPage,
});
```

### 4. Testing Guidelines

**Component Tests:**
```typescript
import { render, screen } from '@testing-library/react';
import { SearchInput } from './SearchInput';

test('renders search input', () => {
  render(<SearchInput onSearch={jest.fn()} />);
  expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
});
```

**Hook Tests:**
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useArticleSearch } from './useArticleSearch';

test('fetches search results', async () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  const { result } = renderHook(
    () => useArticleSearch({ query: 'test', page: 1, page_size: 20 }),
    { wrapper }
  );

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.results).toBeDefined();
});
```

---

## 🎨 UI/UX Considerations

### 1. Search Experience

- **Instant Feedback:** Show loading state immediately
- **Autocomplete:** Suggest queries as user types (2+ chars)
- **Highlight:** Bold search terms in results
- **Empty State:** Show helpful message when no results

### 2. Performance

- **Debouncing:** Wait 300ms before searching
- **Pagination:** Default 20 results per page
- **Caching:** Cache results for 30 seconds
- **Progressive Enhancement:** Load filters after initial results

### 3. Accessibility

- **Keyboard Navigation:** Arrow keys for suggestions
- **Screen Readers:** Announce result counts
- **Focus Management:** Focus search input on page load
- **ARIA Labels:** Proper labels for all interactive elements

---

## 📊 Performance Benchmarks

**Target Metrics:**
- **Time to Interactive:** < 2s
- **Search Response:** < 200ms (cached), < 500ms (fresh)
- **Autocomplete:** < 100ms
- **Result Rendering:** < 50ms (20 results)

**Optimization Strategies:**
1. Use `React.memo()` for ResultCard
2. Virtualize long result lists (react-window)
3. Lazy load facet components
4. Preload popular queries

---

## 🔗 Related Documentation

### Frontend
- [Main Frontend Guide](/home/cytrex/news-microservices/CLAUDE.frontend.md)
- [Feature Organization](/home/cytrex/news-microservices/frontend/src/features/README.md)
- [React Query Setup](/home/cytrex/news-microservices/frontend/src/lib/queryClient.ts)

### Backend
- [Search Service Documentation](/home/cytrex/news-microservices/docs/services/search-service.md)
- [Search API Reference](http://localhost:8106/docs)
- [Search Service Architecture](/home/cytrex/news-microservices/services/search-service/README.md)

### Admin Feature (Statistics)
- [Admin Search Feature](/home/cytrex/news-microservices/frontend/src/features/search/README.md)
- [Search Dashboard Component](/home/cytrex/news-microservices/frontend/src/features/search/components/SearchDashboard.tsx)

---

## 🚨 Troubleshooting

### Issue: Autocomplete not working

**Solution:**
1. Check query length (must be >= 2 chars)
2. Verify Search Service is running: `http://localhost:8106/health`
3. Check browser console for CORS errors
4. Ensure `VITE_SEARCH_API_URL` is configured

### Issue: Slow search results

**Solution:**
1. Check Search Service performance: `GET /api/v1/admin/stats/performance`
2. Verify database indexes exist
3. Increase `staleTime` to reduce API calls
4. Enable Redis caching on backend

### Issue: Results not updating

**Solution:**
1. Check React Query cache: Use React Query DevTools
2. Verify `staleTime` configuration
3. Force refetch: `refetch()` from hook
4. Clear cache: `queryClient.invalidateQueries(['search'])`

---

## 📈 Future Enhancements

### Phase 1 (MVP)
- [x] Basic search input
- [ ] Result list with pagination
- [ ] Source/sentiment filters
- [ ] Date range filter
- [ ] Autocomplete suggestions

### Phase 2 (Advanced)
- [ ] Fuzzy search
- [ ] Search highlighting
- [ ] Faceted search
- [ ] Saved searches
- [ ] Search history

### Phase 3 (Premium)
- [ ] Natural language queries
- [ ] Advanced boolean operators
- [ ] Export results (CSV/PDF)
- [ ] Search alerts
- [ ] Collaborative filters

---

## 📝 Implementation Checklist

Use this checklist when implementing the search-ui feature:

### Components
- [ ] `SearchInput.tsx` - Main search input with autocomplete
- [ ] `SearchFilters.tsx` - Filter panel (source, sentiment, date)
- [ ] `SearchSuggestions.tsx` - Autocomplete dropdown
- [ ] `ResultList.tsx` - Paginated result list
- [ ] `ResultCard.tsx` - Individual result card
- [ ] `ResultPagination.tsx` - Pagination controls
- [ ] `ResultStats.tsx` - Result count and timing
- [ ] `EmptyState.tsx` - No results message

### Hooks
- [ ] `useArticleSearch.ts` - Main search hook
- [ ] `useSuggestions.ts` - Autocomplete suggestions
- [ ] `usePopularQueries.ts` - Popular searches
- [ ] `useRelatedSearches.ts` - Related queries
- [ ] `useSearchHistory.ts` - User search history (optional)

### Types
- [ ] `search.ts` - SearchRequest, SearchResponse
- [ ] `filters.ts` - SearchFilters, Facets
- [ ] `article.ts` - Article type (may already exist)

### Utils
- [ ] `queryBuilder.ts` - Build search query params
- [ ] `highlighter.ts` - Highlight search terms
- [ ] `formatters.ts` - Format dates, numbers

### Integration
- [ ] Connect SearchPage to components
- [ ] Add route to App.tsx
- [ ] Configure API client
- [ ] Add navigation link
- [ ] Write tests

---

## 👥 Contributing

When contributing to the search-ui feature:

1. **Read the template:** See [COMPONENT_TEMPLATE.md](./COMPONENT_TEMPLATE.md)
2. **Follow patterns:** Match existing component structure
3. **Document props:** Add JSDoc to all public interfaces
4. **Test thoroughly:** Write tests for new components/hooks
5. **Update docs:** Update this README when adding features

---

**Created:** 2025-11-02
**Status:** 🚧 In Development
**Maintainer:** Frontend Team
**Related Features:** `/features/search` (admin dashboard)
