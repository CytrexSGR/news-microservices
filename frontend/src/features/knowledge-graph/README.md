# Knowledge Graph Feature

Public-facing Knowledge Graph visualization and exploration.

## Components

### graph-viewer/
- `GraphVisualization.tsx` - Main React Flow canvas
- `NodeRenderer.tsx` - Custom entity node component
- `EdgeRenderer.tsx` - Custom relationship edge component
- `GraphControls.tsx` - Layout switcher, zoom, export controls
- `GraphLegend.tsx` - Entity type color legend

### entity-panel/
- `EntityDetails.tsx` - Selected entity information panel
- `EntityConnections.tsx` - List of entity connections
- `EntityMetadata.tsx` - Wikidata info, type details

### search/
- `EntitySearch.tsx` - Search bar with autocomplete
- `EntitySuggestions.tsx` - Search suggestion dropdown
- `RecentSearches.tsx` - Recent search history

### filters/
- `EntityTypeFilter.tsx` - Filter by entity type (multi-select)
- `RelationshipFilter.tsx` - Filter by relationship type
- `ConfidenceSlider.tsx` - Filter by confidence threshold

## Hooks

- `useEntityConnections.ts` - Fetch entity graph data
- `useEntitySearch.ts` - Search entities with debounce
- `useTopEntities.ts` - Get trending entities
- `useGraphLayout.ts` - Layout algorithm state

## Utils

- `graphTransformer.ts` - Transform API data to React Flow format
- `layoutEngine.ts` - Graph layout algorithms (force, hierarchical, radial)
- `colorScheme.ts` - Entity type color mapping
- `exportGraph.ts` - Export graph as PNG/SVG

## Usage

```typescript
import { KnowledgeGraphPage } from '@/features/knowledge-graph'
```
