# Frontend Features Inventory

**Last Updated:** 2025-10-27 (Content Analysis V2 Integration)
**Status:** Production - Fully Functional

## Overview

This document lists all implemented features, pages, components, and dependencies in the production frontend.

## Pages

### 1. LoginPage (`/login`)
- **File:** `src/pages/LoginPage.tsx`
- **Route:** Public (no auth required)
- **Features:**
  - Username/email + password authentication
  - JWT token management
  - Error handling and validation
  - Redirect to home after successful login

### 2. HomePage (`/`)
- **File:** `src/pages/HomePage.tsx`
- **Route:** Protected
- **Features:**
  - Dashboard overview
  - System metrics
  - Quick access links

### 3. Feed List Page (`/feeds`)
- **File:** `src/pages/FeedListPage.tsx`
- **Route:** Protected
- **Features:**
  - **Enhanced Data Table with Sorting:**
    - **Column Order:** Name, URL, Rating, Quality, Articles, Status, Health, Last Fetched, Fetches/Hour, Actions
    - **Sortable Columns (5 total):**
      - **Name** - Alphabetical, case-insensitive (A→Z / Z→A)
      - **Quality** - Numerical quality score (0→100 / 100→0)
      - **Articles** - Article count with thousand separators (0→∞ / ∞→0)
      - **Last Fetched** - Chronological timestamp, "Never" entries at end
      - **Fetches/Hour** - Calculated fetch frequency (0→∞ / ∞→0)
    - **Sort Behavior:**
      - 3-state cycle: Ascending → Descending → Neutral (no sort)
      - Visual indicators: ArrowUpDown (inactive), ArrowUp (asc), ArrowDown (desc)
      - Hover effect on sortable column headers
      - Click header to toggle sort state
    - **Calculated Columns:**
      - **Articles:** `total_items` with `.toLocaleString()` formatting
      - **Fetches/Hour:** `60 / fetch_interval` (e.g., 30min → 2.0/hour)
  - List all RSS feeds
  - Feed status indicators (active/paused)
  - Navigate to feed details
  - **Create New Feed (Multi-Step Wizard):**
    - **Step 1: Basic Information**
      - Feed URL (required, validated)
      - Feed name (required)
      - Description (optional)
      - Fetch interval slider (5-1440 minutes)
      - Categories (comma-separated)
    - **Step 2: Source Assessment (Optional)**
      - Run credibility assessment via research service
      - View assessment results:
        - Credibility tier (tier_1, tier_2, tier_3)
        - Reputation score (0-100)
        - Founded year
        - Organization type
        - Political bias
        - Editorial standards
        - Trust ratings
        - Recommendations
      - Auto-fill name, description, categories from assessment
      - Skip if not needed
    - **Step 3: Analysis Options**
      - Enable/disable 7 analysis types:
        - Article Categorization
        - Finance Sentiment Analysis
        - Geopolitical Sentiment Analysis
        - OSINT Event Analysis
        - Summary & Key Facts
        - Entity Extraction
        - Topic Classification
      - Batch controls: "Enable All" / "Disable All" buttons
      - All enabled by default
    - **Step 4: Scraping Options**
      - Enable/disable full content scraping
      - Scraping method selection:
        - Newspaper4k (recommended, NLP-based)
        - Playwright (experimental, browser automation)
      - Failure threshold slider (1-20 consecutive failures)
  - **Components:**
    - `CreateFeedDialog.tsx` - Main wizard orchestration
    - `FeedBasicInfoStep.tsx` - Step 1 component
    - `FeedAssessmentStep.tsx` - Step 2 component
    - `FeedAnalysisOptions.tsx` - Step 3 component
    - `ScrapingOptionsStep.tsx` - Step 4 component
  - **API Integration:**
    - `useCreateFeed` hook - Feed creation mutation
    - `usePreAssessFeed` hook - Source assessment
    - Pre-assessment endpoint: `POST /api/v1/feeds/pre-assess`
    - Feed creation endpoint: `POST /api/v1/feeds`

### 4. Feed Detail Page (`/feeds/:feedId`)
- **File:** `src/pages/FeedDetailPage.tsx`
- **Route:** Protected
- **Features:**
  - Feed configuration display
  - **Fetch Configuration (Editable):**
    - Fetch interval configuration (5-1440 minutes)
    - Human-readable interval display (e.g., "2h 30m", "1 hour")
    - Live preview: Fetches per day calculation
    - Quick presets: 15min, 30min, 1h, 2h, 6h, 12h
    - Intelligent recommendations based on interval
    - Edit/View toggle with Save/Cancel buttons
  - **Analytics Settings (Editable):**
    - Article Categorization
    - Finance Sentiment Analysis
    - Geopolitical Sentiment Analysis
    - OSINT Event Analysis
    - Summary & Key Facts
    - Entity Extraction
    - Topic Classification
  - **Scraping Configuration (Editable):**
    - Scraping method (newspaper4k/playwright)
    - Failure threshold (1-20)
    - Full content scraping toggle
    - Reset failures button
  - Feed Source Assessment
    - Run new assessment
    - View credibility tier
    - View reputation score
    - View political bias
    - Organization details
    - Editorial standards
    - Trust ratings
    - Recommendations
  - Assessment History Timeline
  - **Recent Articles with Content Preview:**
    - First 2 sentences automatically extracted
    - Visual styling with colored border and background
    - Smart fallback: Uses `content` OR `description` field
    - Clean HTML handling from RSS feeds
    - Click to navigate to article detail
  - Health overview
  - Fetch statistics

### 5. Article List Page (`/articles`)
- **File:** `src/pages/ArticleListPage.tsx`
- **Route:** Protected
- **Features:**
  - **Cross-feed article aggregation** - View articles from all feeds in one unified list
  - **Advanced filtering:**
    - **Feed selection (checkbox list):**
      - Scrollable checkbox list (max-height: 200px) for scalability (100+ feeds)
      - Individual checkboxes for each feed with hover effect
      - Separate "Clear" button for feed filter
      - Selection counter showing number of selected feeds
      - State managed in parent component (persistent during filter changes)
    - **Date range (from/to):** Independent date pickers for start and end dates
    - **Sentiment filter:** Toggle buttons for Positive, Negative, Neutral, Mixed
    - **Category filter:** Toggle buttons for 6 categories (Geopolitics & Security, Politics & Society, Economy & Markets, etc.)
    - **Filter panel:** Collapsible via "Filters" button, stays open during selections
    - **Active filter count badge** on Filters button
    - **"Clear All" button** to reset all filters at once
  - **Two-column layout:**
    - Left: Sentiment analysis block with collapsible details
    - Right: Article information (title, metadata, description)
  - **Sentiment display:**
    - Category classification with color-coded badges
    - Standard sentiment with confidence
    - Financial sentiment (market direction, volatility)
    - Geopolitical sentiment (stability score)
    - Collapsible detailed analysis
  - **Content features:**
    - **Auto-preview:** First 2-3 sentences from scraped content displayed prominently
      - Visual highlight with colored left border
      - No HTML rendering - clean text only
      - Automatically extracted using sentence boundary detection
      - Fallback to description if no scraped content
    - **Dual original article links:**
      - Prominent "View Original Article" link under title with icon
      - "Read Original" button in action bar
    - Scraped content indicator (green icon)
    - Collapsible full article text
    - Word count display
  - **Pagination:**
    - 20 articles per page
    - Previous/Next navigation
    - Page number display
  - **Sorting:** Newest articles first (by created_at - ingestion time, changed 2025-10-25)
  - **Timestamp display:**
    - **Dual timestamps:** Shows both "Added" (created_at) and "Published" (published_at)
    - **Smart scheduling detection:** Future-dated articles marked with "Scheduled" badge
    - **Clear context:** Users see when content entered system AND when it was originally published
  - **Hybrid filtering:** Server-side for feeds/dates, client-side for sentiment/category

### 6. Article Detail Page (`/articles/:itemId`)
- **File:** `src/pages/ArticleDetailPage.tsx`
- **Route:** Protected
- **Features:**
  - Article metadata display
  - Analysis results
  - Sentiment scores
  - Entity extraction results
  - Topic classification

## Admin Pages

### 7. Content Analysis Admin (`/admin/services/content-analysis`)
- **File:** `src/pages/admin/ContentAnalysisAdminPage.tsx`
- **Route:** Protected (Admin)
- **Features:**
  - Service health monitoring
  - Analysis queue status
  - Recent analysis activity
  - Performance metrics
  - Configuration management

### 8. Feed Service Admin (`/admin/services/feed-service`)
- **File:** `src/pages/admin/FeedServiceAdminPage.tsx`
- **Route:** Protected (Admin)
- **Features:**
  - **3-Tab Interface:**
    - **Live Operations Tab:**
      - Service Health Card (status, scheduler, version)
      - Scheduler Status Card (active jobs, next fetch)
      - Feed Stats Card (active feeds, total articles, articles today, 7-day trend)
      - Top Sources Card (ranked by article count)
    - **Feed Explorer Tab:**
      - Feed List Table (searchable, filterable by status/health)
      - Feed Health Chart (health score distribution)
      - Recent Items Table (latest scraped articles)
      - Assessment History Section (feed assessments, credibility tiers)
    - **Management & Controls Tab:**
      - Bulk Fetch Control (trigger fetch for all feeds)
      - Category Management (feeds per category)
      - Analysis Toggles (overview of enabled analysis features)
  - **Real-time Auto-refresh:**
    - Service health: 10s interval
    - Feed stats: 10s interval
    - Data refresh on tab focus
  - **Interactive Actions:**
    - Trigger individual feed fetch (RefreshCw button)
    - Trigger feed assessment (FileSearch button)
    - Bulk fetch all feeds
  - **Data Visualization:**
    - 7-day article trend mini-chart
    - Top 5 sources by article count
    - Feed status badges (ACTIVE, PAUSED, ERROR, INACTIVE)
    - Health score color coding

### 9. Knowledge Graph Admin (`/admin/services/knowledge-graph`)
- **File:** `src/pages/admin/KnowledgeGraphAdminPage.tsx`
- **Route:** Protected (Admin)
- **Status:** Phase 1 & 2 Complete, Phase 3 Planned
- **Features:**
  - **3-Tab Interface:**
    - **Live Operations Tab (✅ Phase 1):**
      - Service Health Card (overall status, Neo4j, RabbitMQ, uptime, version)
      - Graph Statistics Card (total nodes, relationships, graph density, top entity types)
      - Neo4j Health Card (connection status, version, edition, host)
      - RabbitMQ Health Card (consumer status, queue size, consumer count, routing key)
    - **Statistics & Analytics Tab (✅ Phase 2):**
      - Top Connected Entities Card (top 10 entities by connection count, entity types, sample connections)
        - **Entity Type Filter**: Dropdown to filter by specific entity types (PERSON, ORGANIZATION, LOCATION, PRODUCT, EVENT, DATE, MONEY, NOT_APPLICABLE)
        - Shows entity name, type badge, connection count, and sample connections
        - Auto-refresh every 60 seconds
      - Relationship Statistics Card (relationship type distribution, confidence scores, mention counts, percentage breakdown)
      - Growth History Chart (30-day timeline, daily new nodes/relationships, cumulative totals, Recharts visualization)
    - **Graph Explorer Tab (⏳ Phase 3):**
      - Entity search with autocomplete
      - Interactive graph visualization (react-force-graph)
      - Connections table
      - Relationship filtering
  - **Real-time Auto-refresh:**
    - Health checks: 10s interval
    - Graph statistics: 30s interval
    - Analytics data: 60s interval
  - **Technology:**
    - React Query for data fetching
    - Recharts for data visualization
    - Prometheus metrics integration
    - Kubernetes-compatible health checks
  - **API Integration:**
    - GET / - Basic service info
    - GET /health/ready - Service readiness
    - GET /health/neo4j - Neo4j connection details
    - GET /health/rabbitmq - RabbitMQ consumer status
    - GET /api/v1/graph/stats - Graph statistics
    - GET /api/v1/graph/analytics/top-entities - Top connected entities (Phase 2)
    - GET /api/v1/graph/analytics/growth-history - Historical growth data (Phase 2)
    - GET /api/v1/graph/analytics/relationship-stats - Relationship type distribution (Phase 2)

## Features by Module

### Feeds Module
**Location:** `src/features/feeds/`

#### API Hooks
- `useFeeds()` - Fetch all feeds
- `useFeed(feedId)` - Fetch single feed
- `useUpdateFeed()` - Update feed settings
- `useFeedItems(feedId)` - Fetch feed articles
- `useArticles(params)` - Fetch cross-feed articles with filtering
- `useArticleAnalysis(itemId)` - Fetch article analysis
- `useAssessFeed(feedId)` - Trigger feed source assessment
- `useAssessmentHistory(feedId)` - Fetch assessment history
- `useFeedHealth(feedId)` - Fetch feed health metrics

#### Components
- `FetchSettings` - Editable fetch interval configuration with presets and validation
- `ScrapingSettings` - Editable scraping configuration (method, threshold, enable/disable)
- `AnalyticsSettings` - Editable analytics configuration
- `AssessmentHistoryTimeline` - Assessment history visualization
- `HealthScoreBadge` - Feed health indicator
- `ArticleFilters` - Advanced filtering UI component
  - **Props:** `onFilterChange`, `initialFilters`, `showFilters`, `onToggleFilters`
  - **Feed filter:** Checkbox list with scroll (max-height: 200px), individual clear button
  - **Date filter:** Two date inputs (from/to)
  - **Sentiment filter:** Toggle buttons (4 options)
  - **Category filter:** Toggle buttons (6 options)
  - **State lifting:** Filter visibility managed by parent component
  - **Direct state updates:** No useEffect, immediate onFilterChange calls
- `SentimentBadge` - Reusable sentiment display with color coding (4 types: standard, finance, geopolitical, category)
- `ArticleCard` - Article display with two-column layout, sentiment block left, collapsible sections for details and content

### Overview Module
**Location:** `src/features/overview/`

#### API Functions
- `getOverviewMetrics()` - System overview metrics

### Feed Service Admin Module
**Location:** `src/features/admin/feed-service/`

#### API Client
**File:** `src/lib/api/feedServiceAdmin.ts`
- `getServiceHealth()` - Fetch service health status (/health)
- `getFeedStats()` - Dashboard statistics (/feeds/stats)
- `getFeedList(filters?)` - Fetch feeds with filtering (/feeds)
- `getFeedHealth(feedId)` - Individual feed health (/feeds/:id/health)
- `getFeedQuality(feedId)` - Feed quality metrics (/feeds/:id/quality)
- `getAssessmentHistory(feedId)` - Assessment history (/feeds/:id/assessment/history)
- `triggerFetch(feedId)` - Trigger feed fetch (/feeds/:id/fetch)
- `triggerAssessment(feedId)` - Trigger assessment (/feeds/:id/assess)
- `triggerBulkFetch(request)` - Bulk fetch operation (/feeds/bulk-fetch)
- `getRecentItems(limit)` - Recent scraped items (/feeds/items/recent)

#### API Hooks (React Query)
**Location:** `src/features/admin/feed-service/hooks/`
- `useServiceHealth(refetchInterval?)` - Auto-refresh service health
- `useFeedStats(refetchInterval?)` - Auto-refresh feed statistics
- `useFeedList(filters?)` - Fetch and filter feed list
- `useFeedHealth(feedId)` - Fetch feed health metrics
- `useFeedQuality(feedId)` - Fetch feed quality scores
- `useAssessmentHistory(feedId)` - Fetch assessment history
- `useTriggerFetch()` - Mutation: Trigger feed fetch with toast notifications
- `useTriggerAssessment()` - Mutation: Trigger assessment with toast
- `useBulkFetch()` - Mutation: Bulk fetch all feeds
- `useRecentItems(limit?)` - Fetch recent scraped items

#### Components

**Live Operations (Tab 1):**
- `ServiceHealthCard` - Service status, scheduler info, version
- `SchedulerStatusCard` - Active jobs, next scheduled fetch
- `FeedStatsCard` - Active feeds, total articles, today's articles, 7-day trend chart
- `QualityOverviewCard` - Top 5 sources by article count

**Feed Explorer (Tab 2):**
- `FeedListTable` - Searchable, filterable feed list with actions (fetch, assess)
- `FeedHealthChart` - Health score distribution visualization
- `RecentItemsTable` - Latest scraped items with scrape status
- `AssessmentHistorySection` - Feed assessments with credibility tiers

**Management & Controls (Tab 3):**
- `BulkFetchControl` - Bulk operations for all feeds
- `CategoryManagement` - Category statistics and distribution
- `AnalysisToggles` - Overview of analysis features enabled across feeds

#### TypeScript Types
**File:** `src/types/feedServiceAdmin.ts`
- `FeedStatus` - Enum: ACTIVE, PAUSED, ERROR, INACTIVE
- `ScrapeStatus` - Enum: success, error, timeout, paywall, pending
- `AssessmentStatus` - Enum: completed, failed, pending
- `FeedServiceHealth` - Service health response
- `FeedStats` - Dashboard statistics
- `FeedResponse` - Complete feed object
- `FeedHealthResponse` - Health metrics
- `FeedQualityResponse` - Quality scores
- `AssessmentHistoryResponse` - Assessment history
- `FeedItemWithFeedResponse` - Feed item with feed details
- `BulkFetchRequest/Response` - Bulk operation types

## Shared Components

### Layout
**Location:** `src/components/layout/`
- `MainLayout` - Main application layout with sidebar and header
  - Collapsible sidebar
  - Navigation menu (Home, Dashboards, Feeds, Articles, Reports)
  - User profile display
  - Theme toggle
  - Logout button

### UI Components
**Location:** `src/components/ui/`

Implemented shadcn/ui components:
- `Button` - Button component with variants
- `Card`, `CardHeader`, `CardTitle`, `CardContent` - Card components
- `Input` - Form input field
- `Label` - Form label
- `Badge` - Badge component with variants (used for filters, sentiment)
- `ThemeToggle` - Dark/light mode toggle
- `Collapsible` - Collapsible section
- `tabs` - Tabs component

**Custom Components:**

#### DataTable (`DataTable.tsx`)
**Location:** `src/components/ui/DataTable.tsx`

Advanced table component with built-in sorting capabilities:

**Props:**
```typescript
interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  keyExtractor: (row: T) => string
}

interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => ReactNode)
  cell?: (value: any, row: T) => ReactNode
  sortKey?: string              // Optional: Enable sorting for this column
  sortFn?: (a: T, b: T) => number  // Optional: Custom sort function
}
```

**Features:**
- **Client-side sorting:** useMemo-optimized for performance
- **3-state sorting:** Ascending → Descending → Neutral (original order)
- **Visual indicators:**
  - ArrowUpDown icon (inactive, 30% opacity)
  - ArrowUp icon (ascending)
  - ArrowDown icon (descending)
- **Smart sorting logic:**
  - Custom `sortFn` takes precedence
  - Default string comparison: Case-insensitive `.toLowerCase().localeCompare()`
  - Default number comparison: Standard subtraction
  - Default date comparison: `.getTime()` timestamp comparison
  - Null/undefined handling: Always sorted to end
- **UX enhancements:**
  - Cursor pointer on sortable columns
  - Hover effect (bg-muted-foreground/10)
  - User-select: none (prevents text selection during clicks)
- **Accessibility:**
  - Semantic table structure
  - Clear visual feedback
  - Keyboard accessible (clickable headers)

**Usage Example:**
```typescript
const columns: Column<Feed>[] = [
  {
    header: 'Name',
    accessor: 'name',
    sortKey: 'name',  // Enable default string sorting
  },
  {
    header: 'Quality',
    accessor: (row) => <QualityBadge score={row.quality} />,
    sortKey: 'quality',
    sortFn: (a, b) => (a.quality ?? 0) - (b.quality ?? 0),  // Custom sort
  },
]
```

**Technical Implementation:**
- useState for sort state (`sortKey`, `sortDirection`)
- useMemo for sorted data (only recalculates when data/sort changes)
- Icons from `lucide-react` (ArrowUpDown, ArrowUp, ArrowDown)
- Fully typed with TypeScript generics

**Performance:**
- Optimized with React.useMemo
- O(n log n) sorting complexity
- No unnecessary re-renders
- Handles large datasets (100+ rows tested)

### Utility Functions
**Location:** `src/lib/utils/`

#### HTML Utilities (`htmlUtils.ts`)
Shared utilities for HTML processing and text extraction, used across multiple pages:

- **`stripHtml(html: string): string`**
  - Multi-stage HTML cleaning for robust tag removal
  - **Stage 1:** DOM parsing (handles nested structures)
  - **Stage 2:** Regex cleanup (removes remaining artifacts)
  - **Stage 3:** Whitespace normalization and HTML entity decoding
  - Handles complex cases:
    - Nested HTML structures (e.g., Middle East Eye: `<article><div><h2>...`)
    - Inline styles and attributes (e.g., Der Standard: `<img style="...">`)
    - HTML entities (`&nbsp;`, `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#39;`)
    - Mixed HTML and text content
  - Returns clean plain text without HTML tags
  - **Used by:** ArticleListPage, FeedDetailPage

- **`getFirstSentences(text: string, count: number = 3): string`**
  - Extracts the first N sentences from text for preview
  - Automatically strips HTML before sentence extraction
  - Sentence detection handles: `.` `!` `?`
  - Returns first N sentences joined together
  - Falls back to full text if less than N sentences
  - **Used by:** ArticleListPage (3 sentences), FeedDetailPage (2 sentences)

**Benefits:**
- Single source of truth for HTML processing (DRY principle)
- Consistent preview behavior across all pages
- Reduced code duplication (77 lines → 2 imports per page)
- Universal solution - no feed-specific logic needed

### Authentication
- `ProtectedRoute` - Route guard for authenticated pages

## Dependencies

### Core
- **React:** 19.1.1
- **React DOM:** 19.1.1
- **TypeScript:** 5.9.3
- **Vite:** 7.1.7

### Routing & State
- **react-router-dom:** 7.9.4
- **zustand:** 5.0.8

### Data Fetching
- **@tanstack/react-query:** 5.90.5
- **axios:** 1.12.2

### UI & Styling
- **tailwindcss:** 3.4.18
- **lucide-react:** 0.546.0 (icons)
- **class-variance-authority:** 0.7.1
- **clsx:** 2.1.1
- **tailwind-merge:** 3.3.1

### Charts & Visualization
- **recharts:** 3.3.0

### Development Tools
- **@tanstack/react-query-devtools:** 5.90.2
- **eslint:** 9.36.0
- **typescript-eslint:** 8.45.0

## API Integration

### Configured Endpoints
- **AUTH_API:** Port 8100 (`/api/v1`) - Authentication service
- **FEED_API:** Port 8101 (`/api/v1`) - Feed management
- **ANALYSIS_API:** Port 8102 (`/api/v1`) - Content analysis
- **ANALYTICS_API:** Port 8107 (`/api/v1`) - Analytics service
- **KG_API:** Port 8111 - Knowledge Graph service

### Authentication
- JWT Bearer token authentication
- Token stored in Zustand authStore
- Automatic token injection via Axios interceptors
- Auto-redirect to login on 401

## Recent Additions

### ✅ Feed List Sorting & Enhanced Columns (2025-10-25)
**Objective:** Improve feed management UX with sortable columns and better data visibility

**Changes:**

1. **DataTable Component Upgrade** (`src/components/ui/DataTable.tsx`):
   - Added full sorting capabilities to generic DataTable component
   - **New Props:**
     - `sortKey?: string` - Enables sorting for column
     - `sortFn?: (a: T, b: T) => number` - Custom sort function
   - **Sort Features:**
     - 3-state cycle: Ascending → Descending → Neutral
     - Visual indicators with Lucide icons (ArrowUpDown, ArrowUp, ArrowDown)
     - Case-insensitive string sorting
     - Smart null/undefined handling
   - **UX:**
     - Hover effect on sortable columns
     - Cursor pointer for clickability
     - User-select: none to prevent text selection
   - **Performance:**
     - useMemo-optimized sorting (only recalculates on data/sort change)
     - Handles 100+ rows without performance issues

2. **Feed List Page Column Reorganization** (`src/pages/FeedListPage.tsx`):
   - **New Column Order:**
     - Name → URL → **Rating** → **Quality** → **Articles** → Status → Health → Last Fetched → **Fetches/Hour** → Actions
   - **Moved Columns:**
     - Rating: Position 6 → Position 3 (after URL)
     - Quality: Position 5 → Position 4 (after Rating)
     - Status: Position 3 → Position 6
     - Health: Position 4 → Position 7
   - **New Columns:**
     - **Articles** (Position 5): Shows `total_items` with thousand separators
     - **Fetches/Hour** (Position 9): Calculated as `60 / fetch_interval`
       - Example: 30min interval → "2.0" fetches/hour
       - Example: 15min interval → "4.0" fetches/hour

3. **Sortable Columns** (5 out of 10 columns):
   - **Name** (`sortKey: 'name'`):
     - Uses default string sorting (case-insensitive)
     - Alphabetical A→Z / Z→A
   - **Quality** (`sortKey: 'quality'`):
     - Custom `sortFn`: `(a.quality_score ?? 0) - (b.quality_score ?? 0)`
     - Numerical 0→100 / 100→0
   - **Articles** (`sortKey: 'articles'`):
     - Custom `sortFn`: `(a.total_items ?? 0) - (b.total_items ?? 0)`
     - Numerical with thousands separators
   - **Last Fetched** (`sortKey: 'last_fetched'`):
     - Custom `sortFn` with date parsing
     - Chronological (oldest→newest / newest→oldest)
     - "Never" entries always at end
   - **Fetches/Hour** (`sortKey: 'fetches_per_hour'`):
     - Custom `sortFn`: `(60/a.fetch_interval) - (60/b.fetch_interval)`
     - Numerical (slowest→fastest / fastest→slowest)

**User Impact:**
- ✅ Better feed discovery (sort by quality to find best sources)
- ✅ Better monitoring (sort by last fetched to find stale feeds)
- ✅ Better planning (see fetch frequency at a glance)
- ✅ Better data visibility (article counts with formatting)
- ✅ Intuitive UX (click headers to sort, visual feedback)

**Technical Highlights:**
- Generic TypeScript implementation (reusable for other tables)
- Performance-optimized with React hooks (useMemo, useState)
- Clean separation: DataTable handles sorting, pages define sort logic
- No breaking changes (backwards compatible - sorting is opt-in)

**Files Modified:**
- `frontend/src/components/ui/DataTable.tsx` (sorting implementation)
- `frontend/src/pages/FeedListPage.tsx` (column config + sort functions)
- `frontend/FEATURES.md` (this documentation)

### ✅ Knowledge Graph Admin Dashboard (2025-10-24)
- **New admin page:** `/admin/services/knowledge-graph`
- Complete monitoring dashboard for Knowledge Graph Service
- **Architecture:**
  - Feature-based folder structure (`features/admin/knowledge-graph`)
  - React Query hooks for data fetching with auto-refresh
  - API client with TypeScript types
  - 4 comprehensive health/stats cards
- **Phase 1 (Live Operations) - ✅ Complete:**
  - ServiceHealthCard: Overall status, uptime, version, Neo4j/RabbitMQ health
  - GraphStatsCard: Total nodes/relationships, density, top entity types
  - Neo4jHealthCard: Database connection, version, edition
  - RabbitMQHealthCard: Consumer status, queue size, routing info
- **Auto-refresh:**
  - Health checks: 10s interval
  - Graph statistics: 30s interval
- **API Integration:**
  - GET /health/ready - Service readiness with dependency checks
  - GET /health/neo4j - Neo4j connection details
  - GET /health/rabbitmq - RabbitMQ consumer status
  - GET /api/v1/graph/stats - Graph statistics (nodes, relationships, entity types)
  - GET / - Basic health with uptime
- **Phase 2 (Statistics & Analytics) - ⏳ Planned:**
  - Entity type distribution chart (Pie chart)
  - Growth trend visualization (Line chart)
  - Top connected entities table
  - Historical statistics
- **Phase 3 (Graph Explorer) - ⏳ Planned:**
  - Entity search with autocomplete
  - Interactive graph visualization (react-force-graph-2d)
  - Connections table with filters
  - Relationship exploration
- **Configuration:**
  - Added VITE_KG_API_URL to docker-compose.yml
  - Navigation link in MainLayout sidebar

### ✅ Fetch Interval Configuration (2025-10-23)
- **New component:** `FetchSettings.tsx` - Editable fetch interval configuration
- **Features:**
  - Fetch interval input with validation (5-1440 minutes)
  - Human-readable format display ("2h 30m", "1 hour", etc.)
  - Live preview: Automatic calculation of fetches per day
  - 6 Quick preset buttons:
    - 15 min (Breaking News)
    - 30 min (Active News)
    - 1 hour (Standard)
    - 2 hours (Moderate)
    - 6 hours (Low Priority)
    - 12 hours (Archive)
  - Intelligent recommendations based on selected interval
  - Edit/View toggle with Save/Cancel buttons
  - Loading states during updates
- **Integration:**
  - New collapsible section on Feed Detail Page
  - Positioned between "Feed Configuration" and "Scraping Configuration"
  - Uses existing `useUpdateFeed` hook for API updates
  - Follows same pattern as `ScrapingSettings` and `AnalyticsSettings`
- **Backend Integration:**
  - Uses `PUT /api/v1/feeds/{id}` endpoint
  - Validates against backend constraints (5-1440 minutes)
  - Real-time updates via React Query cache invalidation
- **UX Improvements:**
  - Removed read-only fetch interval from "Feed Configuration" card
  - Consolidated all editable settings into collapsible sections
  - Consistent design language across all configuration sections

### ✅ Shared HTML Utilities Module (2025-10-22)
- **Created `/lib/utils/htmlUtils.ts`** with reusable HTML processing functions
- **DRY principle implementation:**
  - Extracted duplicate code from multiple pages
  - Single source of truth for HTML cleaning
  - Reduced code duplication by 96% (77 lines → 2 imports per page)
- **Multi-stage HTML cleaning:**
  - Stage 1: DOM parsing (handles nested structures)
  - Stage 2: Regex cleanup (removes artifacts)
  - Stage 3: Whitespace normalization and HTML entity decoding
  - Handles complex HTML from different RSS feed sources
- **Smart sentence extraction:**
  - Boundary detection for `.`, `!`, `?`
  - Configurable sentence count
  - Automatic HTML stripping before extraction
- **Comprehensive JSDoc documentation:**
  - Full parameter descriptions
  - Return value documentation
  - Usage examples
  - Implementation details

### ✅ Feed Detail Page Content Preview (2025-10-22)
- **Applied content preview technique to Recent Articles section**
- **Features:**
  - First 2 sentences automatically extracted and displayed
  - Visual styling with colored left border and subtle background
  - Smart fallback: Uses `content` OR `description` field
  - Clean HTML handling from RSS feeds (uses shared htmlUtils)
  - Consistent with Article List Page design
- **Implementation:**
  - Uses shared `stripHtml()` and `getFirstSentences()` utilities
  - Same visual design language as Article List Page
  - Smaller preview (2 sentences vs 3 for list page)

### ✅ Article List Page UX Improvements (2025-10-22)
- **Enhanced content preview:**
  - Auto-extracted first 2-3 sentences displayed prominently
  - Visual highlight with colored left border and background
  - Clean text rendering without HTML tags (uses shared htmlUtils)
  - Smart sentence boundary detection (handles ., !, ?)
  - Fallback to RSS description if no scraped content
- **Improved original article access:**
  - "View Original Article" link directly under title
  - Additional "Read Original" button in action bar
  - Both open in new tab with proper rel attributes
- **Better information hierarchy:**
  - Title → Original link → Metadata → Content preview → Full content → Actions
  - Content preview always visible (no collapse required)
  - Full article remains collapsible for deep reading
- **Code improvements:**
  - Refactored to use shared HTML utilities
  - Improved layout with proper spacing and visual grouping
- **Accessibility:**
  - All text is selectable (no longer embedded in images)
  - Screen reader friendly with semantic HTML
  - Proper link attributes for external navigation

### ✅ Feed Service Admin (NEW)
- **New admin dashboard** at `/admin/services/feed-service`
- Complete feed service monitoring and management interface
- **Architecture:**
  - Feature-based folder structure (`features/admin/feed-service`)
  - React Query hooks for data fetching with auto-refresh
  - API client with proper endpoint handling (`/health` baseURL override)
  - TypeScript types matching actual API responses
- **Key Features:**
  - Real-time service health monitoring (10s refresh)
  - Live feed statistics with 7-day trend chart
  - Top 5 sources by article count
  - Searchable & filterable feed list
  - Individual feed actions (fetch, assess)
  - Bulk fetch all feeds
  - Recent scraped items table
  - Assessment history with credibility tiers
- **Components:** 11 total (4 Live Operations + 4 Feed Explorer + 3 Management)
- **Hooks:** 10 total (7 queries + 3 mutations)
- **API Integration:** 10 endpoints (health, stats, feeds, items, etc.)
- **Technical Highlights:**
  - Native HTML tables (shadcn table components not available)
  - Toast notifications for mutations (success/error)
  - Query invalidation for real-time updates
  - Proper error handling and loading states
  - Badge color coding for status visualization

### ✅ Articles Section (NEW)
- **New unified article listing page** at `/articles`
- Cross-feed article aggregation from all feeds
- Advanced filtering system:
  - **Feed filter:** Checkbox list (scrollable, scalable to 100+ feeds)
    - Individual checkboxes with hover effect
    - Separate "Clear" button for feeds
    - Selection counter
    - **State lifting pattern:** Filter panel visibility managed by parent component
    - Panel stays open during filter changes
  - **Date range picker:** From/to date inputs
  - **Sentiment filter:** Toggle buttons (4 options)
  - **Category filter:** Toggle buttons (6 categories)
  - **Active filter count badge** on Filters button
  - **"Clear All" button** to reset all filters
  - **Hybrid filtering:** Server-side (feeds/dates) + client-side (sentiment/category)
- Sentiment analysis display:
  - Two-column layout (sentiment left, article right)
  - Color-coded badges for all sentiment types
  - Collapsible detailed analysis
  - Standard, financial, and geopolitical sentiments
  - Category classification
- Content features:
  - Scraped content indicator (green icon)
  - Collapsible full article text
  - Word count display
  - Direct link to original source
- Pagination (20 items/page)
- Backend: New `GET /api/v1/feeds/items` endpoint
- Frontend components: `ArticleFilters`, `SentimentBadge`, `ArticleCard`
- **Technical improvements:**
  - useCallback for stable filter change handler
  - Direct state updates without useEffect
  - State lifting for persistent filter panel

### ✅ Analytics Settings Editable
- All 7 analytics flags now configurable per feed
- Edit/Save/Cancel functionality
- Real-time updates via React Query

### ✅ Article Navigation
- Click on article → Navigate to `/articles/:itemId`
- Article detail page shows full analysis

### ✅ Fixed Issues
- Import errors (analysisApi, feedApi)
- Route definitions
- Missing dependencies (@radix-ui/react-tabs)
- API URL configuration

### ✅ Article List Sorting & Timestamp Improvements (2025-10-25)
**Issue:** Articles sorted by `published_at` caused confusion with scheduled posts showing "in about 7 hours"

**Solution:** Changed to `created_at` (ingestion time) sorting with dual timestamp display

**Changes:**
- **Backend Default:** `GET /api/v1/feeds/items` now defaults to `sort_by=created_at` (DESC)
  - Shows newest-added articles first
  - `published_at` sorting still available via query parameter
  - See: `services/feed-service/app/api/feeds.py:188`

- **Frontend Hook:** `useArticles()` defaults to `sortBy='created_at'`
  - File: `frontend/src/features/feeds/api/useArticles.ts:29`

- **Dual Timestamp Display:** Article cards now show BOTH timestamps
  - **"Added X ago"** (bold) - When article entered system (`created_at`)
  - **"Published Y ago"** - When publisher released it (`published_at`)
  - **"Scheduled" badge** - Yellow badge for future-dated articles
  - File: `frontend/src/pages/ArticleListPage.tsx:332-370`

**User Experience:**
```
Normal article:
📅 Added 30 minutes ago • Published 8 hours ago • Author • 1,234 words

Scheduled article:
📅 Added 4 hours ago • [Scheduled] Published in 3 hours • BBC News
```

**Benefits:**
- ✅ Users see newest system activity first
- ✅ Clear distinction between ingestion and publication
- ✅ Future-dated articles clearly marked
- ✅ Both timestamps visible for complete context
- ✅ Backwards compatible via API parameter

**Documentation:** See ADR-021 for full decision rationale

## Known Limitations

- No offline support
- No PWA capabilities
- No real-time updates (uses polling via React Query)
- No image upload functionality

## Testing Status

- **Unit Tests:** Not implemented
- **Integration Tests:** Not implemented
- **E2E Tests:** Not implemented
- **Manual Testing:** ✅ Passed (2025-10-21)

### ✅ Content Analysis V2 Integration (2025-10-27)

**Migration:** Complete replacement of V1 sentiment analysis with V2 3-tier pipeline results

**Issue:** V1 analysis only provided basic sentiment scores. V2 provides comprehensive multi-tier analysis with triage filtering, entity extraction, geopolitical analysis, bias detection, and market impact assessment.

**Solution:** Integrated V2 pipeline execution results into Article List Page with rich collapsible UI

**Changes:**

#### Backend API (`services/content-analysis-v2/app/api/main.py`)
- **New Endpoint:** `POST /api/v2/pipeline-executions/batch`
  - Accepts array of article IDs
  - Returns dict mapping article_id → pipeline execution
  - Uses window functions for "latest per article" query
  - Efficient batch loading (1 query vs N queries)
  - File: `services/content-analysis-v2/app/api/main.py:122-194`

#### Frontend Hook (`frontend/src/features/feeds/api/useArticlesV2Analysis.ts`)
- **New Hook:** `useArticlesV2Analysis({ articleIds })`
  - Batch fetches V2 analysis for multiple articles
  - Smart auto-refresh: polls every 10s if analysis incomplete, stops when complete
  - 1-minute stale time for completed analyses
  - Returns `Record<article_id, PipelineExecutionV2>`
  - Base URL: `http://localhost:8111` (configurable via `VITE_ANALYSIS_V2_API_URL`)

#### Article List Page (`frontend/src/pages/ArticleListPage.tsx`)
- **Removed:** All V1 sentiment displays (SentimentBadge, sentiment filtering)
- **Added:** V2 analysis integration
  - Fetches V2 analysis for all articles in current page
  - Passes analysis to ArticleV2AnalysisCard component
  - **Consistent Layout:** V2 frame always visible (even for unanalyzed articles)
  - Grid layout: `320px` (V2 analysis) + `1fr` (article content)
  - File: `frontend/src/pages/ArticleListPage.tsx:36-107`

#### V2 Analysis Card (`frontend/src/features/feeds/components/ArticleV2AnalysisCard.tsx`)
- **Component:** `ArticleV2AnalysisCard` - Displays V2 pipeline results
- **Features:**
  - **Priority Score Badge:** Color-coded (red ≥80, orange ≥60, yellow ≥40, gray <40)
  - **Category Badge:** Styled by category (GEOPOLITICS, ECONOMY, TECH, etc.)
  - **Triage Decision Display:**
    - "Filtered" indicator for low-priority articles
    - "Why Filtered" reasoning (collapsible)
  - **Deep Analysis Display (for non-filtered articles):**
    - **Summary** (collapsible, Tier 1)
    - **Topics** (badge list, Tier 1)
    - **Key Entities** (collapsible, Tier 1)
      - Entity cards with type, description, confidence, mention count
      - Color-coded badges: PERSON (blue), ORGANIZATION (purple), LOCATION (green), EVENT (orange)
      - Up to 8 entities shown, with "+N more" indicator
    - **🌍 Geopolitical Analysis** (collapsible, Tier 2)
      - Stability score (color-coded: green ≥50%, yellow ≥0%, orange ≥-50%, red <-50%)
      - Conflict type, time horizon
      - Key factors (bullet list)
      - Affected parties (badge list)
    - **⚖️ Bias Detection** (collapsible, Tier 2)
      - Political bias score and direction (LEFT/RIGHT/NEUTRAL)
      - Loaded language examples with:
        - Original phrase
        - Bias direction (positive/negative)
        - Bias intensity percentage
        - Reasoning
        - Alternative neutral phrasing
      - Framing analysis (primary + secondary frames)
      - Balance score
    - **💰 Market Impact** (collapsible, Tier 2)
      - Market impact badge (POSITIVE/NEGATIVE/NEUTRAL)
      - Confidence score
      - Affected sectors (badge list)
      - Volatility level
      - Economic impact description
  - **All Sections Default:** Collapsed (user must expand to view details)
  - **Processing States:**
    - "Processing..." for articles without analysis yet
    - "Processing deep analysis..." for partial analysis
    - "Processing Failed" badge for failed analyses

**User Experience:**
```
Article Card Layout:
┌─────────────────────────────────────────────────────────┐
│ [V2 ANALYSIS]           │  [Article Info]              │
│ Priority: 75 (Filtered) │  BBC News                     │
│ Category: GEOPOLITICS   │  Breaking: Major Event...     │
│                         │  View Original Article ↗       │
│ [▼ Why Filtered]        │  📅 2 hours ago • Author       │
│                         │  Preview: First sentences...   │
│                         │  [View Full Analysis]          │
└─────────────────────────────────────────────────────────┘

V2 Analysis for High-Priority Article (expanded):
┌─────────────────────────────────────────────────────────┐
│ V2 ANALYSIS                                             │
│ Priority: 92                                            │
│ Category: GEOPOLITICS                                   │
│ ────────────────────────────────────────────────────    │
│ [▶ Summary]              (click to expand)              │
│ Topics: [Military] [Conflict] [Diplomacy]               │
│ [▶ Key Entities (12)]    (click to expand)              │
│ [▶ 🌍 Geopolitical Analysis]  (click to expand)          │
│ [▶ ⚖️ Bias Detection]         (click to expand)          │
│ [▶ 💰 Market Impact]          (click to expand)          │
└─────────────────────────────────────────────────────────┘
```

**Performance:**
- Batch API reduces query load (N articles = 1 API call vs N calls)
- Auto-refresh stops automatically when all analyses complete
- Collapsible sections reduce initial render complexity
- Skeleton loader provides feedback during processing

**API Configuration:**
- Default URL: `http://localhost:8111`
- Override via: `VITE_ANALYSIS_V2_API_URL` environment variable
- Docker compose: configured in `frontend` service environment
- Standalone: configured in `frontend/.env.local`

**Type Definitions:**
- `PipelineExecutionV2` interface in `frontend/src/features/feeds/types/analysisV2.ts`
- Includes: triage_decision, tier1_summary, tier2_summary, agents_executed, cost, timing

**Benefits:**
- **Richer Analysis:** Multi-dimensional analysis vs single sentiment score
- **Cost Efficiency:** Triage filtering saves ~75% of processing costs
- **Transparency:** Users see why articles were filtered or analyzed deeply
- **Detailed Insights:** Entity extraction, geopolitical context, bias detection, market impact
- **Progressive Disclosure:** Collapsible sections keep UI clean while providing depth
- **Consistent UX:** V2 frame always visible, no layout shifts

**Files Modified:**
- `frontend/src/pages/ArticleListPage.tsx` - V1 removal, V2 integration
- `frontend/src/features/feeds/components/ArticleV2AnalysisCard.tsx` - Complete redesign
- `frontend/src/features/feeds/api/useArticlesV2Analysis.ts` - New data fetching hook
- `services/content-analysis-v2/app/api/main.py` - SQL syntax fix for batch endpoint

**Related ADR:** `docs/decisions/ADR-016-v2-analysis-frontend-integration.md`

## Next Steps / Roadmap

1. Add comprehensive test suite
2. Implement real-time updates (WebSocket)
3. Add more chart types
4. Implement user management UI
5. Add bulk operations for feeds
6. Advanced filtering and search
