# Frontend State Management Guide

**Date:** 2025-11-02
**Status:** Active
**Applies to:** Production Frontend (`/home/cytrex/news-microservices/frontend/`)

---

## 🎯 Overview

This guide covers state management patterns in the production frontend, including lessons learned from React Router v7 migration.

---

## 📊 State Management Layers

### 1. React State (Local Component State)

**Use for:** Instant, synchronous updates within a component.

```typescript
const [filters, setFilters] = useState<SearchFilters>({
  source: null,
  sentiment: null,
})

// Instant update, reliable
setFilters({ source: 'BBC News' })
```

**Pros:**
- ✅ Synchronous (no timing issues)
- ✅ Simple, predictable
- ✅ Fast

**Cons:**
- ❌ Lost on page refresh
- ❌ Not shareable via URL

**Use cases:**
- UI state (modals, dropdowns, expanded/collapsed)
- **Filter selections** (see ADR-033)
- Form state (before submission)

---

### 2. URL State (Query Parameters)

**Use for:** Shareable, bookmarkable state.

```typescript
const [searchParams, setSearchParams] = useSearchParams()

// Good for query and pagination
const query = searchParams.get('q') || ''
const page = parseInt(searchParams.get('page') || '1', 10)
```

**Pros:**
- ✅ Shareable URLs
- ✅ Persists on page refresh
- ✅ Browser history (back/forward)

**Cons:**
- ❌ **Async in React Router v7** (timing issues)
- ❌ Complex to manage
- ❌ Limited to primitive types

**Use cases:**
- Search queries
- Pagination
- Sort order
- Tab selection (when shareable URLs needed)

---

### 3. TanStack Query (Server State)

**Use for:** API data, caching, background updates.

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['search', params],
  queryFn: () => searchArticles(params),
  staleTime: 5 * 60 * 1000,
})
```

**Pros:**
- ✅ Automatic caching
- ✅ Background refetching
- ✅ Loading/error states
- ✅ Deduplication

**Cons:**
- ❌ Only for server data
- ❌ Additional dependency

**Use cases:**
- API calls
- Data fetching
- Caching
- Optimistic updates

---

## ⚠️ React Router v7 Breaking Changes

### The Problem

React Router v7 changed `navigate()` to be **asynchronous**, causing timing issues with URL-as-state patterns.

```typescript
// React Router v6 (OLD, worked fine)
navigate({ search: '?filter=value' })
// URL updates immediately ✅
console.log(location.search) // Shows new value

// React Router v7 (NEW, async)
navigate({ search: '?filter=value' })
// URL updates LATER ❌
console.log(location.search) // Still shows OLD value!
```

### The Impact

**Broken Pattern:**
```typescript
// BROKEN in v7
const setFilters = (newFilters) => {
  const next = new URLSearchParams()
  next.set('source', newFilters.source)
  navigate({ search: next.toString() })

  // Component re-renders BEFORE URL updates
  // Reading location.search gives OLD value
  // Filters appear to reset ❌
}
```

**Fixed Pattern:**
```typescript
// FIXED: Use React State instead
const [filters, setFilters] = useState({ source: null })

const updateFilters = (newFilters) => {
  setFilters(prev => ({ ...prev, ...newFilters }))
  // State updates synchronously ✅
  // No timing issues
}
```

### Decision

**ADR-033:** Use React State for filters, not URL state.

**See:** `docs/decisions/ADR-033-search-filter-react-state-architecture.md`

---

## 🏗️ Architecture Patterns

### Pattern 1: Search with Filters (Implemented)

**Use case:** Search page with filters that need instant updates.

**Architecture:**
- ✅ React State for filters (instant, no timing issues)
- ✅ URL for query and pagination (shareable links)
- ✅ TanStack Query for API calls

**Files:**
- `src/features/search-ui/hooks/useSearchParams.ts` - State management
- `src/pages/SearchPage.tsx` - Page component
- `src/features/search-ui/components/search-bar/SearchFilters.tsx` - Filter UI

**Data Flow:**
```
User selects filter
   ↓
setFilters({ source: 'BBC News' })  ← React State (instant)
   ↓
Component re-renders with new filters
   ↓
getSearchParams() builds API params
   ↓
useSearch hook triggers API call (TanStack Query)
   ↓
Backend returns filtered results
   ↓
UI updates
```

---

### Pattern 2: Simple URL State (Use with Caution)

**Use case:** Single values that need shareable URLs and don't change often.

**Example:**
```typescript
// OK for simple, infrequent changes
const [searchParams, setSearchParams] = useSearchParams()
const sortOrder = searchParams.get('sort') || 'desc'

// Change sort order (infrequent)
const changeSortOrder = (newSort: string) => {
  setSearchParams({ sort: newSort })
}
```

**⚠️ Warning:** Still async in v7, but OK if:
- Change is infrequent (sort button click)
- UI doesn't depend on immediate URL read
- User doesn't expect instant visual feedback

---

### Pattern 3: Hybrid State + URL Sync

**Use case:** Want instant updates AND shareable URLs.

**Example:**
```typescript
// State for instant updates
const [filters, setFilters] = useState({ source: null })

// Optional: One-way sync to URL (for sharing)
useEffect(() => {
  const params = new URLSearchParams()
  if (filters.source) params.set('source', filters.source)
  navigate({ search: params.toString() }, { replace: true })
}, [filters]) // Sync after state changes
```

**Note:** Currently commented out in useSearchParams.ts (lines 145-167).

---

## 📋 Decision Matrix

| Feature | React State | URL State (v7) | TanStack Query |
|---------|-------------|----------------|----------------|
| **Instant Updates** | ✅ Yes | ❌ No (async) | N/A |
| **Page Refresh** | ❌ Lost | ✅ Persists | ✅ Cached |
| **Shareable URLs** | ❌ No | ✅ Yes | ❌ No |
| **Complexity** | Low | High | Medium |
| **Best For** | UI state, filters | Query, pagination | API data |

---

## 🚨 Common Pitfalls

### 1. Using URL State for Real-Time Filters

**Problem:**
```typescript
// AVOID in React Router v7
const source = searchParams.get('source')
setSearchParams({ source: newValue })
// source is still OLD value in next render ❌
```

**Solution:**
```typescript
// USE React State instead
const [source, setSource] = useState(null)
setSource(newValue)
// source is NEW value in next render ✅
```

---

### 2. Reading URL Immediately After Writing

**Problem:**
```typescript
navigate({ search: '?filter=value' })
console.log(location.search) // Still OLD value ❌
```

**Solution:**
- Use React State for instant reads
- OR use useEffect to detect URL changes
- OR use Router Loaders (v7 pattern)

---

### 3. Mixing State Types

**Problem:**
```typescript
// Some filters in state, some in URL
const [source, setSource] = useState(null) // State
const sentiment = searchParams.get('sentiment') // URL
// Inconsistent, confusing
```

**Solution:**
```typescript
// ALL filters in same place
const [filters, setFilters] = useState({
  source: null,
  sentiment: null,
})
// Consistent, predictable
```

---

## 🧪 Testing State Management

### Unit Tests

```typescript
import { renderHook, act } from '@testing-library/react'
import { useSearchParams } from './useSearchParams'

test('filters update synchronously', () => {
  const { result } = renderHook(() => useSearchParams())

  act(() => {
    result.current.setFilters({ source: 'BBC News' })
  })

  expect(result.current.filters.source).toBe('BBC News')
})
```

### Integration Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchPage } from './SearchPage'

test('filter selection persists', () => {
  render(<SearchPage />)

  const sourceSelect = screen.getByLabelText('Source')
  fireEvent.change(sourceSelect, { target: { value: 'BBC News' } })

  expect(sourceSelect.value).toBe('BBC News')
})
```

---

## 📚 References

**ADRs:**
- [ADR-033: Search Filter React State Architecture](../decisions/ADR-033-search-filter-react-state-architecture.md)

**Implementation:**
- `src/features/search-ui/hooks/useSearchParams.ts` - Reference implementation
- `reports/FILTER_REWRITE_COMPLETE.md` - Implementation notes

**External:**
- [React Router v7 Migration Guide](https://reactrouter.com/en/main/upgrading/v7)
- [TanStack Query Docs](https://tanstack.com/query/latest)

---

**Last Updated:** 2025-11-02
**Next Review:** After React Router v8 release
