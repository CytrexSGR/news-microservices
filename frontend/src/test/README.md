# Frontend Testing Guide

## Overview

This directory contains test infrastructure for the news-microservices frontend.

**Test Framework:** Vitest + React Testing Library + jsdom

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with UI
npm test:ui

# Run with coverage
npm test:coverage
```

## Test Structure

```
frontend/
├── src/
│   ├── test/
│   │   ├── setup.ts                  # Test setup (cleanup, jest-dom matchers)
│   │   ├── mockData/
│   │   │   └── v3Analysis.ts         # Mock V3 analysis data
│   │   └── README.md                 # This file
│   ├── features/
│   │   └── feeds/
│   │       ├── utils/__tests__/
│   │       │   └── validateV3Analysis.test.ts  # Validation logic tests (52 tests)
│   │       └── components/__tests__/
│   │           └── ArticleV3AnalysisCard.test.tsx  # Component tests (27 tests)
│   └── pages/__tests__/
│       └── (future integration tests)
└── vitest.config.ts                  # Vitest configuration
```

## Test Coverage

### Current Status

- **Total Tests:** 79
- **Test Files:** 2
- **Pass Rate:** 100%

### Coverage by Type

1. **Validation Tests** (52 tests)
   - `validateV3Analysis.test.ts`
   - Runtime validation for V3 analysis data structure
   - Covers all validation functions (tier0, tier1, tier1Scores, tier2, full analysis)
   - Tests both valid and invalid data structures

2. **Component Tests** (27 tests)
   - `ArticleV3AnalysisCard.test.tsx`
   - Renders V3 analysis data correctly
   - Tests tier0, tier1, tier2 display
   - Validates nested scores structure (fix for POSTMORTEMS.md Incident #23)
   - Tests compact and full view modes

## Writing Tests

### Test Organization

Follow this structure:

```typescript
describe('ComponentName or Feature', () => {
  describe('Feature Group 1', () => {
    it('should behave in expected way', () => {
      // Arrange
      const props = { ... };

      // Act
      render(<Component {...props} />);

      // Assert
      expect(screen.getByText('Expected')).toBeInTheDocument();
    });
  });
});
```

### Mock Data

Use mock data from `src/test/mockData/`:

```typescript
import {
  mockTier0Kept,
  mockTier1,
  mockV3AnalysisComplete,
} from '@/test/mockData/v3Analysis';
```

### Best Practices

1. **Descriptive Test Names**
   - Use "should" statements
   - Be specific about what is tested
   - Example: `should display foundation scores when tier1 present`

2. **Arrange-Act-Assert Pattern**
   ```typescript
   it('should validate tier1 scores', () => {
     // Arrange
     const scores = { impact_score: 7.5, ... };

     // Act
     const result = () => validateTier1Scores(scores);

     // Assert
     expect(result).not.toThrow();
   });
   ```

3. **Test One Thing**
   - Each test should verify one behavior
   - Split complex scenarios into multiple tests

4. **Use Appropriate Queries**
   - `getByText` - element must exist
   - `queryByText` - element may not exist
   - `findByText` - async, waits for element

5. **Cleanup**
   - Tests auto-cleanup after each test (setup.ts)
   - Use `unmount()` when testing multiple variants in loop

## Testing V3 Analysis Components

**Critical:** V3 analysis has nested data structure.

### Data Structure

```typescript
// Backend transforms flat DB structure to nested frontend structure
tier1: {
  scores: {              // ← IMPORTANT: Nested!
    impact_score: 7.5,
    credibility_score: 8.2,
    urgency_score: 6.1,
  },
  entities: [...],
  relations: [...],
  topics: [...],
}
```

### Common Pitfall

```typescript
// ❌ WRONG (pre-fix bug from Incident #23)
tier1.impact_score

// ✅ CORRECT (nested structure)
tier1.scores.impact_score
```

### Testing Nested Structure

```typescript
it('should access scores via nested structure', () => {
  render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

  // Scores should be displayed (not "N/A")
  expect(screen.getByText(/7\.5/)).toBeInTheDocument();
  expect(screen.getByText(/8\.2/)).toBeInTheDocument();
  expect(screen.getByText(/6\.1/)).toBeInTheDocument();
});
```

## Related Documentation

- **POSTMORTEMS.md Incident #23** - V3 Foundation Scores Display Bug
- **validateV3Analysis.ts** - Runtime validation implementation
- **ArticleDetailPageV3.tsx** - V3 analysis display implementation
- **analysis_loader.py** (backend) - Data transformation logic

## Troubleshooting

### Tests Fail with "Unable to find element"

**Problem:** Component renders text differently than expected

**Solution:** Check actual rendered output:
```typescript
screen.debug(); // Prints DOM to console
```

### Mock Data Structure Mismatch

**Problem:** Tests pass but component shows "N/A" in browser

**Solution:**
1. Check backend response structure
2. Update mock data in `mockData/v3Analysis.ts`
3. Ensure nested `scores` object exists

### Import Errors

**Problem:** `Cannot find module '@/...'`

**Solution:** Check `vitest.config.ts` has path alias:
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

## Performance

- Test suite completes in ~1.4 seconds
- Tests run in parallel by default
- Coverage report generation adds ~2 seconds

## Future Improvements

1. **E2E Tests:** Add Playwright for end-to-end testing
2. **Visual Regression:** Consider adding visual regression tests
3. **Coverage Goals:** Aim for 80%+ coverage on critical paths
4. **Page Tests:** Add integration tests for ArticleDetailPageV3
5. **Hook Tests:** Add tests for custom React hooks

## Last Updated

2025-11-23 - Initial test infrastructure setup
