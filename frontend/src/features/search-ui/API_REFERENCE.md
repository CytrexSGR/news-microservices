# Search API - Quick Reference

## Import

```typescript
import {
  searchArticles,
  advancedSearch,
  getAutocomplete,
  getPopularQueries,
  getRelatedSearches,
  getSearchHistory,
  getSavedSearches,
  saveSearch,
  deleteSavedSearch,
} from '@/lib/api/searchPublic'

import type {
  SearchParams,
  SearchResponse,
  SearchResultItem,
  AutocompleteResponse,
  PopularQueriesResponse,
  RelatedSearchesResponse,
} from '@/features/search-ui/types/search.types'
```

## Core Search Functions

### Basic Search
```typescript
const results = await searchArticles({
  query: 'artificial intelligence',
  page: 1,
  page_size: 20,
  sentiment: 'positive',
  date_from: '2024-01-01',
  date_to: '2024-12-31'
})

// Response Type: SearchResponse
// {
//   query: string
//   total: number
//   page: number
//   page_size: number
//   results: SearchResultItem[]
//   facets?: Record<string, unknown> | null
//   execution_time_ms: number
// }
```

### Advanced Search
```typescript
const results = await advancedSearch({
  query: 'machine learning',
  semantic: true,
  title_boost: 2.0,
  include_facets: true
})
```

## Autocomplete & Suggestions

### Autocomplete
```typescript
const suggestions = await getAutocomplete('artifi', 5)
// Returns: { query: 'artifi', suggestions: ['artificial intelligence', ...] }
```

### Popular Queries
```typescript
const popular = await getPopularQueries(10)
// Returns: {
//   popular_queries: [
//     { query: 'AI', hit_count: 150 },
//     { query: 'blockchain', hit_count: 120 }
//   ],
//   total: 10
// }
```

### Related Searches
```typescript
const related = await getRelatedSearches('machine learning', 5)
// Returns: {
//   query: 'machine learning',
//   related: ['deep learning', 'neural networks', 'AI']
// }
```

## Search History & Saved Searches

### Get Search History
```typescript
const history = await getSearchHistory(20)
```

### Get Saved Searches
```typescript
const saved = await getSavedSearches()
```

### Save a Search
```typescript
const savedSearch = await saveSearch(
  {
    query: 'AI news',
    sentiment: 'positive',
    date_from: '2024-01-01'
  },
  'Positive AI News'
)
```

### Delete Saved Search
```typescript
await deleteSavedSearch('search-id-123')
```

## Type Definitions

### SearchParams
```typescript
interface SearchParams {
  query: string                 // Required, 1-500 characters
  page?: number                 // Optional, min: 1, default: 1
  page_size?: number            // Optional, 1-100, default: 20
  source?: string | null        // Filter by source
  sentiment?: string | null     // Filter by sentiment
  date_from?: string | null     // ISO format date
  date_to?: string | null       // ISO format date
}
```

### SearchResultItem
```typescript
interface SearchResultItem {
  article_id: string
  title: string
  content: string
  author?: string | null
  source?: string | null
  url?: string | null
  published_at?: string | null
  sentiment?: string | null
  entities?: string[] | null
  relevance_score: number
  highlight?: Record<string, string[]> | null
}
```

### SearchResponse
```typescript
interface SearchResponse {
  query: string
  total: number
  page: number
  page_size: number
  results: SearchResultItem[]
  facets?: Record<string, unknown> | null
  execution_time_ms: number
}
```

## Authentication

- ✅ **Public Endpoints:** `getAutocomplete`, `getPopularQueries`, `getRelatedSearches`
- 🔒 **Auth Required:** All other endpoints

JWT token is automatically added by `searchApi` interceptor from `/api/axios.ts`

## Error Handling

```typescript
try {
  const results = await searchArticles({ query: 'test' })
} catch (error) {
  if (error.response?.status === 401) {
    // Not authenticated
  } else if (error.response?.status === 422) {
    // Validation error
  } else {
    // Other error
  }
}
```

## Common Patterns

### Search with Pagination
```typescript
const [page, setPage] = useState(1)
const [results, setResults] = useState<SearchResponse | null>(null)

const handleSearch = async (query: string) => {
  const data = await searchArticles({
    query,
    page,
    page_size: 20
  })
  setResults(data)
}

const nextPage = () => setPage(p => p + 1)
const prevPage = () => setPage(p => Math.max(1, p - 1))
```

### Search with Filters
```typescript
const [filters, setFilters] = useState<SearchFilters>({
  sentiment: null,
  source: null,
  date_from: null,
  date_to: null
})

const handleFilteredSearch = async (query: string) => {
  const results = await searchArticles({
    query,
    ...filters
  })
  return results
}
```

### Autocomplete Debounced
```typescript
import { debounce } from 'lodash'

const debouncedAutocomplete = debounce(async (query: string) => {
  if (query.length < 2) return
  const suggestions = await getAutocomplete(query, 5)
  setSuggestions(suggestions.suggestions)
}, 300)
```

## Performance Notes

- **Autocomplete:** No auth, very fast response
- **Popular Queries:** Cached, instant response
- **Related Searches:** No auth, fast response
- **Basic Search:** Auth required, ~50-200ms response time
- **Advanced Search:** Auth required, semantic processing may take longer

## Best Practices

1. **Debounce autocomplete** - Wait for user to stop typing
2. **Cache popular queries** - They don't change frequently
3. **Use pagination** - Don't load all results at once
4. **Show loading states** - Search can take 100-200ms
5. **Handle empty results** - Show helpful message
6. **Validate query length** - Min 1 char, max 500 chars
7. **Use type guards** - Check for null/undefined before rendering

## Example: Complete Search Component

```typescript
import { useState, useEffect } from 'react'
import { searchArticles, getAutocomplete } from '@/lib/api/searchPublic'
import type { SearchResponse } from '@/features/search-ui/types/search.types'

export function SearchComponent() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  // Autocomplete
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
        const { suggestions } = await getAutocomplete(query, 5)
        setSuggestions(suggestions)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Search
  const handleSearch = async () => {
    setLoading(true)
    try {
      const data = await searchArticles({ query, page_size: 20 })
      setResults(data)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      {suggestions.length > 0 && (
        <ul>
          {suggestions.map((s) => (
            <li key={s} onClick={() => setQuery(s)}>
              {s}
            </li>
          ))}
        </ul>
      )}
      {loading && <div>Searching...</div>}
      {results && (
        <div>
          <p>Found {results.total} results in {results.execution_time_ms}ms</p>
          {results.results.map((item) => (
            <article key={item.article_id}>
              <h3>{item.title}</h3>
              <p>{item.content}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
```
