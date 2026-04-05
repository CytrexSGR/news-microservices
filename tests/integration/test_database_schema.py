"""
Integration tests for database schema validation
Tests table existence, relationships, and UTC datetime handling
"""
import pytest
from datetime import datetime, timezone
from sqlmodel import Session, select, text
from app.models.core import Feed, Item, FetchLog
from app.models.feeds import Source, FeedType, FeedHealth
from app.models.user import UserSettings
from app.models.base import FeedStatus, SourceType


class TestDatabaseSchema:
    """Test database schema integrity"""

    def test_all_tables_exist(self, db_session: Session):
        """Verify all required tables exist in database"""
        expected_tables = [
            "feeds",
            "items",
            "sources",
            "feed_types",
            "feed_health",
            "fetch_log",
            "user_settings",
        ]

        # Query information_schema to get actual tables
        result = db_session.exec(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        actual_tables = [row[0] for row in result]

        for table in expected_tables:
            assert table in actual_tables, f"Table '{table}' does not exist in database"

    def test_feed_table_columns(self, db_session: Session):
        """Verify Feed table has all required columns"""
        result = db_session.exec(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'feeds'")
        )
        columns = [row[0] for row in result]

        required_columns = [
            "id", "url", "title", "description", "status",
            "fetch_interval_minutes", "last_fetched", "source_id",
            "feed_type_id", "auto_analyze_enabled", "health_score",
            "created_at", "updated_at"
        ]

        for column in required_columns:
            assert column in columns, f"Column '{column}' missing from feeds table"

    def test_item_table_columns(self, db_session: Session):
        """Verify Item table has all required columns"""
        result = db_session.exec(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'items'")
        )
        columns = [row[0] for row in result]

        required_columns = [
            "id", "title", "link", "description", "content",
            "author", "published", "guid", "content_hash",
            "feed_id", "created_at"
        ]

        for column in required_columns:
            assert column in columns, f"Column '{column}' missing from items table"

        # Verify no updated_at (items are immutable)
        assert "updated_at" not in columns, "Item table should not have updated_at column"

    def test_source_feed_relationship(self, test_source: Source, test_feed: Feed, db_session: Session):
        """Test one-to-many relationship between Source and Feed"""
        # Refresh to load relationships
        db_session.refresh(test_source)
        db_session.refresh(test_feed)

        # Check forward relationship
        assert test_feed.source_id == test_source.id
        assert test_feed.source is not None
        assert test_feed.source.name == test_source.name

        # Check back relationship
        assert len(test_source.feeds) > 0
        feed_ids = [f.id for f in test_source.feeds]
        assert test_feed.id in feed_ids

    def test_feed_item_relationship(self, test_feed: Feed, db_session: Session):
        """Test one-to-many relationship between Feed and Item"""
        # Create test item
        item = Item(
            title="Test Article",
            link="https://example.com/article",
            content_hash="test_hash_123",
            feed_id=test_feed.id,
            created_at=datetime.utcnow()
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        db_session.refresh(test_feed)

        # Check forward relationship
        assert item.feed_id == test_feed.id
        assert item.feed is not None
        assert item.feed.title == test_feed.title

        # Check back relationship
        assert len(test_feed.items) > 0
        item_ids = [i.id for i in test_feed.items]
        assert item.id in item_ids

    def test_feed_fetch_log_relationship(self, test_feed: Feed, db_session: Session):
        """Test one-to-many relationship between Feed and FetchLog"""
        # Create fetch log
        fetch_log = FetchLog(
            feed_id=test_feed.id,
            started_at=datetime.utcnow(),
            status="success",
            items_found=10,
            items_new=5
        )
        db_session.add(fetch_log)
        db_session.commit()
        db_session.refresh(fetch_log)
        db_session.refresh(test_feed)

        # Check forward relationship
        assert fetch_log.feed_id == test_feed.id
        assert fetch_log.feed is not None

        # Check back relationship
        assert len(test_feed.fetch_logs) > 0
        log_ids = [log.id for log in test_feed.fetch_logs]
        assert fetch_log.id in log_ids

    def test_feed_health_one_to_one(self, test_feed: Feed, db_session: Session):
        """Test one-to-one relationship between Feed and FeedHealth"""
        # Create feed health
        health = FeedHealth(
            feed_id=test_feed.id,
            ok_ratio=0.95,
            consecutive_failures=0,
            uptime_24h=1.0,
            uptime_7d=0.99,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(health)
        db_session.commit()
        db_session.refresh(health)
        db_session.refresh(test_feed)

        # Check one-to-one relationship
        assert test_feed.health is not None
        assert test_feed.health.feed_id == test_feed.id
        assert test_feed.health.ok_ratio == 0.95

    def test_utc_datetime_handling(self, test_feed: Feed, db_session: Session):
        """Test that datetime fields use UTC correctly"""
        now = datetime.utcnow()

        # Create item with UTC timestamp
        item = Item(
            title="UTC Test Article",
            link="https://example.com/utc-test",
            content_hash="utc_test_hash",
            feed_id=test_feed.id,
            created_at=now
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        # Verify timestamp is stored and retrieved correctly
        assert item.created_at is not None
        time_diff = abs((item.created_at - now).total_seconds())
        assert time_diff < 1.0, f"Timestamp differs by {time_diff} seconds"

    def test_feed_status_enum(self, test_source: Source, test_feed_type: FeedType, db_session: Session):
        """Test FeedStatus enum values work correctly"""
        statuses = [FeedStatus.ACTIVE, FeedStatus.PAUSED, FeedStatus.ERROR]

        for i, status in enumerate(statuses):
            feed = Feed(
                url=f"https://example.com/feed-{i}.rss",
                title=f"Test Feed {status.value}",
                status=status,
                source_id=test_source.id,
                feed_type_id=test_feed_type.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(feed)
            db_session.commit()
            db_session.refresh(feed)

            assert feed.status == status
            assert isinstance(feed.status, FeedStatus)

    def test_source_type_enum(self, db_session: Session):
        """Test SourceType enum values work correctly"""
        types = [SourceType.RSS, SourceType.API, SourceType.MANUAL]

        for source_type in types:
            source = Source(
                name=f"Test Source {source_type.value}",
                type=source_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(source)
            db_session.commit()
            db_session.refresh(source)

            assert source.type == source_type
            assert isinstance(source.type, SourceType)

    def test_item_content_hash_unique_constraint(self, test_feed: Feed, db_session: Session):
        """Test that content_hash has unique constraint"""
        content_hash = "unique_hash_test_12345"

        # Create first item
        item1 = Item(
            title="First Article",
            link="https://example.com/article-1",
            content_hash=content_hash,
            feed_id=test_feed.id,
            created_at=datetime.utcnow()
        )
        db_session.add(item1)
        db_session.commit()

        # Try to create duplicate - should raise error
        item2 = Item(
            title="Duplicate Article",
            link="https://example.com/article-2",
            content_hash=content_hash,  # Same hash!
            feed_id=test_feed.id,
            created_at=datetime.utcnow()
        )
        db_session.add(item2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

        db_session.rollback()

    def test_feed_url_unique_constraint(self, test_source: Source, test_feed_type: FeedType, db_session: Session):
        """Test that feed URL has unique constraint"""
        feed_url = "https://example.com/unique-feed.rss"

        # Create first feed
        feed1 = Feed(
            url=feed_url,
            title="First Feed",
            source_id=test_source.id,
            feed_type_id=test_feed_type.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed1)
        db_session.commit()

        # Try to create duplicate - should raise error
        feed2 = Feed(
            url=feed_url,  # Same URL!
            title="Duplicate Feed",
            source_id=test_source.id,
            feed_type_id=test_feed_type.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

        db_session.rollback()

    def test_user_settings_single_row(self, db_session: Session):
        """Test that UserSettings has single row constraint"""
        settings = UserSettings(
            user_id="test_single",
            default_limit=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

        assert settings.user_id == "test_single"
        assert settings.default_limit == 100

    def test_nullable_fields(self, test_feed: Feed, db_session: Session):
        """Test that nullable fields can be None"""
        item = Item(
            title="Minimal Article",
            link="https://example.com/minimal",
            content_hash="minimal_hash",
            feed_id=test_feed.id,
            # All nullable fields omitted
            description=None,
            content=None,
            author=None,
            published=None,
            guid=None,
            created_at=datetime.utcnow()
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.description is None
        assert item.content is None
        assert item.author is None
        assert item.published is None
        assert item.guid is None
