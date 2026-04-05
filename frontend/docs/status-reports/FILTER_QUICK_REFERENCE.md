# Filter Components Quick Reference

**Phase 2.3 - Knowledge Graph Filters**
**Status:** ✅ Production Ready

---

## Quick Import

```typescript
import {
  EntityTypeFilter,
  RelationshipFilter,
  ConfidenceSlider,
  GraphFilters,
} from '@/features/knowledge-graph/components/filters'
```

---

## Component APIs

### 1. EntityTypeFilter

```typescript
<EntityTypeFilter
  value={['PERSON', 'ORGANIZATION']}
  onChange={(types) => console.log(types)}
  className="custom-class"  // optional
/>
```

**Entity Types:**
- PERSON 👤
- ORGANIZATION 🏢
- LOCATION 📍
- EVENT 📅
- PRODUCT 📦
- NOT_APPLICABLE ⚪

---

### 2. RelationshipFilter

```typescript
<RelationshipFilter
  value={['WORKS_FOR', 'LOCATED_IN']}
  onChange={(types) => console.log(types)}
  className="custom-class"  // optional
/>
```

**Relationship Types (16 total):**
- WORKS_FOR 💼
- MANAGES 👔
- FOUNDED_BY 🏗️
- PARTNERS_WITH 🤝
- AFFILIATED_WITH 🔗
- COLLABORATES_WITH 🤝
- LOCATED_IN 📍
- HEADQUARTERED_IN 🏢
- OPERATES_IN 🌍
- OWNS 🏛️
- ACQUIRED_BY 💰
- PART_OF 🧩
- COMPETES_WITH ⚔️
- OPPOSES 🚫
- RELATED_TO ↔️
- MENTIONED_WITH 💬

---

### 3. ConfidenceSlider

```typescript
<ConfidenceSlider
  value={0.5}  // 0.0 - 1.0
  onChange={(confidence) => console.log(confidence)}
  className="custom-class"  // optional
/>
```

**Presets:**
- Low: 0.3 (30%)
- Medium: 0.5 (50%)
- High: 0.7 (70%)

**Color Coding:**
- 🟢 Green: ≥70% (High)
- 🟡 Yellow: 50-69% (Medium)
- 🔴 Red: <50% (Low)

---

### 4. GraphFilters (Wrapper)

```typescript
<GraphFilters
  isOpen={true}
  onClose={() => console.log('closed')}
  className="custom-class"  // optional
/>
```

**Features:**
- Contains all 3 filters
- Slide-in from right
- Backdrop overlay
- Reset All button
- Apply Filters button
- Keyboard support (Escape to close)

---

## Store Integration

```typescript
import { useGraphStore } from '@/features/knowledge-graph/store/graphStore'

// Read filters
const filters = useGraphStore((state) => state.filters)
// filters.entityTypes: string[]
// filters.relationshipTypes: string[]
// filters.minConfidence: number

// Update filters
const setFilters = useGraphStore((state) => state.setFilters)
setFilters({
  entityTypes: ['PERSON'],
  minConfidence: 0.7,
})

// Reset filters
const resetFilters = useGraphStore((state) => state.resetFilters)
resetFilters()
```

---

## Complete Example

```typescript
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { GraphFilters } from '@/features/knowledge-graph/components/filters'
import { useGraphStore } from '@/features/knowledge-graph/store/graphStore'

export function KnowledgeGraphPage() {
  const [filtersOpen, setFiltersOpen] = useState(false)
  const filters = useGraphStore((state) => state.filters)

  return (
    <div className="relative">
      {/* Trigger Button */}
      <Button onClick={() => setFiltersOpen(true)}>
        Open Filters
        {(filters.entityTypes.length > 0 ||
          filters.relationshipTypes.length > 0 ||
          filters.minConfidence !== 0.5) && (
          <span className="ml-2 bg-blue-500 text-white px-2 py-0.5 rounded-full text-xs">
            Active
          </span>
        )}
      </Button>

      {/* Filter Panel */}
      <GraphFilters
        isOpen={filtersOpen}
        onClose={() => setFiltersOpen(false)}
      />

      {/* Your graph component here */}
      <div>
        {/* Graph uses filters from store automatically */}
      </div>
    </div>
  )
}
```

---

## Common Patterns

### Pattern 1: Standalone Filters

```typescript
import { EntityTypeFilter } from '@/features/knowledge-graph/components/filters'

function CustomFilterPanel() {
  const [types, setTypes] = useState<string[]>([])

  return (
    <EntityTypeFilter
      value={types}
      onChange={setTypes}
    />
  )
}
```

### Pattern 2: Pre-filtered State

```typescript
import { useGraphStore } from '@/features/knowledge-graph/store/graphStore'

function BusinessAnalysisView() {
  const setFilters = useGraphStore((state) => state.setFilters)

  useEffect(() => {
    // Auto-apply business-relevant filters
    setFilters({
      entityTypes: ['PERSON', 'ORGANIZATION'],
      relationshipTypes: ['WORKS_FOR', 'MANAGES', 'OWNS'],
      minConfidence: 0.7,
    })
  }, [])

  return <GraphFilters isOpen={true} onClose={() => {}} />
}
```

### Pattern 3: Filter Count Badge

```typescript
function FilterBadge() {
  const filters = useGraphStore((state) => state.filters)

  const activeFiltersCount =
    filters.entityTypes.length +
    filters.relationshipTypes.length +
    (filters.minConfidence !== 0.5 ? 1 : 0)

  if (activeFiltersCount === 0) return null

  return (
    <span className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs">
      {activeFiltersCount} active
    </span>
  )
}
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Close filter panel |
| `Tab` | Navigate between controls |
| `Enter` / `Space` | Toggle checkbox |
| `Arrow Keys` | Adjust slider (when focused) |

---

## Accessibility

All components are fully accessible:
- ✅ Keyboard navigation
- ✅ ARIA attributes
- ✅ Screen reader support
- ✅ Focus management
- ✅ Visible focus indicators

---

## Performance Tips

1. **Use React.memo**: Already applied, no action needed
2. **Debounce slider changes** (for graphs with >1000 nodes):
   ```typescript
   const debouncedSetFilters = useMemo(
     () => debounce(setFilters, 300),
     [setFilters]
   )
   ```

3. **Lazy load panel**:
   ```typescript
   {filtersOpen && <GraphFilters ... />}
   ```

---

## Troubleshooting

### Issue: Filters not applying to graph
**Solution:** Ensure graph component reads from store:
```typescript
const filters = useGraphStore((state) => state.filters)
// Use filters to filter nodes/edges
```

### Issue: Store persists old filters
**Solution:** Clear localStorage:
```typescript
localStorage.removeItem('knowledge-graph-store')
```

### Issue: Colors not matching
**Solution:** Import from color scheme utility:
```typescript
import { ENTITY_TYPE_COLORS } from '@/features/knowledge-graph/utils/colorScheme'
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `EntityTypeFilter.tsx` | Entity type multi-select |
| `RelationshipFilter.tsx` | Relationship type multi-select |
| `ConfidenceSlider.tsx` | Confidence threshold slider |
| `GraphFilters.tsx` | Wrapper panel with all filters |
| `index.ts` | Barrel export |

---

## Related Documentation

- **Full Implementation:** [FILTER_COMPONENTS_SUMMARY.md](FILTER_COMPONENTS_SUMMARY.md)
- **Visual Guide:** [FILTER_COMPONENTS_VISUAL_GUIDE.md](FILTER_COMPONENTS_VISUAL_GUIDE.md)
- **Store Documentation:** `/frontend/src/features/knowledge-graph/store/graphStore.ts`
- **Type Definitions:** `/frontend/src/types/knowledgeGraphPublic.ts`

---

**Need Help?** Check the comprehensive docs or inspect the component source code.

**Last Updated:** 2025-11-02
