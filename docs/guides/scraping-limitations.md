# Scraping Limitations & Known Issues

**Last Updated:** 2025-11-02
**Scraping Service:** newspaper4k (default), playwright (optional)

---

## Overview

This document outlines known limitations of the full-content scraping system, expected failure scenarios, and workaround strategies for difficult-to-scrape sources.

### Overall Performance Baseline

**Expected Success Rates:**
- **Open Content:** 90-100% success
- **Premium/Paywall:** 0-30% success
- **JavaScript-Heavy:** 40-70% success (newspaper4k), 80-95% (playwright)
- **Non-English:** 60-90% success (depends on encoding)

**Current System Performance (November 2, 2025):**
- Overall Success Rate: 72.4% (567/783 articles)
- Error Rate: 18.9% (148 articles)
- Pending: 8.7% (68 articles)

---

## Known Paywall Sources

These premium publications implement hard paywalls that cannot be bypassed with standard scraping:

### 100% Expected Failure

| Source | Articles Tested | Success Rate | Reason |
|--------|----------------|--------------|--------|
| The Economist | 50 | 0% | Hard paywall, subscription required |
| Wall Street Journal | 10 | 0% | Metered paywall, aggressive bot detection |

**Impact:** RSS feeds provide headlines and summaries only. Full content unavailable without subscription.

**Workarounds:**
1. **Accept RSS Snippets:** Use summary from RSS feed instead of scraped content
2. **API Integration:** Use official APIs if available (costly)
3. **Manual Override:** Mark articles as "paywall" and skip scraping

**Implementation:**
```python
# In scraping_worker.py - detect paywall
KNOWN_PAYWALLS = [
    'economist.com',
    'wsj.com',
    'ft.com',
    'nytimes.com'  # Partial paywall
]

if any(domain in article_url for domain in KNOWN_PAYWALLS):
    # Skip scraping, use RSS summary
    article.scrape_status = 'paywall'
    article.content = article.rss_summary
```

---

## Language & Encoding Issues

### Japanese Sources (Asahi Shimbun)

**Problem:**
- 40 articles failed scraping (100% error rate)
- Encoding: Shift-JIS / EUC-JP instead of UTF-8
- HTML structure differs from Western news sites

**Error Pattern:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x... in position ...
```

**Workarounds:**
1. **Encoding Detection:** Use chardet library
   ```python
   import chardet

   encoding = chardet.detect(response.content)['encoding']
   html = response.content.decode(encoding or 'utf-8')
   ```

2. **Language-Specific Parsers:** Configure newspaper4k for Japanese
   ```python
   from newspaper import Config

   config = Config()
   config.language = 'ja'
   config.memoize_articles = False

   article = Article(url, config=config)
   ```

3. **Alternative Libraries:** Use `beautifulsoup4` with lxml parser

### French Sources (Le Monde)

**Problem:**
- 18 articles failed scraping (36% error rate)
- Some articles behind "soft paywall" (free registration)
- JavaScript-rendered content

**Success Rate:** ~60-70% for non-paywall articles

**Workaround:** Accept current success rate or implement playwright for JS rendering

---

## Cryptocurrency News (The Block)

**Problem:**
- 20 articles failed scraping (moderate error rate)
- Heavy JavaScript usage for content loading
- Aggressive bot detection / Cloudflare protection

**Error Pattern:**
```
HTTP 403 Forbidden
Cloudflare security challenge
```

**Workarounds:**
1. **Playwright Scraping:** Browser-based scraping bypasses JS issues
   ```python
   from playwright.async_api import async_playwright

   async with async_playwright() as p:
       browser = await p.chromium.launch()
       page = await browser.new_page()
       await page.goto(url)
       await page.wait_for_load_state('networkidle')
       content = await page.content()
   ```

2. **User-Agent Rotation:** Mimic real browsers
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
   }
   ```

3. **Rate Limiting:** Reduce request frequency to avoid detection
   ```python
   await asyncio.sleep(random.uniform(2, 5))  # Random delay
   ```

---

## Technical Scraping Errors

### KeyError: 'url' (Event Processing)

**Frequency:** Intermittent (affects <5% of events)

**Root Cause:** Some `feed.item.created` events have malformed payloads

**Error Log:**
```python
File "/app/app/workers/scraping_worker.py", line 129, in _process_message
    url = job["url"]
          ~~~^^^^^^^
KeyError: 'url'
```

**Impact:**
- Message is rejected (not re-queued)
- Article not scraped
- Slows queue processing

**Fix Recommendation:**
```python
# Add payload validation
def _process_message(self, body: bytes):
    try:
        job = json.loads(body)

        # Validate required fields
        if 'url' not in job:
            logger.error(f"Invalid event payload: missing 'url' field. Job: {job}")
            return  # Acknowledge message, don't retry

        url = job["url"]
        # ... rest of processing
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in event payload: {body}")
        return
```

### PATCH 405 Method Not Allowed

**Frequency:** Every successful scrape attempt

**Root Cause:** Scraping service tries to update feed stats via PATCH endpoint, but feed-service doesn't support it

**Error Log:**
```
HTTP Request: PATCH http://news-feed-service:8000/api/v1/feeds/{feed_id}
"HTTP/1.1 405 Method Not Allowed"

Failed to reset database failure counter for feed
```

**Impact:**
- Log spam (non-critical)
- Feed failure counters not updated
- **No impact on scraping functionality**

**Fix Options:**
1. **Implement PATCH endpoint** in feed-service
   ```python
   @router.patch("/feeds/{feed_id}")
   async def update_feed_stats(
       feed_id: int,
       stats: FeedStatsUpdate,
       db: AsyncSession = Depends(get_db)
   ):
       # Update feed statistics
       ...
   ```

2. **Remove stats update** from scraping-service
   ```python
   # Comment out or remove this code block
   # update_response = await client.patch(...)
   ```

3. **Accept log spam** (current status)

---

## JavaScript-Heavy Websites

**General Issue:** newspaper4k cannot execute JavaScript, so dynamically loaded content is missed.

**Affected Sources:**
- Modern news aggregators
- Single-Page Applications (SPAs)
- Lazy-loaded article content

**Symptoms:**
- Empty or truncated content
- Missing images/videos
- Incorrect article structure

**Solution:** Switch to playwright for specific feeds

### Playwright Configuration

**Installation:**
```bash
pip install playwright
playwright install chromium
```

**Usage Pattern:**
```python
async def scrape_with_playwright(url: str) -> str:
    """Scrape JavaScript-heavy pages"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 ...'
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_selector('article', timeout=10000)

            content = await page.inner_text('article')
            return content
        finally:
            await browser.close()
```

**Trade-offs:**
- ✅ 90-95% success rate on JS-heavy sites
- ✅ Bypasses basic bot detection
- ❌ 3-5x slower (~3-5s per article vs ~500ms)
- ❌ Higher memory usage (~100MB per browser instance)
- ❌ More complex infrastructure (needs browser binaries)

---

## Performance Considerations

### Current Bottlenecks

1. **Single-Threaded Consumer**
   - Processing rate: ~2 messages/second
   - Queue size: 178 messages (decreasing)
   - Time to clear 776 messages: ~6.5 minutes

2. **Network Latency**
   - HTTP requests: 200-800ms per article
   - Slow news servers increase average time

3. **Sequential Processing**
   - One article at a time
   - No parallelization within worker

### Optimization Strategies

**Multi-Worker Deployment:**
```yaml
# docker-compose.yml
services:
  scraping-service-worker-1:
    image: news-scraping-service
    command: python -m app.workers.scraping_worker

  scraping-service-worker-2:
    image: news-scraping-service
    command: python -m app.workers.scraping_worker

  scraping-service-worker-3:
    image: news-scraping-service
    command: python -m app.workers.scraping_worker
```

**Benefits:**
- 3x throughput (6 messages/second)
- Faster queue clearing (~2 minutes for 776 messages)

**Concurrent Processing (within worker):**
```python
import asyncio

async def process_batch(messages: list):
    """Process multiple articles concurrently"""
    tasks = [scrape_article(msg) for msg in messages]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Benefits:**
- 5-10x throughput (10-20 messages/second)
- Lower latency for batch operations

**Trade-offs:**
- Higher CPU/memory usage
- Risk of rate limiting
- More complex error handling

---

## Monitoring & Alerts

### Key Metrics

**Success Rate per Feed:**
```sql
SELECT
    f.name,
    COUNT(*) FILTER (WHERE fi.scrape_status = 'success') AS success,
    COUNT(*) FILTER (WHERE fi.scrape_status = 'error') AS errors,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fi.scrape_status = 'success') / COUNT(*), 1) AS success_rate
FROM feed_items fi
JOIN feeds f ON fi.feed_id = f.id
WHERE fi.created_at > NOW() - INTERVAL '24 hours'
GROUP BY f.name
HAVING COUNT(*) > 10
ORDER BY success_rate ASC;
```

**Alert Thresholds:**
- **Critical:** Success rate < 30% (excluding known paywalls)
- **Warning:** Success rate < 50%
- **Info:** Success rate < 70%

**RabbitMQ Queue Depth:**
```bash
# Alert if queue grows beyond threshold
rabbitmqadmin list queues name messages | grep scraping.jobs
# Alert if messages > 1000
```

### Recommended Dashboards

**Grafana Metrics:**
1. Scraping success rate (24h rolling window)
2. Queue depth over time
3. Average scraping latency per feed
4. Error rate by error type
5. DLQ message count

**Alert Rules:**
```yaml
# Prometheus AlertManager
groups:
  - name: scraping_alerts
    rules:
      - alert: ScrapingSuccessRateLow
        expr: scraping_success_rate < 0.5
        for: 1h
        annotations:
          summary: "Scraping success rate below 50%"

      - alert: ScrapingQueueBacklog
        expr: rabbitmq_queue_messages{queue="scraping.jobs"} > 1000
        for: 15m
        annotations:
          summary: "Scraping queue has >1000 pending messages"
```

---

## Best Practices

### When to Use newspaper4k
✅ **Use for:**
- Static HTML news sites
- Open content (no paywall)
- Standard article structure
- English/Western European languages

❌ **Don't use for:**
- Hard paywalls (Economist, WSJ)
- Heavy JavaScript sites
- Complex authentication requirements

### When to Use playwright
✅ **Use for:**
- JavaScript-rendered content
- SPAs and modern web frameworks
- Sites with bot detection
- Complex page interactions

❌ **Don't use for:**
- Simple static sites (overkill)
- High-volume scraping (too slow)
- Resource-constrained environments

### Feed Configuration

**Set realistic expectations:**
```python
# In feed configuration
feed_config = {
    "scrape_full_content": True,
    "scrape_method": "newspaper4k",  # or "playwright"
    "scrape_failure_threshold": 5,   # Higher for paywall sources
    "expected_success_rate": 0.7,    # 70% for open content
}
```

**For known paywall sources:**
```python
paywall_config = {
    "scrape_full_content": False,  # Don't attempt scraping
    "use_rss_summary": True,       # Use RSS description instead
    "scrape_failure_threshold": 1, # Mark as failed immediately
}
```

---

## Troubleshooting

### Symptom: 100% Failure Rate for New Feed

**Diagnosis Steps:**
1. Check if feed URL is accessible: `curl -I <feed_url>`
2. Check for paywall: Visit URL in browser
3. Check for JavaScript: View page source vs rendered content
4. Check scraping logs: `docker logs news-scraping-service | grep <feed_name>`

**Common Causes:**
- Paywall (accept RSS summary only)
- Bot detection (add user-agent, slow down requests)
- JavaScript content (switch to playwright)
- Invalid URL (fix in database)

### Symptom: Intermittent Failures

**Diagnosis Steps:**
1. Check network latency: Time pattern in failures?
2. Check rate limiting: 429 errors in logs?
3. Check server uptime: Target site having issues?

**Common Causes:**
- Rate limiting (reduce concurrent requests)
- Temporary server errors (retry with backoff)
- Network timeouts (increase timeout threshold)

### Symptom: Truncated Content

**Diagnosis Steps:**
1. Compare scraped content to browser view
2. Check if content is lazy-loaded (scroll down in browser)
3. Check article.text length vs expected

**Common Causes:**
- JavaScript content loading (use playwright)
- Pagination (article spread across multiple pages)
- Incorrect HTML selector (newspaper4k auto-detection failed)

---

## Future Improvements

### Planned Enhancements

1. **Adaptive Scraping Method Selection**
   - Auto-detect JavaScript requirement
   - Fall back to playwright if newspaper4k fails
   - Per-feed method override

2. **Paywall Detection**
   - Automatic paywall identification
   - Skip scraping for known paywalls
   - Use RSS summary instead

3. **Content Quality Scoring**
   - Detect incomplete scrapes
   - Flag suspiciously short articles
   - Trigger re-scrape with alternative method

4. **Multi-Language Support**
   - Language-specific parsers
   - Encoding auto-detection
   - Translation integration

5. **Smart Retry Logic**
   - Exponential backoff for transient errors
   - Don't retry permanent failures (403, 404)
   - Separate DLQ for paywall vs technical errors

---

## References

- Scraping Service Documentation: [docs/services/scraping-service.md](../services/scraping-service.md)
- Feed Sources: [services/feed-service/docs/feed-sources.md](../../services/feed-service/docs/feed-sources.md)
- RabbitMQ Queue Management: [docs/guides/rabbitmq-guide.md](rabbitmq-guide.md)
- newspaper4k Documentation: https://github.com/AndyTheFactory/newspaper4k
- Playwright Documentation: https://playwright.dev/python/
