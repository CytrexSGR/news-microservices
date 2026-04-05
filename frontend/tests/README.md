# Frontend Test Specifications

This directory contains test specifications for frontend features using a test-first approach.

## Structure

```
tests/
└── hooks/
    └── useNLPExtraction.test.ts - Test specs for NLP extraction hooks
```

## Test-First Development Process

1. **Specification Phase (P1.7 - Complete)**
   - Define expected behavior through comprehensive tests
   - Create type definitions and mock data
   - Document expected API contract
   - File: `hooks/useNLPExtraction.test.ts`

2. **Implementation Phase (P1.5 & P1.6 - Next)**
   - Implement API client (P1.5)
   - Implement React hooks (P1.6)
   - Uncomment tests to activate
   - Verify all tests pass

## Running Tests

```bash
# Install test dependencies (if not already installed)
npm install -D vitest @testing-library/react @testing-library/react-hooks

# Run all tests
npm test

# Run specific test file
npm test -- useNLPExtraction.test.ts

# Run with coverage
npm test -- --coverage

# Watch mode for development
npm test -- --watch
```

## Test Status

### Phase P1.7 Complete
- [x] Test specifications written
- [x] Type definitions created
- [x] Mock data fixtures provided
- [x] Test utilities documented
- [ ] Tests currently commented out (awaiting implementation)

### Next Steps (P1.5)
- [ ] Implement API client
- [ ] Verify against test specifications

### Following (P1.6)
- [ ] Implement React hooks
- [ ] Uncomment tests
- [ ] Achieve >= 90% coverage

## Coverage Goals

Target coverage for P1.6 implementation:
- Statements: >= 90%
- Branches: >= 85%
- Functions: >= 90%
- Lines: >= 90%

## Files Reference

- **Test Specs:** `hooks/useNLPExtraction.test.ts` (1,200+ lines)
- **Types:** `../src/types/nlpExtraction.ts`
- **Implementation Guide:** `../docs/guides/nlp-extraction-implementation-guide.md`

## Notes

- Tests are written first, then implementation follows (TDD)
- All test cases are documented with expected behavior
- Mock data includes realistic Phase 2B features
- Test utilities ensure consistent setup across test cases
