# Frontend Test Specifications - NLP Extraction Hooks

**Task P1.7: Frontend Test Specifications (Test-First Approach)**

## Overview

This directory contains test specifications for the NLP Extraction React Query hooks that will be implemented in **Task P1.6**.

**Important:**
- These tests define the expected behavior BEFORE implementation
- Tests are NOT currently runnable (hooks don't exist yet)
- After P1.6 implementation, these tests should pass
- This is a **test-first/TDD approach** - tests guide implementation

---

## Files

| File | Purpose | Status |
|------|---------|--------|
| `useNLPExtraction.test.ts` | Test specifications (minimal version) | ✅ Created |
| `README.md` | This file - Documentation | ✅ Created |

---

## Test Specifications Summary

### Hook 1: `useNLPExtraction(articleId: string)`

**Purpose:** Fetch single article NLP extraction

**Interface:**
```typescript
const {
  data,           // ExtractionResponse | undefined
  isLoading,      // boolean
  error,          // Error | null
  refetch         // () => Promise<void>
} = useNLPExtraction(articleId: string)
```

**Test Coverage:**

**Happy Path (6 tests):**
1. Initially returns loading state
2. Fetches and returns extraction data successfully
3. Returns data matching ExtractionResponse structure
4. Identifies Phase 2B features correctly
5. Handles legacy extractions without Phase 2B
6. Supports refetch() for manual refresh

**Error Cases (4 tests):**
1. Handles invalid UUID format (400 error)
2. Handles article not found (404 error)
3. Handles network errors
4. Handles server errors (500)

**Edge Cases (3 tests):**
1. Triggers new fetch when articleId changes
2. Handles rapid articleId changes (debouncing/cancellation)
3. Cancels pending requests on component unmount

**Caching (2 tests):**
1. Uses cached data for same articleId
2. Respects staleTime configuration

---

### Hook 2: `useNLPExtractionsBatch(articleIds: string[])`

**Purpose:** Fetch multiple articles in one request (1-100 UUIDs)

**Interface:**
```typescript
const {
  data,           // BatchResponse | undefined
  isLoading,      // boolean
  error,          // Error | null
  refetch         // () => Promise<void>
} = useNLPExtractionsBatch(articleIds: string[])
```

**Test Coverage:**

**Happy Path (5 tests):**
1. Initially returns loading state
2. Fetches and returns batch data successfully
3. Returns BatchResponse with correct statistics
4. Handles mixed found/not found articles
5. Returns empty extractions when all not found

**Error Cases (5 tests):**
1. Handles empty articleIds array (400 error)
2. Handles > 100 articleIds (400 error)
3. Handles invalid UUID in array (400 error)
4. Handles network errors
5. Handles server errors (500)

**Edge Cases (3 tests):**
1. Triggers new fetch when articleIds array changes
2. Handles duplicate articleIds correctly
3. Order-independent caching

---

## React Query Integration

**Requirements:**
- Uses React Query v5 (@tanstack/react-query)
- Query keys:
  - Single: `['nlp-extraction', articleId]`
  - Batch: `['nlp-extraction-batch', articleIds]`
- Stale time: 5 minutes (300,000ms)
- Retry logic: 3 retries with exponential backoff
- Error retry: true (for network errors)

**Test Coverage (4 tests):**
1. Uses React Query for state management
2. Proper query keys for cache isolation
3. staleTime configured appropriately
4. Error retry logic implemented

---

## Performance

**Requirements:**
- No unnecessary re-renders
- Efficient batch updates
- No UI flicker during loading states

**Test Coverage (3 tests):**
1. Single extraction doesn't cause unnecessary re-renders
2. Batch extraction efficiently handles updates
3. Loading states don't cause UI flicker

---

## Type Safety

**Requirements:**
- Strong TypeScript types for all parameters
- Properly typed return values
- Phase 2B optional fields handled correctly

**Test Coverage (3 tests):**
1. Enforces correct types for hook parameters
2. Properly typed return values
3. Correctly typed Phase 2B optional fields

---

## API Endpoints

**Base URL:** `http://localhost:8115`

**Endpoints:**
- **Single:** `GET /api/v1/extractions/{article_id}`
  - Returns: `ExtractionResponse`
  - Errors: 400 (invalid UUID), 404 (not found), 500 (server error)

- **Batch:** `POST /api/v1/extractions/batch`
  - Body: `{"article_ids": ["uuid1", "uuid2", ...]}`
  - Limits: 1-100 UUIDs
  - Returns: `BatchResponse`
  - Errors: 400 (validation), 500 (server error)

- **Stats:** `GET /api/v1/extractions/stats`
  - Returns: `StatsResponse`

---

## TypeScript Types

All types are defined in:
```
/home/cytrex/news-microservices/frontend/src/types/nlp-extraction.types.ts
```

**Key types:**
- `ExtractionResponse` - Single extraction with Phase 2B data
- `BatchResponse` - Batch results with statistics
- `Entity` - Named entity (PERSON, ORG, GPE, etc.)
- `EntitySentiment` - Phase 2B entity sentiment analysis
- `EntityCentrality` - Phase 2B importance scoring
- `QuoteSentiment` - Phase 2B quote sentiment analysis
- `ErrorResponse` - API error structure

---

## Mock Data

**Sample Article IDs (Real Data):**
- **With Phase 2B:** `599e6862-f263-49f7-af6c-4edb406c6a8b`
  - 107 entities
  - Complete Phase 2B data
  - Language: English

- **Legacy (No Phase 2B):** Will be defined in full test implementation

**Mock Responses:** See test file for complete fixtures

---

## Implementation Guide (Task P1.6)

When implementing the hooks in Task P1.6, follow this sequence:

### 1. Create Hook Files
```
frontend/src/hooks/
├── useNLPExtraction.ts          # Single extraction hook
└── useNLPExtractionsBatch.ts    # Batch extraction hook
```

### 2. Implement API Client
```typescript
// frontend/src/api/nlp-extraction.api.ts
const API_BASE_URL = 'http://localhost:8115/api/v1/extractions';

export async function fetchExtraction(articleId: string): Promise<ExtractionResponse> {
  const response = await fetch(`${API_BASE_URL}/${articleId}`);
  if (!response.ok) throw new Error('Failed to fetch extraction');
  return response.json();
}

export async function fetchExtractionsBatch(articleIds: string[]): Promise<BatchResponse> {
  const response = await fetch(`${API_BASE_URL}/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ article_ids: articleIds }),
  });
  if (!response.ok) throw new Error('Failed to fetch batch extractions');
  return response.json();
}
```

### 3. Implement Hooks
```typescript
// frontend/src/hooks/useNLPExtraction.ts
import { useQuery } from '@tanstack/react-query';
import { fetchExtraction } from '@/api/nlp-extraction.api';
import type { ExtractionResponse } from '@/types/nlp-extraction.types';

export function useNLPExtraction(articleId: string) {
  return useQuery({
    queryKey: ['nlp-extraction', articleId],
    queryFn: () => fetchExtraction(articleId),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
```

### 4. Run Tests
```bash
# Run all frontend tests
cd /home/cytrex/news-microservices/frontend
npm test

# Run only NLP extraction tests
npm test -- useNLPExtraction

# Watch mode
npm test -- --watch useNLPExtraction
```

### 5. Verify All Tests Pass
- 50+ test cases should all pass
- No TypeScript errors
- Performance requirements met

---

## Test Execution (After P1.6)

**Prerequisites:**
1. API service running: `docker compose up -d nlp-extraction-api`
2. Frontend dependencies: `npm install`
3. Test environment configured

**Run Tests:**
```bash
# All tests
npm test

# Specific file
npm test useNLPExtraction.test.ts

# Watch mode
npm test -- --watch

# With coverage
npm test -- --coverage
```

**Expected Results:**
- ✅ All 50+ tests pass
- ✅ 100% hook coverage
- ✅ No TypeScript errors
- ✅ Performance tests pass (< 100ms for batch with mocked API)

---

## Known Test Data

**Database Statistics (as of 2025-11-07):**
- Total extractions: 19,744
- Phase 2B coverage: 97.22%
- With entity_sentiments: 19,195
- With entity_centrality: 19,195
- With quote_sentiments: 19,195

**Sample Article for Testing:**
- ID: `599e6862-f263-49f7-af6c-4edb406c6a8b`
- Entities: 107
- Language: English
- Phase 2B: Complete

---

## Next Steps

1. ✅ **Task P1.7 (Current):** Test specifications created
2. ⏳ **Task P1.6 (Next):** Implement hooks based on these specs
3. ⏳ **Task P1.4/P1.5:** Run code review and backend tests
4. ⏳ **Verify Phase 1 Success Criteria:** All tests passing

---

## Questions?

**For Task P1.6 Implementation:**
- All specs are defined in `useNLPExtraction.test.ts`
- Types are in `src/types/nlp-extraction.types.ts`
- API endpoints documented above
- Mock data provided in test file

**Contact:** See main project documentation for support

---

**Last Updated:** 2025-11-07
**Status:** Specifications complete, ready for implementation (P1.6)
