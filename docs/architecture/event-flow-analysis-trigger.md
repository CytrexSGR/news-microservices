# Event Flow: Article Analysis Trigger

**Last Updated:** 2025-12-01
**Related Incident:** [POSTMORTEMS.md - Incident #27](../../POSTMORTEMS.md#incident-27-v3-analysis-not-triggered-for-scraped-articles---timing-issue-2025-12-01)

## Overview

This document describes how V3 content analysis is triggered for articles, with special handling for feeds that use scraping vs. feeds with RSS content.

## Two Paths to Analysis

### Path 1: RSS Content (Immediate Analysis)

For feeds with `scrape_full_content = false`:

```
1. feed-service fetches RSS → Article created WITH content from RSS
2. feed-service checks: content exists AND NOT scrape_full_content
3. feed-service publishes: analysis.v3.request event
4. content-analysis-v3 consumes event → Analyzes article
```

**Timeline:** Analysis happens immediately (within seconds of article creation)

### Path 2: Scraped Content (Delayed Analysis)

For feeds with `scrape_full_content = true` (100% of production feeds):

```
1. feed-service fetches RSS → Article created WITHOUT content (only title/link)
2. feed-service checks: scrape_full_content = true
3. feed-service publishes: feed.item.created event (scraping request)
4. feed-service logs: "Skipping immediate V3 analysis (will be triggered after scraping)"
5. scraping-service consumes event → Scrapes article content
6. scraping-service publishes: analysis.v3.request event (AFTER scraping completes)
7. content-analysis-v3 consumes event → Analyzes article
```

**Timeline:** Analysis happens after scraping completes (2-5 minutes after article creation)

## Key Implementation Details

### feed-service (feed_fetcher.py:318-344)

```python
# Only send immediate analysis if NOT using scraping
if item_data["content"] and not item_data["scrape_full_content"]:
    await session.execute(
        text("""
            INSERT INTO event_outbox (event_type, payload)
            VALUES (:event_type, :payload)
        """),
        {
            "event_type": "analysis.v3.request",
            "payload": json.dumps({
                "article_id": str(item_data["item_id"]),
                "title": item_data["title"],
                "url": item_data["link"],
                "content": item_data["content"],
                "run_tier2": True,
            })
        }
    )
elif item_data["scrape_full_content"]:
    logger.info(
        f"Skipping immediate V3 analysis for article {item_data['item_id']} "
        f"(will be triggered after scraping): {item_data['title']}"
    )
```

### scraping-service (scraping_worker.py:196-203)

```python
# Trigger V3 analysis after successful scraping
if result.content and result.word_count > 50:  # Minimum 50 words
    await self._publish_analysis_request(
        item_id=item_id,
        url=url,
        content=result.content
    )
```

### scraping-service (_publish_analysis_request:356-398)

```python
async def _publish_analysis_request(
    self,
    item_id: str,
    url: str,
    content: str
):
    """
    Publish analysis.v3.request event to RabbitMQ after successful scraping.

    This ensures articles get analyzed even if they had no content when initially created.
    Fixes the timing issue where articles are created before scraping completes.
    """
    try:
        # Get article title from feed service
        response = await self.http_client.get(f"/api/v1/feeds/items/{item_id}")
        if response.status_code != 200:
            logger.warning(f"Failed to get article {item_id} for analysis request")
            return

        article_data = response.json()

        await self.event_publisher.publish_event(
            event_type="analysis.v3.request",
            payload={
                "article_id": item_id,
                "title": article_data.get("title", ""),
                "url": url,
                "content": content,
                "run_tier2": True,
                "triggered_by": "scraping_service",  # Track source
            },
            correlation_id=item_id
        )

        logger.info(f"✅ Published analysis.v3.request for {item_id} ({len(content)} chars)")

    except Exception as e:
        logger.error(f"Failed to publish analysis request for {item_id}: {e}")
```

## Why This Design?

### Problem (Before Fix)

The original design had a race condition:

1. Article created without content
2. feed-service checks `if item_data["content"]:`  → False → No analysis request
3. Scraping adds content later
4. **No mechanism to trigger analysis after scraping**
5. Article never analyzed ❌

### Solution (After Fix)

**Separation of Concerns:**
- feed-service: Responsible for RSS content analysis (immediate)
- scraping-service: Responsible for scraped content analysis (delayed)
- Each service knows when its data is ready

**Event-Driven Coordination:**
- No timing assumptions between services
- Scraping completion explicitly triggers downstream processing
- Clear audit trail via `triggered_by` field

## Monitoring

**Key Metrics:**
- Articles created with `scrape_full_content=true` but no analysis after 10 minutes
- analysis.v3.request events in DLQ
- Latency: scraping completion → analysis start

**Expected Logs:**

```
# feed-service
INFO - Skipping immediate V3 analysis for article <id> (will be triggered after scraping): <title>

# scraping-service
INFO - Successfully scraped <id>: <word_count> words using <method>
INFO - ✅ Published analysis.v3.request for <id> (<content_length> chars)

# content-analysis-v3
INFO - Processing analysis request for article <id>
INFO - ✅ Analysis completed for <id>: cost=$X.XX, tokens=Y
```

## Verification Queries

**Check articles scraped but not analyzed:**
```sql
SELECT fi.id, fi.title, fi.scraped_at, aa.article_id
FROM feed_items fi
LEFT JOIN article_analysis aa ON fi.id = aa.article_id
WHERE fi.scraped_at IS NOT NULL
  AND aa.article_id IS NULL
  AND fi.scraped_at < NOW() - INTERVAL '10 minutes';
```

**Check analysis latency for scraped articles:**
```sql
SELECT
  fi.id,
  fi.scraped_at,
  aa.created_at as analyzed_at,
  EXTRACT(EPOCH FROM (aa.created_at - fi.scraped_at)) as latency_seconds
FROM feed_items fi
JOIN article_analysis aa ON fi.id = aa.article_id
WHERE fi.scraped_at IS NOT NULL
  AND fi.scraped_at > NOW() - INTERVAL '1 hour'
ORDER BY latency_seconds DESC;
```

## Related Documentation

- [POSTMORTEMS.md - Incident #27](../../POSTMORTEMS.md#incident-27) - Full incident report
- [scraping-service README](../services/scraping-service.md) - Scraping service documentation
- [feed-service README](../services/feed-service.md) - Feed service documentation
- [content-analysis-v3 README](../services/content-analysis-v3.md) - Analysis service documentation
