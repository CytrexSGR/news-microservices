"""
Celery tasks for ingesting articles into intelligence events
"""
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from sqlalchemy import text, or_

from app.celery_app import celery_app
from app.database import SyncSessionLocal
from app.clients.feed_client import feed_client
from app.models.event import IntelligenceEvent

# Sentiment Analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Initialize VADER sentiment analyzer (singleton)
_sentiment_analyzer = None


def get_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    """Get or create VADER sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer


# Category mapping (V3 → Intelligence)
CATEGORY_MAPPING = {
    "CONFLICT": "geo", "POLITICS": "geo", "HUMANITARIAN": "geo",
    "SECURITY": "geo", "FINANCE": "finance", "TECHNOLOGY": "tech",
    "HEALTH": "geo", "OTHER": "geo",
}


def _clean_html(html_text: str) -> str:
    """Remove HTML tags and clean text"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return re.sub(r'\s+', ' ', soup.get_text()).strip()


def _normalize_source(source_url: str) -> str:
    """Extract clean source name from URL"""
    if not source_url:
        return "Unknown"
    match = re.search(r'https?://(?:www\.)?([^/]+)', source_url)
    return match.group(1).split('.')[0].capitalize() if match else "Unknown"


@celery_app.task(name="app.tasks.ingestion.ingest_recent_articles", bind=True)
def ingest_recent_articles(self, hours: int = 1, limit: int = 500) -> Dict[str, Any]:
    """
    Celery task to ingest recent articles from feed service.
    Fully synchronous - no async event loop needed.
    """
    logger.info(f"Starting ingestion task: hours={hours}, limit={limit}")

    start_time = datetime.utcnow()
    stats = {
        "task_id": self.request.id,
        "started_at": start_time.isoformat(),
        "fetched": 0,
        "created": 0,
        "duplicates": 0,
        "errors": 0,
    }

    try:
        # Fetch articles using sync method (no async engine needed)
        articles = feed_client.get_recent_articles_sync(hours=hours, limit=limit)
        stats["fetched"] = len(articles)
        logger.info(f"Fetched {len(articles)} articles from Feed Service")

        with SyncSessionLocal() as db:
            # Batch-load existing titles from last 24h for duplicate detection
            # This replaces N individual queries with 1 bulk query
            cutoff_24h = datetime.utcnow() - timedelta(hours=24)
            existing_titles = set()
            title_rows = db.query(IntelligenceEvent.title).filter(
                IntelligenceEvent.published_at >= cutoff_24h
            ).all()
            for row in title_rows:
                if row.title:
                    existing_titles.add(row.title.lower().strip())

            logger.info(f"Loaded {len(existing_titles)} existing titles for dedup")

            for article in articles:
                try:
                    title = _clean_html(article.get("title", ""))
                    description = _clean_html(article.get("description", ""))
                    source_url = article.get("link", article.get("url", ""))
                    source = _normalize_source(source_url)

                    # Parse published date
                    published_at_str = article.get("published_at")
                    if isinstance(published_at_str, str):
                        try:
                            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                        except ValueError:
                            published_at = datetime.utcnow()
                    else:
                        published_at = published_at_str or datetime.utcnow()

                    # Check for duplicates using in-memory title set
                    title_lower = title.lower().strip()
                    if title_lower in existing_titles:
                        stats["duplicates"] += 1
                        continue

                    # Map category
                    category = None
                    v3_analysis = article.get("v3_analysis", {})
                    if v3_analysis:
                        v3_cat = v3_analysis.get("tier0", {}).get("category")
                        category = CATEGORY_MAPPING.get((v3_cat or "").upper(), "geo") if v3_cat else None

                    # Create event (sync)
                    event = IntelligenceEvent(
                        title=title,
                        description=description,
                        source=source,
                        source_url=source_url,
                        published_at=published_at,
                        language=article.get("language", "en"),
                        category=category,
                        keywords=article.get("keywords", []),
                        entities=article.get("entities", []),
                    )
                    db.add(event)
                    existing_titles.add(title_lower)  # Prevent dupes within same batch
                    stats["created"] += 1

                except Exception as e:
                    logger.error(f"Error processing article {article.get('id')}: {e}")
                    stats["errors"] += 1

            db.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        stats["completed_at"] = end_time.isoformat()
        stats["duration_seconds"] = duration
        stats["success"] = True

        logger.info(
            f"Ingestion completed: created={stats['created']}, "
            f"duplicates={stats['duplicates']}, errors={stats['errors']}, "
            f"duration={duration:.2f}s"
        )

        return stats

    except Exception as e:
        logger.error(f"Ingestion task failed: {e}", exc_info=True)
        stats["success"] = False
        stats["error"] = str(e)
        stats["completed_at"] = datetime.utcnow().isoformat()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries), max_retries=3)


@celery_app.task(name="app.tasks.ingestion.backfill_articles")
def backfill_articles(hours: int = 24, limit: int = 1000) -> Dict[str, Any]:
    """
    One-time task to backfill historical articles

    Args:
        hours: Fetch articles from last N hours
        limit: Maximum articles to fetch

    Returns:
        Statistics about backfill
    """
    logger.info(f"Starting backfill task: hours={hours}, limit={limit}")

    return ingest_recent_articles(hours=hours, limit=limit)


@celery_app.task(name="app.tasks.ingestion.enrich_events_with_analysis", bind=True)
def enrich_events_with_analysis(self, hours: int = 24) -> Dict[str, Any]:
    """
    Enrich existing events with analysis data from article_analysis table

    Args:
        hours: Enrich events from last N hours

    Returns:
        Statistics about enrichment
    """
    logger.info(f"Starting event enrichment: last {hours} hours")

    start_time = datetime.utcnow()
    stats = {
        "task_id": self.request.id,
        "started_at": start_time.isoformat(),
        "events_checked": 0,
        "events_enriched": 0,
        "sentiment_calculated": 0,
        "no_analysis": 0,
        "errors": 0,
    }

    try:
        from datetime import timedelta
        from app.database import SyncSessionLocal
        from app.models.event import IntelligenceEvent
        from sqlalchemy import text, or_

        with SyncSessionLocal() as db:
            # Get events without keywords from last N hours
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            events = db.query(IntelligenceEvent).filter(
                IntelligenceEvent.published_at >= cutoff_date,
                or_(
                    IntelligenceEvent.keywords.is_(None),  # NULL
                    IntelligenceEvent.keywords == []        # Empty array
                )
            ).all()

            stats["events_checked"] = len(events)
            logger.info(f"Found {len(events)} events without keywords")

            # Batch-load all analysis data for the time window (1 query instead of N)
            analysis_query = text("""
                SELECT
                    fi.title,
                    fi.published_at,
                    aa.tier1_results->'topics' as topics_json,
                    aa.tier1_results->'entities' as entities_json
                FROM feed_items fi
                JOIN article_analysis aa ON fi.id = aa.article_id AND aa.success = true
                WHERE fi.published_at >= :cutoff_date
            """)
            analysis_rows = db.execute(analysis_query, {"cutoff_date": cutoff_date}).fetchall()

            # Build lookup dict: title -> analysis data
            analysis_by_title = {}
            for row in analysis_rows:
                if row.title:
                    analysis_by_title[row.title.strip()] = {
                        "topics": row.topics_json or [],
                        "entities": row.entities_json or [],
                    }

            logger.info(f"Loaded {len(analysis_by_title)} analysis records for matching")

            # Initialize VADER analyzer once
            analyzer = get_sentiment_analyzer()

            for event in events:
                try:
                    # Match analysis data by title (in-memory lookup)
                    analysis = analysis_by_title.get(event.title.strip() if event.title else "")

                    if analysis:
                        entities = analysis["entities"]

                        # Extract keywords from entities
                        keywords = []
                        for e in entities:
                            if e.get("type") in ["ORGANIZATION", "PERSON", "LOCATION", "PRODUCT"]:
                                keyword = e.get("name") or e.get("normalized_text") or e.get("text") or ""
                                if keyword:
                                    keywords.append(keyword)

                        event.keywords = keywords
                        event.entities = entities

                        stats["events_enriched"] += 1
                        logger.debug(f"Enriched event: {event.title[:50]} with {len(keywords)} keywords")
                    else:
                        stats["no_analysis"] += 1

                    # Calculate sentiment using VADER
                    text_for_sentiment = event.title or ""
                    if event.description:
                        text_for_sentiment += f" {event.description}"

                    if text_for_sentiment.strip():
                        try:
                            sentiment_scores = analyzer.polarity_scores(text_for_sentiment)
                            event.sentiment = sentiment_scores["compound"]
                            stats["sentiment_calculated"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to calculate sentiment for event {event.id}: {e}")

                except Exception as e:
                    logger.error(f"Error enriching event {event.id}: {e}")
                    stats["errors"] += 1

            db.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        stats["completed_at"] = end_time.isoformat()
        stats["duration_seconds"] = duration
        stats["success"] = True

        logger.info(
            f"Enrichment completed: enriched={stats['events_enriched']}, "
            f"sentiment_calculated={stats['sentiment_calculated']}, "
            f"no_analysis={stats['no_analysis']}, errors={stats['errors']}, "
            f"duration={duration:.2f}s"
        )

        return stats

    except Exception as e:
        logger.error(f"Enrichment task failed: {e}", exc_info=True)
        stats["success"] = False
        stats["error"] = str(e)
        stats["completed_at"] = datetime.utcnow().isoformat()
        raise
