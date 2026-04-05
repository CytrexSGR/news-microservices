# Search UI Architecture

**Visual architecture documentation for the public search interface.**

---

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Search UI Feature                        │ │
│  │  /features/search-ui/                                      │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │ Components   │  │    Hooks     │  │    Types     │   │ │
│  │  │              │  │              │  │              │   │ │
│  │  │ - SearchBar  │  │ - useSearch  │  │ - Request    │   │ │
│  │  │ - Results    │  │ - Suggestions│  │ - Response   │   │ │
│  │  │ - Facets     │  │ - Popular    │  │ - Filters    │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  │         │                  │                  │           │ │
│  │         └──────────────────┴──────────────────┘           │ │
│  │                            │                               │ │
│  │                    ┌───────▼────────┐                     │ │
│  │                    │  React Query   │                     │ │
│  │                    │  Cache Layer   │                     │ │
│  │                    └───────┬────────┘                     │ │
│  │                            │                               │ │
│  │                    ┌───────▼────────┐                     │ │
│  │                    │   Axios API    │                     │ │
│  │                    │    Client      │                     │ │
│  │                    └───────┬────────┘                     │ │
│  └────────────────────────────┼────────────────────────────┘ │
└─────────────────────────────────┼────────────────────────────┘
                                  │ HTTP/HTTPS
                        ┌─────────▼──────────┐
                        │   CORS Middleware  │
                        └─────────┬──────────┘
┌─────────────────────────────────┼────────────────────────────┐
│                         BACKEND SERVICES                       │
│                                                                │
│  ┌─────────────────────────────▼────────────────────────────┐ │
│  │           Search Service (Port 8106)                     │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │  Public API Endpoints                              │ │ │
│  │  │                                                     │ │ │
│  │  │  GET  /api/v1/search          - Basic search       │ │ │
│  │  │  POST /api/v1/search/advanced - Advanced search    │ │ │
│  │  │  GET  /api/v1/search/suggest  - Autocomplete       │ │ │
│  │  │  GET  /api/v1/search/popular  - Popular queries    │ │ │
│  │  │  GET  /api/v1/search/related  - Related searches   │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  │         │           │           │          │             │ │
│  │         ▼           ▼           ▼          ▼             │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐      │ │
│  │  │ Search  │ │Suggest  │ │ Stats   │ │  Redis   │      │ │
│  │  │ Service │ │ Service │ │ Service │ │  Cache   │      │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘      │ │
│  │       │           │           │           │              │ │
│  │       └───────────┴───────────┴───────────┘              │ │
│  │                       │                                   │ │
│  │              ┌────────▼─────────┐                        │ │
│  │              │  PostgreSQL DB   │                        │ │
│  │              │                  │                        │ │
│  │              │  - articles      │                        │ │
│  │              │  - search_index  │                        │ │
│  │              │  - search_stats  │                        │ │
│  │              └──────────────────┘                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Component Architecture

### Component Hierarchy

```
SearchPage (Page Component)
│
├─── SearchInput (components/search-bar/)
│    ├─── <Input /> (shadcn/ui)
│    ├─── SearchIcon (lucide-react)
│    └─── SearchSuggestions
│         └─── useSuggestions() hook
│
├─── SearchFilters (components/search-bar/)
│    ├─── SourceFacet (components/facets/)
│    ├─── SentimentFacet (components/facets/)
│    └─── DateRangeFacet (components/facets/)
│
├─── ResultStats (components/results/)
│    └─── Display: "Found X results in Y ms"
│
├─── ResultList (components/results/)
│    └─── ResultCard[] (map over results)
│         ├─── <Card /> (shadcn/ui)
│         ├─── <Badge /> (shadcn/ui)
│         └─── Article metadata
│
└─── ResultPagination (components/results/)
     └─── <Pagination /> (shadcn/ui)
```

### Data Flow

```
User Input
    │
    ▼
SearchInput Component
    │
    ▼ (debounced)
useSuggestions Hook ──────► GET /api/v1/search/suggest
    │                              │
    │                              ▼
    │                       Redis Cache Check
    │                              │
    │                              ▼
    └──────────────────► SearchSuggestions Dropdown


User Submits Search
    │
    ▼
SearchPage Component
    │
    ▼
useArticleSearch Hook ─────► GET /api/v1/search?query=...
    │                              │
    │                              ▼
    │                       Redis Cache Check
    │                              │
    │                              ▼
    │                       PostgreSQL Full-Text Search
    │                              │
    │                              ▼
    └──────────────────► SearchResponse
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
            ResultStats      ResultList      ResultPagination
```

---

## 🔄 State Management

### React Query Cache Architecture

```
QueryClient
    │
    ├─── ['search', 'articles', request]
    │    ├─── staleTime: 30s
    │    ├─── gcTime: 5min
    │    └─── data: SearchResponse
    │
    ├─── ['search', 'suggestions', query]
    │    ├─── staleTime: 60s
    │    ├─── gcTime: 5min
    │    └─── data: string[]
    │
    ├─── ['search', 'popular']
    │    ├─── staleTime: 300s (5min)
    │    ├─── gcTime: 15min
    │    └─── data: PopularQuery[]
    │
    └─── ['search', 'related', query]
         ├─── staleTime: 60s
         ├─── gcTime: 5min
         └─── data: string[]
```

### Local State Flow

```
SearchPage Component
    │
    ├─── query: string (search query)
    │    └─── Updated by SearchInput
    │
    ├─── page: number (current page)
    │    └─── Updated by ResultPagination
    │
    ├─── filters: SearchFilters
    │    └─── Updated by SearchFilters component
    │         ├─── source: string[]
    │         ├─── sentiment: string[]
    │         └─── dateRange: { from, to }
    │
    └─── All state flows into useArticleSearch hook
         which creates queryKey: ['search', 'articles', { query, page, filters }]
```

---

## 🎨 UI Component Structure

### SearchInput Component

```
┌─────────────────────────────────────────────────────────┐
│  🔍  [Search articles...]                    [Loading]  │ ← Input
└─────────────────────────────────────────────────────────┘
      │
      └── Autocomplete Dropdown (when query.length >= 2)
          ┌───────────────────────────────────────────────┐
          │  tesla stock                                  │
          │  tesla earnings                               │
          │  tesla news                                   │
          │  tesla market cap                             │
          │  tesla competition                            │
          └───────────────────────────────────────────────┘
```

### SearchFilters Component

```
┌─────────────────────────────────────────────────────────┐
│  Filters                                      [Clear All]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Source                                                  │
│  ☑ Reuters (234)                                        │
│  ☐ Bloomberg (189)                                      │
│  ☐ CNN (156)                                            │
│  ☐ BBC (142)                                            │
│                                                          │
│  Sentiment                                               │
│  ☑ Positive (423)                                       │
│  ☐ Neutral (389)                                        │
│  ☐ Negative (145)                                       │
│                                                          │
│  Date Range                                              │
│  [2025-01-01] to [2025-11-02]                          │
│                                                          │
│  [Apply Filters]                                        │
└─────────────────────────────────────────────────────────┘
```

### ResultCard Component

```
┌─────────────────────────────────────────────────────────┐
│  Tesla Reports Record Q4 Earnings, Stock Surges         │ ← Title
│                                                          │
│  Reuters • 2 hours ago • Positive                       │ ← Metadata
│                                                          │
│  Tesla Inc. announced record-breaking fourth quarter    │
│  earnings, exceeding analyst expectations and sending   │ ← Summary
│  its stock price surging in after-hours trading...      │
│                                                          │
│  [Read More →]                                          │ ← Action
└─────────────────────────────────────────────────────────┘
```

### ResultList Component

```
┌─────────────────────────────────────────────────────────┐
│  Found 1,234 results in 143ms                           │ ← ResultStats
├─────────────────────────────────────────────────────────┤
│  [ResultCard #1]                                        │
│  [ResultCard #2]                                        │
│  [ResultCard #3]                                        │
│  ...                                                     │
│  [ResultCard #20]                                       │
├─────────────────────────────────────────────────────────┤
│  [< Previous] [1] [2] [3] ... [62] [Next >]            │ ← Pagination
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 API Integration Flow

### Search Request Flow

```
1. User Input
   └─► SearchInput component
       └─► Debounce 300ms
           └─► useArticleSearch hook triggered

2. React Query Check
   └─► Cache hit? (within staleTime)
       ├─► YES: Return cached data immediately
       └─► NO: Proceed to API call

3. API Request
   └─► Axios interceptor adds auth token (optional)
       └─► GET /api/v1/search?query=tesla&page=1&page_size=20
           └─► CORS preflight (if needed)

4. Backend Processing
   ├─► Search Service receives request
   ├─► Check Redis cache (key: "search:tesla:1:20")
   │   ├─► HIT: Return cached results (< 50ms)
   │   └─► MISS: Query PostgreSQL
   ├─► PostgreSQL full-text search
   │   └─► ts_rank(search_vector, to_tsquery('tesla'))
   ├─► Format results
   ├─► Store in Redis (TTL: 5min)
   └─► Return SearchResponse

5. Frontend Updates
   ├─► React Query updates cache
   ├─► Components re-render with new data
   │   ├─► ResultStats shows count & time
   │   ├─► ResultList renders ResultCards
   │   └─► ResultPagination shows page controls
   └─► Background refetch (if stale)
```

### Autocomplete Request Flow

```
1. User Types (2+ characters)
   └─► SearchInput onChange
       └─► Debounce 200ms
           └─► useSuggestions hook triggered

2. API Request
   └─► GET /api/v1/search/suggest?query=te&limit=10

3. Backend Processing
   ├─► Check Redis cache
   │   ├─► HIT: Return suggestions (< 10ms)
   │   └─► MISS: Query database
   ├─► PostgreSQL ILIKE query
   │   └─► Find matching popular queries & article titles
   ├─► Store in Redis (TTL: 10min)
   └─► Return suggestions

4. Frontend Updates
   └─► SearchSuggestions dropdown appears
       └─► User can click to select suggestion
```

---

## 📦 Module Dependencies

### External Dependencies

```
React Ecosystem
├── react (UI framework)
├── react-dom (DOM rendering)
├── react-router-dom (routing)
└── @tanstack/react-query (server state)

UI Components
├── @radix-ui/* (headless components)
├── lucide-react (icons)
└── tailwindcss (styling)

Utilities
├── axios (HTTP client)
├── date-fns (date formatting)
└── clsx (className utilities)
```

### Internal Dependencies

```
@/features/search-ui/
├── components/
│   └── uses: @/components/ui/* (shadcn/ui)
│
├── hooks/
│   ├── uses: @/api/axios (API client)
│   └── uses: @tanstack/react-query
│
├── types/
│   └── standalone (no dependencies)
│
└── utils/
    └── uses: types/ (type imports only)
```

---

## 🚦 Performance Optimizations

### 1. Request Debouncing

```
User Types: "t" → "te" → "tes" → "tesl" → "tesla"
            │     │      │       │        │
            ▼     ▼      ▼       ▼        ▼
Debounced:  ─────────────────────────────► "tesla"
                        300ms delay

Only 1 API call made instead of 5!
```

### 2. React Query Caching

```
Timeline:
0s    → User searches "tesla"
        └─► API call, cache stored (staleTime: 30s)

5s    → User searches "apple"
        └─► API call, cache stored

10s   → User searches "tesla" again
        └─► Cache HIT! No API call (data still fresh)

35s   → User searches "tesla" again
        └─► Background refetch (data stale but shown immediately)
```

### 3. Component Memoization

```tsx
// Prevent re-renders when props haven't changed
export const ResultCard = React.memo(({ article, highlight }: Props) => {
  // Component renders only when article or highlight changes
});
```

### 4. Virtual Scrolling (Future Enhancement)

```
┌────────────────┐
│  [Item 1]      │ ← Rendered
│  [Item 2]      │ ← Rendered
│  [Item 3]      │ ← Rendered
├────────────────┤
│  ...           │ ← Virtual (not in DOM)
│  ...           │ ← Virtual (not in DOM)
│  ...           │ ← Virtual (not in DOM)
└────────────────┘

Only 10-20 items rendered at once,
even with 10,000 total results!
```

---

## 🔒 Authentication Flow

### Optional Authentication

```
┌─────────────────────────────────────────────────────┐
│  User visits /search                                 │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  Auth Token       │
        │  in LocalStorage? │
        └─────────┬─────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
    NO TOKEN             HAS TOKEN
       │                     │
       ▼                     ▼
┌──────────────┐    ┌────────────────┐
│  Public      │    │  Authenticated │
│  Search      │    │  Search        │
│              │    │                │
│ • Basic      │    │ • All features │
│   features   │    │ • Save search  │
│ • No history │    │ • History      │
└──────────────┘    │ • Preferences  │
                    └────────────────┘
```

### API Request Headers

```typescript
// Axios interceptor (automatic)
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Backend uses get_optional_user
// → Returns user data if token valid
// → Returns None if no token or invalid
// → Search works in both cases!
```

---

## 🎯 Search Query Processing

### Backend Query Pipeline

```
User Query: "tesla stock price"
    │
    ├─► Tokenization
    │   └─► ["tesla", "stock", "price"]
    │
    ├─► Stop Word Removal (optional)
    │   └─► ["tesla", "stock", "price"] (no common words removed)
    │
    ├─► Stemming (PostgreSQL ts_vector)
    │   └─► ["tesla", "stock", "price"] → ts_query
    │
    ├─► Full-Text Search
    │   └─► SELECT * FROM articles
    │       WHERE search_vector @@ to_tsquery('tesla & stock & price')
    │
    ├─► Ranking
    │   └─► ORDER BY ts_rank(search_vector, query) DESC
    │
    ├─► Filtering (if filters applied)
    │   ├─► source IN ('reuters', 'bloomberg')
    │   ├─► sentiment = 'positive'
    │   └─► published_at BETWEEN date_from AND date_to
    │
    └─► Pagination
        └─► LIMIT 20 OFFSET (page - 1) * 20
```

### Advanced Search Features

```
1. Phrase Search
   "exact phrase" → to_tsquery('"exact" <-> "phrase"')

2. Boolean Operators
   tesla AND stock → to_tsquery('tesla & stock')
   tesla OR spacex → to_tsquery('tesla | spacex')

3. Exclusion
   tesla NOT musk → to_tsquery('tesla & !musk')

4. Fuzzy Search (Future)
   tsla → tesla (using trigram similarity)
```

---

## 📊 Error Handling Flow

```
API Request
    │
    ├─► Network Error
    │   ├─► Retry 3x (exponential backoff)
    │   │   └─► Still fails?
    │   │       └─► Show error message
    │   │           └─► "Unable to reach server. Check connection."
    │   │
    │   └─► Success after retry
    │       └─► Continue normally
    │
    ├─► 400 Bad Request
    │   └─► Show validation error
    │       └─► "Invalid search query. Try different terms."
    │
    ├─► 401 Unauthorized (optional auth)
    │   └─► Continue with public search
    │       └─► Limited features
    │
    ├─► 404 Not Found
    │   └─► Empty results
    │       └─► "No articles found. Try different terms."
    │
    ├─► 429 Too Many Requests
    │   └─► Show rate limit message
    │       └─► "Too many searches. Try again in 1 minute."
    │
    └─► 500 Server Error
        └─► Show generic error
            └─► "Something went wrong. Please try again."
```

---

## 📈 Performance Metrics

### Target Benchmarks

```
┌─────────────────────────────────────────────────────┐
│  Metric                    Target      Current      │
├─────────────────────────────────────────────────────┤
│  Page Load (FCP)           < 1.5s      TBD          │
│  Time to Interactive       < 2.0s      TBD          │
│  Search Response (cached)  < 200ms     TBD          │
│  Search Response (fresh)   < 500ms     TBD          │
│  Autocomplete Response     < 100ms     TBD          │
│  Result Render (20 items)  < 50ms      TBD          │
│  Bundle Size               < 200KB     TBD          │
└─────────────────────────────────────────────────────┘
```

### Monitoring Points

```
1. Frontend Metrics
   ├─► React Query cache hit rate
   ├─► Component render time
   ├─► Bundle size (code splitting)
   └─► Core Web Vitals (LCP, FID, CLS)

2. API Metrics
   ├─► Request count (per endpoint)
   ├─► Response time (p50, p95, p99)
   ├─► Error rate (4xx, 5xx)
   └─► Cache hit rate (Redis)

3. Backend Metrics
   ├─► PostgreSQL query time
   ├─► Index efficiency
   ├─► Memory usage
   └─► Connection pool status
```

---

## 🔗 Integration Points

### Frontend Integration

```
App.tsx
    │
    └─► Route: /search
        └─► SearchPage component
            └─► Uses SearchInput, ResultList, etc.
                └─► Uses hooks from @/features/search-ui/hooks
                    └─► Connects to Search Service API
```

### Backend Integration

```
Search Service (8106)
    │
    ├─► PostgreSQL Database
    │   ├─► articles table (main data)
    │   ├─► search_stats table (analytics)
    │   └─► Full-text indexes (ts_vector)
    │
    ├─► Redis Cache
    │   ├─► Search results (TTL: 5min)
    │   ├─► Suggestions (TTL: 10min)
    │   └─► Popular queries (TTL: 1hour)
    │
    └─► RabbitMQ (Future)
        └─► Search event publishing
            └─► Analytics tracking
```

---

## 🚀 Future Architecture

### Phase 2: Advanced Features

```
┌─────────────────────────────────────────────────────┐
│  Advanced Search Enhancements                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Elasticsearch Integration (replace PostgreSQL)  │
│     ├─► Better full-text search                     │
│     ├─► Faceted search                              │
│     └─► Aggregations                                │
│                                                      │
│  2. Search History (authenticated users)            │
│     ├─► Save recent searches                        │
│     └─► Search suggestions based on history         │
│                                                      │
│  3. Saved Searches                                   │
│     ├─► Save custom queries                         │
│     ├─► Email alerts                                │
│     └─► RSS feeds                                   │
│                                                      │
│  4. Advanced Filters                                 │
│     ├─► Entity extraction (companies, people)       │
│     ├─► Topic clustering                            │
│     └─► Related articles                            │
│                                                      │
│  5. Natural Language Queries                         │
│     └─► "Show me positive Tesla news from last week"│
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📖 Related Documentation

- [README.md](./README.md) - Feature overview and usage
- [COMPONENT_TEMPLATE.md](./COMPONENT_TEMPLATE.md) - Component creation guide
- [Search Service Docs](/home/cytrex/news-microservices/docs/services/search-service.md)
- [Admin Search Feature](/home/cytrex/news-microservices/frontend/src/features/search/README.md)

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Status:** 🚧 In Development
**Maintained By:** Frontend Team
