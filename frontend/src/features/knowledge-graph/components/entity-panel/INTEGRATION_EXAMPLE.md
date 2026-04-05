# EntityDetails Integration Example

This document shows how to integrate the EntityDetails side panel with the Knowledge Graph visualization.

## Basic Integration

```tsx
import { useState } from 'react'
import { GraphVisualization } from '@/features/knowledge-graph/components/graph-viewer'
import { EntityDetails } from '@/features/knowledge-graph/components/entity-panel'
import { useGraphStore } from '@/features/knowledge-graph/store'
import { useGraphData } from '@/features/knowledge-graph/hooks/useGraphData'

export function KnowledgeGraphPage() {
  // Store state
  const selectedEntity = useGraphStore((state) => state.selectedEntity)
  const detailPanelOpen = useGraphStore((state) => state.detailPanelOpen)
  const toggleDetailPanel = useGraphStore((state) => state.toggleDetailPanel)

  // Fetch graph data
  const { data: graphData, isLoading, error } = useGraphData()

  if (isLoading) {
    return <div>Loading graph...</div>
  }

  if (error || !graphData) {
    return <div>Error loading graph</div>
  }

  return (
    <div className="relative h-screen w-full">
      {/* Main graph visualization */}
      <GraphVisualization graphData={graphData} />

      {/* Entity details panel (auto-opens when entity selected) */}
      {detailPanelOpen && (
        <EntityDetails
          entityName={selectedEntity}
          onClose={toggleDetailPanel}
        />
      )}
    </div>
  )
}
```

## How It Works

### 1. Entity Selection Flow

```
User clicks node
    ↓
GraphVisualization.onNodeClick
    ↓
useGraphStore.setSelectedEntity(nodeId)
    ↓
Store automatically sets detailPanelOpen = true
    ↓
EntityDetails receives entityName prop
    ↓
useEntityConnections hook fetches data
    ↓
Panel displays entity details
```

### 2. Auto-Open Behavior

The store automatically opens the detail panel when an entity is selected:

```typescript
// From graphStore.ts
setSelectedEntity: (entityId) => {
  set({ selectedEntity: entityId }, false, 'setSelectedEntity')

  // Auto-open detail panel when selecting entity
  if (entityId && !get().detailPanelOpen) {
    set({ detailPanelOpen: true }, false, 'autoOpenDetailPanel')
  }
}
```

### 3. Connection Click Flow

```
User clicks connection in EntityDetails
    ↓
ConnectionItem.onClick(targetEntity)
    ↓
EntityDetails.handleConnectionClick
    ↓
useGraphStore.setSelectedEntity(targetEntity)
    ↓
useEntityConnections re-fetches for new entity
    ↓
Panel updates to show new entity
```

### 4. Close Panel Flow

```
User clicks X button OR presses Esc key
    ↓
EntityDetails.handleClose()
    ↓
onClose() callback
    ↓
useGraphStore.toggleDetailPanel()
    ↓
Panel closes with slide-out animation
```

## Advanced Usage

### Custom Layout

```tsx
<div className="grid grid-cols-[1fr_400px] h-screen">
  {/* Left: Graph */}
  <GraphVisualization graphData={graphData} />

  {/* Right: Fixed panel (always visible) */}
  {selectedEntity ? (
    <EntityDetails
      entityName={selectedEntity}
      onClose={() => setSelectedEntity(null)}
      className="relative border-l" // Override fixed positioning
    />
  ) : (
    <div className="border-l bg-muted flex items-center justify-center">
      <p className="text-muted-foreground">Select an entity to view details</p>
    </div>
  )}
</div>
```

### With Tabs (Multiple Panels)

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function KnowledgeGraphWithTabs() {
  const selectedEntity = useGraphStore((state) => state.selectedEntity)
  const detailPanelOpen = useGraphStore((state) => state.detailPanelOpen)

  return (
    <div className="relative h-screen">
      <GraphVisualization graphData={graphData} />

      {detailPanelOpen && (
        <div className="fixed right-0 top-0 h-full w-[500px] bg-background border-l shadow-lg">
          <Tabs defaultValue="details">
            <TabsList className="w-full">
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="articles">Articles</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
            </TabsList>

            <TabsContent value="details">
              <EntityDetails
                entityName={selectedEntity}
                onClose={() => toggleDetailPanel()}
                className="relative" // Override fixed positioning
              />
            </TabsContent>

            <TabsContent value="articles">
              {/* TODO: Article list component */}
            </TabsContent>

            <TabsContent value="timeline">
              {/* TODO: Timeline component */}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}
```

## Responsive Behavior

### Desktop (≥768px)
- Panel slides in from right (400px width)
- Graph remains visible (compressed)
- User can interact with both graph and panel

### Mobile (<768px)
- Panel covers entire screen (full-width overlay)
- Graph hidden behind panel
- Close panel to return to graph

## Keyboard Shortcuts

- **Esc** - Close entity details panel
- **Tab** - Navigate between connections (focus trap)
- **Enter** - Select focused connection
- **Arrow Keys** - Navigate collapsible groups (future)

## State Persistence

The following state is persisted to localStorage:

- ✅ `recentSearches` - Recent entity searches
- ✅ `sidebarOpen` - Sidebar visibility
- ✅ `showLabels` - Edge label visibility
- ✅ `showLegend` - Legend visibility
- ❌ `selectedEntity` - NOT persisted (cleared on page reload)
- ❌ `detailPanelOpen` - NOT persisted (closed on page reload)

## Error Handling

### Network Errors

```tsx
const { data, error, refetch } = useEntityConnections(entityName)

// EntityDetails handles error state automatically
// Shows error icon + retry button
```

### Missing Entity

```tsx
// If entity not found in graph data:
// - Shows error state
// - Displays "Entity not found" message
// - Provides retry button
```

## Performance Considerations

### Memoization
- Component uses `React.memo` to prevent unnecessary re-renders
- All callbacks are wrapped in `useCallback`
- Computed values use `useMemo`

### Data Fetching
- Only fetches when panel is open (`enabled: !!entityName && detailPanelOpen`)
- React Query caching (5 min staleTime, 10 min gcTime)
- Prevents duplicate requests for same entity

### Grouping
- Relationships grouped by type on client side
- Auto-expands only first 3 groups (lazy rendering)
- Load more pagination (max 10 visible per group)

## Testing

### Manual Testing Checklist
- [ ] Click node → panel opens
- [ ] Click X button → panel closes
- [ ] Press Esc → panel closes
- [ ] Click connection → switches to that entity
- [ ] Expand/collapse groups → smooth animation
- [ ] Wikidata link → opens in new tab
- [ ] Responsive → full-width on mobile
- [ ] Loading state → shows spinner
- [ ] Error state → shows retry button
- [ ] Empty state → shows "no connections"

### Unit Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { EntityDetails } from './EntityDetails'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

describe('EntityDetails', () => {
  it('shows loading state while fetching', () => {
    const queryClient = new QueryClient()

    render(
      <QueryClientProvider client={queryClient}>
        <EntityDetails entityName="Tesla" onClose={jest.fn()} />
      </QueryClientProvider>
    )

    expect(screen.getByText(/loading entity details/i)).toBeInTheDocument()
  })

  it('closes when X button clicked', () => {
    const onClose = jest.fn()

    render(
      <EntityDetails entityName="Tesla" onClose={onClose} />
    )

    fireEvent.click(screen.getByLabelText(/close panel/i))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
```

## Troubleshooting

### Panel doesn't open
- Check `detailPanelOpen` state in Zustand devtools
- Verify `setSelectedEntity` is called on node click
- Check auto-open logic in store

### Data not loading
- Check network tab for API calls
- Verify `useEntityConnections` hook is enabled
- Check entity name matches graph data

### Animations broken
- Verify Tailwind CSS is configured correctly
- Check `animate-in` utility is available
- Ensure no conflicting CSS

### Panel too narrow/wide
- Adjust `w-[400px]` in EntityDetails.tsx
- Update responsive breakpoints for mobile

## Next Steps

1. ✅ Basic EntityDetails implementation
2. ⬜ Integrate with GraphViewer (in progress)
3. ⬜ Add search & filters components
4. ⬜ Implement pathfinding dialog (Phase 4)
5. ⬜ Add article list panel (Phase 4)
6. ⬜ Add entity timeline (Phase 4)

---

**Last Updated:** 2025-11-02
**Component Version:** 1.0.0
**Status:** ✅ Ready for Integration
