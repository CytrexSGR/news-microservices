# Frontend Changelog

All notable changes to the News Microservices Frontend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed - 2025-11-06
- **Feed Pages Consolidation** (ADR-040)
  - **Consolidated** all feed management into Admin Feed Service page
  - **Enhanced** Feed Explorer tab with complete feature parity:
    - Added "Create Feed" button and dialog
    - Added "View Details" action (Eye icon) for feed detail navigation
    - Added "Rating" column with Admiralty Code badges
    - Added `admiralty_code` field to TypeScript types
  - **Routing Changes:**
    - Redirect `/feeds` → `/admin/services/feed-service?tab=explorer`
    - Fixed route order: `/feeds/:feedId` before `/feeds` (specificity matters!)
    - Implemented bidirectional URL/tab synchronization
  - **Navigation Update:**
    - Removed "Feeds" from primary navigation
    - Feed management now exclusively under "Admin → Feed Service"
  - **Deprecation:**
    - Moved `FeedListPage.tsx` to `src/pages/_deprecated/`
    - Added comprehensive deprecation notice with migration guide
    - Removed lazy import from App.tsx
  - **Benefits:**
    - Single source of truth for feed management
    - Cleaner primary navigation (one less item)
    - Better UX: Logical grouping of admin functions
    - Shareable URLs with tab state (`?tab=explorer`)
    - No maintenance burden from duplicate components

### Added - 2025-10-27
- **Content Analysis V2 Integration**
  - Complete migration from V1 sentiment analysis to V2 3-tier pipeline
  - New batch API endpoint: `POST /api/v2/pipeline-executions/batch`
  - React Query hook: `useArticlesV2Analysis()` with smart auto-refresh
  - Rich collapsible UI component: `ArticleV2AnalysisCard`
  - V2 analysis displays:
    - Priority score badge (color-coded by severity)
    - Category badge (GEOPOLITICS, ECONOMY, TECH, etc.)
    - Triage filtering explanation ("Why Filtered")
    - Tier 1: Summary, topics, key entities (with type, confidence, mentions)
    - Tier 2: Geopolitical analysis, bias detection, market impact
  - All sections default to collapsed for progressive disclosure
  - Consistent layout: V2 frame always visible (320px fixed width)
  - Auto-refresh: Polls every 10s for incomplete analyses, stops automatically when complete
  - Performance: Batch loading (1 API call for N articles)

### Changed - 2025-10-27
- **Article List Page** (`/articles`)
  - Removed all V1 sentiment analysis displays (SentimentBadge, sentiment filtering)
  - Replaced with comprehensive V2 analysis integration
  - Grid layout: 320px V2 analysis (left) + flexible article content (right)
  - V2 frame visible even for unanalyzed articles ("Processing..." state)

### Removed - 2025-10-27
- V1 sentiment analysis UI components from Article List Page
- V1 sentiment filter options
- V1 client-side filtering logic

### Added - 2025-10-22
- **Shared HTML Utilities Module**
  - Created `/lib/utils/htmlUtils.ts` with reusable functions:
    - `stripHtml()`: Multi-stage HTML cleaning with full JSDoc documentation
    - `getFirstSentences()`: Smart sentence extraction for previews
  - Used across ArticleListPage and FeedDetailPage
  - DRY principle: Single source of truth for HTML processing

- **Feed Detail Page Content Preview**
  - Applied same content preview technique as Article List Page
  - "Recent Articles" section now shows first 2 sentences
  - Visual styling with colored border and subtle background
  - Smart fallback: Uses `content` OR `description` field
  - Handles HTML from RSS feeds cleanly

- **Article List Page UX Improvements**
  - Auto-preview: First 2-3 sentences from scraped content now displayed prominently
  - Content preview with visual highlight (colored left border + background)
  - Dual original article links:
    - "View Original Article" link under title
    - "Read Original" button in action bar
  - Smart fallback: Uses `content` field or falls back to RSS `description`

- **Multi-Stage HTML Cleaning**
  - Enhanced `stripHtml()` function with 3-stage cleaning:
    1. DOM parsing (handles nested structures)
    2. Regex cleanup (removes artifacts)
    3. Whitespace normalization
  - Handles complex HTML from different feed sources:
    - Middle East Eye: Nested `<article>`, `<div>`, `<h2>` structures
    - Der Standard: Inline `<img style="...">` fragments
  - Decodes common HTML entities (&nbsp;, &amp;, etc.)
  - Universal solution - no feed-specific logic needed

### Changed - 2025-10-22
- Improved information hierarchy: Title → Original link → Metadata → Preview → Full content → Actions
- Content preview always visible (no collapse required)
- Better visual grouping with proper spacing
- Content preview now uses `content` OR `description` field (whichever is available)
- Removed HTML rendering from previews (clean text only)

### Improved - 2025-10-22
- Accessibility: All text now selectable (no longer embedded in images)
- Screen reader friendly with semantic HTML
- Proper `rel="noopener noreferrer"` attributes on external links
- Robust HTML handling for all RSS feed formats

### Fixed - 2025-10-22
- HTML artifacts appearing in article previews
- Complex nested HTML structures not properly cleaned
- Inline styles and attributes showing in text

## [Previous Versions]

### Added - 2025-10-21
- Feed Service Admin page with 3-tab interface
- Real-time service health monitoring
- Cross-feed article aggregation
- Advanced filtering system (feeds, dates, sentiment, category)
- Sentiment analysis display with collapsible details
- Analytics settings editor per feed
- Feed source assessment feature
- Assessment history timeline

### Added - 2025-10-20
- Initial production frontend deployment
- Authentication system (login, JWT)
- Dashboard management (list, create, edit, delete)
- Feed management (list, details, configuration)
- Article browsing and detail view
- Reports page
- Main layout with sidebar navigation
- Dark/light theme toggle
