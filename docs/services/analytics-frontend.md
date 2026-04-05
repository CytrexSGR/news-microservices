# Analytics Frontend Documentation

## Overview

React-based frontend application for the News Analytics platform. Provides user interface for system monitoring, dashboard management, and report generation.

**Key Responsibilities:**
- Display real-time system overview metrics
- Manage custom user dashboards
- Generate and download reports (PDF/CSV)
- User authentication and session management
- Responsive UI with dark/light mode support

## Quick Start

### Prerequisites

- Node.js 18+
- npm 9+
- Access to backend services (auth, analytics, feed)

### Installation

```bash
# Navigate to frontend directory
cd /home/cytrex/analytics-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URLs

# Start development server
npm run dev

# Access application
# http://localhost:5173 (or next available port)
```

### Environment Configuration

Create `.env.local`:

```env
VITE_AUTH_API_URL=http://localhost:8100/api/v1
VITE_ANALYTICS_API_URL=http://localhost:8107/api/v1
VITE_FEED_API_URL=http://localhost:8101/api/v1
```

## Architecture

### Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.3.1 |
| Build Tool | Vite | 5.4.11 |
| Language | TypeScript | 5.6.3 |
| Styling | TailwindCSS | 3.4.15 |
| State Management | Zustand | 5.0.2 |
| Data Fetching | React Query | 5.62.7 |
| HTTP Client | Axios | 1.7.9 |
| Routing | React Router | 7.1.1 |
| UI Components | Radix UI + Custom | - |
| Icons | Lucide React | 0.469.0 |
| Grid Layout | react-grid-layout | 1.5.0 |
| Charts | Recharts | 2.15.0 |
| WebSocket | Native WebSocket API | - |

### Project Structure

```
analytics-frontend/
├── src/
│   ├── api/                    # API client configuration
│   │   └── axios.ts           # Axios instances with interceptors
│   ├── components/            # Reusable components
│   │   ├── ui/               # UI primitives (Button, Card, etc.)
│   │   ├── layout/           # Layout components (MainLayout)
│   │   └── shared/           # Shared business components
│   ├── features/              # Feature-based modules
│   │   ├── auth/             # Authentication logic
│   │   ├── dashboards/       # Dashboard management
│   │   │   ├── api/          # Dashboard API hooks
│   │   │   │   ├── getDashboards.ts
│   │   │   │   ├── getDashboard.ts
│   │   │   │   └── getWidgetData.ts    # Widget data with auto-refresh
│   │   │   └── components/   # Dashboard widgets
│   │   │       ├── WidgetGrid.tsx
│   │   │       ├── WidgetRenderer.tsx
│   │   │       ├── StatCard.tsx
│   │   │       ├── TimeSeriesChart.tsx
│   │   │       ├── BarChartWidget.tsx
│   │   │       └── PieChartWidget.tsx
│   │   ├── overview/         # System overview
│   │   │   └── api/          # Overview metrics API
│   │   └── reports/          # Report management
│   │       └── api/          # Reports API hooks
│   ├── pages/                 # Route-level pages
│   │   ├── LoginPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── DashboardListPage.tsx
│   │   ├── DashboardDetailPage.tsx  # With WebSocket integration
│   │   └── ReportsPage.tsx
│   ├── services/              # External services
│   │   └── websocketService.ts  # WebSocket client with reconnection
│   ├── store/                 # Zustand stores
│   │   └── authStore.ts      # Authentication state
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utilities
│   │   └── utils.ts          # Helper functions
│   ├── App.tsx               # Root component with routing
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles
├── public/                    # Static assets
├── .env.local                # Environment variables (not in git)
├── .env.example              # Environment template
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite build configuration
└── tailwind.config.js        # TailwindCSS configuration
```

### System Architecture

```
┌─────────────────┐
│   Browser       │
└────────┬────────┘
         │ HTTP
         v
┌─────────────────┐
│  Analytics UI   │
│  (React/Vite)   │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    v         v        v        v
┌────────┐ ┌────────┐ ┌────────┐
│Auth API│ │Feed API│ │Analytics│
│ :8100  │ │ :8101  │ │  :8107  │
└────────┘ └────────┘ └────────┘
```

## Application Routes

| Path | Component | Protected | Description |
|------|-----------|-----------|-------------|
| `/login` | LoginPage | No | User authentication |
| `/` | HomePage | Yes | System overview dashboard |
| `/dashboards` | DashboardListPage | Yes | List of user dashboards |
| `/dashboards/:id` | DashboardDetailPage | Yes | Dashboard detail view (MVP: skeleton) |
| `/reports` | ReportsPage | Yes | Reports list with download |

### Route Protection

All routes except `/login` require authentication. Protected routes check for valid JWT token in localStorage.

```typescript
<Route
  path="/"
  element={
    <ProtectedRoute>
      <MainLayout>
        <HomePage />
      </MainLayout>
    </ProtectedRoute>
  }
/>
```

## Features

### 1. Authentication

**Location:** `src/features/auth/`, `src/store/authStore.ts`

**Flow:**
1. User enters credentials on LoginPage
2. POST to `/api/v1/auth/login`
3. Store JWT token in localStorage
4. Update Zustand authStore with user data
5. Redirect to HomePage

**Logout:**
- Clears localStorage token
- Resets authStore
- Redirects to `/login`

### 2. System Overview (HomePage)

**Location:** `src/pages/HomePage.tsx`, `src/features/overview/api/`

**Metrics Displayed:**
- Total Users (from auth-service)
- Active Feeds (from feed-service)
- Total Articles
- Articles Today

**Data Sources:**
- `GET /api/v1/auth/stats` - User statistics
- `GET /api/v1/feeds/stats` - Feed statistics

**Update Frequency:** 60 seconds (staleTime)

### 3. Dashboard Management

**Location:** `src/pages/DashboardListPage.tsx`, `src/features/dashboards/api/`

**Features:**
- Grid layout (1/2/3 columns responsive)
- Card-based dashboard preview
- Click to navigate to detail view

**API:**
- `GET /api/v1/analytics/dashboards` - List all dashboards

**MVP Phase 1:** Read-only list view only. Detail page is placeholder.

### 4. Reports Management

**Location:** `src/pages/ReportsPage.tsx`, `src/features/reports/api/`

**Features:**
- DataTable with sortable columns
- Download button per report
- Status indicators (pending/completed/failed)
- Format badges (PDF/CSV)

**API:**
- `GET /api/v1/analytics/reports` - List all reports
- `GET /api/v1/analytics/reports/{id}/download` - Download file

**Download Flow:**
1. User clicks Download button
2. Fetch report as Blob (`responseType: 'blob'`)
3. Extract filename from `Content-Disposition` header
4. Create blob URL and trigger browser download
5. Cleanup blob URL

### 5. Dashboard Detail with Live Widgets

**Location:** `src/pages/DashboardDetailPage.tsx`, `src/features/dashboards/components/`, `src/features/dashboards/api/getWidgetData.ts`

**Features:**
- Dynamic widget grid with react-grid-layout
- Real-time data updates via React Query auto-refresh (30s interval)
- Auto-refresh indicator showing "Auto-refresh: 30s"
- Optimistic updates with placeholderData (no UI flicker during refresh)
- Support for multiple widget types (stat cards, line charts, bar charts, pie charts)

**Widget Types:**
- **StatCard**: Display single metrics with optional trend indicators
- **TimeSeriesChart**: Line charts for time-series data (using Recharts)
- **BarChartWidget**: Bar charts for categorical data
- **PieChartWidget**: Pie charts for distribution visualization

**Data Fetching Strategy:**
- React Query `useWidgetData` hook with automatic refetching every 30 seconds
- Query key: `['widget-data', dashboardId]`
- `placeholderData` keeps previous data during refetch (prevents UI flicker)
- Data structure: `{ [widgetId: string]: WidgetData }`
- Supports all widget types: stat_card, line_chart, bar_chart, pie_chart, table

**Dashboard Configuration:**
```typescript
interface Dashboard {
  id: string
  name: string
  description: string
  layout: {
    cols: number
    rowHeight: number
    compactType?: 'vertical' | 'horizontal' | null
  }
  widgets: WidgetConfig[]
}

interface WidgetConfig {
  id: string
  type: 'line_chart' | 'bar_chart' | 'stat_card' | 'pie_chart'
  title: string
  x: number  // Grid position
  y: number
  w: number  // Grid width
  h: number  // Grid height
  options?: {
    color?: string
    unit?: string
    format?: 'number' | 'currency' | 'percentage'
    [key: string]: any
  }
}
```

**Data Flow:**
1. Load dashboard configuration from API: `GET /api/v1/dashboards/{id}`
2. Fetch widget data: `GET /api/v1/dashboards/{id}/widgets/data`
3. Render widgets based on configuration
4. Auto-refresh widget data every 30 seconds via React Query
5. Clean up queries on unmount

**MVP Implementation:**
- Static grid layout (no drag & drop)
- Read-only widgets
- Auto-refresh every 30 seconds
- No UI flicker during refresh (placeholderData)

### 6. UI Components

**Base Components:** `src/components/ui/`
- Button - Multiple variants (default, ghost, outline, destructive)
- Card - Container with header/content sections
- Input - Form input with error states
- Skeleton - Loading placeholders
- DataTable - Generic table with custom columns
- ThemeToggle - Dark/Light mode switcher

**Layout Components:** `src/components/layout/`
- MainLayout - Sidebar + Header + Content
- Sidebar navigation with active state
- Collapsible sidebar (Desktop)

**Theme System:**
- ThemeProvider with localStorage persistence
- Dark/Light mode toggle
- CSS variables for colors
- All components fully compatible

## API Integration

### API Client Setup

**Location:** `src/api/axios.ts`

Three axios instances for different services:

```typescript
const authApi = axios.create({
  baseURL: import.meta.env.VITE_AUTH_API_URL,
})

const analyticsApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYTICS_API_URL,
})

const feedApi = axios.create({
  baseURL: import.meta.env.VITE_FEED_API_URL,
})
```

**Request Interceptor:**
- Automatically adds `Authorization: Bearer <token>` header
- Reads token from authStore

```typescript
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### React Query Integration

**Configuration:** `src/main.tsx`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})
```

**Usage Pattern:**

```typescript
// src/features/reports/api/getReports.ts
export const useReports = () => {
  return useQuery({
    queryKey: ['analytics', 'reports'],
    queryFn: getReports,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// In component
const { data: reports, isLoading, error } = useReports()
```

**Query Keys Convention:**
- `['analytics', 'overview']` - Overview metrics
- `['analytics', 'reports']` - Reports list
- `['analytics', 'dashboards']` - Dashboards list

### API Endpoints Used

**Auth Service (8100):**
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/stats` - User statistics

**Analytics Service (8107):**
- `GET /api/v1/analytics/overview` - System overview (planned)
- `GET /api/v1/dashboards` - List dashboards
- `GET /api/v1/dashboards/{id}` - Get dashboard configuration
- `GET /api/v1/dashboards/{id}/widgets/data` - Get widget data (auto-refresh every 30s)
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/{id}/download` - Download report

**Feed Service (8101):**
- `GET /api/v1/feeds/stats` - Feed statistics

## State Management

### Zustand Stores

**authStore** (`src/store/authStore.ts`)

```typescript
interface AuthState {
  accessToken: string | null
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
}
```

Persisted to localStorage with key: `auth-storage`

**Future:** Additional stores for dashboard state, preferences, etc.

### React Query Cache

Used for all server state:
- Automatic background refetching
- Cache invalidation on mutations
- Optimistic updates (future)

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Development Server

- **Hot Module Replacement (HMR)** - Instant updates without page reload
- **Fast Refresh** - Preserves component state during edits
- **TypeScript checking** - Real-time type errors in console

### Code Organization Patterns

**Feature-First Structure:**
```
features/
└── reports/
    └── api/
        ├── getReports.ts      # Query hook
        └── downloadReport.ts  # Mutation/action
```

**Type Definitions:**
- Colocated with API hooks
- Exported interfaces for reuse

```typescript
// getReports.ts
export interface Report {
  id: string
  name: string
  format: 'PDF' | 'CSV'
  status: 'pending' | 'completed' | 'failed'
  created_at: string
}
```

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_AUTH_API_URL` | Yes | Auth service base URL | `http://localhost:8100/api/v1` |
| `VITE_ANALYTICS_API_URL` | Yes | Analytics service base URL | `http://localhost:8107/api/v1` |
| `VITE_FEED_API_URL` | Yes | Feed service base URL | `http://localhost:8101/api/v1` |

**Note:** All environment variables must be prefixed with `VITE_` to be exposed to the client.

### TypeScript Configuration

**Compiler Options:**
- `strict: true` - Full type safety
- `verbatimModuleSyntax: true` - Explicit type imports
- Path aliases: `@/*` → `src/*`

**Type-Only Imports:**
```typescript
// Required with verbatimModuleSyntax
import { type ReactNode } from 'react'
import { type Column } from '@/components/ui/DataTable'
```

## Build & Deployment

### Production Build

```bash
npm run build
```

**Output:** `dist/` directory with optimized bundles

**Build Optimizations:**
- Tree-shaking (unused code removal)
- Minification (Terser)
- Code splitting (dynamic imports)
- Asset optimization (images, fonts)

### Build Configuration

**Vite Config:** `vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Environment-Specific Builds

```bash
# Development
npm run dev

# Production preview (local)
npm run build && npm run preview

# Production deployment
npm run build
# Deploy dist/ to web server
```

## Testing Strategy

**Current Status:** Tests not yet implemented

**Planned:**
- Unit tests: Vitest
- Component tests: React Testing Library
- E2E tests: Playwright
- Coverage target: 80%+

## Troubleshooting

### Common Issues

**White page / Blank screen**
- Check browser console for errors
- Verify backend services are running
- Check environment variables are set
- Run `npm run build` to catch TypeScript errors

**Login fails with 401 or ERR_CONNECTION_REFUSED**
- Verify `VITE_AUTH_API_URL` is correct
- Check auth-service is running: `curl http://localhost:8100/health`
- Use correct credentials: andreas / Aug2012#
- **IMPORTANT:** If accessing frontend via IP address (e.g., http://localhost:5173), you MUST use IP address in .env.local API URLs, NOT localhost
  - ❌ Wrong: `VITE_AUTH_API_URL=http://localhost:8100/api/v1` (when accessing via IP)
  - ✅ Correct: `VITE_AUTH_API_URL=http://localhost:8100/api/v1`
  - Restart Vite after changing .env.local: `kill <vite-pid> && PORT=5173 npm run dev`
  - Reason: `localhost` in browser points to user's machine, not server

**API calls return CORS errors**
- Backend services must allow frontend origin
- Check backend service logs for actual error (CORS might be symptom)
- Verify correct origin in docker-compose.yml CORS_ORIGINS (port 5173, not 5175 or others)

**Build errors: Type imports**
- Use `type` keyword for type-only imports
- Example: `import { type Column }` not `import { Column }`

**HMR not working**
- Restart dev server
- Check Vite log for errors
- Clear browser cache

**Widgets not displaying data**
- Check browser console for API errors
- Verify analytics-service is running: `curl http://localhost:8107/health`
- Check widget data API: `GET /api/v1/dashboards/{id}/widgets/data`
- Verify dashboard has widgets configured
- Check React Query DevTools for query status

**Widgets not auto-refreshing**
- Verify React Query is enabled for the dashboard page
- Check `refetchInterval: 30000` is set in useWidgetData hook
- Look for "Auto-refresh: 30s" indicator on dashboard page
- Check browser console for API calls every 30 seconds

**Dashboard shows "No widgets configured"**
- Verify dashboard has widgets in API response
- Check `GET /api/v1/analytics/dashboards/{id}` returns widgets array
- Verify dashboard.widgets.length > 0

### Debug Commands

```bash
# Check TypeScript compilation
npx tsc --noEmit

# Build with verbose output
npm run build -- --debug

# Check Vite cache
ls -la node_modules/.vite

# Clean and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Security Considerations

### Authentication
- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- Tokens expire after configured time
- Automatic logout on 401 responses

### API Security
- All protected routes require valid JWT
- CORS configured on backend
- No sensitive data in client-side code

### Environment Variables
- Never commit `.env.local`
- Use `.env.example` as template
- Backend URLs should use HTTPS in production

## Performance

### Current Metrics
- **Build size:** ~654 KB (gzipped: ~205 KB)
- **Initial load:** < 1s on localhost
- **HMR:** < 100ms

### Optimization Opportunities
- Code splitting by route (dynamic imports)
- Image optimization (if images added)
- Bundle size reduction (manual chunks)

## Implemented Features (MVP Complete)

✅ **Phase 1 Complete:**
- Dashboard list view with card grid
- Reports list with download functionality
- System overview with metrics
- Authentication flow
- Dark/Light mode support
- Responsive design

✅ **Phase 2 Complete:**
- ✅ Widget system for dashboards (StatCard, Line/Bar/Pie Charts, Table)
- ✅ Real-time data via React Query auto-refresh (30s interval)
- ✅ Widget data API with time-range filtering (24h, 7d, 30d)
- ⏳ Drag-and-drop dashboard builder (future enhancement)

## Future Enhancements

### Phase 3: Dashboard Customization
- Drag-and-drop widget positioning
- Widget resizing
- Dashboard creation/editing UI
- Widget configuration editor
- Dashboard templates

### Phase 4: Reports
- Report generation UI
- Custom report filters
- Scheduled reports
- Report templates

### Phase 5: Advanced Features
- User preferences
- Notification center
- Advanced analytics
- Multi-user collaboration
- Data export formats (Excel, JSON)

## Related Documentation

- [Documentation Guide](../guides/documentation-guide.md) - How to document
- [Analytics Service API](../api/analytics-api.md) - Backend API reference
- [Auth Service API](../api/auth-api.md) - Authentication endpoints
- [Development Workflow](../guides/DEVELOPMENT_WORKFLOW.md) - General dev guide

---

**Application Version:** 1.0.0 (MVP Phase 1 & 2 Complete)
**Default Port:** 5173 (Vite dev server)
**Last Updated:** 2025-10-19 (Widget Data API implemented)
**Status:** Production Ready (MVP)
