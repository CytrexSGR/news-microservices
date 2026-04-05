# EntityDetails Component Structure

Visual guide to the EntityDetails side panel architecture.

---

## Component Hierarchy

```
EntityDetails (Main Container)
├── Header Section
│   ├── Title: "Entity Details"
│   └── Close Button (X icon)
│
├── Scrollable Content
│   ├── Entity Header Section
│   │   ├── Entity Name (h3)
│   │   ├── Entity Type Badge (colored)
│   │   ├── Wikidata Link (optional)
│   │   └── Connection Count
│   │
│   ├── Connections Section
│   │   ├── Section Title: "Connected To (N)"
│   │   └── Grouped Connections
│   │       └── For each relationship type:
│   │           ├── Group Header (collapsible)
│   │           │   ├── Chevron Icon (expand/collapse)
│   │           │   ├── Relationship Type
│   │           │   └── Count Badge
│   │           │
│   │           └── Group Content (when expanded)
│   │               ├── ConnectionItem (1)
│   │               ├── ConnectionItem (2)
│   │               ├── ...
│   │               ├── ConnectionItem (10)
│   │               └── "Load more" button (if >10)
│   │
│   └── Actions Section
│       ├── "Explore Connections" button
│       ├── "Find Path To..." button
│       └── "View in Neo4j" button (disabled)
│
└── Loading/Error/Empty States (conditional)
    ├── Loading: Spinner + "Loading entity details..."
    ├── Error: Error icon + message + Retry button
    └── Empty: "No entity selected" message
```

---

## ConnectionItem Sub-Component

```
ConnectionItem (Single Relationship Display)
├── Left Side (Target Entity Info)
│   ├── Entity Name (clickable, truncated)
│   └── Entity Type (small text)
│
└── Right Side (Confidence Indicator)
    ├── Confidence Percentage (color-coded)
    └── Confidence Dot (colored circle)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Action                              │
│                    (Click node in graph)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GraphVisualization                             │
│                   handleNodeClick(nodeId)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Zustand Store                                 │
│              setSelectedEntity(nodeId)                           │
│              detailPanelOpen = true (auto)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EntityDetails                                 │
│              Receives: entityName prop                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               useEntityConnections Hook                          │
│         Fetches: nodes[] + edges[] from API                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                React Query Cache                                 │
│           (5 min staleTime, 10 min gcTime)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              EntityDetails Component                             │
│         Groups edges by relationshipType                         │
│         Renders ConnectionItem for each                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Management

### Component State (Local)

```typescript
// EntityDetails.tsx
const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
// Tracks which relationship type groups are expanded
```

### Store State (Zustand)

```typescript
// graphStore.ts
interface GraphStore {
  selectedEntity: string | null        // Currently selected entity
  detailPanelOpen: boolean            // Panel visibility
  setSelectedEntity: (id: string) => void
  toggleDetailPanel: () => void
}
```

### Query State (React Query)

```typescript
// useEntityConnections hook
const {
  data: GraphResponse | undefined,   // Graph data (nodes + edges)
  isLoading: boolean,                 // Loading state
  error: Error | null,                // Error state
  refetch: () => void                 // Manual refetch
}
```

---

## Computed Values (useMemo)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Raw Data (from API)                           │
│             nodes: GraphNode[]                                   │
│             edges: GraphEdge[]                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               selectedNode (useMemo)                             │
│         Find node matching selectedEntity                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│           groupedConnections (useMemo)                           │
│      Group edges by relationshipType                             │
│      {                                                            │
│        "WORKS_FOR": [connection1, connection2, ...],            │
│        "LOCATED_IN": [connection3, connection4, ...],           │
│        ...                                                        │
│      }                                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│          sortedRelationshipTypes (useMemo)                       │
│      Sort by connection count (descending)                       │
│      ["WORKS_FOR", "LOCATED_IN", "PART_OF", ...]                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            totalConnections (useMemo)                            │
│      Sum all connections across groups                           │
│      47 connections                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Event Flow

### Click Connection → Switch Entity

```
User clicks ConnectionItem
    ↓
ConnectionItem.onClick(targetEntity)
    ↓
EntityDetails.handleConnectionClick(targetEntity)
    ↓
useGraphStore.setSelectedEntity(targetEntity)
    ↓
React Query invalidates cache + refetches
    ↓
EntityDetails re-renders with new entity
    ↓
Panel shows new entity details
```

### Expand/Collapse Group

```
User clicks Group Header
    ↓
EntityDetails.toggleGroup(relationshipType)
    ↓
setExpandedGroups((prev) => {
  if (prev.has(type)) {
    prev.delete(type)  // Collapse
  } else {
    prev.add(type)     // Expand
  }
  return new Set(prev)
})
    ↓
React re-renders group (smooth animation)
```

### Close Panel

```
User clicks X button OR presses Esc key
    ↓
EntityDetails.handleClose()
    ↓
onClose() callback
    ↓
useGraphStore.toggleDetailPanel()
    ↓
detailPanelOpen = false
    ↓
Panel unmounts with slide-out animation
```

---

## CSS Classes Structure

### Panel Container

```css
.fixed                    /* Fixed positioning */
.right-0                  /* Align to right */
.top-0                    /* Align to top */
.h-full                   /* Full height */
.w-[400px]                /* 400px width (desktop) */
.max-md:w-full            /* Full width (mobile) */
.bg-background            /* Theme background */
.border-l                 /* Left border */
.shadow-lg                /* Drop shadow */
.z-50                     /* High z-index (above graph) */
.animate-in               /* Animation utility */
.slide-in-from-right      /* Slide animation */
.duration-300             /* 300ms duration */
```

### Group Header (Collapsible Trigger)

```css
.w-full                   /* Full width */
.flex                     /* Flexbox */
.items-center             /* Vertical center */
.justify-between          /* Space between */
.p-3                      /* Padding */
.hover:bg-muted/50        /* Hover background */
.transition-colors        /* Smooth transition */
.focus:outline-none       /* Remove outline */
.focus:ring-2             /* Focus ring */
.focus:ring-primary       /* Primary color ring */
```

### ConnectionItem

```css
.w-full                   /* Full width */
.p-3                      /* Padding */
.text-left                /* Left-aligned text */
.hover:bg-muted           /* Hover background */
.transition-colors        /* Smooth transition */
.group                    /* Group for child selectors */
.focus:ring-2             /* Focus ring */
.group-hover:text-primary /* Text color on group hover */
```

---

## Accessibility Features

### ARIA Attributes

```html
<!-- Panel -->
<div role="dialog" aria-labelledby="entity-details-title" aria-modal="true">

<!-- Close Button -->
<Button aria-label="Close panel">

<!-- Collapsible Group -->
<button aria-expanded={isExpanded} aria-controls={`group-${type}`}>
<div id={`group-${type}`}>

<!-- ConnectionItem -->
<button aria-label={`View details for ${targetEntity}`}>

<!-- Confidence Indicator -->
<div title="Confidence: High (92%)" aria-label="Confidence: High">
```

### Keyboard Navigation

- **Tab** - Move focus between interactive elements
- **Enter/Space** - Activate focused button/link
- **Esc** - Close panel
- **Arrow Keys** - (Future) Navigate between connections

### Focus Management

- Focus trap within panel (prevents tabbing out)
- Visible focus indicators (ring-2 ring-primary)
- Logical tab order (top to bottom)

---

## Responsive Breakpoints

### Desktop (≥768px)

```
┌─────────────────────────────────────────────┬───────────┐
│                                             │           │
│         Graph Visualization                 │  Entity   │
│                                             │  Details  │
│                                             │  Panel    │
│         (compressed to fit)                 │  (400px)  │
│                                             │           │
└─────────────────────────────────────────────┴───────────┘
```

### Mobile (<768px)

```
┌───────────────────┐
│                   │
│   Entity Details  │
│      Panel        │
│   (full-screen)   │
│                   │
└───────────────────┘

(Graph hidden behind panel)
```

---

## Performance Optimizations

### 1. React.memo

```typescript
export const EntityDetails = memo(function EntityDetails({ ... }) {
  // Only re-renders when props change
})

export const ConnectionItem = memo(function ConnectionItem({ ... }) {
  // Only re-renders when connection data changes
})
```

### 2. useMemo (Computed Values)

```typescript
const selectedNode = useMemo(() => {
  // Expensive: Find node in large array
  return graphData.nodes.find(node => node.id === entityName)
}, [graphData, entityName])

const groupedConnections = useMemo(() => {
  // Expensive: Group edges by type
  // Only recalculates when graphData or entityName changes
}, [graphData, entityName])
```

### 3. useCallback (Stable References)

```typescript
const handleClose = useCallback(() => {
  onClose()
  setSelectedEntity(null)
}, [onClose, setSelectedEntity])
// Reference stays stable, prevents child re-renders
```

### 4. Conditional Fetching

```typescript
useEntityConnections(entityName, {
  enabled: !!entityName && detailPanelOpen
  // Only fetches when both conditions true
  // Prevents unnecessary API calls
})
```

### 5. React Query Caching

```typescript
staleTime: 5 * 60 * 1000,  // 5 minutes
gcTime: 10 * 60 * 1000,    // 10 minutes
// Reduces duplicate network requests
// Instant data when navigating back to entity
```

---

## File Size Breakdown

| File | Lines | Purpose |
|------|-------|---------|
| EntityDetails.tsx | 454 | Main panel component |
| ConnectionItem.tsx | 96 | Relationship display |
| index.ts | 8 | Exports |
| **Total** | **558** | **TypeScript code** |

---

## Dependencies

### External Packages

```json
{
  "react": "^19.0.0",
  "lucide-react": "^0.x.x",
  "@tanstack/react-query": "^5.x.x",
  "zustand": "^4.x.x",
  "tailwindcss": "^3.x.x"
}
```

### Internal Dependencies

```typescript
// UI Components
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'

// Hooks
import { useEntityConnections } from '../../hooks/useEntityConnections'

// Store
import { useGraphStore } from '../../store/graphStore'

// Utils
import { ENTITY_TYPE_COLORS, getEntityTypeDisplayName, getConfidenceColor, getConfidenceLabel } from '../../utils/colorScheme'
import { cn } from '@/lib/utils'

// Types
import type { GraphEdge, GraphNode } from '@/types/knowledgeGraphPublic'
```

---

**Last Updated:** 2025-11-02
**Component Version:** 1.0.0
**Status:** ✅ Production Ready
