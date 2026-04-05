# Feed Sources Documentation

**Last Updated:** 2025-11-02
**Total Feeds:** 56
**Active Feeds:** 56

---

## Overview

This document lists all configured RSS/Atom feeds in the News Microservices platform, including their configuration, credibility assessment, and operational status.

### Configuration Summary

All 56 feeds are configured with:
- **Fetch Interval:** 15 minutes
- **Full-Content Scraping:** Enabled (newspaper4k method)
- **Source Assessment:** Completed via Research Service
- **Analysis Options:** All 7 enabled
  - Categorization
  - Finance Sentiment Analysis
  - Geopolitical Sentiment Analysis
  - OSINT Analysis
  - Summary Generation
  - Entity Extraction
  - Topic Classification

---

## Feed Categories

### Politics & World News (10 feeds)

| Feed Name | URL | Tier | Reputation | Status |
|-----------|-----|------|------------|--------|
| BBC News - World | http://feeds.bbci.co.uk/news/world/rss.xml | tier_1 | 95/100 | ✅ Active |
| The Guardian - World | https://www.theguardian.com/world/rss | tier_1 | 92/100 | ✅ Active |
| The New York Times - World | https://rss.nytimes.com/services/xml/rss/nyt/World.xml | tier_1 | 90/100 | ✅ Active |
| Washington Post World | https://feeds.washingtonpost.com/rss/world | tier_1 | 95/100 | ✅ Active |
| Times of India - World | https://timesofindia.indiatimes.com/rssfeeds/296589292.cms | tier_2 | 85/100 | ✅ Active |
| Times of India - Top Stories | https://timesofindia.indiatimes.com/rssfeedstopstories.cms | tier_2 | 85/100 | ✅ Active |
| Xinhua News English | https://www.xinhuanet.com/english/rss/worldrss.xml | tier_2 | 65/100 | ✅ Active |
| POLITICO - Politics | https://rss.politico.com/politics-news.xml | tier_2 | 85/100 | ✅ Active |
| Le Monde English | https://www.lemonde.fr/en/rss/une.xml | tier_1 | 95/100 | ✅ Active |
| Asahi Shimbun | https://www.asahi.com/rss/asahi/newsheadlines.rdf | tier_1 | 95/100 | ✅ Active |

### Finance & Business (7 feeds)

| Feed Name | URL | Tier | Reputation | Status |
|-----------|-----|------|------------|--------|
| The Economist - World this week | https://www.economist.com/the-world-this-week/rss.xml | tier_1 | 95/100 | ✅ Active |
| Wall Street Journal - Markets | https://feeds.content.dowjones.io/public/rss/mw_bulletins | tier_1 | 95/100 | ✅ Active |
| Bank for International Settlements | https://www.bis.org/doclist/rss_all_categories.rss | tier_1 | 98/100 | ✅ Active |
| U.S. Federal Reserve | https://www.federalreserve.gov/feeds/press_all.xml | tier_1 | 98/100 | ✅ Active |
| The Block (Crypto) | https://www.theblock.co/rss.xml | tier_2 | 75/100 | ✅ Active |
| Coindesk | [URL from existing feed] | tier_2 | 75/100 | ✅ Active |
| connectmoney.com | https://www.connectmoney.com/feed/ | tier_2 | 75/100 | ✅ Active |

### Security & Defense (8 feeds)

| Feed Name | URL | Tier | Reputation | Status |
|-----------|-----|------|------------|--------|
| Krebs on Security | https://krebsonsecurity.com/feed/ | tier_1 | 95/100 | ✅ Active |
| The Hacker News | https://thehackernews.com/feeds/posts/default | tier_2 | 75/100 | ✅ Active |
| Threatpost | https://threatpost.com/feed/ | tier_2 | 85/100 | ✅ Active |
| Defense News | https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml | tier_2 | 85/100 | ✅ Active |
| Bellingcat Investigations | https://www.bellingcat.com/feed/ | tier_1 | 90/100 | ✅ Active |
| War on the Rocks | https://warontherocks.com/feed/ | tier_2 | 80/100 | ✅ Active |
| The Diplomat | https://thediplomat.com/feed/ | tier_1 | 90/100 | ✅ Active |
| ReliefWeb | https://reliefweb.int/updates/rss.xml | tier_1 | 90/100 | ✅ Active |

### Regional News (6 feeds)

| Feed Name | URL | Tier | Reputation | Status |
|-----------|-----|------|------------|--------|
| Meduza English | https://meduza.io/rss/en/all | tier_1 | 92/100 | ✅ Active |
| The Moscow Times | https://www.themoscowtimes.com/rss/news | tier_2 | 85/100 | ✅ Active |
| Ukrainska Pravda English | https://www.pravda.com.ua/eng/rss/ | tier_2 | 85/100 | ✅ Active |
| MercoPress (Latin America) | https://en.mercopress.com/rss/latin-america | tier_2 | 65/100 | ✅ Active |
| The Star Malaysia | https://www.thestar.com.my/rss/news/ | tier_2 | 75/100 | ✅ Active |
| derStandard.at International | https://www.derstandard.at/rss/international | tier_1 | 92/100 | ✅ Active |

### European News (2 feeds)

| Feed Name | URL | Tier | Reputation | Status |
|-----------|-----|------|------------|--------|
| FAZ.net (German) | https://www.faz.net/rss/aktuell/edition/ | tier_1 | 90/100 | ✅ Active |
| Der Standard (Austrian) | [URL from existing feed] | tier_1 | 92/100 | ✅ Active |

### Other Existing Feeds (23 feeds)

Legacy feeds from initial setup - see feed-service database for complete list including:
- democracy now
- ABC News Australia
- Various regional and specialized sources

---

## Scraping Performance by Feed

### High Success Rate (90-100%)

**Top Performers:**
- The Hacker News: 100% (50/50)
- The Diplomat: 100% (50/50)
- The Moscow Times: 100% (50/50)
- War on the Rocks: 100% (50/50)
- The Guardian - World: 100% (45/45)
- Times of India - Top Stories: 100% (45/45)
- Meduza English: 100% (30/30)
- BIS: 100% (25/25)
- Defense News: 100% (25/25)
- ReliefWeb: 100% (20/20)

### Known Scraping Limitations (Paywall/Technical)

**See:** [docs/guides/scraping-limitations.md](../guides/scraping-limitations.md)

Feeds with expected scraping errors:
- The Economist: 0% success (paywall)
- Asahi Shimbun: 0% success (Japanese encoding)
- The Block: Partial success (20 errors)
- Le Monde: Partial success (18 errors)
- WSJ Markets: Partial success (10 errors, paywall)

---

## Import History

### Initial Import (October 2024)
- 24 feeds imported manually

### Batch Import (November 2, 2025)
- 32 premium feeds imported via automated script
- Source assessment performed for all feeds
- All analysis options enabled
- Scraping activated on 4 legacy feeds

**Import Script:** `/tmp/import_feeds_batch.py`
**Import Results:** `/tmp/import_results.json`

---

## Maintenance Notes

### Fetch Schedule
- **Interval:** 15 minutes
- **Staggering:** Not implemented (all feeds fetch simultaneously)
- **Impact:** Low (system handles concurrent fetches well)

### Monitoring
- **Success Rate Target:** >70% overall
- **Alert Threshold:** <50% success rate per feed
- **Error Tracking:** RabbitMQ DLQ for failed scraping jobs

### Known Issues
1. **PATCH Endpoint 405:** Feed-service doesn't support `last_fetched_at` updates
2. **Event Format Errors:** Some `feed.item.created` events missing `url` field
3. **Paywall Sources:** Expected 0-30% success rate for premium publications

---

## Feed Management

### Adding New Feeds

**Recommended Method:** Batch import script with source assessment

```bash
# 1. Create CSV with feed data
# Format: Name,URL,Category,Source

# 2. Get auth token
/tmp/get_token.sh

# 3. Run import script
python3 /tmp/import_feeds_batch.py <AUTH_TOKEN>
```

**Manual Method:** Frontend interface at `http://localhost:3000/feeds`

**See:** [docs/guides/feed-import-guide.md](../guides/feed-import-guide.md)

### Disabling Feeds

```sql
UPDATE feeds
SET is_active = false
WHERE name = 'Feed Name';
```

### Updating Feed Configuration

Use frontend interface or direct database updates:
```sql
UPDATE feeds
SET fetch_interval = 30,
    scrape_full_content = true
WHERE id = <feed_id>;
```

---

## Statistics

**As of November 2, 2025:**
- Total Feeds: 56
- Active Feeds: 56
- Tier 1 Sources: 28 (50%)
- Tier 2 Sources: 28 (50%)
- Average Reputation Score: 86/100
- Overall Scraping Success Rate: 72%
- Total Articles Fetched (initial): 774
- Articles Successfully Scraped: 567

---

## References

- Feed Service API: [docs/api/feed-service-api.md](../api/feed-service-api.md)
- Scraping Service: [docs/services/scraping-service.md](../services/scraping-service.md)
- Research Service: [docs/services/research-service.md](../services/research-service.md)
- Import Guide: [docs/guides/feed-import-guide.md](../guides/feed-import-guide.md)
