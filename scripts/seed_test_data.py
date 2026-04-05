#!/usr/bin/env python3
"""
Seed test data into Feed Service with UUID support
"""
import requests
import sys

# Service URLs
AUTH_URL = "http://localhost:8000/api/v1/auth"
FEED_URL = "http://localhost:8001/api/v1/feeds"

# Test user
TEST_USER = {
    "email": "admin@test.com",
    "password": "Admin123!",
    "username": "admin"
}

# Test feeds
TEST_FEEDS = [
    {
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "name": "NY Times - Homepage",
        "fetch_interval": 30,
        "scrape_full_content": True
    },
    {
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "name": "BBC News",
        "fetch_interval": 30,
        "scrape_full_content": False
    },
    {
        "url": "https://www.theguardian.com/world/rss",
        "name": "The Guardian - World News",
        "fetch_interval": 60,
        "scrape_full_content": False
    }
]

def get_auth_token():
    """Get authentication token"""
    try:
        # Try login
        response = requests.post(f"{AUTH_URL}/login", json=TEST_USER)
        if response.status_code == 200:
            return response.json().get('access_token')
    except:
        pass

    # Register if login failed
    try:
        response = requests.post(f"{AUTH_URL}/register", json=TEST_USER)
        if response.status_code in [200, 201]:
            # Login after registration
            response = requests.post(f"{AUTH_URL}/login", json=TEST_USER)
            if response.status_code == 200:
                return response.json().get('access_token')
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None

def create_feeds(token):
    """Create test feeds"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    created_feeds = []

    for feed_data in TEST_FEEDS:
        try:
            response = requests.post(
                FEED_URL,
                json=feed_data,
                headers=headers
            )

            if response.status_code in [200, 201]:
                feed = response.json()
                print(f"✅ Created feed: {feed['name']} (ID: {feed['id']})")
                created_feeds.append(feed)
            else:
                print(f"❌ Failed to create {feed_data['name']}: {response.text}")
        except Exception as e:
            print(f"❌ Error creating feed: {e}")

    return created_feeds

def fetch_feeds(token, feed_ids):
    """Trigger fetch for all feeds"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for feed_id in feed_ids:
        try:
            response = requests.post(
                f"{FEED_URL}/{feed_id}/fetch",
                headers=headers
            )

            if response.status_code in [200, 202]:
                print(f"✅ Triggered fetch for feed {feed_id}")
            else:
                print(f"⚠️  Fetch failed for {feed_id}: {response.text}")
        except Exception as e:
            print(f"❌ Error fetching feed: {e}")

def main():
    print("=" * 70)
    print("  SEEDING TEST DATA WITH UUID SUPPORT")
    print("=" * 70)

    # Step 1: Authenticate
    print("\n1. Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print(f"✅ Authenticated")

    # Step 2: Create feeds
    print("\n2. Creating test feeds...")
    feeds = create_feeds(token)
    if not feeds:
        print("❌ No feeds created")
        sys.exit(1)
    print(f"✅ Created {len(feeds)} feeds")

    # Step 3: Fetch feed content
    print("\n3. Fetching feed content...")
    feed_ids = [f['id'] for f in feeds]
    fetch_feeds(token, feed_ids)

    print("\n" + "=" * 70)
    print(f"✅ SEEDING COMPLETE - {len(feeds)} feeds created")
    print("=" * 70)
    print("\nFeed IDs (UUIDs):")
    for feed in feeds:
        print(f"  - {feed['name']}: {feed['id']}")

if __name__ == "__main__":
    main()
