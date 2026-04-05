"""
Intelligence API Router for analytics-service.

Provides endpoints for:
- Signal Decay (time-based relevance weighting)
- Burst Detection (Kleinberg algorithm for breaking news)
- Sentiment Momentum (first derivative of sentiment)
- Contrarian Alerts (extreme sentiment detection)
- Novelty Score (duplicate story detection)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import structlog

from app.core.database import get_async_db
from app.core.auth import get_current_user, get_optional_user
from app.services.signal_decay import signal_decay_service
from app.services.burst_detection import burst_detection_service
from app.services.sentiment_momentum import sentiment_momentum_service
from app.services.contrarian_alerts import contrarian_alert_service
from app.services.novelty_scoring import novelty_scorer
from app.services.webhook_notifier import webhook_notifier
from app.services.rag_service import get_rag_service

logger = structlog.get_logger()

router = APIRouter()


# ==================== TOP STORIES (Signal Decay) ====================

@router.get("/top-stories")
async def get_top_stories(
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    apply_decay: bool = Query(True, description="Apply signal decay weighting"),
    min_priority: float = Query(7.0, ge=0, le=10, description="Minimum PriorityScore"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get top stories with optional signal decay applied.

    Signal decay weights articles by age - breaking news decays faster
    than feature articles.

    Half-lives:
    - BREAKING: 4 hours
    - EARNINGS: 12 hours
    - ANALYSIS: 24 hours
    - FEATURE: 48 hours
    """
    from sqlalchemy import text

    # Build query with interval directly (hours is validated integer)
    query = text(f"""
        SELECT
            aa.article_id,
            COALESCE(aa.triage_results->>'priority_score', '5') as priority_score,
            COALESCE(aa.tier1_results->'summary'->>'event_type', 'DEFAULT') as event_type,
            aa.created_at,
            COALESCE(aa.tier1_results->'topics'->>0, 'Unknown') as topic,
            fi.title as title,
            fi.link as source_url,
            COALESCE(aa.tier1_results->>'summary', fi.description) as summary
        FROM article_analysis aa
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.created_at > NOW() - INTERVAL '{hours} hours'
          AND COALESCE((aa.triage_results->>'priority_score')::float, 5) >= :min_priority
          AND aa.tier1_results IS NOT NULL
        ORDER BY COALESCE((aa.triage_results->>'priority_score')::float, 5) DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {
        "min_priority": min_priority,
        "limit": limit * 2  # Fetch more for decay filtering
    })

    articles = []
    for row in result.fetchall():
        try:
            priority = float(row.priority_score) if row.priority_score else 5.0
        except (ValueError, TypeError):
            priority = 5.0

        article = {
            "article_id": str(row.article_id),
            "priority_score": priority,
            "event_type": row.event_type or "DEFAULT",
            "published_at": row.created_at.isoformat() if row.created_at else None,
            "topic": row.topic or "Unknown",
            "title": row.title or "Untitled",
            "source_url": row.source_url,
            "summary": row.summary[:200] if row.summary else ""
        }
        articles.append(article)

    if apply_decay:
        ranked = signal_decay_service.rank_articles(
            articles,
            score_field="priority_score",
            published_field="published_at",
            event_type_field="event_type"
        )
        return ranked[:limit]

    return articles[:limit]


# ==================== BURST DETECTION ====================

@router.get("/bursts")
async def get_bursts(
    entity: Optional[str] = Query(None, description="Entity to analyze"),
    hours: int = Query(24, ge=1, le=168, description="Time window"),
    min_level: int = Query(2, ge=1, le=5, description="Minimum burst intensity"),
    notify_webhook: bool = Query(False, description="Send alerts to n8n"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Detect entity mention bursts (breaking news indicator).

    Uses Kleinberg's burst detection algorithm to find sudden
    spikes in entity mentions.

    - **entity**: Specific entity to check (scans all if omitted)
    - **min_level**: Minimum burst intensity (1-5)
    - **notify_webhook**: Trigger n8n workflow for high-level bursts
    """
    try:
        if entity:
            bursts = await burst_detection_service.detect_bursts(
                entity, hours, db=db
            )
            bursts = [b for b in bursts if b.level >= min_level]
        else:
            bursts = await burst_detection_service.get_all_active_bursts(
                hours, min_level, db=db
            )

        # Convert to dicts
        burst_dicts = [b.to_dict() for b in bursts[:limit]]

        # Optionally notify n8n webhook
        if notify_webhook:
            for burst in bursts[:3]:  # Top 3 only
                if burst.level >= 3:  # High intensity only
                    await webhook_notifier.notify_burst(
                        burst.to_dict(),
                        articles=[]  # TODO: fetch related articles
                    )

        return {
            "bursts": burst_dicts,
            "total_found": len(burst_dicts),
            "time_window_hours": hours,
            "min_level": min_level
        }

    except Exception as e:
        logger.error("Burst detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Burst detection failed: {str(e)}")


# ==================== SENTIMENT MOMENTUM ====================

@router.get("/momentum")
async def get_sentiment_momentum(
    entity: Optional[str] = Query(None, description="Entity to analyze"),
    days: int = Query(7, ge=3, le=30, description="Analysis window"),
    direction: Optional[str] = Query(
        None,
        regex="^(improving|deteriorating)$",
        description="Filter by momentum direction"
    ),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate sentiment momentum (rate of change).

    Detects when sentiment is changing direction - often precedes
    price reversals.

    - **entity**: Specific entity (optional)
    - **direction**: Filter by "improving" or "deteriorating"
    - **days**: Number of days to analyze (minimum 3)
    """
    try:
        if entity:
            result = await sentiment_momentum_service.calculate_momentum(
                entity, days, db
            )
            return result.to_dict()
        else:
            direction_filter = direction or "improving"
            results = await sentiment_momentum_service.get_momentum_leaders(
                direction=direction_filter,
                days=days,
                limit=limit,
                db=db
            )
            return {
                "momentum_leaders": [r.to_dict() for r in results],
                "direction": direction_filter,
                "days_analyzed": days
            }

    except Exception as e:
        logger.error("Momentum calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Momentum calculation failed: {str(e)}")


# ==================== CONTRARIAN ALERTS ====================

@router.get("/contrarian-alerts")
async def get_contrarian_alerts(
    entity: Optional[str] = Query(None, description="Entity to check"),
    history_days: int = Query(90, ge=30, le=365, description="Historical window"),
    limit: int = Query(20, ge=1, le=50, description="Max alerts"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Detect extreme sentiment conditions (contrarian signals).

    - **EUPHORIA**: Sentiment >3 std above mean
    - **PANIC**: Sentiment >3 std below mean

    When sentiment is at historical extremes, it often signals
    a reversal opportunity.
    """
    try:
        if entity:
            alert = await contrarian_alert_service.check_entity(
                entity, history_days, db
            )
            if alert:
                return alert.to_dict()
            return {
                "entity": entity,
                "alert_type": None,
                "message": "No extreme sentiment detected"
            }
        else:
            alerts = await contrarian_alert_service.scan_all_entities(
                history_days, limit, db
            )
            return {
                "alerts": [a.to_dict() for a in alerts],
                "total_found": len(alerts),
                "history_days": history_days,
                "euphoria_count": len([a for a in alerts if a.alert_type == "EUPHORIA"]),
                "panic_count": len([a for a in alerts if a.alert_type == "PANIC"])
            }

    except Exception as e:
        logger.error("Contrarian alert scan failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Contrarian scan failed: {str(e)}")


# ==================== NOVELTY SCORE ====================

@router.post("/novelty")
async def calculate_novelty(
    article_id: str = Query(..., description="Article ID"),
    entities: List[str] = Query(..., description="Entity names"),
    event_type: str = Query("DEFAULT", description="Event type"),
    primary_topic: str = Query("", description="Primary topic"),
    published_at: Optional[datetime] = Query(None, description="Publication time"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate novelty score for an article.

    Uses fingerprinting to detect if similar stories have been
    recently reported.

    Returns:
    - **novelty_score**: 0.0 (duplicate) to 1.0 (completely new)
    - **is_novel**: True if score > threshold
    - **similar_article_id**: ID of similar article (if found)
    """
    try:
        pub_time = published_at or datetime.utcnow()

        result = await novelty_scorer.calculate_novelty(
            article_id=article_id,
            entities=entities,
            event_type=event_type,
            primary_topic=primary_topic,
            published_at=pub_time
        )

        return result.to_dict()

    except Exception as e:
        logger.error("Novelty calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Novelty calculation failed: {str(e)}")


@router.get("/novelty/stats")
async def get_novelty_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get novelty cache statistics.
    """
    return await novelty_scorer.get_cache_stats()


# ==================== ENTITY SENTIMENT TIMESERIES ====================

@router.get("/entity-sentiment-history")
async def get_entity_sentiment_history(
    entity: str = Query(..., min_length=1, max_length=200, description="Entity name to search for (e.g., 'Trump', 'Rheinmetall')"),
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    db: AsyncSession = Depends(get_async_db),
    # Note: No auth required - public endpoint for MCP tools
):
    """
    Get sentiment timeseries for an entity.

    Aggregates bias_score by day for all articles mentioning the entity.
    Useful for tracking sentiment changes over time.

    - **entity**: Entity name (case-insensitive search)
    - **days**: Number of days to look back (default: 30)

    Returns daily aggregated sentiment with article counts.
    """
    from sqlalchemy import text

    try:
        # Query with interval directly (days is validated integer)
        query = text(f"""
            WITH entity_articles AS (
                SELECT
                    fi.published_at::date as day,
                    (aa.tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_score')::float as sentiment,
                    e.value->>'name' as entity_name
                FROM article_analysis aa
                JOIN feed_items fi ON aa.article_id = fi.id
                CROSS JOIN LATERAL jsonb_array_elements(aa.tier1_results->'entities') as e
                WHERE LOWER(e.value->>'name') LIKE LOWER(:entity_pattern)
                  AND aa.tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_score' IS NOT NULL
                  AND fi.published_at >= NOW() - INTERVAL '{days} days'
            )
            SELECT
                day,
                ROUND(AVG(sentiment)::numeric, 3) as avg_sentiment,
                COUNT(*) as article_count,
                ROUND(STDDEV(sentiment)::numeric, 3) as sentiment_stddev,
                ROUND(MIN(sentiment)::numeric, 3) as min_sentiment,
                ROUND(MAX(sentiment)::numeric, 3) as max_sentiment
            FROM entity_articles
            GROUP BY day
            ORDER BY day DESC
        """)

        result = await db.execute(query, {"entity_pattern": f"%{entity}%"})
        rows = result.fetchall()

        if not rows:
            return {
                "entity": entity,
                "days_requested": days,
                "data": [],
                "total_days": 0,
                "message": f"No articles found mentioning '{entity}' in the last {days} days"
            }

        timeseries = [
            {
                "date": row.day.isoformat(),
                "sentiment": float(row.avg_sentiment) if row.avg_sentiment else None,
                "article_count": row.article_count,
                "sentiment_stddev": float(row.sentiment_stddev) if row.sentiment_stddev else None,
                "min_sentiment": float(row.min_sentiment) if row.min_sentiment else None,
                "max_sentiment": float(row.max_sentiment) if row.max_sentiment else None
            }
            for row in rows
        ]

        # Calculate summary statistics
        total_articles = sum(d["article_count"] for d in timeseries)
        avg_overall = sum(d["sentiment"] * d["article_count"] for d in timeseries if d["sentiment"]) / total_articles if total_articles > 0 else None

        return {
            "entity": entity,
            "days_requested": days,
            "total_days": len(timeseries),
            "total_articles": total_articles,
            "avg_sentiment_overall": round(avg_overall, 3) if avg_overall else None,
            "data": timeseries
        }

    except Exception as e:
        logger.error("Entity sentiment history failed", entity=entity, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get entity sentiment history: {str(e)}")


# ==================== COMBINED INTELLIGENCE ====================

@router.get("/summary")
async def get_intelligence_summary(
    hours: int = Query(24, ge=1, le=168, description="Time window"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_optional_user)
):
    """
    Get combined intelligence summary.

    Returns all active signals:
    - Active bursts
    - Sentiment turnarounds
    - Contrarian alerts
    """
    try:
        # Get active bursts
        bursts = await burst_detection_service.get_all_active_bursts(
            hours=min(hours, 6),  # Bursts are short-term
            min_level=2,
            db=db
        )

        # Get momentum leaders (both directions)
        improving = await sentiment_momentum_service.get_momentum_leaders(
            direction="improving",
            days=7,
            limit=5,
            db=db
        )
        deteriorating = await sentiment_momentum_service.get_momentum_leaders(
            direction="deteriorating",
            days=7,
            limit=5,
            db=db
        )

        # Get contrarian alerts
        alerts = await contrarian_alert_service.scan_all_entities(
            history_days=90,
            limit=10,
            db=db
        )

        return {
            "time_window_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            "bursts": {
                "count": len(bursts),
                "items": [b.to_dict() for b in bursts[:5]]
            },
            "momentum": {
                "improving": [m.to_dict() for m in improving],
                "deteriorating": [m.to_dict() for m in deteriorating]
            },
            "contrarian": {
                "count": len(alerts),
                "euphoria": [a.to_dict() for a in alerts if a.alert_type == "EUPHORIA"][:3],
                "panic": [a.to_dict() for a in alerts if a.alert_type == "PANIC"][:3]
            }
        }

    except Exception as e:
        logger.error("Intelligence summary failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


# ==================== ASK INTELLIGENCE (RAG) ====================

@router.get("/ask")
async def ask_intelligence(
    question: str = Query(..., min_length=5, max_length=500, description="Natural language question"),
    depth: str = Query("brief", regex="^(brief|detailed)$", description="Response depth: brief (2-3 sentences) or detailed (full analysis)"),
    # Note: No auth required - public endpoint for MCP tools
):
    """
    Ask an intelligence question and get a concise answer.

    Uses RAG (Retrieval-Augmented Generation) to:
    1. Find relevant articles via semantic search
    2. Aggregate intelligence context (bursts, sentiment, etc.)
    3. Generate answer using LLM

    This endpoint does the heavy lifting so Claude doesn't have to process raw data.

    **Examples:**
    - "What are the top risks for Defense ETFs?"
    - "How has sentiment changed for Rheinmetall this week?"
    - "What's driving the Iran news cluster?"

    **Depth options:**
    - `brief`: 2-3 sentence answer (default)
    - `detailed`: Full analysis with evidence and risk assessment
    """
    try:
        rag_service = get_rag_service()
        result = await rag_service.ask(question=question, depth=depth)

        return {
            "question": question,
            "answer": result.answer,
            "depth": result.depth,
            "sources": [
                {
                    "title": s.title,
                    "url": s.url,
                    "similarity": s.similarity,
                    "published_at": s.published_at,
                }
                for s in result.sources
            ],
            "metadata": {
                "tokens_used": result.tokens_used,
                "context_articles": result.context_articles,
                "model": result.metadata.get("model"),
            }
        }

    except Exception as e:
        logger.error("Ask intelligence failed", question=question, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


# ==================== GET INTELLIGENCE CONTEXT (No LLM) ====================

@router.get("/context")
async def get_intelligence_context(
    question: str = Query(..., min_length=3, max_length=500, description="Natural language question for semantic search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum articles to return"),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    entity: Optional[str] = Query(None, description="Filter by entity name"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    days: int = Query(7, ge=1, le=90, description="Time window in days"),
    # Note: No auth required - public endpoint for MCP tools
):
    """
    Get intelligence context data for Claude to interpret directly.

    Unlike `/ask` which uses an LLM to generate answers, this endpoint
    returns raw, structured data that Claude Desktop interprets directly.

    **Use this tool for:**
    - Claude Desktop queries (eliminates redundant LLM call)
    - Programmatic access to intelligence context
    - Custom analysis workflows

    **Use `/ask` instead for:**
    - Quick human-readable answers
    - Non-Claude clients needing pre-interpreted data
    - API spot-checks

    **Response format follows iterative drill-down pattern:**
    - `total_found`: Total matching articles
    - `showing`: Number returned (respects limit)
    - `has_more`: True if more results available
    - `filters_applied`: What filters are active
    - `articles`: Structured article data with snippets
    - `intelligence_summary`: Current bursts, momentum, contrarian signals
    """
    from app.services.intelligence_context import get_intelligence_context_service

    try:
        service = get_intelligence_context_service()
        result = await service.get_context(
            question=question,
            limit=limit,
            min_similarity=min_similarity,
            entity_filter=entity,
            sector_filter=sector,
            days=days,
        )
        return result

    except Exception as e:
        logger.error("Get intelligence context failed", question=question, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")
