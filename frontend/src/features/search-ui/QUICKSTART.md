# Quick Start Guide - Search UI Feature

**Get started with the public search interface in 5 minutes.**

---

## ⚡ Installation (Already Done)

The search-ui feature is part of the main frontend codebase. No additional installation needed!

```bash
# Location
cd /home/cytrex/news-microservices/frontend/src/features/search-ui
```

---

## 🚀 5-Minute Quick Start

### Step 1: Import Components

```tsx
import {
  SearchInput,
  ResultList,
  ResultCard,
  ResultPagination
} from '@/features/search-ui/components';
```

### Step 2: Import Hooks

```tsx
import {
  useArticleSearch,
  useSuggestions
} from '@/features/search-ui/hooks';
```

### Step 3: Create Your Search Page

```tsx
import { useState } from 'react';
import { SearchInput, ResultList } from '@/features/search-ui/components';
import { useArticleSearch } from '@/features/search-ui/hooks';

export function MySearchPage() {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useArticleSearch({
    query,
    page,
    page_size: 20,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Search Articles</h1>

      <SearchInput onSearch={setQuery} />

      {isLoading && <div>Loading...</div>}
      {error && <div>Error: {error.message}</div>}

      {data && (
        <>
          <p className="text-sm text-muted-foreground">
            Found {data.total} results
          </p>

          <ResultList results={data.results} />

          <ResultPagination
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

### Step 4: Add Route

Edit `/home/cytrex/news-microservices/frontend/src/App.tsx`:

```tsx
import { MySearchPage } from '@/pages/MySearchPage';

// In Routes:
<Route path="/search" element={<MySearchPage />} />
```

### Step 5: Test It!

```bash
# Start dev server (if not running)
cd /home/cytrex/news-microservices
docker compose up -d

# Open browser
http://localhost:3000/search
```

---

## 🎯 Common Use Cases

### 1. Basic Search

**Goal:** Simple search input with results

```tsx
import { useState } from 'react';
import { useArticleSearch } from '@/features/search-ui/hooks';

export function BasicSearch() {
  const [query, setQuery] = useState('');

  const { data, isLoading } = useArticleSearch({
    query,
    page: 1,
    page_size: 20,
  });

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
      />

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <ul>
          {data?.results.map((article) => (
            <li key={article.id}>{article.title}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### 2. Search with Autocomplete

**Goal:** Show suggestions as user types

```tsx
import { useState } from 'react';
import { useSuggestions } from '@/features/search-ui/hooks';

export function SearchWithAutocomplete() {
  const [query, setQuery] = useState('');
  const { data: suggestions } = useSuggestions(query);

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type to search..."
      />

      {suggestions && suggestions.length > 0 && (
        <div className="absolute mt-1 bg-white border rounded shadow-lg">
          {suggestions.map((suggestion, i) => (
            <div
              key={i}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
              onClick={() => setQuery(suggestion)}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 3. Search with Filters

**Goal:** Filter results by source and sentiment

```tsx
import { useState } from 'react';
import { useArticleSearch } from '@/features/search-ui/hooks';
import type { SearchFilters } from '@/features/search-ui/types';

export function FilteredSearch() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});

  const { data } = useArticleSearch({
    query,
    page: 1,
    page_size: 20,
    filters,
  });

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Sidebar Filters */}
      <aside className="col-span-3">
        <h3>Filters</h3>

        <div>
          <h4>Source</h4>
          <label>
            <input
              type="checkbox"
              onChange={(e) => {
                setFilters({
                  ...filters,
                  source: e.target.checked
                    ? [...(filters.source || []), 'reuters']
                    : filters.source?.filter((s) => s !== 'reuters'),
                });
              }}
            />
            Reuters
          </label>
        </div>

        <div>
          <h4>Sentiment</h4>
          <label>
            <input
              type="checkbox"
              onChange={(e) => {
                setFilters({
                  ...filters,
                  sentiment: e.target.checked
                    ? [...(filters.sentiment || []), 'positive']
                    : filters.sentiment?.filter((s) => s !== 'positive'),
                });
              }}
            />
            Positive
          </label>
        </div>
      </aside>

      {/* Results */}
      <main className="col-span-9">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
        />

        <div>Found {data?.total || 0} results</div>

        <ul>
          {data?.results.map((article) => (
            <li key={article.id}>{article.title}</li>
          ))}
        </ul>
      </main>
    </div>
  );
}
```

### 4. Search with Pagination

**Goal:** Handle multiple pages of results

```tsx
import { useState } from 'react';
import { useArticleSearch } from '@/features/search-ui/hooks';

export function PaginatedSearch() {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const { data, isLoading } = useArticleSearch({
    query,
    page,
    page_size: PAGE_SIZE,
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setPage(1); // Reset to page 1 on new search
        }}
        placeholder="Search..."
      />

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div>
            Showing {(page - 1) * PAGE_SIZE + 1}-
            {Math.min(page * PAGE_SIZE, data?.total || 0)} of {data?.total || 0}
          </div>

          <ul>
            {data?.results.map((article) => (
              <li key={article.id}>{article.title}</li>
            ))}
          </ul>

          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              Previous
            </button>

            <span>
              Page {page} of {totalPages}
            </span>

            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

### 5. Search with Popular Queries

**Goal:** Show trending searches

```tsx
import { usePopularQueries } from '@/features/search-ui/hooks';

export function PopularSearches() {
  const { data: popular } = usePopularQueries(10);

  return (
    <div>
      <h3>Trending Searches</h3>
      <ul>
        {popular?.popular_queries.map((q) => (
          <li key={q.query}>
            <a href={`/search?q=${q.query}`}>
              {q.query} ({q.hits} searches)
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 🎨 Component Examples

### Pre-built Components (To Be Implemented)

Once implemented, you can use these ready-made components:

```tsx
// SearchInput with autocomplete
import { SearchInput } from '@/features/search-ui/components';

<SearchInput
  onSearch={(query) => console.log(query)}
  placeholder="Search articles..."
/>

// ResultCard
import { ResultCard } from '@/features/search-ui/components';

<ResultCard
  article={article}
  highlight="search term"
/>

// ResultList
import { ResultList } from '@/features/search-ui/components';

<ResultList
  results={articles}
  highlight="search term"
/>

// Filters
import { SearchFilters } from '@/features/search-ui/components';

<SearchFilters
  filters={filters}
  onChange={setFilters}
  facets={facets}
/>
```

---

## 🪝 Available Hooks

### useArticleSearch

**Main search hook**

```typescript
const { data, isLoading, error, refetch } = useArticleSearch({
  query: 'tesla',
  page: 1,
  page_size: 20,
  filters: {
    source: ['reuters', 'bloomberg'],
    sentiment: ['positive'],
    date_from: '2025-01-01',
    date_to: '2025-11-02',
  },
});

// data.results: Article[]
// data.total: number
// data.execution_time_ms: number
```

### useSuggestions

**Autocomplete suggestions**

```typescript
const { data: suggestions } = useSuggestions(
  'tes',  // query (2+ chars)
  10      // limit
);

// suggestions: string[]
```

### usePopularQueries

**Trending searches**

```typescript
const { data: popular } = usePopularQueries(10);

// popular.popular_queries: { query: string; hits: number }[]
```

### useRelatedSearches

**Related queries**

```typescript
const { data: related } = useRelatedSearches('tesla', 5);

// related.related: string[]
```

---

## 🔧 Configuration

### API Endpoint

Ensure Search Service URL is configured in `.env`:

```env
VITE_SEARCH_API_URL=http://localhost:8106
```

### React Query Options

Customize cache behavior:

```typescript
const { data } = useArticleSearch(
  { query: 'tesla', page: 1, page_size: 20 },
  {
    staleTime: 60000,      // Cache for 60 seconds
    refetchInterval: 5000, // Auto-refresh every 5 seconds
    enabled: true,         // Enable/disable query
  }
);
```

---

## 🧪 Testing Your Search

### 1. Manual Testing

```bash
# Start services
docker compose up -d

# Check Search Service is running
curl http://localhost:8106/health

# Test search endpoint
curl "http://localhost:8106/api/v1/search?query=test&page=1&page_size=5"

# Test suggestions
curl "http://localhost:8106/api/v1/search/suggest?query=te&limit=10"
```

### 2. Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BasicSearch } from './BasicSearch';

test('renders search input', () => {
  const queryClient = new QueryClient();

  render(
    <QueryClientProvider client={queryClient}>
      <BasicSearch />
    </QueryClientProvider>
  );

  expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
});
```

---

## 🐛 Troubleshooting

### Issue: "No results found"

**Solutions:**
1. Check Search Service is running: `docker compose ps search-service`
2. Verify articles are indexed: `curl http://localhost:8106/api/v1/admin/stats/index`
3. Check search query is valid (1-500 chars)
4. Try simpler query (single word)

### Issue: "CORS error"

**Solutions:**
1. Verify `VITE_SEARCH_API_URL` in `.env`
2. Check CORS settings in Search Service
3. Ensure frontend and backend are on same domain in production

### Issue: "Autocomplete not working"

**Solutions:**
1. Query must be 2+ characters
2. Check Search Service `/suggest` endpoint
3. Verify React Query hook is enabled
4. Check browser console for errors

### Issue: "Slow search results"

**Solutions:**
1. Enable Redis caching on backend
2. Increase `staleTime` to reduce API calls
3. Check Search Service performance stats
4. Verify database indexes exist

---

## 📚 Next Steps

### Learn More

1. **Full Documentation:** [README.md](./README.md)
2. **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
3. **Component Guide:** [COMPONENT_TEMPLATE.md](./COMPONENT_TEMPLATE.md)
4. **API Reference:** http://localhost:8106/docs

### Build Your Feature

1. **Create Components:**
   - Copy template from `COMPONENT_TEMPLATE.md`
   - Implement your component
   - Add to `components/index.ts`

2. **Create Hooks:**
   - Follow hook template pattern
   - Use React Query
   - Add to `hooks/index.ts`

3. **Add Tests:**
   - Create `__tests__` directory
   - Write component tests
   - Test hooks with React Testing Library

4. **Document:**
   - Add JSDoc comments
   - Update README with usage
   - Add examples

---

## 💡 Pro Tips

### 1. Debounce User Input

```tsx
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

const [query, setQuery] = useState('');
const debouncedQuery = useDebouncedValue(query, 300);

const { data } = useArticleSearch({ query: debouncedQuery });
```

### 2. Show Loading State Immediately

```tsx
const { data, isLoading, isFetching } = useArticleSearch({ query });

{isLoading && <div>Loading initial results...</div>}
{isFetching && !isLoading && <div>Updating...</div>}
```

### 3. Handle Empty States

```tsx
{data && data.results.length === 0 && (
  <div>
    <p>No results found for "{query}"</p>
    <p>Try different keywords or filters</p>
  </div>
)}
```

### 4. Highlight Search Terms

```tsx
const highlightText = (text: string, highlight: string) => {
  if (!highlight) return text;

  const regex = new RegExp(`(${highlight})`, 'gi');
  return text.split(regex).map((part, i) =>
    regex.test(part) ? <mark key={i}>{part}</mark> : part
  );
};
```

### 5. Prefetch Next Page

```tsx
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const prefetchNextPage = () => {
  queryClient.prefetchQuery({
    queryKey: ['search', 'articles', { query, page: page + 1 }],
    queryFn: () => fetchArticles(query, page + 1),
  });
};
```

---

## 🎉 Success Checklist

- [ ] Search Service is running (`docker compose ps`)
- [ ] Frontend dev server is running (`npm run dev`)
- [ ] Can search for articles
- [ ] Results are displayed
- [ ] Pagination works
- [ ] Autocomplete appears (2+ chars)
- [ ] Filters work (if implemented)
- [ ] No console errors
- [ ] Tests pass (if written)

---

## 🆘 Get Help

1. **Documentation:** Check [README.md](./README.md)
2. **Examples:** See `examples/` directory
3. **Backend API:** http://localhost:8106/docs
4. **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
5. **Template:** [COMPONENT_TEMPLATE.md](./COMPONENT_TEMPLATE.md)

---

**Happy Searching! 🔍**

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Status:** Ready to Use
