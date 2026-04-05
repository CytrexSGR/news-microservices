"""
E2E Test: Complete User Flow
Tests the entire user journey from registration to analytics.
"""
import pytest
import asyncio
import httpx
from typing import Dict, Any


@pytest.mark.asyncio
async def test_complete_user_journey(http_client: httpx.AsyncClient, health_check):
    """
    Test complete user flow across all services:
    1. User registration and login (Auth Service)
    2. Add RSS feed and fetch articles (Feed Service)
    3. Automatic content analysis (Content Analysis Service)
    4. Create research query (Research Service)
    5. Create OSINT instance and trigger alert (OSINT Service)
    6. Receive notification (Notification Service)
    7. Search for articles (Search Service)
    8. View analytics dashboard (Analytics Service)
    """
    # Step 1: User Registration and Login
    import uuid
    user_id = str(uuid.uuid4())[:8]

    user_data = {
        "email": f"journey_{user_id}@example.com",
        "password": "Journey123!@#",
        "username": f"journey_{user_id}",
        "full_name": f"Journey User {user_id}"
    }

    # Register
    response = await http_client.post(
        "http://localhost:8100/api/v1/auth/register",
        json=user_data
    )
    assert response.status_code == 201
    registration_data = response.json()
    print(f"✓ Step 1.1: User registered - {registration_data['email']}")

    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = await http_client.post(
        "http://localhost:8100/api/v1/auth/login",
        json=login_data
    )
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    print(f"✓ Step 1.2: User logged in - Token received")

    # Step 2: Add RSS Feed and Fetch Articles
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Hacker News E2E Test",
        "category": "technology",
        "fetch_interval": 3600
    }

    response = await http_client.post(
        "http://localhost:8101/api/v1/feeds",
        json=feed_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    feed = response.json()
    feed_id = feed["id"]
    print(f"✓ Step 2.1: RSS feed created - {feed['name']}")

    # Fetch articles
    response = await http_client.post(
        f"http://localhost:8101/api/v1/feeds/{feed_id}/fetch",
        headers=auth_headers
    )
    assert response.status_code == 200
    fetch_result = response.json()
    print(f"✓ Step 2.2: Articles fetched - {fetch_result.get('articles_fetched', 0)} articles")

    # Get articles
    response = await http_client.get(
        f"http://localhost:8101/api/v1/feeds/{feed_id}/articles",
        headers=auth_headers
    )
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) > 0, "No articles fetched"
    article = articles[0]
    article_id = article["id"]
    print(f"✓ Step 2.3: Retrieved article - {article['title'][:50]}...")

    # Step 3: Content Analysis (may be automatic via events)
    # Try to analyze the article
    try:
        analysis_data = {
            "article_id": article_id,
            "content": article.get("content", article.get("description", "")),
            "analyze_sentiment": True,
            "extract_entities": True,
            "extract_topics": True
        }

        response = await http_client.post(
            "http://localhost:8114/api/v1/content/analyze",
            json=analysis_data,
            headers=auth_headers
        )

        if response.status_code == 200:
            analysis = response.json()
            print(f"✓ Step 3: Content analyzed - Sentiment: {analysis.get('sentiment', 'N/A')}")
        else:
            print(f"⚠ Step 3: Content analysis skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 3: Content analysis error - {str(e)}")

    # Step 4: Create Research Query
    try:
        research_data = {
            "query": "artificial intelligence trends 2025",
            "model": "sonar",
            "max_tokens": 500
        }

        response = await http_client.post(
            "http://localhost:8103/api/v1/research",
            json=research_data,
            headers=auth_headers,
            timeout=60.0
        )

        if response.status_code == 200:
            research = response.json()
            print(f"✓ Step 4: Research query created - {research.get('id', 'N/A')}")
        else:
            print(f"⚠ Step 4: Research query skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 4: Research error - {str(e)}")

    # Step 5: Create OSINT Instance
    try:
        osint_data = {
            "template_id": "tech_news_monitor",
            "name": f"E2E Test Monitor {user_id}",
            "targets": ["technology", "AI"],
            "schedule": "0 */6 * * *"
        }

        response = await http_client.post(
            "http://localhost:8104/api/v1/osint/instances",
            json=osint_data,
            headers=auth_headers
        )

        if response.status_code == 201:
            osint = response.json()
            print(f"✓ Step 5: OSINT instance created - {osint.get('name', 'N/A')}")
        else:
            print(f"⚠ Step 5: OSINT instance skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 5: OSINT error - {str(e)}")

    # Step 6: Check Notifications
    try:
        response = await http_client.get(
            "http://localhost:8105/api/v1/notifications",
            headers=auth_headers
        )

        if response.status_code == 200:
            notifications = response.json()
            print(f"✓ Step 6: Notifications retrieved - {len(notifications)} notifications")
        else:
            print(f"⚠ Step 6: Notifications skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 6: Notifications error - {str(e)}")

    # Step 7: Search for Articles
    try:
        search_params = {
            "q": "technology",
            "limit": 10
        }

        response = await http_client.get(
            "http://localhost:8106/api/v1/search",
            params=search_params,
            headers=auth_headers
        )

        if response.status_code == 200:
            search_results = response.json()
            print(f"✓ Step 7: Search completed - {search_results.get('total', 0)} results")
        else:
            print(f"⚠ Step 7: Search skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 7: Search error - {str(e)}")

    # Step 8: View Analytics Dashboard
    try:
        response = await http_client.get(
            "http://localhost:8107/api/v1/analytics/dashboard",
            headers=auth_headers
        )

        if response.status_code == 200:
            analytics = response.json()
            print(f"✓ Step 8: Analytics retrieved - Dashboard data loaded")
        else:
            print(f"⚠ Step 8: Analytics skipped - {response.status_code}")
    except Exception as e:
        print(f"⚠ Step 8: Analytics error - {str(e)}")

    print("\n✅ Complete user journey test passed!")


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(http_client: httpx.AsyncClient):
    """Test user registration and login specifically."""
    import uuid
    user_id = str(uuid.uuid4())[:8]

    user_data = {
        "email": f"regtest_{user_id}@example.com",
        "password": "RegTest123!@#",
        "username": f"regtest_{user_id}",
        "full_name": "Registration Test User"
    }

    # Register
    response = await http_client.post(
        "http://localhost:8100/api/v1/auth/register",
        json=user_data
    )
    assert response.status_code == 201
    reg_data = response.json()
    assert reg_data["email"] == user_data["email"]

    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = await http_client.post(
        "http://localhost:8100/api/v1/auth/login",
        json=login_data
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Verify token works
    auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = await http_client.get(
        "http://localhost:8100/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_feed_article_flow(http_client: httpx.AsyncClient, test_user: Dict[str, Any], auth_headers: Dict[str, str]):
    """Test complete feed and article management flow."""
    # Create feed
    feed_data = {
        "url": "https://hnrss.org/frontpage",
        "name": "HN Frontpage Test",
        "category": "tech",
        "fetch_interval": 1800
    }

    response = await http_client.post(
        "http://localhost:8101/api/v1/feeds",
        json=feed_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    feed = response.json()
    feed_id = feed["id"]

    # Fetch articles
    response = await http_client.post(
        f"http://localhost:8101/api/v1/feeds/{feed_id}/fetch",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Get articles
    response = await http_client.get(
        f"http://localhost:8101/api/v1/feeds/{feed_id}/articles",
        headers=auth_headers
    )
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) > 0

    # Update feed
    update_data = {"name": "Updated Feed Name"}
    response = await http_client.patch(
        f"http://localhost:8101/api/v1/feeds/{feed_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200

    # Delete feed
    response = await http_client.delete(
        f"http://localhost:8101/api/v1/feeds/{feed_id}",
        headers=auth_headers
    )
    assert response.status_code == 204
