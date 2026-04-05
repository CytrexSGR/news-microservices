# Knowledge Graph Page - Router Integration Guide

**Quick guide to integrate the KnowledgeGraphPage into your React app.**

---

## Step 1: Add Route to App.tsx

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { KnowledgeGraphPage } from '@/pages/knowledge-graph'

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000,   // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Existing routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/articles" element={<ArticlesPage />} />

          {/* ADD THIS: Knowledge Graph route */}
          <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
```

---

## Step 2: Add Navigation Link

```tsx
// src/components/Navigation.tsx
import { Link } from 'react-router-dom'
import { Home, FileText, Network } from 'lucide-react'

function Navigation() {
  return (
    <nav className="flex items-center gap-4">
      <Link to="/" className="flex items-center gap-2">
        <Home className="h-5 w-5" />
        <span>Home</span>
      </Link>

      <Link to="/articles" className="flex items-center gap-2">
        <FileText className="h-5 w-5" />
        <span>Articles</span>
      </Link>

      {/* ADD THIS: Knowledge Graph link */}
      <Link to="/knowledge-graph" className="flex items-center gap-2">
        <Network className="h-5 w-5" />
        <span>Knowledge Graph</span>
      </Link>
    </nav>
  )
}
```

---

## Step 3: Test in Browser

1. **Start dev server:**
   ```bash
   npm run dev
   ```

2. **Navigate to page:**
   ```
   http://localhost:3000/knowledge-graph
   ```

3. **Test features:**
   - ✅ Empty state shows
   - ✅ Search for entity (e.g., "Tesla")
   - ✅ Graph loads and renders
   - ✅ Detail panel opens on node click
   - ✅ Filters panel opens
   - ✅ URL updates to `?entity=Tesla`
   - ✅ Refresh keeps entity selected
   - ✅ Keyboard shortcuts work (`/`, `Esc`)

---

## Step 4: Link from Articles

```tsx
// src/components/ArticleCard.tsx
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Network } from 'lucide-react'

interface ArticleCardProps {
  article: Article
}

function ArticleCard({ article }: ArticleCardProps) {
  const navigate = useNavigate()

  const handleViewGraph = () => {
    // Extract main entity from article (or use article title)
    const entity = article.entities?.[0]?.name || article.title
    navigate(`/knowledge-graph?entity=${encodeURIComponent(entity)}`)
  }

  return (
    <div className="card">
      <h3>{article.title}</h3>
      <p>{article.summary}</p>

      {/* ADD THIS: View in Knowledge Graph button */}
      <Button
        onClick={handleViewGraph}
        variant="outline"
        size="sm"
        className="mt-4"
      >
        <Network className="mr-2 h-4 w-4" />
        View in Knowledge Graph
      </Button>
    </div>
  )
}
```

---

## Troubleshooting

### Issue: React Flow not rendering

**Solution:** Ensure `ReactFlowProvider` is wrapping the page:

```tsx
// Already included in KnowledgeGraphPage.tsx
<ReactFlowProvider>
  <div>...</div>
</ReactFlowProvider>
```

### Issue: Toast notifications not showing

**Solution:** Ensure `Toaster` component is rendered:

```tsx
// Already included in KnowledgeGraphPage.tsx
import { Toaster } from 'react-hot-toast'

<Toaster position="top-right" />
```

### Issue: Graph controls not working

**Solution:** Ensure React Flow CSS is imported:

```tsx
// Already included in GraphVisualization.tsx
import '@xyflow/react/dist/style.css'
```

### Issue: Store not persisting

**Solution:** Check localStorage permissions and Zustand persist config:

```tsx
// Already configured in graphStore.ts
persist(
  (set, get) => ({ ... }),
  { name: 'knowledge-graph-store' }
)
```

---

## Optional: Add to Main Menu

```tsx
// src/layouts/MainLayout.tsx
import { Outlet } from 'react-router-dom'
import Navigation from '@/components/Navigation'

function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <Navigation />
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
```

---

## API Configuration

Ensure your API client is configured correctly:

```typescript
// src/lib/api/client.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8111'

export const knowledgeGraphApi = {
  baseURL: `${API_BASE_URL}/api/v1`,
  // ... rest of config
}
```

---

## Environment Variables

Add to `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8111
VITE_ENABLE_KNOWLEDGE_GRAPH=true
```

---

## Next Steps

1. ✅ Add route to App.tsx
2. ✅ Add navigation link
3. ✅ Test in browser
4. ✅ Fix any import errors
5. ✅ Test all features
6. 📝 Write unit tests (Phase 3)
7. 📝 Write E2E tests (Phase 3)

---

**That's it!** The Knowledge Graph page is ready to use. 🚀
