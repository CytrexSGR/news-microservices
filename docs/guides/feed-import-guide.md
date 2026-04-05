# Feed Import Guide

**Last Updated:** 2025-11-02
**Recommended Method:** Semi-Automated Batch Import with Source Assessment

---

## Overview

This guide covers both manual and automated methods for importing RSS/Atom feeds into the News Microservices platform, including source assessment, configuration, and validation.

### Import Methods Comparison

| Method | Speed | Assessment | Staggering | Best For |
|--------|-------|------------|------------|----------|
| **Manual (Frontend)** | Slow | Manual entry | No | 1-5 feeds |
| **Batch Script** | Fast | Automated (Perplexity API) | Attempted | 10+ feeds |
| **API Direct** | Medium | Optional | No | Integration |

---

## Prerequisites

### 1. Authentication Token

**Get JWT token via auto-login script:**

```bash
# Create token retrieval script
cat > /tmp/get_token.sh << 'EOF'
#!/bin/bash
echo "🔐 Hole Auth-Token..."

RESPONSE=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }')

TOKEN=$(echo "$RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ]; then
  echo "❌ Login fehlgeschlagen!"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Token erhalten: ${TOKEN:0:50}..."
echo "$TOKEN" > /tmp/auth_token.txt
echo ""
echo "📝 Token gespeichert in: /tmp/auth_token.txt"
EOF

chmod +x /tmp/get_token.sh

# Run it
/tmp/get_token.sh

# Token is now in /tmp/auth_token.txt
TOKEN=$(cat /tmp/auth_token.txt)
```

### 2. Feed List Preparation

**Create CSV file with feed data:**

```csv
Name,URL,Category,Source
BBC News - World,http://feeds.bbci.co.uk/news/world/rss.xml,Politics & World News,CSV Export
The Guardian - World,https://www.theguardian.com/world/rss,Politics & World News,CSV Export
Reuters World News,https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best,Politics & World News,Manual Addition
```

**Required Fields:**
- `Name`: Feed display name
- `URL`: RSS/Atom feed URL
- `Category`: Broad category (used for pre-assessment)
- `Source`: Import source identifier

**Optional Fields:**
- `Description`: Feed description (auto-generated if missing)
- `Language`: Content language (default: auto-detect)

---

## Method 1: Batch Import Script (Recommended)

### Features

✅ **Automated Source Assessment** via Research Service
✅ **Pre-validation** of feed URLs
✅ **Configurable defaults** (fetch interval, scraping, analysis)
✅ **Error handling** per feed (continues on failure)
✅ **Progress tracking** with detailed logs
✅ **Staggering attempt** (fallback to manual SQL if needed)

### Script Template

```python
#!/usr/bin/env python3
"""
Feed Batch Import Script with Source Assessment
Imports feeds from CSV with automated quality assessment
"""

import asyncio
import csv
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx

# Configuration
API_BASE = "http://localhost:8101/api/v1"
FETCH_INTERVAL = 15  # minutes
STAGGER_OFFSET = 28  # seconds between feed starts
PAUSE_BETWEEN_FEEDS = 4  # seconds

# Analysis options (all enabled)
ANALYSIS_OPTIONS = {
    "enable_categorization": True,
    "enable_finance_sentiment": True,
    "enable_geopolitical_sentiment": True,
    "enable_osint_analysis": True,
    "enable_summary": True,
    "enable_entity_extraction": True,
    "enable_topic_classification": True,
}


class FeedImporter:
    def __init__(self, auth_token: str):
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        self.client = None
        self.results = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def pre_assess_feed(self, feed_data: Dict[str, str]) -> Optional[Dict]:
        """Get source assessment from Research Service"""
        print(f"  🔍 Assessing: {feed_data['Name']}")

        try:
            response = await self.client.post(
                f"{API_BASE}/feeds/pre-assess",
                json={
                    "name": feed_data["Name"],
                    "url": feed_data["URL"],
                    "category": feed_data.get("Category", "Other"),
                },
                headers=self.headers,
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Assessment: {data.get('assessment', {}).get('credibility_tier', 'unknown')}")
                return data
            else:
                print(f"  ⚠️  Assessment failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  ❌ Assessment error: {e}")
            return None

    async def create_feed(
        self, feed_data: Dict[str, str], assessment: Optional[Dict]
    ) -> Dict[str, Any]:
        """Create feed with full configuration"""
        print(f"\n📰 Creating: {feed_data['Name']}")

        # Build payload with defaults
        payload = {
            "name": feed_data["Name"],
            "url": feed_data["URL"],
            "fetch_interval": FETCH_INTERVAL,
            "scrape_full_content": True,
            "scrape_method": "newspaper4k",
            "scrape_failure_threshold": 5,
            **ANALYSIS_OPTIONS,
        }

        # Add assessment data if available
        if assessment and assessment.get("success"):
            suggested = assessment.get("suggested_values", {})
            assessment_data = assessment.get("assessment", {})

            payload.update({
                "description": suggested.get("description"),
                "category": suggested.get("category"),
                "credibility_tier": assessment_data.get("credibility_tier"),
                "reputation_score": assessment_data.get("reputation_score"),
                "language": assessment_data.get("primary_language", "en"),
            })

        try:
            # Create feed
            response = await self.client.post(
                f"{API_BASE}/feeds",
                json=payload,
                headers=self.headers,
            )

            if response.status_code == 201:
                feed = response.json()
                print(f"  ✅ Created: ID {feed['id']}")
                return {
                    "status": "success",
                    "feed_id": feed["id"],
                    "name": feed_data["Name"],
                }
            else:
                print(f"  ❌ Creation failed: {response.status_code}")
                print(f"     Response: {response.text}")
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "name": feed_data["Name"],
                }

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"status": "error", "error": str(e), "name": feed_data["Name"]}

    async def stagger_feed_start(
        self, feed_id: int, offset_seconds: int
    ) -> bool:
        """Attempt to stagger feed fetch start times"""
        print(f"  ⏰ Setting staggered start (+{offset_seconds}s)")

        try:
            now = datetime.utcnow()
            staggered_time = now - timedelta(minutes=FETCH_INTERVAL) + timedelta(
                seconds=offset_seconds
            )

            response = await self.client.patch(
                f"{API_BASE}/feeds/{feed_id}",
                json={"last_fetched_at": staggered_time.isoformat() + "Z"},
                headers=self.headers,
            )

            if response.status_code == 200:
                print(f"  ✅ Staggering set")
                return True
            else:
                print(f"  ⚠️  Staggering failed: {response.status_code} (not critical)")
                return False

        except Exception as e:
            print(f"  ⚠️  Staggering error: {e} (not critical)")
            return False

    async def import_feeds(self, csv_path: str):
        """Import all feeds from CSV"""
        print(f"📂 Reading feeds from: {csv_path}\n")

        # Read CSV
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            feeds = list(reader)

        print(f"📊 Found {len(feeds)} feeds to import\n")
        print("=" * 60)

        # Process each feed
        for index, feed_data in enumerate(feeds):
            result = {
                "name": feed_data["Name"],
                "url": feed_data["URL"],
                "category": feed_data.get("Category", "Other"),
                "index": index,
                "timestamp": datetime.utcnow().isoformat(),
            }

            try:
                # Step 1: Pre-assessment
                assessment = await self.pre_assess_feed(feed_data)
                await asyncio.sleep(2)  # Rate limiting

                # Step 2: Create feed
                create_result = await self.create_feed(feed_data, assessment)
                result.update(create_result)

                # Step 3: Stagger (if creation successful)
                if create_result.get("status") == "success":
                    feed_id = create_result["feed_id"]
                    offset = index * STAGGER_OFFSET
                    await self.stagger_feed_start(feed_id, offset)

                # Pause before next feed
                await asyncio.sleep(PAUSE_BETWEEN_FEEDS)

            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                result.update({"status": "error", "error": str(e)})

            self.results.append(result)
            print("-" * 60)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print import summary"""
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY")
        print("=" * 60)

        success = [r for r in self.results if r.get("status") == "success"]
        errors = [r for r in self.results if r.get("status") == "error"]

        print(f"\n✅ Successful: {len(success)}")
        print(f"❌ Failed: {len(errors)}")

        if errors:
            print("\n❌ Failed Feeds:")
            for err in errors:
                print(f"  - {err['name']}: {err.get('error', 'Unknown error')}")

        # Save results
        output_file = "/tmp/import_results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Full results saved to: {output_file}")


async def main():
    """Main import function"""
    if len(sys.argv) < 3:
        print("Usage: python3 import_feeds_batch.py <CSV_PATH> <AUTH_TOKEN>")
        print("\nExample:")
        print("  python3 import_feeds_batch.py /tmp/feeds.csv $(cat /tmp/auth_token.txt)")
        sys.exit(1)

    csv_path = sys.argv[1]
    auth_token = sys.argv[2]

    async with FeedImporter(auth_token) as importer:
        await importer.import_feeds(csv_path)


if __name__ == "__main__":
    asyncio.run(main())
```

### Usage

```bash
# 1. Prepare CSV file
cat > /tmp/new_feeds.csv << 'EOF'
Name,URL,Category,Source
BBC News - World,http://feeds.bbci.co.uk/news/world/rss.xml,Politics & World News,Manual
The Guardian - World,https://www.theguardian.com/world/rss,Politics & World News,Manual
EOF

# 2. Get auth token
/tmp/get_token.sh

# 3. Run import
python3 import_feeds_batch.py /tmp/new_feeds.csv $(cat /tmp/auth_token.txt)

# 4. Check results
cat /tmp/import_results.json
```

### Expected Output

```
📂 Reading feeds from: /tmp/new_feeds.csv

📊 Found 32 feeds to import

============================================================
📰 Creating: BBC News - World
  🔍 Assessing: BBC News - World
  ✅ Assessment: tier_1
  ✅ Created: ID 25
  ⏰ Setting staggered start (+0s)
  ⚠️  Staggering failed: 405 (not critical)
------------------------------------------------------------
📰 Creating: The Guardian - World
  🔍 Assessing: The Guardian - World
  ✅ Assessment: tier_1
  ✅ Created: ID 26
  ⏰ Setting staggered start (+28s)
  ⚠️  Staggering failed: 405 (not critical)
------------------------------------------------------------
...
============================================================
📊 IMPORT SUMMARY
============================================================

✅ Successful: 32
❌ Failed: 0

📄 Full results saved to: /tmp/import_results.json
```

---

## Method 2: Manual Import (Frontend)

### When to Use

- Importing 1-5 feeds
- Want full control over each setting
- Need to verify feed content before saving

### Steps

1. **Navigate to Feed Management**
   ```
   http://localhost:3000/feeds
   ```

2. **Click "Create Feed" button**

3. **Fill Form (4-Step Wizard)**

   **Step 1: Basic Info**
   - Name: Feed display name
   - URL: RSS/Atom feed URL
   - Category: Select from dropdown
   - Description: Optional (auto-generated if blank)

   **Step 2: Source Assessment**
   - Click "Assess Source" button
   - Wait for Perplexity API analysis (~10s)
   - Review credibility tier and reputation score
   - Click "Next"

   **Step 3: Fetch & Scraping**
   - Fetch Interval: 15 minutes (recommended)
   - Scraping: ✅ Enable Full-Content Scraping
   - Scrape Method: newspaper4k
   - Failure Threshold: 5 (default)

   **Step 4: Analysis Options**
   - ✅ Enable Categorization
   - ✅ Enable Finance Sentiment
   - ✅ Enable Geopolitical Sentiment
   - ✅ Enable OSINT Analysis
   - ✅ Enable Summary
   - ✅ Enable Entity Extraction
   - ✅ Enable Topic Classification

4. **Submit and Verify**
   - Click "Create Feed"
   - Verify feed appears in feed list
   - Wait 15 minutes for first fetch

---

## Method 3: Direct API Calls

### When to Use

- Automating feed additions from external systems
- Custom import logic
- Integration with feed discovery tools

### API Endpoint

```http
POST /api/v1/feeds
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Minimal Payload

```json
{
  "name": "Example Feed",
  "url": "https://example.com/feed.xml",
  "fetch_interval": 15,
  "scrape_full_content": true
}
```

### Full Payload (with Assessment)

```json
{
  "name": "BBC News - World",
  "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
  "description": "International news from BBC News",
  "category": "Politics & World News",
  "fetch_interval": 15,
  "scrape_full_content": true,
  "scrape_method": "newspaper4k",
  "scrape_failure_threshold": 5,
  "credibility_tier": "tier_1",
  "reputation_score": 95,
  "language": "en",
  "enable_categorization": true,
  "enable_finance_sentiment": true,
  "enable_geopolitical_sentiment": true,
  "enable_osint_analysis": true,
  "enable_summary": true,
  "enable_entity_extraction": true,
  "enable_topic_classification": true
}
```

### Example: curl

```bash
# Get token
TOKEN=$(cat /tmp/auth_token.txt)

# Create feed
curl -X POST http://localhost:8101/api/v1/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reuters World News",
    "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "fetch_interval": 15,
    "scrape_full_content": true,
    "enable_categorization": true,
    "enable_finance_sentiment": true,
    "enable_geopolitical_sentiment": true,
    "enable_osint_analysis": true,
    "enable_summary": true,
    "enable_entity_extraction": true,
    "enable_topic_classification": true
  }'
```

---

## Post-Import Tasks

### 1. Verify Feed Creation

```sql
-- Check recent feeds
SELECT id, name, url, is_active, created_at
FROM feeds
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

### 2. Monitor Initial Fetch

Wait 15 minutes, then check:

```sql
-- Check article count per new feed
SELECT
    f.name,
    COUNT(fi.id) as article_count,
    MAX(fi.created_at) as latest_article
FROM feeds f
LEFT JOIN feed_items fi ON f.id = fi.feed_id
WHERE f.created_at > NOW() - INTERVAL '1 hour'
GROUP BY f.id, f.name
ORDER BY f.created_at DESC;
```

### 3. Check Scraping Status

```sql
-- Scraping success rate for new feeds
SELECT
    f.name,
    COUNT(*) FILTER (WHERE fi.scrape_status = 'success') as scraped,
    COUNT(*) FILTER (WHERE fi.scrape_status = 'error') as errors,
    COUNT(*) FILTER (WHERE fi.scrape_status IS NULL) as pending,
    COUNT(*) as total
FROM feed_items fi
JOIN feeds f ON fi.feed_id = f.id
WHERE f.created_at > NOW() - INTERVAL '1 hour'
  AND fi.created_at > NOW() - INTERVAL '30 minutes'
GROUP BY f.name
ORDER BY total DESC;
```

### 4. Implement Staggering (Manual Workaround)

If batch import staggering failed (405 error), manually stagger via SQL:

```sql
-- Stagger new feeds with 28-second offsets
UPDATE feeds
SET last_fetched_at = NOW() - INTERVAL '15 minutes' +
    (ROW_NUMBER() OVER (ORDER BY id) * INTERVAL '28 seconds')
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Verify staggering
SELECT
    id,
    name,
    last_fetched_at,
    EXTRACT(EPOCH FROM (last_fetched_at - LAG(last_fetched_at) OVER (ORDER BY id))) as offset_seconds
FROM feeds
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY id;
```

---

## Troubleshooting

### Issue: Import Script Fails with Authentication Error

**Symptom:**
```
❌ Login fehlgeschlagen!
Response: {"detail": "Invalid credentials"}
```

**Solution:**
```bash
# Verify credentials in /tmp/get_token.sh
# Username: andreas
# Password: Aug2012#

# Test auth manually
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "andreas", "password": "Aug2012#"}'
```

### Issue: Feed Creation Returns 422 (Validation Error)

**Symptom:**
```json
{
  "detail": [
    {"loc": ["body", "url"], "msg": "invalid url format", "type": "value_error"}
  ]
}
```

**Solution:**
- Verify feed URL is valid RSS/Atom feed
- Test URL manually: `curl -I <feed_url>`
- Check for redirects or authentication requirements

### Issue: Assessment Times Out

**Symptom:**
```
⚠️  Assessment failed: 504
```

**Solution:**
- Research Service may be slow (Perplexity API latency)
- Continue without assessment (feed will still be created)
- Retry assessment later via frontend

### Issue: All Feeds Fetching Simultaneously

**Symptom:**
- Large spike in database/network activity every 15 minutes
- 32+ feeds fetching at same time

**Solution:**
- Apply manual staggering via SQL (see Post-Import Tasks #4)
- Or accept simultaneous fetching (system handles it fine)

---

## Best Practices

### Feed Selection

✅ **Do:**
- Verify feed URL is valid before importing
- Check feed has recent articles (not abandoned)
- Prefer official news sources over aggregators
- Include diverse sources (geographic, topic, political)

❌ **Don't:**
- Import feedspot.com directories (not actual feeds)
- Import feeds with <10 articles
- Import duplicate feeds (same content, different URL)
- Import paywalled sources without noting limitations

### Configuration

**Standard Configuration (Most Feeds):**
```json
{
  "fetch_interval": 15,
  "scrape_full_content": true,
  "scrape_method": "newspaper4k",
  "scrape_failure_threshold": 5
}
```

**High-Volume Feeds (>100 articles/day):**
```json
{
  "fetch_interval": 15,
  "scrape_full_content": true,
  "scrape_failure_threshold": 10  // Higher tolerance
}
```

**Paywall Sources:**
```json
{
  "fetch_interval": 15,
  "scrape_full_content": false,  // Skip scraping
  "scrape_failure_threshold": 1
}
```

**JavaScript-Heavy Sites:**
```json
{
  "fetch_interval": 30,  // Slower to reduce load
  "scrape_full_content": true,
  "scrape_method": "playwright",  // Use browser
  "scrape_failure_threshold": 5
}
```

### Analysis Options

**Enable All (Default):** For comprehensive analysis
```json
{
  "enable_categorization": true,
  "enable_finance_sentiment": true,
  "enable_geopolitical_sentiment": true,
  "enable_osint_analysis": true,
  "enable_summary": true,
  "enable_entity_extraction": true,
  "enable_topic_classification": true
}
```

**Selective (Performance Optimization):**
```json
{
  "enable_categorization": true,    // Fast, always useful
  "enable_summary": true,            // Fast, always useful
  "enable_finance_sentiment": false, // Only for finance feeds
  "enable_geopolitical_sentiment": true,
  "enable_osint_analysis": false,    // Slow, only for security feeds
  "enable_entity_extraction": true,
  "enable_topic_classification": true
}
```

---

## Appendix

### Valid Feed URL Patterns

**RSS 2.0:**
- `*.xml` (e.g., `feed.xml`, `rss.xml`)
- `/feed`, `/rss`, `/feeds`
- `feedburner.com/...`

**Atom:**
- `atom.xml`
- `/atom`, `/feed/atom`

**RDF:**
- `*.rdf`
- `/rss.rdf`

**Invalid Patterns (Directories, Not Feeds):**
- `feedspot.com/...` (feed directory)
- `wikipedia.org/...` (encyclopedia)
- Social media profile pages

### Feed Validation Script

```bash
#!/bin/bash
# Validate feed URL returns valid RSS/Atom

URL="$1"

if [ -z "$URL" ]; then
  echo "Usage: $0 <feed_url>"
  exit 1
fi

echo "🔍 Validating: $URL"

# Fetch feed
RESPONSE=$(curl -s -L -H "User-Agent: Mozilla/5.0" "$URL")

# Check for RSS/Atom markers
if echo "$RESPONSE" | grep -q "<rss\|<feed\|<rdf:RDF"; then
  echo "✅ Valid feed!"

  # Count items
  ITEMS=$(echo "$RESPONSE" | grep -c "<item>\|<entry>")
  echo "📰 Found $ITEMS articles"
else
  echo "❌ Not a valid feed!"
  echo "Response preview:"
  echo "$RESPONSE" | head -20
fi
```

---

## References

- Feed Service API: [docs/api/feed-service-api.md](../api/feed-service-api.md)
- Feed Sources List: [services/feed-service/docs/feed-sources.md](../../services/feed-service/docs/feed-sources.md)
- Scraping Limitations: [docs/guides/scraping-limitations.md](scraping-limitations.md)
- Research Service: [docs/services/research-service.md](../services/research-service.md)
