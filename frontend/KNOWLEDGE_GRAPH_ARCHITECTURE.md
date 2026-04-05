# Knowledge Graph Page - Architecture Diagram

Visual representation of the component hierarchy and data flow.

---

## Component Hierarchy

```
KnowledgeGraphPage (Main Container)
│
├─ ReactFlowProvider (Context Provider)
│  │
│  ├─ Toaster (Toast Notifications)
│  │
│  ├─ <header> (Fixed Top Bar)
│  │  ├─ EntitySearch (Autocomplete)
│  │  └─ GraphControls (Toolbar)
│  │     └─ Filter Toggle Button
│  │
│  ├─ <main> (Graph Area)
│  │  │
│  │  ├─ LoadingState (Conditional)
│  │  │  └─ Loader2 Spinner
│  │  │
│  │  ├─ ErrorState (Conditional)
│  │  │  ├─ AlertCircle Icon
│  │  │  ├─ Error Message
│  │  │  ├─ Retry Button
│  │  │  └─ Back to Search Button
│  │  │
│  │  ├─ EmptyState (Conditional)
│  │  │  ├─ Search Icon
│  │  │  ├─ Popular Entities
│  │  │  └─ Recent Searches
│  │  │
│  │  └─ GraphVisualization (Conditional)
│  │     ├─ ReactFlow Canvas
│  │     │  ├─ EntityNodeComponent (Custom Nodes)
│  │     │  ├─ RelationshipEdgeComponent (Custom Edges)
│  │     │  ├─ Background Pattern
│  │     │  ├─ Controls (Zoom)
│  │     │  ├─ MiniMap
│  │     │  └─ Statistics Panel
│  │     └─ Legend (Optional)
│  │
│  ├─ EntityDetails (Slide-in Panel)
│  │  ├─ Close Button
│  │  ├─ Entity Header
│  │  │  ├─ Entity Name
│  │  │  ├─ Entity Type Badge
│  │  │  └─ Wikidata Link
│  │  ├─ Connection Groups (Collapsible)
│  │  │  └─ ConnectionItem (List)
│  │  └─ Action Buttons
│  │     ├─ Explore Connections
│  │     ├─ Find Path To...
│  │     └─ View in Neo4j
│  │
│  └─ GraphFilters (Slide-in Panel)
│     ├─ Close Button
│     ├─ EntityTypeFilter
│     ├─ RelationshipFilter
│     ├─ ConfidenceSlider
│     ├─ Reset All Button
│     └─ Apply Filters Button
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     KnowledgeGraphPage                          │
│                                                                 │
│  ┌──────────────┐        ┌──────────────┐                      │
│  │ Local State  │        │ Zustand      │                      │
│  │              │        │ Store        │                      │
│  │ - selectedEntity ────▶│ - selectedEntity                    │
│  │ - filtersOpen   │     │ - detailPanelOpen                   │
│  └──────────────┘        │ - filters                           │
│         │                │ - layoutType                         │
│         ▼                └──────────────┘                       │
│  ┌──────────────────────────────────────────┐                  │
│  │  useEntityConnections(selectedEntity)    │                  │
│  │  (React Query Hook)                      │                  │
│  └──────────────────────────────────────────┘                  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                  │
│  │  API Call: GET /api/v1/entities/{name}/connections         │
│  └──────────────────────────────────────────┘                  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                  │
│  │  GraphResponse { nodes, edges }           │                  │
│  └──────────────────────────────────────────┘                  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                  │
│  │  transformToReactFlow() + filterGraph()   │                  │
│  │  (Transform & Filter)                     │                  │
│  └──────────────────────────────────────────┘                  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                  │
│  │  GraphVisualization                       │                  │
│  │  (React Flow Canvas)                      │                  │
│  └──────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     State Management                            │
└─────────────────────────────────────────────────────────────────┘

USER ACTION: Click entity in search
    │
    ▼
handleEntitySelect('Tesla')
    │
    ├─▶ setSelectedEntity('Tesla')         [Local State]
    │   └─▶ Trigger useEntityConnections   [React Query]
    │
    ├─▶ setSelectedEntityStore('Tesla')    [Zustand Store]
    │   └─▶ Auto-open detail panel         [Side Effect]
    │
    ├─▶ setSearchParams({ entity: 'Tesla' }) [URL State]
    │   └─▶ Update browser URL             [History API]
    │
    └─▶ localStorage.setItem('Tesla')      [Persistence]
        └─▶ Save for next session          [Browser Storage]

────────────────────────────────────────────────────────────────────

USER ACTION: Click Filters button
    │
    ▼
handleFilterToggle()
    │
    └─▶ setFiltersOpen(true)               [Local State]
        └─▶ <GraphFilters isOpen={true} /> [Conditional Render]
            └─▶ Slide-in animation         [CSS Transition]

────────────────────────────────────────────────────────────────────

USER ACTION: Update filter
    │
    ▼
setFilters({ entityTypes: ['PERSON'] })    [Zustand Store]
    │
    └─▶ filterGraph(nodes, edges, filters) [Transform]
        └─▶ Update GraphVisualization       [Re-render]
```

---

## Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Event Flow                               │
└─────────────────────────────────────────────────────────────────┘

SEARCH → LOAD → DISPLAY → INTERACT

1. SEARCH
   User types "Tesla" in EntitySearch
        │
        ▼
   Debounce 300ms
        │
        ▼
   useEntitySearch('Tesla')
        │
        ▼
   API: GET /api/v1/entities/search?query=Tesla
        │
        ▼
   Display autocomplete results
        │
        ▼
   User clicks "Tesla, Inc."

2. LOAD
   handleEntitySelect('Tesla, Inc.')
        │
        ▼
   useEntityConnections('Tesla, Inc.')
        │
        ▼
   API: GET /api/v1/entities/Tesla%2C%20Inc./connections
        │
        ▼
   Show LoadingState (spinner)
        │
        ▼
   Receive GraphResponse { 50 nodes, 120 edges }

3. DISPLAY
   transformToReactFlow(graphData, 'force')
        │
        ▼
   filterGraph(nodes, edges, filters)
        │
        ▼
   Render GraphVisualization
        │
        ▼
   Calculate force-directed layout
        │
        ▼
   Animate nodes to positions

4. INTERACT
   User clicks node "Elon Musk"
        │
        ▼
   handleNodeClick('Elon Musk')
        │
        ├─▶ setSelectedEntity('Elon Musk')
        │   └─▶ Fetch new connections
        │
        └─▶ Open EntityDetails panel
            └─▶ Show relationships
```

---

## Panel State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    Panel State Machine                          │
└─────────────────────────────────────────────────────────────────┘

STATE: Closed
    │
    ├─ EVENT: User clicks node
    │     │
    │     └─▶ Transition to: Opening
    │           └─▶ Transition to: Open
    │
    └─ EVENT: User clicks Filters button
          │
          └─▶ Transition to: Opening
                └─▶ Transition to: Open

STATE: Open
    │
    ├─ EVENT: User clicks close button
    │     │
    │     └─▶ Transition to: Closing
    │           └─▶ Transition to: Closed
    │
    ├─ EVENT: User clicks outside panel
    │     │
    │     └─▶ Transition to: Closing
    │           └─▶ Transition to: Closed
    │
    └─ EVENT: User presses Esc key
          │
          └─▶ Transition to: Closing
                └─▶ Transition to: Closed

ANIMATIONS:
- Opening:  300ms slide-in from right
- Closing:  300ms slide-out to right
- Backdrop: 200ms fade-in/out
```

---

## URL State Sync

```
┌─────────────────────────────────────────────────────────────────┐
│                      URL State Sync                             │
└─────────────────────────────────────────────────────────────────┘

SCENARIO 1: User navigates to /knowledge-graph?entity=Tesla
    │
    ├─ useSearchParams() reads "Tesla"
    │     │
    │     └─▶ setSelectedEntity('Tesla')
    │           │
    │           └─▶ useEntityConnections('Tesla')
    │                 │
    │                 └─▶ Load graph
    │
    └─ localStorage saves "Tesla"

────────────────────────────────────────────────────────────────────

SCENARIO 2: User selects entity in UI
    │
    ├─ handleEntitySelect('Apple')
    │     │
    │     └─▶ setSearchParams({ entity: 'Apple' })
    │           │
    │           └─▶ URL becomes: /knowledge-graph?entity=Apple
    │
    └─ Browser history: new entry added

────────────────────────────────────────────────────────────────────

SCENARIO 3: User clicks browser back button
    │
    ├─ URL changes: /knowledge-graph?entity=Apple
    │                → /knowledge-graph?entity=Tesla
    │     │
    │     └─▶ useSearchParams() detects change
    │           │
    │           └─▶ useEffect updates selectedEntity
    │                 │
    │                 └─▶ Fetch new graph

────────────────────────────────────────────────────────────────────

SCENARIO 4: User reloads page
    │
    ├─ URL: /knowledge-graph?entity=Tesla
    │     │
    │     └─▶ useSearchParams() reads "Tesla"
    │           │
    │           └─▶ setSelectedEntity('Tesla')
    │                 │
    │                 └─▶ Load graph (from cache if available)
    │
    └─ localStorage has "Tesla" (redundant backup)
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                          │
└─────────────────────────────────────────────────────────────────┘

API CALL: GET /api/v1/entities/{name}/connections
    │
    ├─ SUCCESS (200 OK)
    │     │
    │     └─▶ GraphVisualization renders
    │
    ├─ ERROR (404 Not Found)
    │     │
    │     └─▶ ErrorState renders
    │           └─▶ Message: "Entity not found"
    │                 └─▶ Button: "Back to Search"
    │
    ├─ ERROR (500 Server Error)
    │     │
    │     └─▶ ErrorState renders
    │           └─▶ Message: "Server error occurred"
    │                 ├─▶ Button: "Retry"
    │                 └─▶ Button: "Back to Search"
    │
    └─ ERROR (Network Failure)
          │
          └─▶ ErrorState renders
                └─▶ Message: "Network error"
                      ├─▶ Button: "Retry"
                      └─▶ Technical details (collapsible)

────────────────────────────────────────────────────────────────────

USER CLICKS: Retry button
    │
    └─▶ refetch()                          [React Query]
          │
          ├─▶ Show LoadingState
          │
          └─▶ Retry API call
                │
                ├─▶ Success → GraphVisualization
                └─▶ Failure → ErrorState again
```

---

## Performance Optimization Points

```
┌─────────────────────────────────────────────────────────────────┐
│                   Performance Optimizations                     │
└─────────────────────────────────────────────────────────────────┘

1. COMPONENT LEVEL
   ├─ React.memo() on all components
   ├─ useCallback() for event handlers
   ├─ useMemo() for computed values
   └─ Conditional rendering (prevent unnecessary mounts)

2. STATE MANAGEMENT
   ├─ Zustand: Selective subscriptions (only re-render on change)
   ├─ localStorage: Debounced writes (avoid blocking)
   └─ URL params: Replace instead of push (avoid history pollution)

3. DATA FETCHING
   ├─ React Query caching (5 min stale, 10 min gc)
   ├─ Automatic deduplication (same queries share result)
   ├─ Background refetching (keep data fresh)
   └─ Optimistic updates (instant UI feedback)

4. GRAPH RENDERING
   ├─ React Flow: Only render visible nodes
   ├─ Layout calculation: Memoized by algorithm
   ├─ Transform pipeline: Cached results
   └─ Filter operations: Optimized predicates

5. ANIMATIONS
   ├─ CSS transforms (GPU-accelerated)
   ├─ Will-change hints (prepare GPU layers)
   ├─ RequestAnimationFrame (smooth 60fps)
   └─ Debounced interactions (prevent jank)
```

---

## Bundle Size Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                      Bundle Size                                │
└─────────────────────────────────────────────────────────────────┘

KnowledgeGraphPage Module:
├─ KnowledgeGraphPage.tsx       14.2 KB
├─ LoadingState.tsx             1.1 KB
├─ ErrorState.tsx               3.8 KB
├─ EmptyState.tsx               5.1 KB
└─ index.ts                     0.5 KB
                              ─────────
    Total (uncompressed):      24.7 KB
    Gzipped (estimated):       ~6.2 KB

Dependencies (shared):
├─ @xyflow/react               ~150 KB (shared with GraphVisualization)
├─ @tanstack/react-query       ~40 KB (shared with all queries)
├─ react-router-dom            ~20 KB (shared with all routes)
├─ zustand                     ~3 KB (shared with store)
├─ react-hot-toast             ~15 KB (unique to this page)
└─ lucide-react               ~5 KB (shared, tree-shakeable)

TOTAL PAGE IMPACT: ~30 KB (after shared dependencies)
```

---

**Summary:**

This architecture provides:
- ✅ Clear component hierarchy
- ✅ Unidirectional data flow
- ✅ Predictable state management
- ✅ Robust error handling
- ✅ Performance optimizations
- ✅ Maintainable code structure

Ready for production deployment! 🚀
