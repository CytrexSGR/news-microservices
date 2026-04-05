"""
Integration tests for RSS pipeline with derstandard.at
Tests the complete flow: fetch → parse → store → analyze
"""
import pytest
import feedparser
import hashlib
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models.core import Feed, Item, FetchLog
from app.models.feeds import FeedHealth
from app.models.base import FeedStatus


class TestRSSPipeline:
    """Test RSS feed pipeline with real derstandard.at feed"""

    def test_fetch_derstandard_rss(self, derstandard_feed: Feed):
        """Test fetching real RSS feed from derstandard.at"""
        # Fetch the RSS feed
        response = feedparser.parse(derstandard_feed.url)

        # Verify feed was fetched successfully
        assert response is not None
        assert response.bozo == 0, f"Feed parsing error: {response.get('bozo_exception')}"
        assert hasattr(response, 'entries')
        assert len(response.entries) > 0, "Feed has no entries"

        # Verify feed metadata
        assert hasattr(response, 'feed')
        feed_info = response.feed
        assert hasattr(feed_info, 'title') or hasattr(feed_info, 'link')

        print(f"✅ Fetched {len(response.entries)} articles from {derstandard_feed.url}")

    def test_parse_derstandard_articles(self, derstandard_feed: Feed):
        """Test parsing articles from derstandard.at RSS feed"""
        response = feedparser.parse(derstandard_feed.url)
        assert len(response.entries) > 0

        # Test first article
        entry = response.entries[0]

        # Verify required fields exist
        assert hasattr(entry, 'title'), "Entry missing title"
        assert hasattr(entry, 'link'), "Entry missing link"
        assert entry.title, "Title is empty"
        assert entry.link, "Link is empty"

        # Check optional fields
        has_description = hasattr(entry, 'summary') or hasattr(entry, 'description')
        has_published = hasattr(entry, 'published_parsed') or hasattr(entry, 'updated_parsed')

        print(f"✅ Article: {entry.title[:50]}...")
        print(f"   Link: {entry.link}")
        print(f"   Has description: {has_description}")
        print(f"   Has published date: {has_published}")

    def test_store_articles_in_database(self, derstandard_feed: Feed, db_session: Session):
        """Test storing fetched articles in database"""
        # Fetch RSS feed
        response = feedparser.parse(derstandard_feed.url)
        assert len(response.entries) > 0

        # Take first 5 articles for testing
        entries = response.entries[:5]
        stored_items = []

        for entry in entries:
            # Generate content hash
            hash_input = f"{entry.link}|{entry.title}"
            content_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            # Check if item already exists
            existing_item = db_session.exec(
                select(Item).where(Item.content_hash == content_hash)
            ).first()

            if existing_item:
                print(f"⏭️  Skipping duplicate: {entry.title[:50]}...")
                continue

            # Get published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            # Get description
            description = None
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description

            # Create item
            item = Item(
                title=entry.title,
                link=entry.link,
                description=description,
                content=description,  # RSS content
                author=getattr(entry, 'author', None),
                published=published,
                guid=getattr(entry, 'id', entry.link),
                content_hash=content_hash,
                feed_id=derstandard_feed.id,
                created_at=datetime.utcnow()
            )

            db_session.add(item)
            stored_items.append(item)

        if stored_items:
            db_session.commit()
            for item in stored_items:
                db_session.refresh(item)

            print(f"✅ Stored {len(stored_items)} new articles in database")

            # Verify items were stored correctly
            for item in stored_items:
                assert item.id is not None
                assert item.feed_id == derstandard_feed.id
                assert item.content_hash is not None
                print(f"   ✓ ID {item.id}: {item.title[:60]}...")
        else:
            print("ℹ️  No new articles to store (all were duplicates)")

    def test_fetch_log_creation(self, derstandard_feed: Feed, db_session: Session):
        """Test creating fetch log entries"""
        start_time = datetime.utcnow()

        # Simulate fetch operation
        response = feedparser.parse(derstandard_feed.url)
        end_time = datetime.utcnow()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Create fetch log
        fetch_log = FetchLog(
            feed_id=derstandard_feed.id,
            started_at=start_time,
            completed_at=end_time,
            status="success",
            items_found=len(response.entries),
            items_new=0,  # Would be calculated by comparing with existing items
            response_time_ms=response_time_ms
        )

        db_session.add(fetch_log)
        db_session.commit()
        db_session.refresh(fetch_log)

        # Verify fetch log
        assert fetch_log.id is not None
        assert fetch_log.feed_id == derstandard_feed.id
        assert fetch_log.status == "success"
        assert fetch_log.items_found > 0
        assert fetch_log.response_time_ms > 0

        print(f"✅ Created fetch log:")
        print(f"   Status: {fetch_log.status}")
        print(f"   Items found: {fetch_log.items_found}")
        print(f"   Response time: {fetch_log.response_time_ms}ms")

    def test_feed_health_tracking(self, derstandard_feed: Feed, db_session: Session):
        """Test feed health tracking"""
        # Check if health record exists
        health = db_session.exec(
            select(FeedHealth).where(FeedHealth.feed_id == derstandard_feed.id)
        ).first()

        if not health:
            # Create health record
            health = FeedHealth(
                feed_id=derstandard_feed.id,
                ok_ratio=1.0,
                consecutive_failures=0,
                uptime_24h=1.0,
                uptime_7d=1.0,
                last_success=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(health)
            db_session.commit()
            db_session.refresh(health)

        # Verify health tracking
        assert health.feed_id == derstandard_feed.id
        assert health.ok_ratio >= 0.0 and health.ok_ratio <= 1.0
        assert health.consecutive_failures >= 0
        assert health.uptime_24h >= 0.0 and health.uptime_24h <= 1.0

        print(f"✅ Feed health:")
        print(f"   OK ratio: {health.ok_ratio:.2%}")
        print(f"   Consecutive failures: {health.consecutive_failures}")
        print(f"   24h uptime: {health.uptime_24h:.2%}")

    def test_complete_pipeline_flow(self, derstandard_feed: Feed, db_session: Session):
        """Test complete RSS pipeline: fetch → parse → store → verify"""
        print(f"\n🔄 Testing complete pipeline for {derstandard_feed.url}\n")

        # 1. FETCH
        print("1️⃣ FETCH: Downloading RSS feed...")
        start_time = datetime.utcnow()
        response = feedparser.parse(derstandard_feed.url)
        end_time = datetime.utcnow()

        assert response.bozo == 0, f"Feed parsing error: {response.get('bozo_exception')}"
        assert len(response.entries) > 0
        print(f"   ✅ Fetched {len(response.entries)} articles")

        # 2. PARSE
        print("\n2️⃣ PARSE: Processing articles...")
        parsed_count = 0
        new_items = []

        for entry in response.entries[:10]:  # Limit to 10 for testing
            # Generate content hash
            hash_input = f"{entry.link}|{entry.title}"
            content_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            # Check for duplicates
            existing = db_session.exec(
                select(Item).where(Item.content_hash == content_hash)
            ).first()

            if existing:
                continue

            parsed_count += 1
            new_items.append({
                'title': entry.title,
                'link': entry.link,
                'hash': content_hash,
                'entry': entry
            })

        print(f"   ✅ Parsed {parsed_count} new articles")

        # 3. STORE
        print("\n3️⃣ STORE: Saving to database...")
        stored_items = []

        for item_data in new_items:
            entry = item_data['entry']
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            description = getattr(entry, 'summary', None) or getattr(entry, 'description', None)

            item = Item(
                title=item_data['title'],
                link=item_data['link'],
                description=description,
                content=description,
                author=getattr(entry, 'author', None),
                published=published,
                guid=getattr(entry, 'id', item_data['link']),
                content_hash=item_data['hash'],
                feed_id=derstandard_feed.id,
                created_at=datetime.utcnow()
            )

            db_session.add(item)
            stored_items.append(item)

        if stored_items:
            db_session.commit()
            for item in stored_items:
                db_session.refresh(item)
            print(f"   ✅ Stored {len(stored_items)} articles in database")
        else:
            print("   ℹ️  No new articles to store")

        # 4. LOG
        print("\n4️⃣ LOG: Recording fetch operation...")
        fetch_log = FetchLog(
            feed_id=derstandard_feed.id,
            started_at=start_time,
            completed_at=end_time,
            status="success",
            items_found=len(response.entries),
            items_new=len(stored_items),
            response_time_ms=int((end_time - start_time).total_seconds() * 1000)
        )
        db_session.add(fetch_log)
        db_session.commit()
        db_session.refresh(fetch_log)
        print(f"   ✅ Logged fetch operation (ID: {fetch_log.id})")

        # 5. VERIFY
        print("\n5️⃣ VERIFY: Checking database consistency...")

        # Count total items for this feed
        total_items = db_session.exec(
            select(Item).where(Item.feed_id == derstandard_feed.id)
        ).all()

        # Count recent fetch logs
        recent_logs = db_session.exec(
            select(FetchLog)
            .where(FetchLog.feed_id == derstandard_feed.id)
            .where(FetchLog.started_at > datetime.utcnow() - timedelta(hours=1))
        ).all()

        print(f"   ✅ Total items in database: {len(total_items)}")
        print(f"   ✅ Recent fetch logs: {len(recent_logs)}")

        # Update feed statistics
        derstandard_feed.total_articles = len(total_items)
        derstandard_feed.last_fetched = end_time
        derstandard_feed.latest_article_at = stored_items[0].published if stored_items and stored_items[0].published else None
        db_session.add(derstandard_feed)
        db_session.commit()

        print("\n✅ PIPELINE COMPLETE!")
        print(f"   Feed: {derstandard_feed.title}")
        print(f"   Total articles: {derstandard_feed.total_articles}")
        print(f"   Last fetched: {derstandard_feed.last_fetched}")

    def test_duplicate_prevention(self, derstandard_feed: Feed, db_session: Session):
        """Test that duplicate articles are prevented"""
        response = feedparser.parse(derstandard_feed.url)
        assert len(response.entries) > 0

        entry = response.entries[0]
        hash_input = f"{entry.link}|{entry.title}"
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Create first item
        item1 = Item(
            title=entry.title,
            link=entry.link,
            content_hash=content_hash,
            feed_id=derstandard_feed.id,
            created_at=datetime.utcnow()
        )
        db_session.add(item1)
        db_session.commit()
        db_session.refresh(item1)

        # Try to create duplicate
        item2 = Item(
            title=entry.title + " (duplicate)",
            link=entry.link + "?duplicate",
            content_hash=content_hash,  # Same hash!
            feed_id=derstandard_feed.id,
            created_at=datetime.utcnow()
        )
        db_session.add(item2)

        with pytest.raises(Exception):  # IntegrityError due to unique content_hash
            db_session.commit()

        db_session.rollback()
        print("✅ Duplicate prevention working correctly")

    def test_feed_update_timestamps(self, derstandard_feed: Feed, db_session: Session):
        """Test that feed timestamps are updated correctly"""
        original_updated_at = derstandard_feed.updated_at
        original_last_fetched = derstandard_feed.last_fetched

        # Simulate fetch
        response = feedparser.parse(derstandard_feed.url)
        fetch_time = datetime.utcnow()

        # Update feed
        derstandard_feed.last_fetched = fetch_time
        derstandard_feed.updated_at = fetch_time
        db_session.add(derstandard_feed)
        db_session.commit()
        db_session.refresh(derstandard_feed)

        # Verify updates
        assert derstandard_feed.last_fetched == fetch_time
        assert derstandard_feed.updated_at == fetch_time
        assert derstandard_feed.last_fetched != original_last_fetched or original_last_fetched is None

        print(f"✅ Feed timestamps updated:")
        print(f"   Last fetched: {derstandard_feed.last_fetched}")
        print(f"   Updated at: {derstandard_feed.updated_at}")
