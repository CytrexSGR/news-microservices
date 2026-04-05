# Knowledge Graph Public API Client - Usage Guide

## Quick Start

```typescript
import {
  searchEntities,
  findPath,
  getArticleEntities,
  getEntityConnections
} from '@/lib/api/knowledgeGraphPublic'
```

## API Functions

### 1. Entity Search (Autocomplete)

**Use Case:** Search bar, entity lookup, autocomplete dropdown

```typescript
// Basic search
const results = await searchEntities('Tesla')

// Search with limit
const results = await searchEntities('Elon', 20)

// Filter by entity type
const people = await searchEntities('Elon', 10, 'PERSON')
const orgs = await searchEntities('Tesla', 10, 'ORGANIZATION')

// Response structure
interface EntitySearchResponse {
  results: EntitySearchResult[]  // Matching entities
  total_results: number           // Count of results
  query_time_ms: number          // Query execution time
  query: string                  // Original query
  entity_type_filter: string | null  // Applied filter
}

interface EntitySearchResult {
  name: string              // "Tesla"
  type: string              // "ORGANIZATION"
  last_seen: string | null  // "2024-11-02T10:30:00Z"
  connection_count: number  // 45 (how connected this entity is)
  wikidata_id: string | null  // "Q478214" (if enriched)
}
```

**UI Example:**
```tsx
const [searchQuery, setSearchQuery] = useState('')
const [results, setResults] = useState<EntitySearchResult[]>([])

const handleSearch = async (query: string) => {
  if (query.length < 2) return
  const response = await searchEntities(query, 10)
  setResults(response.results)
}

return (
  <Autocomplete
    onInputChange={(_, value) => handleSearch(value)}
    options={results}
    getOptionLabel={(option) => option.name}
    renderOption={(props, option) => (
      <li {...props}>
        <span>{option.name}</span>
        <span className="text-sm text-gray-500">({option.type})</span>
        <span className="text-xs">{option.connection_count} connections</span>
      </li>
    )}
  />
)
```

---

### 2. Pathfinding Between Entities

**Use Case:** "How are these entities connected?", relationship discovery, network analysis

```typescript
// Find path between two entities
const paths = await findPath('Elon Musk', 'Tesla')

// Custom parameters
const paths = await findPath(
  'Elon Musk',    // Source entity
  'SpaceX',       // Target entity
  2,              // Max 2 hops
  5,              // Return top 5 paths
  0.7             // Only high-confidence relationships (≥0.7)
)

// Response structure
interface PathfindingResponse {
  paths: PathResult[]           // All found paths
  shortest_path_length: number  // Length of shortest path (hops)
  query_time_ms: number        // Query execution time
  entity1: string              // Source entity name
  entity2: string              // Target entity name
  max_depth: number            // Max depth searched
  total_paths_found: number    // Total paths found
}

interface PathResult {
  length: number                      // Path length (1 = direct connection)
  nodes: PathNode[]                   // Entities in path
  relationships: PathRelationship[]   // Connections between entities
}

interface PathNode {
  name: string  // "Elon Musk"
  type: string  // "PERSON"
}

interface PathRelationship {
  type: string           // "CEO_OF"
  confidence: number     // 0.95 (0.0-1.0)
  evidence: string | null  // "Elon Musk is CEO of Tesla"
}
```

**UI Example:**
```tsx
const [pathData, setPathData] = useState<PathfindingResponse | null>(null)

const findConnection = async (entity1: string, entity2: string) => {
  const result = await findPath(entity1, entity2, 3, 3, 0.5)
  setPathData(result)

  if (result.total_paths_found === 0) {
    toast.error(`No connection found between ${entity1} and ${entity2}`)
  } else {
    toast.success(`Found ${result.total_paths_found} paths, shortest: ${result.shortest_path_length} hops`)
  }
}

return (
  <div>
    {pathData?.paths.map((path, idx) => (
      <div key={idx} className="path-visualization">
        <h3>Path {idx + 1} ({path.length} hops)</h3>
        {path.nodes.map((node, i) => (
          <React.Fragment key={i}>
            <EntityNode entity={node} />
            {i < path.relationships.length && (
              <RelationshipEdge relationship={path.relationships[i]} />
            )}
          </React.Fragment>
        ))}
      </div>
    ))}
  </div>
)
```

---

### 3. Article Entities

**Use Case:** "What entities are mentioned in this article?", article analysis, entity highlighting

```typescript
// Get all entities from article
const entities = await getArticleEntities('abc123')

// Filter by entity type
const people = await getArticleEntities('abc123', 'PERSON', 20)
const orgs = await getArticleEntities('abc123', 'ORGANIZATION')

// Response structure
interface ArticleEntitiesResponse {
  article_id: string              // "abc123"
  article_title: string | null    // "Tesla Earnings Report Q3 2024"
  article_url: string | null      // "https://example.com/article"
  total_entities: number          // 15
  entities: ArticleEntity[]       // Extracted entities
  query_time_ms: number          // Query execution time
}

interface ArticleEntity {
  name: string                    // "Elon Musk"
  type: string                    // "PERSON"
  wikidata_id: string | null     // "Q317521"
  confidence: number             // 0.95 (extraction confidence)
  mention_count: number          // 5 (times mentioned in article)
  first_mention_index: number | null  // 234 (char index of first mention)
}
```

**UI Example:**
```tsx
const [articleEntities, setArticleEntities] = useState<ArticleEntity[]>([])

const loadArticleEntities = async (articleId: string) => {
  const response = await getArticleEntities(articleId, undefined, 50)
  setArticleEntities(response.entities)

  // Group by type for visualization
  const byType = response.entities.reduce((acc, entity) => {
    if (!acc[entity.type]) acc[entity.type] = []
    acc[entity.type].push(entity)
    return acc
  }, {} as Record<string, ArticleEntity[]>)

  console.log('People:', byType.PERSON?.length)
  console.log('Organizations:', byType.ORGANIZATION?.length)
  console.log('Locations:', byType.LOCATION?.length)
}

return (
  <div className="article-entities">
    <h3>{articleEntities.length} Entities Mentioned</h3>
    {articleEntities.map(entity => (
      <EntityTag
        key={entity.name}
        entity={entity}
        badge={`${entity.mention_count}x`}
        onClick={() => navigateToEntity(entity.name)}
      />
    ))}
  </div>
)
```

---

### 4. Entity Connections

**Use Case:** "Show all connections for this entity", entity detail page, relationship graph

```typescript
// Get all connections
const graph = await getEntityConnections('Tesla')

// Filter by relationship type
const employees = await getEntityConnections('Tesla', 'WORKS_FOR', 50)
const partners = await getEntityConnections('Tesla', 'PARTNERS_WITH')

// Response structure
interface GraphResponse {
  nodes: GraphNode[]        // Connected entities
  edges: GraphEdge[]        // Relationships
  total_nodes: number       // Count of nodes
  total_edges: number       // Count of relationships
  query_time_ms: number    // Query execution time
}

interface GraphNode {
  name: string              // "Elon Musk"
  type: string              // "PERSON"
  connection_count: number  // Total connections for this entity
}

interface GraphEdge {
  source: string              // "Elon Musk"
  target: string              // "Tesla"
  relationship_type: string   // "CEO_OF"
  confidence: number          // 0.95
  mention_count: number       // 12 (times mentioned together)
  evidence?: string           // Optional evidence text
}
```

**UI Example (D3/React-Flow Graph):**
```tsx
const [graphData, setGraphData] = useState<GraphResponse | null>(null)

const loadEntityGraph = async (entityName: string) => {
  const graph = await getEntityConnections(entityName, undefined, 100)
  setGraphData(graph)

  // Transform for D3.js visualization
  const d3Data = {
    nodes: graph.nodes.map(n => ({ id: n.name, type: n.type })),
    links: graph.edges.map(e => ({
      source: e.source,
      target: e.target,
      type: e.relationship_type,
      confidence: e.confidence
    }))
  }

  renderD3Graph(d3Data)
}

return (
  <div>
    <h2>Entity Network: {graphData?.total_nodes} connected entities</h2>
    <svg ref={svgRef} className="graph-visualization" />
    <div className="stats">
      <p>Total Connections: {graphData?.total_edges}</p>
      <p>Relationship Types: {new Set(graphData?.edges.map(e => e.relationship_type)).size}</p>
    </div>
  </div>
)
```

---

## Error Handling

All functions throw errors with meaningful messages:

```typescript
try {
  const results = await searchEntities('Tesla')
} catch (error) {
  // Error messages:
  // "Entity search failed: Resource not found in knowledge graph" (404)
  // "Entity search failed: Query timeout - try reducing max_depth or limit" (408)
  // "Entity search failed: Network error - cannot reach knowledge graph service"
  console.error(error.message)
}
```

**Recommended UI Pattern:**
```tsx
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

const handleSearch = async () => {
  setIsLoading(true)
  setError(null)

  try {
    const results = await searchEntities(query)
    // Handle success
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error')
    toast.error(error)
  } finally {
    setIsLoading(false)
  }
}
```

---

## Configuration

Set the knowledge graph service URL in `.env`:

```bash
# .env or .env.local
VITE_KG_API_URL=http://localhost:8111
```

**Default:** `http://localhost:8111` (used if env var not set)

---

## Performance Considerations

### Query Timeouts
- Default timeout: **30 seconds** (for complex graph queries)
- If you get 408 errors:
  - Reduce `max_depth` in pathfinding
  - Reduce `limit` parameter
  - Add more specific filters (entity_type, relationship_type)

### Response Sizes
- **Entity Search:** Returns max 100 entities (limit parameter)
- **Pathfinding:** Returns max 10 paths (limit parameter)
- **Article Entities:** Returns max 200 entities (limit parameter)
- **Entity Connections:** Returns max ~1000 connections (backend enforced)

### Caching Recommendations
```typescript
import { useQuery } from '@tanstack/react-query'

const { data, isLoading } = useQuery({
  queryKey: ['entity-search', query],
  queryFn: () => searchEntities(query, 10),
  enabled: query.length >= 2,
  staleTime: 5 * 60 * 1000  // 5 minutes
})
```

---

## Common Patterns

### Autocomplete Search with Debouncing
```tsx
import { useDebouncedCallback } from 'use-debounce'

const debouncedSearch = useDebouncedCallback(
  async (query: string) => {
    if (query.length < 2) return
    const results = await searchEntities(query, 10)
    setOptions(results.results)
  },
  300  // 300ms delay
)

<TextField
  onChange={(e) => debouncedSearch(e.target.value)}
  placeholder="Search entities..."
/>
```

### Entity Type Filters
```typescript
const ENTITY_TYPES = [
  { value: 'PERSON', label: 'People', icon: '👤' },
  { value: 'ORGANIZATION', label: 'Organizations', icon: '🏢' },
  { value: 'LOCATION', label: 'Locations', icon: '📍' },
  { value: 'EVENT', label: 'Events', icon: '📅' },
  { value: 'PRODUCT', label: 'Products', icon: '📦' }
]

const [selectedType, setSelectedType] = useState<string | undefined>()

const results = await searchEntities(query, 20, selectedType)
```

### Batch Loading Multiple Articles
```typescript
const loadMultipleArticles = async (articleIds: string[]) => {
  const results = await Promise.all(
    articleIds.map(id => getArticleEntities(id))
  )

  // Combine and deduplicate entities
  const allEntities = results.flatMap(r => r.entities)
  const uniqueEntities = Array.from(
    new Map(allEntities.map(e => [e.name, e])).values()
  )

  return uniqueEntities
}
```

---

## Testing

### Mock for Unit Tests
```typescript
import { vi } from 'vitest'

vi.mock('@/lib/api/knowledgeGraphPublic', () => ({
  searchEntities: vi.fn(async () => ({
    results: [
      { name: 'Tesla', type: 'ORGANIZATION', connection_count: 45 }
    ],
    total_results: 1,
    query_time_ms: 123
  })),
  findPath: vi.fn(async () => ({
    paths: [],
    shortest_path_length: 0,
    total_paths_found: 0
  }))
}))
```

---

## Related Files

- **Backend API:** `/services/knowledge-graph-service/app/api/routes/`
- **Admin Client:** `/frontend/src/lib/api/knowledgeGraphAdmin.ts`
- **Type Definitions:** Defined inline (or move to `/frontend/src/types/knowledgeGraphPublic.ts`)

---

## Support

- **Backend Swagger:** `http://localhost:8111/docs`
- **Health Check:** `http://localhost:8111/health/ready`
- **Service Status:** Check `docker compose ps knowledge-graph-service`
