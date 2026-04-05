# Feed Creation Wizard

**Created:** 2025-10-23
**Status:** Production Ready
**Feature Type:** Frontend + Backend Integration
**Location:** `/feeds` → "Create Feed" button

## Overview

The Feed Creation Wizard is a multi-step dialog that guides users through creating a new RSS/Atom feed with comprehensive configuration options. It integrates with the research service to provide optional source credibility assessment before feed creation.

## User Journey

### 1. Entry Point
- User navigates to `/feeds` (Feed List Page)
- Clicks the "Create Feed" button in the top-right corner
- Multi-step wizard dialog opens (4 steps)

### 2. Step 1: Basic Information
**Purpose:** Collect essential feed metadata

**Fields:**
- **Feed URL** (required)
  - Validation: Must be valid HTTP/HTTPS URL
  - Format: `https://example.com/rss`
  - Error messages in German
- **Feed Name** (required)
  - Auto-filled from assessment if run
  - Max 200 characters
  - Blue badge indicator when auto-filled
- **Description** (optional)
  - Auto-filled from assessment if run
  - Max 500 characters
  - Multiline textarea
- **Fetch Interval**
  - Slider: 5-1440 minutes
  - Default: 60 minutes
  - Shows current value next to slider
- **Categories** (optional)
  - Comma-separated input
  - Auto-filled from assessment if run
  - Example: "Technology, News, Blog"

**Navigation:**
- "Next" button → Step 2
- "Cancel" button → Close dialog

### 3. Step 2: Source Assessment (Optional)
**Purpose:** Evaluate feed source credibility before creation

**Actions:**
- **"Run Assessment" button**
  - Enabled only when valid URL provided
  - Shows loading spinner during assessment
  - Calls research service via `POST /api/v1/feeds/pre-assess`
  - Polling mechanism: max 30 seconds (15 attempts × 2s)

**Assessment Results Display:**
- **Credibility Tier** (badge)
  - tier_1: Green badge
  - tier_2: Yellow badge
  - tier_3: Orange badge
- **Reputation Score** (0-100 with star icon)
- **Political Bias** (colored badge based on bias)
- **Founded Year**
- **Organization Type**
- **Editorial Standards**
  - Fact checking level
  - Corrections policy
  - Source attribution
- **Assessment Summary** (blue info box)
- **Recommendations** (green success box)
  - Skip waiting period
  - Initial quality boost
  - Bot detection threshold

**Auto-Fill Behavior:**
- Only fills empty fields
- Preserves user edits
- Shows blue "Auto-filled" badge on affected fields
- Updates: name, description, categories

**Error Handling:**
- Shows error message if assessment fails
- User can continue without assessment
- Does not block feed creation

**Navigation:**
- "Previous" → Step 1
- "Next" → Step 3
- "Skip" → Step 3 (without running assessment)

### 4. Step 3: Analysis Options
**Purpose:** Configure automatic article analysis settings

**Features:**
- 7 analysis toggles (all enabled by default):
  1. **Article Categorization** (Stage 1)
     - Icon: Tags
     - Description: "Automatische Kategorisierung in 6 vordefinierte Kategorien"
  2. **Topic Classification & Keywords**
     - Icon: Sparkles
     - Description: "Erkennung von Themen, Hierarchien und relevanten Schlüsselwörtern"
  3. **Entity Extraction**
     - Icon: Users
     - Description: "Erkennung von Personen, Organisationen und Orten im Text"
  4. **Finance Sentiment Analysis** (Stage 2)
     - Icon: TrendingUp
     - Description: "Markt-Sentiment, Volatilität und wirtschaftliche Auswirkungen"
  5. **Geopolitical Sentiment Analysis** (Stage 2)
     - Icon: Globe
     - Description: "Stabilitäts-Scores, Eskalationspotenzial und diplomatische Auswirkungen"
  6. **OSINT Event Analysis** (Stage 3)
     - Icon: Shield
     - Description: "Open Source Intelligence Analyse für sicherheitsrelevante Events"
  7. **Summary & Key Facts**
     - Icon: FileText
     - Description: "Automatische Zusammenfassung mit wichtigsten Punkten"

**Batch Controls:**
- **"Alle aktivieren" button** (primary blue)
  - Sets all 7 flags to true
- **"Alle deaktivieren" button** (secondary gray)
  - Sets all 7 flags to false

**Visual Feedback:**
- Active toggles: Blue toggle icon + blue icon
- Inactive toggles: Gray toggle icon + gray icon
- Grouped by category:
  - Content Analysis (3 options)
  - Sentiment Analysis (2 options)
  - Intelligence & Summary (2 options)

**Navigation:**
- "Previous" → Step 2
- "Next" → Step 4

### 5. Step 4: Scraping Options
**Purpose:** Configure full-content scraping behavior

**Fields:**
- **Enable Full Content Scraping** (checkbox)
  - Default: false (disabled)
  - Icon changes color when enabled (primary vs muted)
  - Shows warning box when disabled

**Conditional Fields (only visible if scraping enabled):**
- **Scraping Method** (radio buttons)
  - **Newspaper4k** (recommended, green badge)
    - Icon: FileCode
    - Description: "Schnelle, effiziente Python-Library für Article-Scraping. Funktioniert mit den meisten Webseiten ohne JavaScript."
  - **Playwright** (experimental, yellow badge)
    - Icon: Globe
    - Description: "Browser-Automation für JavaScript-lastige Webseiten. Langsamer, aber funktioniert mit dynamischem Content."
  - Visual: Clickable cards with border highlighting when selected

- **Failure Threshold** (slider)
  - Range: 1-20 consecutive failures
  - Default: 5
  - Description: "Nach wie vielen aufeinanderfolgenden Fehlern soll das Scraping automatisch deaktiviert werden?"

**Info Boxes:**
- Yellow warning when scraping disabled: "Ohne Content-Scraping werden nur die Daten aus dem RSS-Feed verwendet."

**Navigation:**
- "Previous" → Step 3
- "Create Feed" → Submit form

### 6. Form Submission
**Process:**
1. Validate all fields with Zod schema
2. Remove internal fields (_hasRunAssessment, _assessmentData)
3. Call `POST /api/v1/feeds` with form data
4. Show success toast notification
5. Close dialog
6. Refresh feed list (React Query invalidation)

**Error Handling:**
- Validation errors shown inline with red text
- API errors shown as toast notifications
- 409 Conflict: "Feed with this URL already exists"

## Technical Architecture

### Frontend Components

```
features/feeds/
├── components/
│   ├── CreateFeedDialog.tsx          # Main wizard orchestrator
│   ├── FeedBasicInfoStep.tsx         # Step 1
│   ├── FeedAssessmentStep.tsx        # Step 2
│   ├── FeedAnalysisOptions.tsx       # Step 3
│   └── ScrapingOptionsStep.tsx       # Step 4
├── types/
│   └── createFeed.ts                 # TypeScript types
├── schemas/
│   └── createFeedSchema.ts           # Zod validation
└── api/
    ├── useCreateFeed.ts              # Feed creation hook
    └── usePreAssessFeed.ts           # Assessment hook
```

### Backend Endpoints

**1. Pre-Assessment Endpoint**
- **Path:** `POST /api/v1/feeds/pre-assess`
- **Authentication:** Bearer JWT required
- **Query Parameters:** `url` (string, required)
- **Process:**
  1. Extract domain from URL
  2. Create research task via research service
  3. Poll for task completion (15 attempts × 2s)
  4. Parse structured_data or fallback to regex parsing
  5. Generate suggested feed values
- **Response:** `PreAssessmentResponse` object
- **Timeout:** 30 seconds max
- **Error Handling:** Returns 500 if assessment fails, user can continue

**2. Feed Creation Endpoint**
- **Path:** `POST /api/v1/feeds`
- **Authentication:** Bearer JWT required
- **Body:** `FeedCreateInput` object
- **Process:**
  1. Validate input with Pydantic
  2. Check for duplicate URL
  3. Create feed record in database
  4. Create initial health record
  5. Trigger background fetch
  6. Publish `feed.created` event
- **Response:** Created feed object (201)

### Data Flow

```
User Action
    ↓
CreateFeedDialog (React Hook Form)
    ↓
Step 2: Run Assessment → usePreAssessFeed
    ↓
POST /api/v1/feeds/pre-assess
    ↓
Feed Service → Research Service (JWT forwarded)
    ↓
Research Service → Perplexity AI
    ↓
Poll for completion (max 30s)
    ↓
Parse response (structured_data or regex)
    ↓
Return assessment + suggested values
    ↓
Auto-fill form fields (if empty)
    ↓
User completes all steps
    ↓
Submit → useCreateFeed
    ↓
POST /api/v1/feeds
    ↓
Create feed + health record
    ↓
Publish feed.created event
    ↓
Background fetch triggered
    ↓
Success → Close dialog, refresh list
```

## Default Values

```typescript
const DEFAULT_FEED_VALUES = {
  fetch_interval: 60,                      // 60 minutes
  scrape_full_content: false,              // Disabled
  scrape_method: 'newspaper4k',            // Recommended method
  scrape_failure_threshold: 5,             // 5 consecutive failures

  // All analysis options enabled by default
  enable_categorization: true,
  enable_finance_sentiment: true,
  enable_geopolitical_sentiment: true,
  enable_osint_analysis: true,
  enable_summary: true,
  enable_entity_extraction: true,
  enable_topic_classification: true,
};
```

## Validation Rules

### URL
- Must be valid HTTP/HTTPS URL
- Must start with `http://` or `https://`
- Error: "URL muss mit http:// oder https:// beginnen"

### Name
- Required
- Max 200 characters
- Error: "Name ist erforderlich"

### Description
- Optional
- Max 500 characters

### Fetch Interval
- Integer: 5-1440 minutes
- Error: "Mindestens 5 Minuten" / "Maximal 1440 Minuten"

### Scrape Failure Threshold
- Integer: 1-20
- Only validated if scraping enabled

## User Experience Features

### Progressive Disclosure
- Step-by-step flow reduces cognitive load
- Optional assessment doesn't block progress
- Advanced options (scraping) hidden until needed

### Smart Auto-Fill
- Preserves user edits (only fills empty fields)
- Visual indicators (blue badges) show auto-filled values
- Works across steps (assessment in Step 2, fields in Step 1)

### Batch Operations
- "Enable All" / "Disable All" for quick configuration
- Reduces clicks from 7 to 1

### Visual Feedback
- Color-coded badges (tier, bias, method)
- Icons for each analysis type
- Loading spinners during async operations
- Toast notifications for success/error

### Responsive Design
- Works on desktop and mobile
- Dialog centers on screen
- Scrollable content within dialog

## Integration Points

### Research Service
- **Endpoint:** `POST /api/v1/research/`
- **Function:** `feed_source_assessment`
- **Parameters:** `feed_url`, `feed_name`, `domain`
- **Authentication:** JWT token forwarded from feed service
- **Timeout:** 30 seconds with polling

### RabbitMQ Events
- **Event:** `feed.created`
- **Publisher:** Feed Service
- **Subscribers:** Content Analysis Service, Analytics Service
- **Payload:** Feed object + analysis configuration

### Database
- **Tables:** `feeds`, `feed_health`
- **Transaction:** Atomic creation of both records

## Error Handling

### Frontend Errors
1. **Validation Errors**
   - Shown inline below fields
   - Red text with error icon
   - German language

2. **API Errors**
   - Toast notifications (react-hot-toast)
   - Error details from backend
   - User can retry or cancel

3. **Assessment Errors**
   - Error message displayed in Step 2
   - User can skip and continue
   - Does not block feed creation

### Backend Errors
1. **URL Validation**
   - 400 Bad Request
   - "Invalid URL provided"

2. **Duplicate Feed**
   - 409 Conflict
   - "Feed with this URL already exists"

3. **Authentication**
   - 403 Forbidden
   - "Not authenticated"

4. **Research Service Unavailable**
   - 500 Internal Server Error
   - "Assessment failed: {error details}"
   - User can continue without assessment

5. **Assessment Timeout**
   - 500 Internal Server Error
   - "Failed to retrieve assessment results"
   - After 30 seconds (15 polls × 2s)

## Performance Considerations

### Polling Mechanism
- **Interval:** 2 seconds between polls
- **Max Attempts:** 15 (30 seconds total)
- **Early Exit:** Stops when status = "completed" or "failed"
- **Resource Efficient:** Single connection, small payloads

### React Query Optimization
- **Mutation Caching:** Feed creation result cached
- **Invalidation:** Feed list auto-refreshes after creation
- **Optimistic Updates:** None (waits for confirmation)

### Frontend Bundle Size
- **Zod:** Already included in project
- **React Hook Form:** Already included
- **New Components:** ~15KB total (minified)
- **No New Dependencies:** Uses existing libraries

## Testing Strategy

### Manual Testing Checklist
- [ ] Create feed with valid URL
- [ ] Create feed with invalid URL (validation)
- [ ] Run assessment with tier_1 source
- [ ] Run assessment with tier_3 source
- [ ] Skip assessment, create feed manually
- [ ] Auto-fill preserves user edits
- [ ] Batch enable/disable all analysis options
- [ ] Enable scraping, select method
- [ ] Disable scraping, see warning
- [ ] Create duplicate feed (409 error)
- [ ] Create feed without authentication (403)
- [ ] Assessment timeout handling
- [ ] All 4 steps navigable back/forward
- [ ] Cancel dialog at each step
- [ ] Mobile responsive layout

### API Testing
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r '.access_token')

# Test pre-assessment
curl -X POST "http://localhost:8101/api/v1/feeds/pre-assess?url=https://www.techcrunch.com/feed/" \
  -H "Authorization: Bearer $TOKEN"

# Test feed creation
curl -X POST "http://localhost:8101/api/v1/feeds" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechCrunch",
    "url": "https://www.techcrunch.com/feed/",
    "description": "Technology news",
    "fetch_interval": 60,
    "enable_categorization": true,
    "enable_finance_sentiment": true,
    "enable_geopolitical_sentiment": true,
    "enable_osint_analysis": true,
    "enable_summary": true,
    "enable_entity_extraction": true,
    "enable_topic_classification": true
  }'
```

## Future Enhancements

### Planned
- [ ] Feed preview (show 5 latest items before creation)
- [ ] Bulk feed import (CSV/OPML)
- [ ] Template presets (News, Tech, Finance, etc.)
- [ ] Schedule first fetch (delay by X hours)
- [ ] Custom category management

### Under Consideration
- [ ] URL validation via HEAD request
- [ ] Auto-detect feed format (RSS vs Atom)
- [ ] Duplicate detection (similar URLs)
- [ ] Import from browser bookmarks

## Troubleshooting

### Common Issues

**Issue:** Assessment returns 500 error
- **Cause:** Research service timeout or missing domain parameter
- **Solution:** Check research service logs, verify Perplexity API key
- **Workaround:** Skip assessment, create feed manually

**Issue:** Feed creation returns 409
- **Cause:** Feed with this URL already exists
- **Solution:** Check existing feeds, use different URL
- **Workaround:** Edit existing feed instead

**Issue:** Auto-fill not working
- **Cause:** Assessment didn't return suggested_values
- **Solution:** Check pre-assessment response structure
- **Workaround:** Fill fields manually

**Issue:** Analysis options not saving
- **Cause:** Fields not included in form submission
- **Solution:** Verify form values before submit
- **Debug:** Add console.log in onSubmit handler

## Documentation References

- **API Docs:** `/docs/api/feed-service-api.md`
- **Frontend Features:** `/frontend/FEATURES.md`
- **Research Service:** `/docs/api/research-service-api.md`
- **Database Schema:** `/docs/DATABASE-ARCHITECTURE.md`

## Change Log

### 2025-10-23 - Initial Release
- Created multi-step feed creation wizard
- Added source assessment integration
- Implemented auto-fill from assessment
- Added batch analysis toggle controls
- Added comprehensive validation
- Added error handling and recovery
- Documented all components and flows

---

**Feature Owner:** Feed Service Team
**Last Reviewed:** 2025-10-23
**Next Review:** 2025-11-23
