# Frontend Architecture

**Last Updated:** 2025-10-21

## Tech Stack

### Core Framework
- **React:** 19.1.1
- **TypeScript:** 5.9.3
- **Vite:** 7.1.7 (Build tool & dev server)

### Routing
- **react-router-dom:** 7.9.4
  - Client-side routing
  - Route protection
  - URL-based navigation

### State Management
- **Zustand:** 5.0.8
  - Lightweight state management
  - Currently used for auth store only
  - Simple API, minimal boilerplate

### Data Fetching & Caching
- **@tanstack/react-query:** 5.90.5
  - Server state management
  - Automatic caching
  - Background refetching
  - Optimistic updates
  - Query invalidation

### HTTP Client
- **Axios:** 1.12.2
  - HTTP request library
  - Request/response interceptors
  - Automatic auth header injection

### UI Framework
- **Tailwind CSS:** 3.4.18
  - Utility-first CSS
  - Responsive design
  - Dark mode support

- **shadcn/ui:**
  - Component library based on Radix UI
  - Accessible components
  - Customizable with Tailwind

- **Radix UI:**
  - Headless UI primitives
  - Accessibility built-in

### Icons & Charts
- **lucide-react:** 0.546.0 (Icons)
- **recharts:** 3.3.0 (Charts & visualizations)

### Utilities
- **clsx:** 2.1.1 - Conditional classnames
- **tailwind-merge:** 3.3.1 - Merge Tailwind classes
- **class-variance-authority:** 0.7.1 - Component variants

## Directory Structure

```
frontend/
├── src/
│   ├── api/                    # API client instances
│   │   └── axios.ts           # authApi, feedApi, analysisApi, analyticsApi
│   │
│   ├── components/             # Shared components
│   │   ├── layout/            # Layout components
│   │   │   └── MainLayout.tsx # Sidebar + header layout
│   │   └── ui/                # shadcn/ui components
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       ├── tabs.tsx
│   │       └── ...
│   │
│   ├── features/               # Feature-based modules
│   │   ├── feeds/
│   │   │   ├── api/           # Feed API hooks
│   │   │   │   ├── useFeeds.ts
│   │   │   │   ├── useFeed.ts
│   │   │   │   ├── useUpdateFeed.ts
│   │   │   │   ├── useFeedItems.ts
│   │   │   │   ├── useArticleAnalysis.ts
│   │   │   │   ├── useAssessFeed.ts
│   │   │   │   └── ...
│   │   │   ├── components/    # Feed components
│   │   │   │   ├── AnalyticsSettings.tsx
│   │   │   │   ├── AssessmentHistoryTimeline.tsx
│   │   │   │   └── HealthScoreBadge.tsx
│   │   │   └── types/         # TypeScript types
│   │   │       └── index.ts   # Feed interface
│   │   │
│   │   ├── overview/
│   │   │   └── api/
│   │   │
│   │   ├── market/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types/
│   │   │
│   │   └── admin/
│   │       ├── content-analysis/
│   │       ├── feed-service/
│   │       ├── knowledge-graph/
│   │       └── fmp-service/
│   │
│   ├── pages/                  # Route pages
│   │   ├── LoginPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── FeedListPage.tsx
│   │   ├── FeedDetailPage.tsx
│   │   ├── ArticleListPage.tsx
│   │   ├── ArticleDetailPageV2.tsx
│   │   ├── MarketOverviewPage.tsx
│   │   └── admin/
│   │       ├── ContentAnalysisV2AdminPage.tsx
│   │       ├── FeedServiceAdminPage.tsx
│   │       ├── KnowledgeGraphAdminPage.tsx
│   │       └── FMPServiceAdminPage.tsx
│   │
│   ├── store/                  # Zustand stores
│   │   └── authStore.ts       # Authentication state
│   │
│   ├── lib/                    # Utilities
│   │   └── utils.ts           # Helper functions
│   │
│   ├── App.tsx                 # Root component & routing
│   ├── main.tsx                # Application entry point
│   └── index.css               # Global styles & Tailwind imports
│
├── public/                     # Static assets
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
├── tsconfig.json               # TypeScript base config
├── tsconfig.app.json           # App TypeScript config
├── tsconfig.node.json          # Node TypeScript config
├── postcss.config.js           # PostCSS configuration
├── components.json             # shadcn/ui configuration
├── package.json                # Dependencies & scripts
└── .env.local                  # Environment variables
```

## Architecture Patterns

### Feature-Based Organization
- Code organized by feature/domain (feeds, articles, market, admin)
- Each feature contains:
  - API hooks (`api/`)
  - UI components (`components/`)
  - TypeScript types (`types/`)

### API Layer Pattern

#### Axios Instances
```typescript
// src/api/axios.ts

// Separate instance per backend service
const authApi = axios.create({
  baseURL: import.meta.env.VITE_AUTH_API_URL
});

const feedApi = axios.create({
  baseURL: import.meta.env.VITE_FEED_API_URL
});

const analysisApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYSIS_API_URL
});

const analyticsApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYTICS_API_URL
});

// Auth interceptor adds token to all requests
addAuthInterceptor(authApi);
addAuthInterceptor(feedApi);
addAuthInterceptor(analysisApi);
addAuthInterceptor(analyticsApi);
```

#### React Query Hooks
```typescript
// Example: src/features/feeds/api/useFeeds.ts

export function useFeeds() {
  return useQuery({
    queryKey: ['feeds'],
    queryFn: async () => {
      const { data } = await feedApi.get('/feeds');
      return data;
    }
  });
}
```

### State Management Strategy

#### Server State
- **Managed by:** React Query
- **Usage:** API data, remote state
- **Features:** Caching, automatic refetching, optimistic updates

#### Client State
- **Managed by:** Zustand
- **Usage:** Authentication, UI state
- **Store:** `authStore` (accessToken, refreshToken, user, login, logout)

#### Local Component State
- **Managed by:** React useState
- **Usage:** Form inputs, UI toggles, temporary state

### Routing Architecture

```typescript
// src/App.tsx

<BrowserRouter>
  <Routes>
    {/* Public routes */}
    <Route path="/login" element={<LoginPage />} />

    {/* Protected routes */}
    <Route path="/" element={
      <ProtectedRoute>
        <MainLayout>
          <HomePage />
        </MainLayout>
      </ProtectedRoute>
    } />

    {/* ... more protected routes */}
  </Routes>
</BrowserRouter>
```

### Authentication Flow

1. **Login:** User enters credentials → `authStore.login()`
2. **Token Storage:** JWT tokens stored in Zustand authStore
3. **Request Interceptor:** Axios adds `Authorization: Bearer <token>` to all requests
4. **Protected Routes:** `ProtectedRoute` checks for token, redirects to `/login` if missing
5. **401 Handling:** Future improvement - auto-refresh or logout

## API Integration

### Environment Variables

Required in `.env.local` or `docker-compose.yml`:

```bash
VITE_AUTH_API_URL="http://localhost:8100/api/v1"
VITE_FEED_API_URL="http://localhost:8101/api/v1"
VITE_ANALYSIS_API_URL="http://localhost:8102/api/v1"
VITE_ANALYTICS_API_URL="http://localhost:8107/api/v1"
```

**IMPORTANT:** Vite requires `VITE_` prefix for env vars to be exposed to client.

### Backend Services

| Service | Port | Base Path | API Instance |
|---------|------|-----------|--------------|
| Auth Service | 8100 | `/api/v1` | `authApi` |
| Feed Service | 8101 | `/api/v1` | `feedApi` |
| Content Analysis | 8102 | `/api/v1` | `analysisApi` |
| Analytics Service | 8107 | `/api/v1` | `analyticsApi` |

### Request Flow

```
Component
  ↓
React Query Hook (useFeeds)
  ↓
Axios Instance (feedApi)
  ↓
Request Interceptor (add auth token)
  ↓
HTTP Request → Backend Service
  ↓
Response
  ↓
React Query Cache
  ↓
Component Re-render
```

## Styling Architecture

### Tailwind CSS
- Utility-first approach
- Responsive design with mobile-first breakpoints
- Dark mode support via `dark:` prefix

### shadcn/ui Components
- Pre-built accessible components
- Customizable via `components.json`
- Styled with Tailwind CSS
- Based on Radix UI primitives

### Theme Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // Toggle via class on <html>
  theme: {
    extend: {
      colors: {
        // Custom color palette
      }
    }
  }
}
```

## Performance Considerations

### Code Splitting
- Automatic code splitting via Vite
- Each route lazy-loaded (future improvement)

### React Query Caching
```typescript
{
  staleTime: 5 * 60 * 1000,  // 5 minutes
  cacheTime: 10 * 60 * 1000,  // 10 minutes
  refetchOnWindowFocus: false
}
```

### Build Optimization
- Vite's fast HMR (Hot Module Replacement)
- Tree-shaking for production builds
- CSS purging via Tailwind

## Development vs Production

### Development
- **Port:** 3000 (Docker) or 5173 (standalone)
- **Hot Reload:** Enabled via Vite HMR
- **Source Maps:** Enabled
- **React Query Devtools:** Enabled

### Production
- **Build:** `npm run build` → `dist/`
- **Minification:** Enabled
- **Source Maps:** Disabled
- **React Query Devtools:** Disabled

## Critical Files

### Configuration
- `vite.config.ts` - Build configuration, port settings, path aliases
- `tailwind.config.js` - Styling configuration
- `tsconfig.json` - TypeScript configuration
- `components.json` - shadcn/ui component config

### Entry Points
- `index.html` - HTML template
- `src/main.tsx` - JavaScript entry point
- `src/App.tsx` - Root React component

### Styles
- `src/index.css` - Global styles, Tailwind imports, CSS variables

## Dependencies Management

### Adding Dependencies

```bash
# In Docker
docker exec news-frontend npm install <package>

# Standalone
npm install <package>
```

**CRITICAL:** Always commit `package.json` and `package-lock.json` after adding dependencies!

### Dependency Categories

- **Core:** React, TypeScript, Vite
- **Routing:** react-router-dom
- **State:** Zustand, React Query
- **HTTP:** Axios
- **UI:** Tailwind, shadcn/ui, Radix UI, Lucide icons
- **Charts:** Recharts
- **Dev:** ESLint, TypeScript ESLint

## Future Improvements

1. **Lazy Loading:** Implement route-based code splitting
2. **Error Boundaries:** Add React error boundaries
3. **Service Worker:** PWA support for offline mode
4. **WebSocket:** Real-time updates instead of polling
5. **Unit Tests:** Jest + React Testing Library
6. **E2E Tests:** Playwright or Cypress
7. **Storybook:** Component documentation
8. **i18n:** Internationalization support
