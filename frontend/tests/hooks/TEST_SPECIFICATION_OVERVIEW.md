# Test Specification Overview - NLP Extraction Hooks

**Generated:** 2025-11-07
**Phase:** P1.7 (Test-First Specification)
**Status:** Complete and Ready for Implementation

---

## Quick Start

### What This Is
Complete test specifications for two React hooks that will be implemented in Phase P1.6:
1. **useNLPExtraction** - Extract NLP data from a single article
2. **useNLPExtractionsBatch** - Extract NLP data from multiple articles

### What You're Getting
- **1,342 lines** of comprehensive test cases (50+ tests)
- **627 lines** of TypeScript type definitions
- **608 lines** of implementation guidance
- **2,577 total lines** of specifications and types

### Test Activation Timeline

```
Phase P1.7: ✅ Tests written (you are here)
   ↓
Phase P1.5: API client implementation (2-3 days)
   ↓
Phase P1.6: Hook implementation + activate tests (2-3 days)
   ↓
✨ All 50+ tests pass with >= 90% coverage
```

---

## This File Contents

### Test File: useNLPExtraction.test.ts (42 KB, 1,342 lines)

#### Test Organization

```
useNLPExtraction Hook (Single Article)
├── Happy Path Tests (5 tests)
│   ├── Initial loading state
│   ├── Successful extraction fetch
│   ├── Data structure validation
│   ├── Phase 2B features validation
│   └── Refetch functionality
├── Error Cases (6 tests)
│   ├── Invalid UUID handling
│   ├── 404 Not Found handling
│   ├── Network error handling
│   ├── Server error (500) handling
│   └── Timeout error handling
├── Edge Cases (5 tests)
│   ├── Article ID changes
│   ├── Rapid ID changes (debouncing)
│   ├── Component unmount cancellation
│   ├── Empty/null ID handling
│   └── Type safety edge cases
├── React Query Integration (4 tests)
│   ├── Caching behavior
│   ├── Query key isolation
│   ├── staleTime configuration
│   └── Retry logic configuration

useNLPExtractionsBatch Hook (Batch Processing)
├── Happy Path Tests (5 tests)
│   ├── Initial loading state
│   ├── Successful batch fetch
│   ├── Mixed found/not found results
│   ├── Empty arrays when all found
│   └── Data structure validation
├── Error Cases (5 tests)
│   ├── Empty array validation
│   ├── > 100 articles validation
│   ├── Invalid UUID validation
│   ├── Network/server errors
│   └── Timeout handling
├── Edge Cases (5 tests)
│   ├── Array changes
│   ├── Duplicate handling
│   ├── Order independence
│   └── Type safety
├── Batch-Specific (3 tests)
│   ├── Efficient batch updates
│   ├── Statistics in response
│   └── Batch constraints

Additional Test Suites
├── API Client Integration (2 tests)
├── Type Safety & Interfaces (3 tests)
└── Documentation & Notes
```

#### Test Statistics

| Category | Count |
|----------|-------|
| Describe Blocks | 8 |
| Test Cases | 50+ |
| Assertions | 100+ |
| Mock Fixtures | 3 |
| Setup Utilities | 2 |
| Comment Lines | 200+ |

#### Key Features

✅ Tests written BEFORE implementation (Test-Driven Development)
✅ All tests currently commented out (awaiting implementation)
✅ Clear TODO markers showing where implementation is needed
✅ Realistic mock data including Phase 2B features
✅ Complete error scenarios covered
✅ React Query best practices enforced

---

### Types File: nlpExtraction.ts (16 KB, 627 lines)

#### Type Categories

**Core Entity Types:**
```typescript
Entity                 // Single extracted entity
EntityLabel           // NER label enumeration
```

**Extraction Response:**
```typescript
ExtractionResponse    // Complete response for single article
BatchResponse         // Batch processing response
```

**Phase 2B Features:**
```typescript
EntitySentiment       // Sentiment per entity
EntityCentrality      // Importance/centrality scores
QuoteSentiment        // Quote extraction & sentiment
Sentiment             // Article-level sentiment
Keyword               // Extracted keywords & relevance
```

**Hook Types:**
```typescript
UseNLPExtractionReturn        // Single hook return type
UseNLPExtractionBatchReturn   // Batch hook return type
UseNLPExtractionBatchOptions  // Hook configuration options
```

**Utilities:**
```typescript
Type Guards (3)               // Runtime type validation
Color Helpers (2)             // UI rendering utilities
Constants (5)                 // API config, cache settings
Description Maps (2)          // Human-readable labels
```

#### Total Exports: 20+ types

---

### Implementation Guide: nlp-extraction-implementation-guide.md (17 KB, 608 lines)

#### Sections Included

1. **Overview** - Test-first approach explanation
2. **Files Created** - Summary of P1.7 deliverables
3. **Implementation Roadmap** - Detailed P1.5 & P1.6 tasks
4. **API Specifications** - Endpoint documentation
5. **React Query Config** - Cache and retry strategy
6. **Testing Approach** - Running tests and coverage goals
7. **Environment Setup** - Required environment variables
8. **Auth Integration** - How auth works with hooks
9. **Performance** - Optimization strategies
10. **Troubleshooting** - Common issues and solutions
11. **Next Steps** - Immediate action items
12. **Checklist** - Implementation verification

#### Code Examples Included

- Complete `useNLPExtraction` implementation (20 lines)
- Complete `useNLPExtractionsBatch` implementation (35 lines)
- Query key structure examples
- Error handling patterns
- Test running commands

---

## How to Use These Specifications

### For Phase P1.5 (API Client Implementation)

1. **Read:** Implementation guide sections 3-4
2. **Review:** Type definitions for data structures
3. **Implement:** API client functions
4. **Verify:** Functions match API specifications
5. **Test:** With backend NLP service

### For Phase P1.6 (Hook Implementation)

1. **Read:** Implementation guide sections 3, 4, 5
2. **Implement:** Two hooks using specifications
3. **Test:** Uncomment tests in test file
4. **Verify:** All 50+ tests pass
5. **Measure:** Achieve >= 90% code coverage

### For Component Development (Phase P1.8+)

1. **Import:** Types from `@/types/nlpExtraction`
2. **Use:** Hooks in your components
3. **Reference:** Type definitions for data structures
4. **Style:** Use color helper functions for UI

---

## Test Activation Process

### Step 1: After API Client (P1.5)
- API client functions are working
- Mock client can be replaced with real client
- Tests can use actual API responses

### Step 2: After Hook Implementation (P1.6)
```bash
# Open useNLPExtraction.test.ts
# Find: // TODO: Implement hook (appears ~30 times)
# Replace: with actual test code (uncommented)

# Search for: // const { result } = renderHook
# Replace with: const { result } = renderHook
```

### Step 3: Run Tests
```bash
npm test -- useNLPExtraction.test.ts
```

### Step 4: Coverage Check
```bash
npm test -- useNLPExtraction.test.ts --coverage
# Expected: >= 90% all categories
```

---

## File Locations

### Created in P1.7

```
frontend/
├── tests/
│   ├── README.md
│   └── hooks/
│       ├── TEST_SPECIFICATION_OVERVIEW.md  ← You are here
│       └── useNLPExtraction.test.ts       ← Main test file
└── src/
    └── types/
        └── nlpExtraction.ts               ← Type definitions

docs/
└── guides/
    └── nlp-extraction-implementation-guide.md  ← Implementation guide
```

### Will Be Created in P1.5

```
frontend/src/lib/api/
└── nlpExtraction.ts                       ← API client
```

### Will Be Created in P1.6

```
frontend/src/features/nlp-extraction/
├── hooks/
│   ├── index.ts
│   ├── useNLPExtraction.ts               ← Single extraction hook
│   └── useNLPExtractionsBatch.ts         ← Batch extraction hook
└── components/
    └── (future UI components)
```

---

## Key Test Specifications

### useNLPExtraction Hook

**Expected Behavior:**
```typescript
// When called with valid article ID
const { data, isLoading, error, refetch } = useNLPExtraction('article-uuid-123')

// Initially:
// data = undefined, isLoading = true, error = null

// After API call succeeds:
// data = ExtractionResponse, isLoading = false, error = null

// If API returns 404:
// data = undefined, isLoading = false, error = Error('Article not found')

// Call refetch() manually to trigger new fetch
await refetch()
// data is refreshed with latest extraction
```

### useNLPExtractionsBatch Hook

**Expected Behavior:**
```typescript
// When called with array of article IDs
const { data, isLoading, error, refetch } = useNLPExtractionsBatch([
  'article-1', 'article-2', 'article-3'
])

// Response includes statistics:
// {
//   total_requested: 3,
//   total_found: 2,
//   total_not_found: 1,
//   not_found_ids: ['article-3'],
//   extractions: [ExtractionResponse, ExtractionResponse]
// }
```

---

## Mock Data Example

### Single Extraction Mock

```typescript
{
  article_id: '599e6862-f263-49f7-af6c-4edb406c6a8b',
  language: 'en',
  entity_count: 107,
  entities: [
    { id: 'ent_001', text: 'OpenAI', label: 'ORG', ... },
    { id: 'ent_002', text: 'Sam Altman', label: 'PERSON', ... }
  ],
  entity_sentiments: [
    { entity_id: 'ent_001', sentiment_label: 'positive', sentiment_score: 0.82 }
  ],
  entity_centrality: [
    { entity_id: 'ent_001', centrality_score: 0.94, mention_count: 12 }
  ],
  quote_sentiments: [...],
  sentiment_overall: { label: 'positive', score: 0.71 },
  keywords: [...]
}
```

---

## React Query Configuration

The hooks are configured with:

```typescript
{
  staleTime: 5 * 60 * 1000,    // Data fresh for 5 minutes
  gcTime: 10 * 60 * 1000,      // Cache kept for 10 minutes
  retry: 3,                     // Retry failed requests 3 times
  retryDelay: exponential,      // Backoff: 1s, 2s, 4s
  enabled: !!articleId          // Only fetch when ID provided
}
```

**What This Means:**
- First request for an article: API call (data cached)
- Same request within 5 min: Returns cached data instantly
- Same request after 5 min: API call (data is stale)
- After 10 min with no requests: Cache discarded
- Failed requests: Automatic retry with backoff

---

## Error Handling

Tests verify proper handling of:

| Error Type | HTTP Status | User Message |
|-----------|------------|--------------|
| Invalid UUID | 400 | "Invalid UUID format" |
| Not Found | 404 | "Article not found" |
| Network Error | 0 | "Network request failed" |
| Server Error | 500 | "Internal server error" |
| Timeout | 0 | "Request timeout" |
| Too Many Articles | 400 | "Maximum 100 articles" |

---

## Coverage Goals (Phase P1.6)

When hooks are implemented, tests will verify:

```
✅ Statement Coverage: >= 90%
✅ Branch Coverage: >= 85%
✅ Function Coverage: >= 90%
✅ Line Coverage: >= 90%
```

This ensures:
- All code paths executed in tests
- Error branches tested
- Edge cases covered
- High code quality

---

## Next Action Items

### Immediate (Before P1.5)
- [ ] Review this specification document
- [ ] Review type definitions (`nlpExtraction.ts`)
- [ ] Read implementation guide (sections 1-3)

### During P1.5
- [ ] Create API client file
- [ ] Implement API functions
- [ ] Verify against specifications
- [ ] Test with backend service

### During P1.6
- [ ] Create hooks directory structure
- [ ] Implement both hooks
- [ ] Uncomment tests in test file
- [ ] Run full test suite
- [ ] Verify all tests pass

---

## References

### In This Repository
- **Test File:** `frontend/tests/hooks/useNLPExtraction.test.ts`
- **Types:** `frontend/src/types/nlpExtraction.ts`
- **Guide:** `docs/guides/nlp-extraction-implementation-guide.md`
- **Completion Summary:** `TASK_P1.7_COMPLETION_SUMMARY.md`

### External Documentation
- React Query: https://tanstack.com/query/latest
- Vitest Testing: https://vitest.dev/
- React Testing Library: https://testing-library.com/react

### System Documentation
- Architecture: `/ARCHITECTURE.md`
- Frontend Guide: `/CLAUDE.frontend.md`

---

## Quick Reference Checklist

### Phase P1.5 (API Client) Tasks
- [ ] Create `/frontend/src/lib/api/nlpExtraction.ts`
- [ ] Implement `getSingleExtraction()` function
- [ ] Implement `getBatchExtractions()` function
- [ ] Test API functions with backend
- [ ] Verify error handling for all cases
- [ ] Check type exports match specifications

### Phase P1.6 (Hooks) Tasks
- [ ] Create `/frontend/src/features/nlp-extraction/hooks/` directory
- [ ] Implement `useNLPExtraction.ts` hook
- [ ] Implement `useNLPExtractionsBatch.ts` hook
- [ ] Create `index.ts` for exports
- [ ] Uncomment tests in `useNLPExtraction.test.ts`
- [ ] Run `npm test -- useNLPExtraction.test.ts`
- [ ] Verify all 50+ tests pass
- [ ] Achieve >= 90% code coverage

---

## Support

### Questions About Tests?
Refer to specific test case comments in `useNLPExtraction.test.ts`

### Questions About Types?
Refer to JSDoc comments in `nlpExtraction.ts`

### Questions About Implementation?
Refer to `nlp-extraction-implementation-guide.md`

---

**Document:** Test Specification Overview
**Status:** Complete and Ready for Use
**Last Updated:** 2025-11-07
**Next Phase:** P1.5 - API Client Implementation
