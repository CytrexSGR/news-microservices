# Component Template - Search UI Feature

This template provides a standardized structure for creating new components in the search-ui feature.

---

## 📋 Component Template

### File: `components/{category}/{ComponentName}.tsx`

```tsx
/**
 * ComponentName - Brief one-line description
 *
 * Detailed description of what this component does, its purpose,
 * and when to use it.
 *
 * @component
 * @example
 * <ComponentName
 *   prop1="value"
 *   prop2={42}
 *   onAction={(data) => console.log(data)}
 * />
 */

import { useState } from 'react';
import type { ComponentType } from './types'; // Import types

// UI components (shadcn/ui)
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

// Icons (lucide-react)
import { Search, Filter } from 'lucide-react';

// Hooks
import { useCustomHook } from '@/features/search-ui/hooks';

/**
 * Props for ComponentName component
 */
export interface ComponentNameProps {
  /**
   * Description of prop1
   * @example "example value"
   */
  prop1: string;

  /**
   * Description of prop2
   * @default 10
   */
  prop2?: number;

  /**
   * Callback when action occurs
   * @param data - Data passed to callback
   */
  onAction?: (data: ComponentType) => void;

  /**
   * Additional CSS classes
   */
  className?: string;
}

/**
 * ComponentName component implementation
 */
export function ComponentName({
  prop1,
  prop2 = 10,
  onAction,
  className,
}: ComponentNameProps) {
  // State
  const [localState, setLocalState] = useState<string>('');

  // Hooks
  const { data, isLoading, error } = useCustomHook(prop1);

  // Handlers
  const handleClick = () => {
    if (onAction && data) {
      onAction(data);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={className}>
        <p>Loading...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={className}>
        <p className="text-destructive">Error: {error.message}</p>
      </div>
    );
  }

  // Main render
  return (
    <Card className={className}>
      <div className="space-y-4">
        {/* Component content */}
        <h3 className="text-lg font-semibold">{prop1}</h3>

        {data && (
          <div>
            {/* Render data */}
            <p>{data.someProperty}</p>
          </div>
        )}

        {/* Actions */}
        <Button onClick={handleClick}>
          <Search className="mr-2 h-4 w-4" />
          Action
        </Button>
      </div>
    </Card>
  );
}
```

---

## 🎨 Component Categories

### 1. Search Bar Components (`components/search-bar/`)

Components related to the search input and query building.

**Examples:**
- `SearchInput.tsx` - Main search input field
- `SearchFilters.tsx` - Advanced filter panel
- `SearchSuggestions.tsx` - Autocomplete dropdown
- `SearchHistory.tsx` - Recent searches

**Common Props:**
- `onSearch: (query: string) => void` - Search callback
- `placeholder?: string` - Input placeholder
- `defaultValue?: string` - Initial value

### 2. Result Components (`components/results/`)

Components for displaying search results.

**Examples:**
- `ResultList.tsx` - List container
- `ResultCard.tsx` - Individual result
- `ResultPagination.tsx` - Pagination controls
- `ResultStats.tsx` - Result metadata

**Common Props:**
- `results: Article[]` - Array of results
- `onSelect?: (article: Article) => void` - Selection callback
- `highlight?: string` - Query to highlight

### 3. Facet Components (`components/facets/`)

Components for filtering and faceted search.

**Examples:**
- `SourceFacet.tsx` - Filter by source
- `SentimentFacet.tsx` - Filter by sentiment
- `DateRangeFacet.tsx` - Date range selector
- `CategoryFacet.tsx` - Filter by category

**Common Props:**
- `values: string[]` - Selected values
- `onChange: (values: string[]) => void` - Change callback
- `options?: FacetOption[]` - Available options
- `counts?: Record<string, number>` - Result counts per option

---

## 🪝 Hook Template

### File: `hooks/useCustomHook.ts`

```typescript
/**
 * useCustomHook - Brief description of what this hook does
 *
 * Detailed explanation of the hook's purpose, when to use it,
 * and any important considerations.
 *
 * @param param1 - Description of param1
 * @param param2 - Description of param2
 * @returns React Query result with data, loading, and error states
 *
 * @example
 * const { data, isLoading, error } = useCustomHook('query', { page: 1 });
 */

import { useQuery } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import type { CustomResponse, CustomParams } from '../types';

export function useCustomHook(
  param1: string,
  param2?: CustomParams,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
) {
  return useQuery<CustomResponse, Error>({
    queryKey: ['search', 'custom', param1, param2],

    queryFn: async (): Promise<CustomResponse> => {
      const { data } = await searchApi.get('/api/v1/endpoint', {
        params: {
          param1,
          ...param2,
        },
      });
      return data;
    },

    // Configuration
    enabled: options?.enabled ?? true,
    staleTime: 30000,        // 30 seconds
    gcTime: 300000,          // 5 minutes
    refetchInterval: options?.refetchInterval,
    refetchOnWindowFocus: false,

    // Error handling
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
```

---

## 📘 Type Definition Template

### File: `types/customType.ts`

```typescript
/**
 * Type definitions for custom feature
 */

/**
 * Main request type
 */
export interface CustomRequest {
  /**
   * Property description
   * @example "example value"
   */
  property1: string;

  /**
   * Optional property with default
   * @default 10
   */
  property2?: number;
}

/**
 * Main response type
 */
export interface CustomResponse {
  data: CustomData[];
  total: number;
  metadata: ResponseMetadata;
}

/**
 * Data item type
 */
export interface CustomData {
  id: string;
  name: string;
  value: number;
  createdAt: string;
}

/**
 * Response metadata
 */
export interface ResponseMetadata {
  page: number;
  pageSize: number;
  executionTimeMs: number;
}
```

---

## 🧪 Test Template

### File: `components/{category}/__tests__/{ComponentName}.test.tsx`

```typescript
/**
 * Tests for ComponentName component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ComponentName } from '../ComponentName';

// Create test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

// Wrapper with providers
const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ComponentName', () => {
  it('renders with required props', () => {
    render(
      <ComponentName prop1="test value" />,
      { wrapper }
    );

    expect(screen.getByText('test value')).toBeInTheDocument();
  });

  it('calls onAction when button clicked', () => {
    const onAction = jest.fn();

    render(
      <ComponentName prop1="test" onAction={onAction} />,
      { wrapper }
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', async () => {
    render(
      <ComponentName prop1="test" />,
      { wrapper }
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ComponentName prop1="error-trigger" />,
      { wrapper }
    );

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('renders with custom className', () => {
    const { container } = render(
      <ComponentName prop1="test" className="custom-class" />,
      { wrapper }
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
```

---

## 📐 Naming Conventions

### Components
- **PascalCase:** `SearchInput`, `ResultCard`, `DateRangeFacet`
- **Descriptive:** Name describes what it does
- **Suffixes:** Use `-Input`, `-Card`, `-List`, `-Panel` for clarity

### Hooks
- **camelCase with 'use' prefix:** `useArticleSearch`, `useSuggestions`
- **Descriptive action:** Hook name describes the action or data

### Types
- **PascalCase:** `SearchRequest`, `SearchResponse`
- **Descriptive suffix:** `-Request`, `-Response`, `-Props`, `-Options`

### Files
- **PascalCase for components:** `SearchInput.tsx`
- **camelCase for hooks:** `useArticleSearch.ts`
- **camelCase for utilities:** `queryBuilder.ts`

---

## 🎯 Component Best Practices

### 1. Props
- ✅ **DO:** Provide default values for optional props
- ✅ **DO:** Document all props with JSDoc
- ✅ **DO:** Use TypeScript interfaces for props
- ❌ **DON'T:** Use `any` types
- ❌ **DON'T:** Have more than 8 props (consider composition)

### 2. State Management
- ✅ **DO:** Keep state as local as possible
- ✅ **DO:** Use React Query for server state
- ✅ **DO:** Use `useState` for UI state
- ❌ **DON'T:** Store server data in component state
- ❌ **DON'T:** Prop drill more than 2 levels

### 3. Performance
- ✅ **DO:** Use `React.memo()` for expensive components
- ✅ **DO:** Debounce search input
- ✅ **DO:** Lazy load heavy components
- ❌ **DON'T:** Create inline functions in render
- ❌ **DON'T:** Create objects/arrays in render

### 4. Accessibility
- ✅ **DO:** Use semantic HTML
- ✅ **DO:** Add ARIA labels
- ✅ **DO:** Support keyboard navigation
- ❌ **DON'T:** Use `<div>` for buttons
- ❌ **DON'T:** Forget focus management

### 5. Error Handling
- ✅ **DO:** Show user-friendly error messages
- ✅ **DO:** Provide retry mechanisms
- ✅ **DO:** Log errors for debugging
- ❌ **DON'T:** Show raw error stack traces
- ❌ **DON'T:** Fail silently

---

## 🔧 Utility Template

### File: `utils/customUtil.ts`

```typescript
/**
 * Utility functions for custom feature
 */

/**
 * Brief description of what this function does
 *
 * @param input - Description of input
 * @returns Description of return value
 *
 * @example
 * const result = customFunction('input');
 * // result: 'OUTPUT'
 */
export function customFunction(input: string): string {
  // Implementation
  return input.toUpperCase();
}

/**
 * Another utility function
 *
 * @param data - Input data
 * @param options - Configuration options
 * @returns Processed data
 */
export function processData<T>(
  data: T[],
  options?: {
    limit?: number;
    filter?: (item: T) => boolean;
  }
): T[] {
  let result = data;

  if (options?.filter) {
    result = result.filter(options.filter);
  }

  if (options?.limit) {
    result = result.slice(0, options.limit);
  }

  return result;
}
```

---

## 📦 Barrel Export Template

### File: `components/index.ts`

```typescript
/**
 * Barrel export for search-ui components
 *
 * Import components like:
 * import { SearchInput, ResultCard } from '@/features/search-ui/components';
 */

// Search Bar
export { SearchInput } from './search-bar/SearchInput';
export { SearchFilters } from './search-bar/SearchFilters';
export { SearchSuggestions } from './search-bar/SearchSuggestions';

// Results
export { ResultList } from './results/ResultList';
export { ResultCard } from './results/ResultCard';
export { ResultPagination } from './results/ResultPagination';
export { ResultStats } from './results/ResultStats';

// Facets
export { SourceFacet } from './facets/SourceFacet';
export { SentimentFacet } from './facets/SentimentFacet';
export { DateRangeFacet } from './facets/DateRangeFacet';

// Types
export type { SearchInputProps } from './search-bar/SearchInput';
export type { ResultCardProps } from './results/ResultCard';
// ... more type exports
```

---

## 🎨 Styling Guidelines

### 1. Use Tailwind Classes
```tsx
// ✅ Good
<div className="flex items-center gap-2 p-4">

// ❌ Bad
<div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '1rem' }}>
```

### 2. Use CSS Variables for Colors
```tsx
// ✅ Good
<div className="bg-primary text-primary-foreground">

// ❌ Bad
<div className="bg-blue-500 text-white">
```

### 3. Responsive Design
```tsx
// ✅ Good
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Use breakpoints: sm, md, lg, xl, 2xl
```

### 4. Use shadcn/ui Components
```tsx
// ✅ Good - Use existing components
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

// ❌ Bad - Don't recreate basic components
```

---

## 📚 Documentation Checklist

When creating a component, ensure you document:

- [ ] Component purpose (what it does)
- [ ] When to use it
- [ ] Props with descriptions and examples
- [ ] Usage example
- [ ] Default values for optional props
- [ ] Return type (for hooks)
- [ ] Related components/hooks
- [ ] Common patterns
- [ ] Known limitations
- [ ] Accessibility considerations

---

## 🚀 Quick Start

1. **Copy template** from this file
2. **Replace `ComponentName`** with your component name
3. **Update props** interface with your props
4. **Implement logic** inside component
5. **Add to barrel export** in `components/index.ts`
6. **Write tests** using test template
7. **Update README** with usage example

---

## 📖 Additional Resources

- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)

---

**Last Updated:** 2025-11-02
**Maintained By:** Frontend Team
