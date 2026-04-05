"""
Tests for article update API endpoints.

Epic 0.4: Tests for PUT /items/{id} and GET /items/{id}/versions endpoints.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock

from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db import get_async_db
from app.models import Feed, FeedItem
from app.models.intelligence import ArticleVersion
from app.api.dependencies import get_current_user_id
from app.services.article_update_service import ArticleUpdateService
from app.services import event_publisher as event_publisher_module


class TestArticleUpdateAPI:
    """Test article update API endpoints."""

    @pytest_asyncio.fixture
    async def article(self, db_session: AsyncSession):
        """Create test article with required NewsML-G2 fields."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="Test Feed",
        )
        db_session.add(feed)
        await db_session.flush()

        item = FeedItem(
            feed_id=feed.id,
            title="Original Title",
            link=f"https://example.com/article/{uuid4()}",
            content="Original content for testing",
            description="Original description",
            content_hash=f"hash{uuid4().hex[:8]}",
            version=1,
            version_created_at=datetime.now(timezone.utc),
            pub_status='usable',
            # Use smaller value that fits in SQLite INTEGER for tests
            # PostgreSQL BIGINT supports larger values in production
            simhash_fingerprint=1234567890123456,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        return item

    @pytest_asyncio.fixture
    async def async_test_client(self, db_session: AsyncSession) -> AsyncClient:
        """Create async test client with mocked dependencies."""

        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return "test-user-id"

        app.dependency_overrides[get_async_db] = override_get_db
        app.dependency_overrides[get_current_user_id] = override_get_current_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_article_success(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """PUT /items/{id} should update article and increment version."""
        # Mock event publisher to avoid RabbitMQ connection
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={
                    "title": "Updated Title",
                    "content": "Updated content",
                    "change_type": "update",
                },
            )

        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["id"] == str(article.id)

    @pytest.mark.asyncio
    async def test_update_article_increments_version(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Article update should increment version number."""
        original_version = article.version

        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={
                    "title": "Updated Title",
                    "change_type": "update",
                },
            )

        assert response.status_code == 200

        # Refresh article from DB
        await db_session.refresh(article)
        assert article.version == original_version + 1

    @pytest.mark.asyncio
    async def test_update_article_creates_version_record(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Update should create ArticleVersion record for history."""
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={
                    "title": "Updated Title",
                    "content": "Updated content",
                    "change_type": "update",
                },
            )

        assert response.status_code == 200

        # Query version history
        stmt = select(ArticleVersion).where(ArticleVersion.article_id == article.id)
        result = await db_session.execute(stmt)
        versions = result.scalars().all()

        assert len(versions) == 1
        assert versions[0].version == 1  # Snapshot of OLD version
        assert versions[0].title == "Original Title"
        assert versions[0].change_type == "update"

    @pytest.mark.asyncio
    async def test_get_version_history(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """GET /items/{id}/versions should return history."""
        # First update the article to create version history
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={"title": "V2 Title", "change_type": "update"},
            )

        # Get history
        response = await async_test_client.get(
            f"/api/v1/feeds/items/{article.id}/versions",
        )

        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        assert len(data) == 1  # One version snapshot (original)
        assert data[0]["version"] == 1
        assert data[0]["title"] == "Original Title"
        assert data[0]["change_type"] == "update"

    @pytest.mark.asyncio
    async def test_withdrawal_sets_canceled_status(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Withdrawal should set pub_status to canceled."""
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={
                    "change_type": "withdrawal",
                    "change_reason": "Content was incorrect",
                },
            )

        assert response.status_code == 200

        # Refresh and check status
        await db_session.refresh(article)
        assert article.pub_status == "canceled"

    @pytest.mark.asyncio
    async def test_correction_records_reason(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Correction should record the change reason in version history."""
        # Mock SimHasher to return SQLite-compatible value
        with patch('app.services.article_update_service.SimHasher') as mock_hasher:
            mock_hasher.compute_fingerprint.return_value = 987654321  # SQLite-compatible value
            with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
                mock_pub_instance = AsyncMock()
                mock_pub_instance.publish_event = AsyncMock(return_value=True)
                mock_publisher.return_value = mock_pub_instance

                response = await async_test_client.put(
                    f"/api/v1/feeds/items/{article.id}",
                    json={
                        "title": "Corrected Title",
                        "change_type": "correction",
                        "change_reason": "Fixed factual error",
                    },
                )

        assert response.status_code == 200

        # Check version history for reason
        stmt = select(ArticleVersion).where(ArticleVersion.article_id == article.id)
        result = await db_session.execute(stmt)
        versions = result.scalars().all()

        assert len(versions) == 1
        assert versions[0].change_type == "correction"
        assert versions[0].change_reason == "Fixed factual error"

    @pytest.mark.asyncio
    async def test_update_article_not_found(
        self, async_test_client: AsyncClient, db_session: AsyncSession
    ):
        """PUT /items/{id} should return 404 for non-existent article."""
        fake_id = uuid4()

        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{fake_id}",
                json={
                    "title": "Updated Title",
                    "change_type": "update",
                },
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_versions_not_found(
        self, async_test_client: AsyncClient, db_session: AsyncSession
    ):
        """GET /items/{id}/versions should return 404 for non-existent article."""
        fake_id = uuid4()

        response = await async_test_client.get(
            f"/api/v1/feeds/items/{fake_id}/versions",
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_change_type_rejected(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Invalid change_type should be rejected by schema validation."""
        response = await async_test_client.put(
            f"/api/v1/feeds/items/{article.id}",
            json={
                "title": "Updated Title",
                "change_type": "invalid_type",
            },
        )

        # Should be rejected by Pydantic validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_updates_create_multiple_versions(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """Multiple updates should create corresponding version records."""
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            # Update 1
            await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={"title": "V2 Title", "change_type": "update"},
            )

            # Update 2
            await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={"title": "V3 Title", "change_type": "correction", "change_reason": "Fix typo"},
            )

        # Get history
        response = await async_test_client.get(
            f"/api/v1/feeds/items/{article.id}/versions",
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 2 version snapshots (v1 and v2), newest first
        assert len(data) == 2
        assert data[0]["version"] == 2  # Most recent snapshot
        assert data[0]["title"] == "V2 Title"
        assert data[1]["version"] == 1  # Original
        assert data[1]["title"] == "Original Title"

        # Check current article version
        await db_session.refresh(article)
        assert article.version == 3
        assert article.title == "V3 Title"

    @pytest.mark.asyncio
    async def test_event_published_on_update(
        self, async_test_client: AsyncClient, article: FeedItem, db_session: AsyncSession
    ):
        """article.updated event should be published on update."""
        with patch.object(event_publisher_module, 'get_event_publisher') as mock_publisher:
            mock_pub_instance = AsyncMock()
            mock_pub_instance.publish_event = AsyncMock(return_value=True)
            mock_publisher.return_value = mock_pub_instance

            response = await async_test_client.put(
                f"/api/v1/feeds/items/{article.id}",
                json={
                    "title": "Updated Title",
                    "change_type": "update",
                },
            )

        assert response.status_code == 200

        # Verify event was published
        mock_pub_instance.publish_event.assert_called_once()
        call_args = mock_pub_instance.publish_event.call_args

        assert call_args[0][0] == "article.updated"
        event_payload = call_args[0][1]
        assert event_payload["item_id"] == str(article.id)
        assert event_payload["version"] == 2
        assert event_payload["change_type"] == "update"
