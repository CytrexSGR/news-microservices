#!/usr/bin/env python3
"""
Seed Data Script for News-MCP
Creates initial test data including derstandard.at RSS feed
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "news-mcp"))

from datetime import datetime
from sqlmodel import Session, select
from app.database import engine
from app.models.core import Feed
from app.models.feeds import Source, FeedType
from app.models.base import FeedStatus, SourceType
from app.models.user import UserSettings


def seed_database():
    """Create initial data for testing"""
    print("🌱 Starting database seeding...")

    with Session(engine) as session:
        # 1. Check if Source already exists
        existing_source = session.exec(
            select(Source).where(Source.name == "Der Standard")
        ).first()

        if not existing_source:
            print("📰 Creating Source: Der Standard")
            source = Source(
                name="Der Standard",
                type=SourceType.RSS,
                description="Austrian quality newspaper - DER STANDARD",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            print(f"✅ Source created with ID: {source.id}")
        else:
            source = existing_source
            print(f"✓ Source already exists with ID: {source.id}")

        # 2. Check if FeedType exists
        existing_feed_type = session.exec(
            select(FeedType).where(FeedType.name == "News RSS")
        ).first()

        if not existing_feed_type:
            print("📋 Creating FeedType: News RSS")
            feed_type = FeedType(
                name="News RSS",
                default_interval_minutes=15,
                description="Standard news RSS feed with 15-minute refresh",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(feed_type)
            session.commit()
            session.refresh(feed_type)
            print(f"✅ FeedType created with ID: {feed_type.id}")
        else:
            feed_type = existing_feed_type
            print(f"✓ FeedType already exists with ID: {feed_type.id}")

        # 3. Check if derstandard.at feed already exists
        derstandard_url = "https://www.derstandard.at/rss"
        existing_feed = session.exec(
            select(Feed).where(Feed.url == derstandard_url)
        ).first()

        if not existing_feed:
            print(f"📡 Creating Feed: {derstandard_url}")
            feed = Feed(
                url=derstandard_url,
                title="Der Standard - Hauptfeed",
                description="Der Standard RSS Feed - Austrian News",
                status=FeedStatus.ACTIVE,
                fetch_interval_minutes=15,
                source_id=source.id,
                feed_type_id=feed_type.id,
                auto_analyze_enabled=True,
                health_score=100,
                total_articles=0,
                articles_24h=0,
                analyzed_count=0,
                analyzed_percentage=0.0,
                scrape_full_content=False,
                scrape_method="auto",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(feed)
            session.commit()
            session.refresh(feed)
            print(f"✅ Feed created with ID: {feed.id}")
            print(f"   URL: {feed.url}")
            print(f"   Auto-analyze: {feed.auto_analyze_enabled}")
        else:
            feed = existing_feed
            print(f"✓ Feed already exists with ID: {feed.id}")
            print(f"   URL: {feed.url}")
            print(f"   Status: {feed.status}")

        # 4. Check if user settings exist
        existing_settings = session.exec(
            select(UserSettings).where(UserSettings.user_id == "default")
        ).first()

        if not existing_settings:
            print("⚙️ Creating default UserSettings")
            settings = UserSettings(
                user_id="default",
                default_limit=200,
                default_rate_per_second=1.0,
                default_model_tag="gpt-4o-mini",
                default_dry_run=False,
                default_override_existing=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(settings)
            session.commit()
            print("✅ UserSettings created")
        else:
            print("✓ UserSettings already exist")

        print("\n🎉 Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Source: {source.name} (ID: {source.id})")
        print(f"   - FeedType: {feed_type.name} (ID: {feed_type.id})")
        print(f"   - Feed: {feed.title} (ID: {feed.id})")
        print(f"   - URL: {feed.url}")
        print(f"   - Status: {feed.status}")
        print(f"   - Auto-analyze: {feed.auto_analyze_enabled}")

        return {
            "source": source,
            "feed_type": feed_type,
            "feed": feed
        }


if __name__ == "__main__":
    try:
        result = seed_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
