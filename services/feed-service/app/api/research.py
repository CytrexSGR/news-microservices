"""
Research Article & Analysis Trigger API endpoints

Handles research article creation and V3 analysis triggering.
Split from feeds.py for better maintainability.
"""
from datetime import datetime
from uuid import UUID
import json
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import FeedItem
from app.schemas import (
    FeedItemResponse,
    ResearchArticleCreate,
)
from app.api.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["research"])


@router.post("/items/{item_id}/analyze", response_model=dict)
async def trigger_article_analysis(
    item_id: UUID,
    run_tier2: bool = Query(default=True, description="Enable Tier2 specialist analysis"),
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Trigger V3 content analysis for an existing article.

    This endpoint queues an analysis.v3.request event for the specified article,
    which will be processed by the content-analysis-v3 service.

    Works for any article type (RSS, research, manual, etc.).

    - **item_id**: UUID of the article to analyze
    - **run_tier2**: Enable Tier2 specialist analysis (default: true)
    """
    # Get the article
    result = await db.execute(
        select(FeedItem).where(FeedItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail=f"Article {item_id} not found")

    # Check if article has content
    if not item.content:
        raise HTTPException(
            status_code=400,
            detail="Article has no content. Cannot trigger analysis without content."
        )

    # Insert analysis.v3.request event to outbox
    await db.execute(
        text("""
            INSERT INTO event_outbox (event_type, payload)
            VALUES (:event_type, :payload)
        """),
        {
            "event_type": "analysis.v3.request",
            "payload": json.dumps({
                "article_id": str(item.id),
                "title": item.title,
                "url": item.link,
                "content": item.content,
                "run_tier2": run_tier2,
            })
        }
    )

    await db.commit()

    logger.info(f"Triggered V3 analysis for article {item_id} (run_tier2={run_tier2})")

    return {
        "success": True,
        "article_id": str(item_id),
        "message": f"V3 analysis queued for article: {item.title[:50]}...",
        "event_type": "analysis.v3.request",
        "run_tier2": run_tier2,
    }


@router.post("/items/research", response_model=FeedItemResponse, status_code=201)
async def create_research_article(
    research: ResearchArticleCreate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a research article (e.g., from Perplexity API).

    Research articles are stored with source_type='perplexity_research' and can be
    linked to a parent article via parent_article_id.

    Optionally triggers V3 content analysis automatically (default: enabled).

    - **title**: Research article title
    - **link**: URL of the research source
    - **content**: Research content (required for analysis)
    - **parent_article_id**: Optional parent article UUID to link research to
    - **source_metadata**: Optional metadata (model, cost, query, citations)
    - **trigger_analysis**: Auto-trigger V3 analysis (default: true)
    """
    # Validate parent article exists if provided
    if research.parent_article_id:
        parent_result = await db.execute(
            select(FeedItem.id).where(FeedItem.id == research.parent_article_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"Parent article {research.parent_article_id} not found"
            )

    # Generate content hash for deduplication
    content_hash = hashlib.md5(
        f"{research.title}{research.content}".encode()
    ).hexdigest()

    # Check for duplicates
    existing = await db.execute(
        select(FeedItem.id).where(FeedItem.content_hash == content_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Research article with identical content already exists"
        )

    # Create the research article
    new_item = FeedItem(
        title=research.title,
        link=research.link,
        description=research.description,
        content=research.content,
        author=research.author,
        published_at=research.published_at or datetime.utcnow(),
        content_hash=content_hash,
        feed_id=None,  # Research articles don't belong to a feed
        source_type="perplexity_research",
        source_metadata=research.source_metadata,
        parent_article_id=research.parent_article_id,
    )

    db.add(new_item)
    await db.flush()  # Get the ID before committing

    # Trigger V3 analysis if requested
    if research.trigger_analysis:
        await db.execute(
            text("""
                INSERT INTO event_outbox (event_type, payload)
                VALUES (:event_type, :payload)
            """),
            {
                "event_type": "analysis.v3.request",
                "payload": json.dumps({
                    "article_id": str(new_item.id),
                    "title": new_item.title,
                    "url": new_item.link,
                    "content": new_item.content,
                    "run_tier2": True,
                })
            }
        )
        logger.info(f"Queued V3 analysis for new research article {new_item.id}")

    await db.commit()
    await db.refresh(new_item)

    logger.info(
        f"Created research article {new_item.id}: {new_item.title[:50]}... "
        f"(parent={research.parent_article_id}, analysis={'queued' if research.trigger_analysis else 'skipped'})"
    )

    return FeedItemResponse(
        id=new_item.id,
        feed_id=new_item.feed_id,
        title=new_item.title,
        link=new_item.link,
        description=new_item.description,
        content=new_item.content,
        author=new_item.author,
        published_at=new_item.published_at,
        guid=new_item.guid,
        content_hash=new_item.content_hash,
        scraped_at=new_item.scraped_at,
        scrape_status=new_item.scrape_status,
        scrape_word_count=new_item.scrape_word_count,
        created_at=new_item.created_at,
        source_type=new_item.source_type,
        source_metadata=new_item.source_metadata,
        parent_article_id=new_item.parent_article_id,
    )
