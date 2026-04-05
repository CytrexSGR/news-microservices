"""
Article Update Service for NewsML-G2 compliant version tracking.

Epic 0.4: Handles article updates with version history, SimHash recalculation,
and proper NewsML-G2 status transitions.
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FeedItem
from app.models.intelligence import ArticleVersion
from news_intelligence_common import SimHasher


class ArticleUpdateService:
    """
    Service for updating articles with version tracking.

    Features:
    - Version increment on each update
    - ArticleVersion snapshot for history
    - SimHash recalculation on content change
    - NewsML-G2 pub_status management
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_article(
        self,
        article_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        change_type: str = "update",  # update, correction, withdrawal
        change_reason: Optional[str] = None,
    ) -> FeedItem:
        """
        Update an article with version tracking.

        Args:
            article_id: UUID of article to update
            title: New title (optional)
            content: New content (optional)
            description: New description (optional)
            change_type: Type of change (update, correction, withdrawal)
            change_reason: Reason for the change (optional)

        Returns:
            Updated FeedItem

        Raises:
            ValueError: If article not found or invalid change_type
        """
        # Validate change_type
        if change_type not in ('update', 'correction', 'withdrawal'):
            raise ValueError(f"Invalid change_type: {change_type}")

        # Get article
        result = await self.session.execute(
            select(FeedItem).where(FeedItem.id == article_id)
        )
        article = result.scalar_one_or_none()

        if not article:
            raise ValueError(f"Article not found: {article_id}")

        # Create version snapshot BEFORE update
        content_for_hash = f"{article.title}{article.link}{article.description or ''}"
        version_snapshot = ArticleVersion(
            article_id=article.id,
            version=article.version,
            pub_status=article.pub_status,
            title=article.title,
            content_hash=hashlib.sha256(content_for_hash.encode()).hexdigest(),
            change_type=change_type,
            change_reason=change_reason,
        )
        self.session.add(version_snapshot)

        # Update article
        article.version += 1
        article.version_created_at = datetime.now(timezone.utc)

        # Apply field updates
        content_changed = False
        if title is not None and title != article.title:
            article.title = title
            content_changed = True
        if content is not None and content != article.content:
            article.content = content
            content_changed = True
        if description is not None and description != article.description:
            article.description = description
            content_changed = True

        # Handle change type specific logic
        if change_type == "withdrawal":
            article.pub_status = 'canceled'
        elif change_type == "correction":
            # For self-correction, just update - no special flag needed
            # is_correction flag is for articles that correct OTHER articles
            pass

        # Recalculate SimHash if content changed
        if content_changed:
            simhash_text = article.title or ""
            if article.content:
                simhash_text = f"{simhash_text} {article.content}"
            elif article.description:
                simhash_text = f"{simhash_text} {article.description}"

            if simhash_text.strip():
                article.simhash_fingerprint = SimHasher.compute_fingerprint(simhash_text)

        await self.session.flush()
        return article

    async def get_version_history(self, article_id: UUID) -> list[ArticleVersion]:
        """
        Get version history for an article.

        Args:
            article_id: UUID of article

        Returns:
            List of ArticleVersion records, newest first
        """
        result = await self.session.execute(
            select(ArticleVersion)
            .where(ArticleVersion.article_id == article_id)
            .order_by(ArticleVersion.version.desc())
        )
        return list(result.scalars().all())
