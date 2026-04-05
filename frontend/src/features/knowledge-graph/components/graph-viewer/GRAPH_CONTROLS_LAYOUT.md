# GraphControls Component Layout

## Visual Layout

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  GraphControls Toolbar                                                                 │
│  [White background, rounded borders, shadow, padding]                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────┐  ┌─────────────────────┐  ┌───────────────┐  │  ┌──────────────┐    │
│  │   Layout ▾   │  │ [-] │ [⊡] │ [+]    │  │ [👁] Labels   │  │  │ [⊙] Filters  │    │
│  │   Force      │  │ Zoom Out│Fit│Zoom In│  │ [  ] Legend   │  │  │              │    │
│  └──────────────┘  └─────────────────────┘  └───────────────┘  │  └──────────────┘    │
│  (Dropdown)        (Grouped buttons)          (Toggle buttons)  │  (Conditional)       │
│                                                                                         │
│  ┌───────────┐  │  ┌────────────────┐                                                  │
│  │ [↻] Reset │  │  │  Export ▾     │                                                   │
│  └───────────┘  │  │  • JSON        │                                                  │
│  (Only if        │  │  • PNG (4)     │                                                  │
│   filters         │  │  • SVG (4)     │                                                  │
│   active)         │  └────────────────┘                                                  │
│                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

Legend:
  ▾  = Dropdown indicator
  [👁] = Eye icon (show/hide)
  [⊙] = Filter icon with badge
  [↻] = Reset icon
  (4) = Phase 4 placeholder
  │  = Visual divider
```

---

## Control Groups Breakdown

### Group 1: Layout Selector
```
┌──────────────────┐
│  [≡] Force    ▾  │ ← Dropdown trigger
└──────────────────┘
        ↓
┌──────────────────────┐
│  Graph Layout        │ ← Dropdown menu
├──────────────────────┤
│  [□] Force-Directed  │ [Active]
│  [≡] Hierarchical    │
│  [↻] Radial          │
└──────────────────────┘
```

**Features:**
- Shows current layout in trigger button
- Active layout gets green "Active" badge
- Icons: Grid (Force), Layout (Hierarchical), RotateCcw (Radial)

---

### Group 2: Zoom Controls
```
┌─────────────────────────┐
│  [-] │ [⊡] │ [+]       │ ← Single bordered container
└─────────────────────────┘
 Zoom  Fit   Zoom
 Out   View  In
```

**Features:**
- 3 buttons in unified container
- 300ms smooth transitions
- React Flow integration
- Icons: ZoomOut, Maximize2, ZoomIn

---

### Group 3: View Toggles
```
┌────────────────┐  ┌────────────────┐
│  [👁] Labels   │  │    Legend      │
└────────────────┘  └────────────────┘
  Active state       Inactive state
  (default variant)  (outline variant)
```

**Features:**
- Labels: Shows Eye (visible) or EyeOff (hidden) icon
- Legend: Text only, no icon
- Active = default variant (filled)
- Inactive = outline variant

---

### Group 4: Filter Controls (Conditional)
```
┌──────────────────┐
│  [⊙] Filters     │  ← Only shows if onFilterToggle provided
│      [Active!]   │  ← Red badge if filters active
└──────────────────┘

┌──────────────────┐
│  [↻] Reset       │  ← Only shows if hasActiveFilters = true
└──────────────────┘
```

**Features:**
- Filter button always visible if `onFilterToggle` prop provided
- Red "Active" badge appears when filters applied
- Reset button conditionally rendered
- Red accent styling on reset for danger action

---

### Group 5: Export Menu
```
┌────────────────┐
│  [↓] Export ▾  │ ← Dropdown trigger
└────────────────┘
        ↓
┌──────────────────────────┐
│  Export Graph            │
├──────────────────────────┤
│  [↓] Export as JSON      │ ← Functional
│  [↓] Export as PNG (4)   │ ← Disabled (stub)
│  [↓] Export as SVG (4)   │ ← Disabled (stub)
└──────────────────────────┘
```

**Features:**
- JSON: Fully functional, downloads immediately
- PNG/SVG: Disabled with "(Phase 4)" label
- Loading state: "Exporting..." text
- Disabled during export operation

---

## Responsive Behavior

### Desktop (> 1024px)
```
[Layout] [Zoom Controls] [View Toggles] | [Filters] [Reset] | [Export]
```
All controls visible in single row

### Tablet (768px - 1024px)
```
[Layout] [Zoom] [View] | [Filters] | [Export]
[Reset] (wraps to second row)
```
Minor wrapping for reset button

### Mobile (< 768px)
```
[Layout] [Zoom]
[View] [Filters]
[Export]
```
Controls wrap to multiple rows

*Note: Explicit responsive breakpoints not implemented yet. Current flexbox with gap will naturally wrap.*

---

## State Management Integration

### Zustand Store Connections

```typescript
// Read from store
layoutType          → Shows in layout dropdown
showLabels          → Toggles Labels button state
showLegend          → Toggles Legend button state
hasActiveFilters    → Shows/hides reset button, badge

// Write to store
setLayoutType       → Layout dropdown items
toggleLabels        → Labels button click
toggleLegend        → Legend button click
resetFilters        → Reset button click
```

### React Flow Integration

```typescript
// React Flow hooks
useReactFlow()      → Get flow instance

// Methods used
zoomIn()            → Zoom in button
zoomOut()           → Zoom out button
fitView()           → Fit view button
getNodes()          → Export functions
getEdges()          → Export functions
```

---

## Toast Notifications

### Success Toasts
- "Zoomed in" (zoom in clicked)
- "Zoomed out" (zoom out clicked)
- "View fit to graph" (fit view clicked)
- "Layout changed to [type]" (layout changed)
- "Graph exported as JSON" (JSON export success)
- "Filters reset" (reset clicked)

### Error Toasts
- "No graph data to export" (empty graph)
- "Export failed: [error]" (export error)
- "PNG export coming in Phase 4" (PNG clicked)
- "SVG export coming in Phase 4" (SVG clicked)

---

## Accessibility Features

### Keyboard Navigation
- All buttons focusable with Tab
- Dropdowns open with Enter/Space
- Menu items navigable with arrows
- Escape closes dropdowns

### ARIA Attributes
- Button roles via shadcn/ui
- Dropdown menus with proper roles
- Disabled states announced
- Loading states announced

### Visual Indicators
- Focus rings on keyboard navigation
- Active states clearly visible
- Disabled items grayed out
- Color contrast WCAG AA compliant

### Screen Reader Support
- Title attributes on all buttons
- Icon buttons have text labels
- Dropdown labels announced
- State changes announced via toasts

---

## Performance Optimizations

### Zustand Selectors
```typescript
// Optimized selectors prevent unnecessary re-renders
const layoutType = useGraphStore(state => state.layoutType)
// Only re-renders when layoutType changes
```

### React Memoization
```typescript
// Local state only for export loading
const [isExporting, setIsExporting] = useState(false)
// Prevents full component re-render during export
```

### Conditional Rendering
```typescript
// Reset button only renders when needed
{hasActiveFilters && <Button>Reset</Button>}
// Reduces DOM nodes when not in use
```

---

## Testing Checklist

### Unit Tests
- [ ] Layout selection changes store state
- [ ] Zoom functions called with correct params
- [ ] View toggles update store
- [ ] Filter reset clears all filters
- [ ] Export functions handle errors gracefully

### Integration Tests
- [ ] Store changes trigger re-renders
- [ ] React Flow instance methods work
- [ ] Toast notifications appear
- [ ] Dropdown menus open/close

### E2E Tests
- [ ] User can change layout
- [ ] Zoom controls work visually
- [ ] View toggles affect graph display
- [ ] JSON export downloads file
- [ ] Phase 4 exports show warning

---

**Component Status:** ✅ Complete
**File:** `GraphControls.tsx`
**Exports:** Named export `GraphControls`, type export `GraphControlsProps`
**Dependencies:** React Flow, Zustand, shadcn/ui, Lucide icons, react-hot-toast
