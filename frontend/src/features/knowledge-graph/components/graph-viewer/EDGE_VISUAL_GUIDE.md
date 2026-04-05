# Edge Components - Visual Design Guide

Visual reference for relationship edge styling based on confidence levels.

---

## 🎨 Confidence-Based Styling

### Color Coding

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  HIGH (0.7 - 1.0)                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━  🟢 Green (#10B981) │
│  "WORKS FOR" | HIGH (85%)                          │
│                                                     │
│  MEDIUM (0.4 - 0.7)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━  🔵 Blue (#3B82F6)    │
│  "LOCATED IN" | MEDIUM (55%)                       │
│                                                     │
│  LOW (0.0 - 0.4)                                   │
│  ━━━━━━━━━━━━━━━━━━━━━  ⚫ Gray (#6B7280)        │
│  "RELATED TO" | LOW (25%)                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📏 Stroke Width Progression

```
Confidence | Width  | Visual Representation
-----------|--------|--------------------------------------------
0.95       | 3.4px  | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0.75       | 3.0px  | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0.55       | 2.6px  | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0.35       | 2.2px  | ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0.15       | 1.8px  | ━━━━━━━━━━━━━━━━━━━━━━━━━━

Selected   | +1px   | (Add 1px to above width)
```

**Formula:** `strokeWidth = 1.5 + (confidence * 2)`

---

## 💫 Opacity Progression

```
Confidence | Opacity | Visual
-----------|---------|-------------------------------------
0.95       | 97%     | ████████████████████████████████████
0.75       | 85%     | ███████████████████████████████░░░░░
0.55       | 73%     | ██████████████████████████░░░░░░░░░░
0.35       | 61%     | ████████████████████░░░░░░░░░░░░░░░░
0.15       | 49%     | █████████████░░░░░░░░░░░░░░░░░░░░░░░

Selected   | 100%    | ████████████████████████████████████
```

**Formula:** `opacity = 0.4 + (confidence * 0.6)`

---

## 🏷️ Label Components

### When Edge is Selected

```
┌────────────────────────┐
│                        │
│   ╭──────────────╮    │  ← Relationship Type Badge
│   │  WORKS FOR   │    │    (Border color matches confidence)
│   ╰──────────────╯    │
│                        │
│   ╭────────────╮      │  ← Confidence Badge
│   │ HIGH (85%) │      │    (Outline style)
│   ╰────────────╯      │
│                        │
│  ╭─────────────────╮  │  ← Evidence Tooltip (if available)
│  │ Mentioned in 5  │  │    (Gray text, max-width: 320px)
│  │ articles...     │  │
│  ╰─────────────────╯  │
│                        │
└────────────────────────┘
```

### When Edge is NOT Selected
```
No labels shown (clean visualization)
```

---

## 🎬 Animation States

### Standard Edge (RelationshipEdgeComponent)
```
State: Default
─────────────────────────────────────
│ Smooth step path                   │
│ Static color based on confidence   │
│ Transition: all 0.2s ease         │
─────────────────────────────────────
```

### Animated Edge (AnimatedRelationshipEdge)
```
State: Pulsing (2s cycle)

Time: 0s
═══════════════════════════════════════
Gradient: [20%─────80%─────20%]

Time: 1s
═══════════════════════════════════════
Gradient: [80%─────20%─────80%]

Time: 2s (repeat)
═══════════════════════════════════════
Gradient: [20%─────80%─────20%]
```

**Animation Details:**
- Duration: 2000ms
- Easing: Linear (for smooth continuous animation)
- Stops: 3 (start, middle, end)
- Opacity range: 0.2 → 0.8 → 0.2

---

## 🔄 Selection States

### Standard Edge

```
NOT SELECTED:
━━━━━━━━━━━━━━━━━━━━━━━━
Opacity: 40-100% (confidence-based)
Width: 1.5-3.5px (confidence-based)
Labels: Hidden

SELECTED:
━━━━━━━━━━━━━━━━━━━━━━━━━━
Opacity: 100% (always)
Width: +1px (increased)
Labels: Visible
Transition: Smooth 0.2s
```

### Animated Edge

```
ALWAYS ANIMATED:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Opacity: 70-100% (confidence-based)
Width: 2-4px (confidence-based)
Gradient: Pulsing continuously
Labels: Not shown (for performance)
```

---

## 🎯 Edge Type Decision Matrix

```
Confidence Level | Edge Type | Reason
-----------------|-----------|--------------------------------
0.90 - 1.00      | animated  | Very high confidence, draw attention
0.80 - 0.89      | animated  | High confidence, highlight importance
0.40 - 0.79      | custom    | Medium confidence, standard display
0.00 - 0.39      | custom    | Low confidence, minimal prominence
```

**Code:**
```typescript
const edgeType = confidence >= 0.8 ? 'animated' : 'custom'
```

---

## 📐 Path Styles

### Smooth Step Path (Both Components)

```
Node A          Node B
  ●━━━┓
      ┃
      ┗━━━━━━●

Border Radius: 10px
Creates organic, curved transitions
```

**Why Smooth Step?**
- ✅ Avoids overlapping edges
- ✅ Better readability in dense graphs
- ✅ Professional appearance
- ✅ Clear directional flow

---

## 🎨 Color Reference

### Confidence Color Palette

```css
/* High Confidence */
.high-confidence {
  color: #10B981; /* Green-500 */
  description: "Verified, strong evidence";
}

/* Medium Confidence */
.medium-confidence {
  color: #3B82F6; /* Blue-500 */
  description: "Probable, moderate evidence";
}

/* Low Confidence */
.low-confidence {
  color: #6B7280; /* Gray-500 */
  description: "Possible, weak evidence";
}
```

### Badge Styles

```css
/* Relationship Type Badge */
.relationship-badge {
  background: white;
  border: 1px solid [confidence-color];
  color: [confidence-color];
  padding: 2px 8px;
  font-size: 0.75rem; /* 12px */
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Confidence Badge */
.confidence-badge {
  background: white;
  border: 1px solid [confidence-color];
  color: [confidence-color];
  padding: 0px 6px;
  font-size: 0.75rem; /* 12px */
  variant: outline;
}

/* Evidence Tooltip */
.evidence-tooltip {
  background: white;
  color: #4B5563; /* Gray-600 */
  padding: 4px 8px;
  font-size: 0.75rem; /* 12px */
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

---

## 🖱️ Interaction Guide

### Mouse Events

```
CLICK EDGE
  └─> Sets selected state
      └─> Shows labels
      └─> Increases opacity to 100%
      └─> Increases width by 1px

CLICK ELSEWHERE
  └─> Deselects edge
      └─> Hides labels
      └─> Restores confidence-based opacity
      └─> Restores confidence-based width
```

### Label Behavior

```
Edge Selected = TRUE
  ├─> Relationship Type: Visible
  ├─> Confidence Badge: Visible
  └─> Evidence Tooltip: Visible (if evidence exists)

Edge Selected = FALSE
  ├─> Relationship Type: Hidden
  ├─> Confidence Badge: Hidden
  └─> Evidence Tooltip: Hidden
```

---

## 📊 Visual Comparison

### Low vs High Confidence

```
LOW CONFIDENCE (0.25)
━━━━━━━━━━━━━━━━━━ (Gray, thin, semi-transparent)

HIGH CONFIDENCE (0.85)
━━━━━━━━━━━━━━━━━━━━━━━━━━━ (Green, thick, opaque)
```

### Static vs Animated

```
STATIC EDGE (confidence: 0.65)
━━━━━━━━━━━━━━━━━━━━━━━━ (Blue, constant)

ANIMATED EDGE (confidence: 0.85)
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌ (Green, pulsing)
```

### Selected vs Unselected

```
UNSELECTED
━━━━━━━━━━━━━━━━ (confidence-based opacity)

SELECTED
━━━━━━━━━━━━━━━━━━━ (100% opacity, +1px width)
   ╭──────────╮
   │ WORKS FOR│ (labels visible)
   ╰──────────╯
```

---

## 🎯 Best Practices

### When to Use Animated Edges
✅ **Use for:**
- Confidence ≥ 0.8
- Critical relationships
- Recently discovered connections
- User-highlighted paths

❌ **Avoid for:**
- Low confidence edges (visual noise)
- Dense graphs (performance impact)
- Print/export views (animation not visible)

### Label Display Strategy
✅ **Show labels:**
- On edge selection
- On user hover (future feature)
- In detail/focus mode

❌ **Hide labels:**
- In overview mode (too cluttered)
- For unselected edges
- In dense graph areas (>50 edges visible)

### Performance Optimization
✅ **Good practices:**
- Memoize components (already done)
- Use CSS animations (GPU-accelerated)
- Limit animated edges to <20% of total
- Hide labels when not selected

❌ **Avoid:**
- JavaScript-based animations
- Showing all labels simultaneously
- Animating low-confidence edges
- Complex gradient patterns

---

## 🚀 Future Enhancements

### Visual Improvements
1. **Hover state** - Temporary highlight without full selection
2. **Fade-in animation** - When edge first appears
3. **Directional indicators** - Show relationship direction explicitly
4. **Edge thickness slider** - User-controlled width multiplier

### Interactive Features
1. **Click-to-edit** - Inline confidence adjustment
2. **Drag-to-curve** - User-controlled path shape
3. **Double-click** - Show full evidence modal
4. **Right-click menu** - Edge-specific actions

### Performance
1. **LOD system** - Simplify edges when zoomed out
2. **Edge culling** - Hide off-screen edges
3. **Batch animations** - Group similar edges
4. **WebGL rendering** - For large graphs (>1000 edges)

---

**Last Updated:** 2025-11-02
**Components:** RelationshipEdgeComponent, AnimatedRelationshipEdge
