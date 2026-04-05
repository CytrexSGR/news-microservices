# Knowledge Graph Page - Testing Checklist

Comprehensive testing checklist for manual QA and automated tests.

---

## Manual Testing Checklist

### 1. Page Load

- [ ] Page loads without errors
- [ ] Empty state displays correctly
- [ ] Search bar is visible and focused
- [ ] Controls toolbar is visible
- [ ] No console errors
- [ ] No TypeScript errors

### 2. Entity Search

**Basic Search:**
- [ ] Typing shows autocomplete dropdown
- [ ] Results update as you type (300ms debounce)
- [ ] No results show "No entities found"
- [ ] Click result selects entity
- [ ] Enter key selects highlighted result

**Keyboard Navigation:**
- [ ] Arrow Down highlights next result
- [ ] Arrow Up highlights previous result
- [ ] Enter selects highlighted result
- [ ] Esc closes dropdown
- [ ] Tab navigates out of dropdown

**Recent Searches:**
- [ ] Recent searches show when input is empty
- [ ] Click recent search selects it
- [ ] Recent searches persist after reload
- [ ] Max 5 recent searches displayed

### 3. Graph Visualization

**Data Loading:**
- [ ] Loading state shows during fetch
- [ ] Loading message is clear
- [ ] Graph renders after load
- [ ] Nodes and edges display correctly
- [ ] Layout algorithm applies correctly

**Interactions:**
- [ ] Click node selects it
- [ ] Selected node highlights
- [ ] Hover shows node tooltip (if implemented)
- [ ] Drag nodes repositions them
- [ ] Zoom in/out works
- [ ] Pan works (drag empty space)
- [ ] Fit view button centers graph

**Visual Quality:**
- [ ] Node colors match entity types
- [ ] Edge labels are readable
- [ ] No overlapping nodes (in force layout)
- [ ] Animations are smooth (60fps)
- [ ] Graph is responsive on resize

### 4. Entity Details Panel

**Opening:**
- [ ] Panel opens on node click
- [ ] Slide-in animation is smooth
- [ ] Panel displays correct entity
- [ ] Entity name and type shown
- [ ] Connection count correct

**Content:**
- [ ] Wikidata link works (if available)
- [ ] Connection groups are collapsible
- [ ] Click connection selects that entity
- [ ] Action buttons are visible
- [ ] Scroll works for long lists

**Closing:**
- [ ] X button closes panel
- [ ] Esc key closes panel
- [ ] Slide-out animation is smooth
- [ ] Panel doesn't reopen unexpectedly

### 5. Graph Filters

**Opening:**
- [ ] Filter button opens panel
- [ ] Slide-in animation is smooth
- [ ] All filter sections visible
- [ ] Active filter badge shows

**Entity Type Filter:**
- [ ] All entity types listed
- [ ] Click type toggles selection
- [ ] Graph updates on selection
- [ ] Multiple types can be selected

**Relationship Filter:**
- [ ] All relationship types listed
- [ ] Click type toggles selection
- [ ] Graph updates on selection
- [ ] Multiple types can be selected

**Confidence Slider:**
- [ ] Slider moves smoothly
- [ ] Value updates on drag
- [ ] Graph filters on value change
- [ ] Min/max values correct (0-1)

**Actions:**
- [ ] Reset All clears all filters
- [ ] Apply Filters closes panel
- [ ] Filters persist on panel close

### 6. Layout Controls

**Layout Selector:**
- [ ] Dropdown opens on click
- [ ] All layouts listed (Force, Hierarchical, Radial)
- [ ] Click layout applies it
- [ ] Active layout shows badge
- [ ] Graph updates with new layout

**Zoom Controls:**
- [ ] Zoom In button works
- [ ] Zoom Out button works
- [ ] Fit View centers graph
- [ ] Toast notifications show

**View Toggles:**
- [ ] Labels toggle works
- [ ] Legend toggle works
- [ ] Active state shows correctly

**Export:**
- [ ] Export dropdown opens
- [ ] JSON export downloads file
- [ ] PNG export shows "Phase 4" message
- [ ] SVG export shows "Phase 4" message

### 7. URL State Management

**Initial Load:**
- [ ] `?entity=Tesla` loads Tesla
- [ ] Invalid entity shows error
- [ ] No param shows empty state
- [ ] URL decodes correctly (`%20` → space)

**Navigation:**
- [ ] Selecting entity updates URL
- [ ] URL updates without page reload
- [ ] Browser back button works
- [ ] Browser forward button works
- [ ] Refresh preserves entity

### 8. Keyboard Shortcuts

- [ ] `/` focuses search input
- [ ] `?` shows help (Phase 4 stub)
- [ ] `Esc` closes open panel
- [ ] `Esc` closes dropdown
- [ ] Tab navigates elements
- [ ] Shortcuts don't conflict

### 9. Error Handling

**Network Errors:**
- [ ] Offline shows error state
- [ ] Error message is clear
- [ ] Retry button works
- [ ] Back to Search clears error

**API Errors:**
- [ ] 404 shows "Entity not found"
- [ ] 500 shows "Server error"
- [ ] 403 shows "Unauthorized"
- [ ] Technical details collapsible

**Client Errors:**
- [ ] Invalid entity name handled
- [ ] Malformed URL handled
- [ ] localStorage quota handled

### 10. Responsive Design

**Desktop (>1024px):**
- [ ] Search bar 400px width
- [ ] Controls full width
- [ ] Panels 400px width
- [ ] Graph fills space

**Tablet (768-1024px):**
- [ ] Search bar 300px width
- [ ] Controls compact
- [ ] Panels 80% width
- [ ] Graph fits well

**Mobile (<768px):**
- [ ] Search bar full width
- [ ] Controls stack vertically
- [ ] Panels full screen
- [ ] Graph is usable
- [ ] Touch gestures work

### 11. Accessibility

**Keyboard Navigation:**
- [ ] All interactive elements focusable
- [ ] Tab order is logical
- [ ] Focus visible (outline)
- [ ] Escape key closes panels

**ARIA:**
- [ ] Landmarks present (header, main)
- [ ] Dialog roles correct
- [ ] Labels on icon buttons
- [ ] Expanded states correct

**Screen Reader:**
- [ ] Page title announced
- [ ] Panel open/close announced
- [ ] Button actions announced
- [ ] Error messages announced

### 12. Performance

**Load Times:**
- [ ] Initial load < 1s
- [ ] Entity fetch < 500ms
- [ ] Graph render < 200ms
- [ ] Panel animation 300ms

**Interactions:**
- [ ] Search debounce 300ms
- [ ] Graph pan is smooth
- [ ] Zoom is smooth
- [ ] No lag on interactions

**Memory:**
- [ ] No memory leaks
- [ ] localStorage < 1 KB
- [ ] Graph memory reasonable

### 13. Browser Compatibility

**Chrome:**
- [ ] All features work
- [ ] Animations smooth
- [ ] No console errors

**Firefox:**
- [ ] All features work
- [ ] Animations smooth
- [ ] No console errors

**Safari:**
- [ ] All features work
- [ ] Animations smooth
- [ ] No console errors

**Edge:**
- [ ] All features work
- [ ] Animations smooth
- [ ] No console errors

### 14. Edge Cases

**Empty Data:**
- [ ] Empty graph shows message
- [ ] No entities to display
- [ ] No connections for entity

**Large Data:**
- [ ] 200+ nodes render
- [ ] Performance acceptable
- [ ] Memory reasonable

**Special Characters:**
- [ ] Entity names with spaces
- [ ] Entity names with symbols
- [ ] Unicode characters work

**Network:**
- [ ] Slow network shows loading
- [ ] Timeout handled
- [ ] Retry works

---

## Automated Test Cases

### Unit Tests

```typescript
// LoadingState.test.tsx
describe('LoadingState', () => {
  test('renders loading spinner', () => {})
  test('displays loading message', () => {})
  test('has correct ARIA attributes', () => {})
})

// ErrorState.test.tsx
describe('ErrorState', () => {
  test('displays error message', () => {})
  test('calls onRetry when retry clicked', () => {})
  test('calls onBackToSearch when back clicked', () => {})
  test('toggles technical details', () => {})
  test('handles Error object', () => {})
  test('handles string error', () => {})
})

// EmptyState.test.tsx
describe('EmptyState', () => {
  test('renders search prompt', () => {})
  test('displays popular entities', () => {})
  test('displays recent searches', () => {})
  test('calls onEntitySelect when entity clicked', () => {})
  test('shows keyboard shortcuts hint', () => {})
})

// KnowledgeGraphPage.test.tsx
describe('KnowledgeGraphPage', () => {
  test('loads entity from URL param', () => {})
  test('shows empty state by default', () => {})
  test('updates URL on entity selection', () => {})
  test('opens detail panel on entity select', () => {})
  test('closes panel on Esc key', () => {})
  test('handles keyboard shortcuts', () => {})
  test('saves to localStorage', () => {})
  test('restores from localStorage', () => {})
})
```

### Integration Tests

```typescript
// KnowledgeGraphPage.integration.test.tsx
describe('KnowledgeGraphPage Integration', () => {
  test('completes full entity selection flow', async () => {
    // 1. Render page
    // 2. Search for entity
    // 3. Select from results
    // 4. Verify graph loads
    // 5. Verify detail panel opens
    // 6. Verify URL updates
  })

  test('handles error and retry flow', async () => {
    // 1. Mock API error
    // 2. Verify error state shows
    // 3. Click retry
    // 4. Verify success on retry
  })

  test('persists state across reload', async () => {
    // 1. Select entity
    // 2. Reload page
    // 3. Verify entity still selected
  })

  test('filters graph correctly', async () => {
    // 1. Load graph
    // 2. Open filters
    // 3. Apply filters
    // 4. Verify graph updates
  })
})
```

### E2E Tests (Playwright)

```typescript
// knowledge-graph.spec.ts
test.describe('Knowledge Graph Page', () => {
  test('user can search and view entity', async ({ page }) => {
    await page.goto('/knowledge-graph')
    await page.fill('input[type="text"]', 'Tesla')
    await page.click('text=Tesla, Inc.')
    await expect(page.locator('[data-testid="graph-canvas"]')).toBeVisible()
    await expect(page.locator('[data-testid="entity-details"]')).toBeVisible()
    expect(page.url()).toContain('?entity=Tesla')
  })

  test('user can filter graph', async ({ page }) => {
    await page.goto('/knowledge-graph?entity=Tesla')
    await page.click('button:has-text("Filters")')
    await page.click('text=PERSON')
    await page.click('button:has-text("Apply Filters")')
    // Verify filtered graph
  })

  test('user can navigate with keyboard', async ({ page }) => {
    await page.goto('/knowledge-graph')
    await page.keyboard.press('/')
    await expect(page.locator('input[type="text"]')).toBeFocused()
    await page.keyboard.press('Escape')
    // Verify dropdown closed
  })
})
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Initial page load | < 1s | _____ | ⏳ |
| Entity fetch | < 500ms | _____ | ⏳ |
| Graph render (50 nodes) | < 200ms | _____ | ⏳ |
| Panel animation | 300ms | _____ | ⏳ |
| Search debounce | 300ms | _____ | ⏳ |
| Memory usage (base) | < 5 MB | _____ | ⏳ |
| Memory usage (200 nodes) | < 20 MB | _____ | ⏳ |

### Load Testing

- [ ] 50 nodes: Performance good
- [ ] 100 nodes: Performance acceptable
- [ ] 200 nodes: Performance acceptable
- [ ] 500 nodes: Performance warning
- [ ] 1000 nodes: Virtual scrolling needed

---

## Security Checklist

- [ ] XSS: Entity names sanitized
- [ ] CSRF: Not applicable (read-only)
- [ ] localStorage: No sensitive data
- [ ] URL params: Decoded safely
- [ ] API calls: HTTPS only
- [ ] Auth: JWT tokens handled (if required)

---

## Deployment Checklist

### Pre-deployment

- [ ] All tests passing
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] No console.log statements
- [ ] Environment variables configured
- [ ] API endpoints correct

### Deployment

- [ ] Build succeeds
- [ ] Bundle size acceptable (< 50 KB)
- [ ] Source maps generated
- [ ] Assets uploaded to CDN
- [ ] Cache headers set

### Post-deployment

- [ ] Page loads in production
- [ ] API calls work
- [ ] No 404 errors
- [ ] Analytics tracking works
- [ ] Error monitoring configured

---

## Bug Report Template

```markdown
**Bug Title:** [Clear, descriptive title]

**Environment:**
- Browser: [Chrome 120.0]
- OS: [macOS 14.0]
- Screen: [1920x1080]

**Steps to Reproduce:**
1. Go to /knowledge-graph
2. Search for "Tesla"
3. Click first result
4. ...

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Screenshots:**
[Attach screenshots]

**Console Errors:**
[Copy console output]

**Additional Context:**
[Any other relevant info]
```

---

## Test Coverage Goals

| Category | Goal | Actual | Status |
|----------|------|--------|--------|
| Unit Tests | 80% | _____ | ⏳ |
| Integration Tests | 70% | _____ | ⏳ |
| E2E Tests | 50% | _____ | ⏳ |
| Manual QA | 100% | _____ | ⏳ |

---

**Summary:**

This checklist ensures:
- ✅ Comprehensive testing coverage
- ✅ All features work correctly
- ✅ Performance meets targets
- ✅ Accessibility standards met
- ✅ Production ready

Use this checklist before each release! 🚀
