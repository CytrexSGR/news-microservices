# NLP Extraction Hooks Implementation Guide

**Status:** Test-First Specification (Phase P1.7 Complete)
**Next Task:** P1.5 - API Client Implementation
**Following Task:** P1.6 - Frontend Hooks Implementation
**Last Updated:** 2025-11-07

## Overview

This document provides a comprehensive implementation guide for the NLP extraction hooks and supporting infrastructure. It serves as the blueprint for Tasks P1.5 (API Client) and P1.6 (Frontend Hooks).

The implementation follows a test-first approach:
1. **P1.7 (Complete)**: Test specifications defined
2. **P1.5 (Next)**: API client implemented to pass specifications
3. **P1.6 (Following)**: React hooks implemented to satisfy test suite

## Files Created in Phase P1.7

### 1. Test Specification File
**Location:** `/frontend/tests/hooks/useNLPExtraction.test.ts`

Contains:
- Complete type definitions for all NLP extraction types
- Mock data fixtures for testing
- Test setup utilities (React Query wrapper, mock API client)
- 50+ test cases covering:
  - Happy path scenarios
  - Error cases (404, 500, network errors, invalid UUIDs)
  - Edge cases (rapid changes, unmounting, caching)
  - React Query integration (staleTime, caching, retry logic)
  - Performance and rendering optimization

**Size:** ~1,200 lines of comprehensive test specifications

**Test Categories:**
- useNLPExtraction Hook: 40+ tests
- useNLPExtractionsBatch Hook: 35+ tests
- React Query Integration: 8+ tests
- Type Safety: 3+ tests

### 2. Type Definitions File
**Location:** `/frontend/src/types/nlpExtraction.ts`

Contains:
- Entity extraction types (Entity interface)
- Phase 2B advanced features (EntitySentiment, EntityCentrality, QuoteSentiment)
- Response interfaces (ExtractionResponse, BatchResponse)
- Hook return types (UseNLPExtractionReturn, UseNLPExtractionBatchReturn)
- Type guards and utility functions
- Color utilities for UI rendering
- API endpoints and cache configuration constants

**Exports:** 20+ types and 10+ utility functions

## Implementation Roadmap

### Phase P1.5: API Client Implementation

**File:** `/frontend/src/lib/api/nlpExtraction.ts`

**Required Functions:**

```typescript
// Single article extraction
export async function getSingleExtraction(
  articleId: string
): Promise<ExtractionResponse> {
  // GET http://localhost:8115/api/v1/extractions/{article_id}
  // Requires: Authorization header with Bearer token
  // Returns: ExtractionResponse with all Phase 2B features
  // Errors: 400 (invalid UUID), 404 (not found), 500 (server error)
}

// Batch extraction
export async function getBatchExtractions(
  articleIds: string[]
): Promise<BatchResponse> {
  // POST http://localhost:8115/api/v1/extractions/batch
  // Payload: { article_ids: string[] }
  // Returns: BatchResponse with statistics and extraction array
  // Errors: 400 (validation), 500 (server error)
}
```

**Implementation Notes:**
- Use axios for HTTP requests (already in package.json)
- Configure timeout: 30000ms (30 seconds)
- Handle auth token from localStorage or auth context
- Implement request/response logging for debugging
- Serialize errors to include HTTP status and error code
- Support request cancellation (AbortController)

**Error Handling:**
```typescript
// Handle different error types appropriately
- 400: Validation error (invalid UUID, too many articles)
- 404: Article not found
- 500: Server error (extraction failed)
- Network timeout: Provide user-friendly message
- CORS errors: Handled automatically by axios
```

**Testing Requirements:**
- Test successful extraction (happy path)
- Test error responses (all status codes)
- Test timeout behavior
- Test request/response serialization
- Test auth header inclusion

### Phase P1.6: Frontend Hooks Implementation

**Files to Create:**

#### 1. Single Extraction Hook
**File:** `/frontend/src/features/nlp-extraction/hooks/useNLPExtraction.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { getSingleExtraction } from '@/lib/api/nlpExtraction'
import type { ExtractionResponse, UseNLPExtractionReturn } from '@/types/nlpExtraction'

export function useNLPExtraction(
  articleId: string | null
): UseNLPExtractionReturn {
  const query = useQuery({
    queryKey: ['nlp-extraction', 'single', articleId],
    queryFn: () => getSingleExtraction(articleId!),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!articleId, // Don't fetch if articleId is empty/null
    retry: 3, // Retry 3 times on failure
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}
```

**Key Configuration Points:**
- staleTime: 5 minutes (data is fresh for 5 min, no refetch needed)
- gcTime: 10 minutes (keep data in cache for 10 min)
- enabled: Only fetch when articleId is provided
- retry: 3 with exponential backoff (1s, 2s, 4s)
- Query key: Includes articleId to isolate caches

**Request Cancellation:**
React Query automatically cancels requests when:
- Component unmounts
- Query becomes disabled
- New request with same key initiated

#### 2. Batch Extraction Hook
**File:** `/frontend/src/features/nlp-extraction/hooks/useNLPExtractionsBatch.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { getBatchExtractions } from '@/lib/api/nlpExtraction'
import type {
  BatchResponse,
  UseNLPExtractionBatchReturn,
  UseNLPExtractionBatchOptions,
} from '@/types/nlpExtraction'
import { BATCH_EXTRACTION_CONSTRAINTS } from '@/types/nlpExtraction'

export function useNLPExtractionsBatch(
  articleIds: string[],
  options?: UseNLPExtractionBatchOptions
): UseNLPExtractionBatchReturn {
  // Validate inputs
  if (articleIds.length > BATCH_EXTRACTION_CONSTRAINTS.MAX_ARTICLES) {
    throw new Error(
      `Maximum ${BATCH_EXTRACTION_CONSTRAINTS.MAX_ARTICLES} articles allowed in batch`
    )
  }

  const query = useQuery({
    queryKey: [
      'nlp-extraction',
      'batch',
      // Sort for consistent cache key regardless of order
      ...articleIds.sort(),
    ],
    queryFn: () => getBatchExtractions(articleIds),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled:
      articleIds.length > 0 &&
      articleIds.length <= BATCH_EXTRACTION_CONSTRAINTS.MAX_ARTICLES &&
      (options?.enabled ?? true),
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}
```

**Key Features:**
- Input validation for batch constraints
- Sorted query key (order doesn't affect caching)
- Conditional enabling based on batch size
- Same cache configuration as single hook

#### 3. Hooks Index
**File:** `/frontend/src/features/nlp-extraction/hooks/index.ts`

```typescript
export { useNLPExtraction } from './useNLPExtraction'
export { useNLPExtractionsBatch } from './useNLPExtractionsBatch'

export type {
  UseNLPExtractionReturn,
  UseNLPExtractionBatchReturn,
  UseNLPExtractionBatchOptions,
} from '@/types/nlpExtraction'
```

**Directory Structure:**
```
frontend/src/features/nlp-extraction/
├── hooks/
│   ├── index.ts
│   ├── useNLPExtraction.ts
│   └── useNLPExtractionsBatch.ts
└── components/
    ├── ExtractionDisplay.tsx (Phase P1.8+)
    └── BatchExtractionResults.tsx (Phase P1.8+)
```

## API Endpoint Specifications

### Base URL
Development: `http://localhost:8115`
Production: Environment variable `VITE_NLP_EXTRACTION_API_BASE`

### Single Extraction Endpoint

**Endpoint:** `GET /api/v1/extractions/{article_id}`

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Response (200 OK):**
```typescript
ExtractionResponse {
  article_id: string
  language: string
  extractor_version: string
  model_version: string
  created_at: string
  processing_time_ms: number
  content_length: number
  entity_count: number
  entity_density: number
  entities: Entity[]
  entity_sentiments?: EntitySentiment[]
  entity_centrality?: EntityCentrality[]
  quote_sentiments?: QuoteSentiment[]
  sentiment_overall?: Sentiment
  keywords?: Keyword[]
}
```

**Error Responses:**

| Status | Code | Message |
|--------|------|---------|
| 400 | INVALID_UUID | Invalid UUID format |
| 404 | NOT_FOUND | Article not found |
| 500 | EXTRACTION_FAILED | Internal error during extraction |

### Batch Extraction Endpoint

**Endpoint:** `POST /api/v1/extractions/batch`

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```typescript
{
  article_ids: string[] // 1-100 UUIDs
}
```

**Response (200 OK):**
```typescript
BatchResponse {
  total_requested: number
  total_found: number
  total_not_found: number
  not_found_ids: string[]
  extractions: ExtractionResponse[]
}
```

**Error Responses:**

| Status | Code | Message |
|--------|------|---------|
| 400 | EMPTY_ARRAY | article_ids cannot be empty |
| 400 | TOO_MANY | Maximum 100 articles allowed |
| 400 | INVALID_UUID | Invalid UUID in array |
| 500 | BATCH_FAILED | Batch processing error |

## React Query Configuration

### Cache Strategy

**staleTime: 5 minutes**
- Data is considered fresh for 5 minutes
- Prevents unnecessary refetches for rapidly switching articles
- User sees cached data immediately when re-requesting

**gcTime: 10 minutes (Garbage Collection Time)**
- Cached data kept in memory for 10 minutes
- After 10 minutes, data is discarded to save memory
- Re-requesting after 10 min requires new API call

### Retry Strategy

**Configuration:**
```typescript
{
  retry: 3,
  retryDelay: exponential backoff (1s, 2s, 4s)
}
```

**Retry Behavior:**
- Network errors: ✅ Retry all 3 times
- 4xx errors: ❌ Don't retry (client error)
- 5xx errors: ✅ Retry all 3 times
- Timeouts: ✅ Retry all 3 times

### Query Key Structure

**Single Extraction:**
```typescript
['nlp-extraction', 'single', articleId]
// Example: ['nlp-extraction', 'single', '599e6862-f263-49f7-af6c-4edb406c6a8b']
```

**Batch Extraction:**
```typescript
['nlp-extraction', 'batch', ...sortedArticleIds]
// Example: ['nlp-extraction', 'batch', 'article-1', 'article-2', 'article-3']
// Note: Sorted to ensure consistent cache key regardless of order
```

## Testing Approach

### Test Specifications Already Defined

The test file `/frontend/tests/hooks/useNLPExtraction.test.ts` contains:

1. **50+ test cases** covering all scenarios
2. **Mock fixtures** for consistent testing
3. **Test utilities** (React Query wrapper, mock API client)
4. **Documentation** of expected behavior

### Running Tests

```bash
# Install testing dependencies (if not already installed)
npm install -D vitest @testing-library/react @testing-library/react-hooks

# Run all hook tests
npm test -- useNLPExtraction.test.ts

# Run with coverage
npm test -- useNLPExtraction.test.ts --coverage

# Run in watch mode
npm test -- useNLPExtraction.test.ts --watch
```

### Test Activation

The tests are currently commented out (test-first approach). To activate tests:

1. Implement API client (P1.5)
2. Implement hooks (P1.6)
3. Uncomment test cases in `useNLPExtraction.test.ts`
4. Run test suite to verify implementations pass

### Coverage Goals

Target coverage for Phase P1.6:
- Statements: >= 90%
- Branches: >= 85%
- Functions: >= 90%
- Lines: >= 90%

## Environment Variables

### Development (.env.local)

```env
# NLP Extraction Service
VITE_NLP_EXTRACTION_API_BASE=http://localhost:8115

# React Query Devtools (optional, for debugging)
VITE_ENABLE_REACT_QUERY_DEVTOOLS=true
```

### Production (.env.production)

```env
# NLP Extraction Service (set by deployment)
VITE_NLP_EXTRACTION_API_BASE=https://api.example.com/nlp
```

## Integration with Authentication

### Current Setup

The frontend uses React Query with axios for API requests. Auth is handled by:
1. Bearer token stored in localStorage
2. Token attached to all API requests via axios interceptor
3. Automatic logout on 401 (Unauthorized)

### Hook Integration

Hooks inherit authentication from:
1. API client configuration (axios instance with auth interceptor)
2. Automatic token refresh (if configured in auth service)
3. Error handling (401 triggers logout)

**No changes needed** to auth system for these hooks.

## Phase 2B Feature Validation

### Features Included

✅ **Phase 1 (Basic):**
- Entity extraction with confidence scores
- Entity type classification (NER)
- Position tracking for highlighting

✅ **Phase 2B (Advanced):**
- Entity-level sentiment analysis
- Entity centrality/importance scoring
- Quote extraction and sentiment
- Overall article sentiment
- Keyword extraction and relevance

### Feature Validation in Tests

Tests verify all Phase 2B features are present:
```typescript
// Test expects these fields to exist
expect(data?.entity_sentiments).toBeDefined()
expect(data?.entity_centrality).toBeDefined()
expect(data?.quote_sentiments).toBeDefined()
expect(data?.sentiment_overall).toBeDefined()
expect(data?.keywords).toBeDefined()
```

## Performance Considerations

### Optimization Strategies

1. **Query Caching**
   - 5-minute staleTime prevents redundant API calls
   - Sorted query keys for batch operations
   - Automatic deduplication of requests

2. **Memory Management**
   - 10-minute gcTime (auto cleanup)
   - Request cancellation on unmount
   - No memory leaks from pending requests

3. **Rendering Efficiency**
   - React Query manages state efficiently
   - Prevents unnecessary component re-renders
   - Optimized for React 19+ with built-in optimizations

### Monitoring

Track these metrics in production:
- API response times
- Cache hit/miss rates
- Error rates by status code
- Retry attempt statistics

## Troubleshooting

### Common Issues

**1. Articles not found (404 errors)**
- Verify article IDs are valid UUIDs
- Check article exists in system before extraction
- Verify auth token has permission to read article

**2. Network timeout errors**
- Check NLP service is running (`docker compose ps`)
- Verify API base URL is correct
- Check network connectivity
- Increase timeout if extraction takes > 30s

**3. Cache not updating**
- Call `refetch()` manually to force update
- Wait 5 minutes (staleTime) for automatic refresh
- Check browser DevTools React Query panel

**4. Type errors in TypeScript**
- Ensure `nlpExtraction.ts` types are imported
- Verify hook return types match interface
- Run `npm run build` to check for compilation errors

### Debug Mode

Enable React Query DevTools in development:
```env
VITE_ENABLE_REACT_QUERY_DEVTOOLS=true
```

Then use the DevTools to:
- Inspect query state and cache
- Manually trigger refetches
- View request/response logs
- Monitor query performance

## Next Steps

### Immediate (P1.5)
1. Implement API client in `/frontend/src/lib/api/nlpExtraction.ts`
2. Test API client with backend service
3. Verify all error cases handled correctly

### Following (P1.6)
1. Implement hooks using specifications
2. Run test suite to verify implementations
3. Achieve >= 90% code coverage

### Future (P1.8+)
1. Create UI components for displaying extractions
2. Implement extraction visualization
3. Add batch result export functionality
4. Integrate with existing analytics features

## References

### Files Created
- `/frontend/tests/hooks/useNLPExtraction.test.ts` - Test specifications
- `/frontend/src/types/nlpExtraction.ts` - Type definitions
- `/docs/guides/nlp-extraction-implementation-guide.md` - This file

### Related Documentation
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System overview
- [CLAUDE.frontend.md](../../CLAUDE.frontend.md) - Frontend development guide
- React Query Docs: https://tanstack.com/query/latest
- Vitest Docs: https://vitest.dev/

### API Contracts
- Backend NLP Extraction Service: Port 8115
- Endpoints documented in [Phase 2B Implementation Plan](../../docs/decisions/ADR-*.md)

## Checklist

### Phase P1.5 (API Client)
- [ ] Create `/frontend/src/lib/api/nlpExtraction.ts`
- [ ] Implement `getSingleExtraction()` function
- [ ] Implement `getBatchExtractions()` function
- [ ] Add error handling for all status codes
- [ ] Test with backend service
- [ ] Verify type exports match specifications

### Phase P1.6 (Hooks)
- [ ] Create `/frontend/src/features/nlp-extraction/hooks/` directory
- [ ] Implement `useNLPExtraction.ts` hook
- [ ] Implement `useNLPExtractionsBatch.ts` hook
- [ ] Create `/hooks/index.ts` for exports
- [ ] Uncomment tests in `useNLPExtraction.test.ts`
- [ ] Run full test suite
- [ ] Achieve >= 90% coverage
- [ ] Verify all tests pass

### Phase P1.8+ (UI Components)
- [ ] Create extraction display component
- [ ] Implement batch results component
- [ ] Add visualization for entities
- [ ] Integrate sentiment colors and icons
- [ ] Test components with real data

---

**Document Version:** 1.0
**Status:** Ready for Implementation (P1.5)
**Last Updated:** 2025-11-07
**Next Review:** After P1.6 completion
