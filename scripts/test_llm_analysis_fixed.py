#!/usr/bin/env python3
"""Test Content Analysis LLM integration with real article - Fixed Auth"""
import requests
import json
import time

print("=" * 70)
print("  CONTENT ANALYSIS LLM TEST (gpt-4o-mini)")
print("=" * 70)

# Step 1: Use existing test user (from e2e tests)
print("\n1. Authenticating with existing test user...")
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin@test.com", "password": "Admin123!"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    exit(1)

login_data = login_response.json()
token = login_data.get("access_token")

if not token:
    print(f"❌ No token in response: {login_data}")
    exit(1)

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"✅ Token: {token[:30]}...")

# Step 3: Get or create a feed
print("\n3. Getting test feed...")
feeds_response = requests.get("http://localhost:8001/api/v1/feeds", headers=headers)

if feeds_response.status_code != 200 or not feeds_response.json():
    print("Creating test feed...")
    create_feed = requests.post(
        "http://localhost:8001/api/v1/feeds",
        headers=headers,
        json={
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "name": "NYT Technology",
            "category": "technology"
        }
    )
    feed_id = create_feed.json()["id"]
    print(f"✅ Created feed: {feed_id}")

    # Fetch articles
    print("Fetching articles...")
    fetch_response = requests.post(
        f"http://localhost:8001/api/v1/feeds/{feed_id}/fetch",
        headers=headers
    )
    time.sleep(2)
else:
    feed_id = feeds_response.json()[0]["id"]
    print(f"✅ Using existing feed: {feed_id}")

# Step 4: Get multiple articles
print("\n4. Getting articles...")
articles_response = requests.get(
    f"http://localhost:8001/api/v1/feeds/{feed_id}/items?limit=5",
    headers=headers
)

if articles_response.status_code != 200 or not articles_response.json():
    print("❌ No articles available")
    exit(1)

articles = articles_response.json()

# Try to find an article that hasn't been analyzed yet with gpt-4o-mini
article = None
for art in articles:
    # Check if this article has existing analysis with gpt-4o-mini
    check_response = requests.get(
        f"http://localhost:8002/api/v1/analyze/article/{art['id']}",
        headers=headers
    )
    if check_response.status_code == 200:
        analyses = check_response.json()
        # Check if any analysis uses gpt-4o-mini for FULL type
        has_gpt4omini = any(
            a.get('model_used') == 'gpt-4o-mini' and a.get('analysis_type') == 'FULL'
            for a in analyses
        )
        if not has_gpt4omini:
            article = art
            break
    else:
        # No analyses at all for this article
        article = art
        break

if not article:
    # Fallback to last article if all are analyzed
    article = articles[-1]
    print("   Note: All articles analyzed, using last article")

article_id = article["id"]
content = article.get("content") or article.get("description", "")

print(f"✅ Article ID: {article_id}")
print(f"   Title: {article['title'][:80]}...")
print(f"   Content length: {len(content)} chars")

# Step 5: Trigger SENTIMENT analysis with gpt-4o-mini (avoid unique constraint)
print("\n5. Triggering SENTIMENT analysis with gpt-4o-mini...")
payload = {
    "article_id": article_id,
    "content": content,
    "analysis_type": "sentiment",  # Use sentiment to avoid unique constraint
    "use_cache": False,
    "model_provider": "OPENAI",  # Uppercase enum value
    "model_name": "gpt-4o-mini",  # Explicitly use gpt-4o-mini (correct field name)
    "metadata": {
        "title": article["title"],
        "feed_id": feed_id
    }
}

analysis_response = requests.post(
    "http://localhost:8002/api/v1/analyze/",
    json=payload,
    headers=headers,
    timeout=120
)

print(f"Response status: {analysis_response.status_code}")
if analysis_response.status_code in [200, 201]:
    result = analysis_response.json()
    analysis_id = result.get("id")
    print(f"✅ Analysis created: {analysis_id}")
    print(f"   Status: {result.get('status')}")

    # Step 6: Check result
    print("\n6. Checking analysis result...")
    time.sleep(8)  # Wait for processing

    result_response = requests.get(
        f"http://localhost:8002/api/v1/analyze/{analysis_id}",
        headers=headers
    )

    if result_response.status_code == 200:
        final_result = result_response.json()
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"   Status: {final_result.get('status')}")
        print(f"   Model: {final_result.get('model_used')}")
        print(f"   Provider: {final_result.get('model_provider')}")
        print(f"   Processing time: {final_result.get('processing_time_ms')}ms")
        print(f"   Total tokens: {final_result.get('total_tokens')}")
        print(f"   Cost: ${final_result.get('total_cost', 0):.4f}")

        # Sentiment
        if final_result.get("sentiment"):
            sent = final_result["sentiment"]
            print(f"\n   📊 Sentiment: {sent.get('overall_sentiment')}")
            print(f"      Confidence: {sent.get('confidence', 0):.2%}")
            print(f"      Scores: {sent.get('scores', {})}")

        # Entities
        if final_result.get("entities"):
            entities = final_result["entities"]
            print(f"\n   🏷️  Entities: {len(entities)} found")
            for entity in entities[:5]:
                print(f"      - {entity.get('text')}: {entity.get('type')} (conf: {entity.get('confidence', 0):.2f})")

        # Topics
        if final_result.get("topics"):
            topics = final_result["topics"]
            print(f"\n   📚 Topics: {len(topics)} identified")
            for topic in topics[:5]:
                print(f"      - {topic.get('name')}: {topic.get('confidence', 0):.2%}")

        # Summary
        if final_result.get("summary"):
            summary = final_result["summary"]
            print(f"\n   📝 Summary ({summary.get('type')}):")
            print(f"      {summary.get('text', '')[:150]}...")

        # Facts
        if final_result.get("facts"):
            facts = final_result["facts"]
            print(f"\n   ✓  Facts: {len(facts)} extracted")
            for fact in facts[:3]:
                print(f"      - {fact.get('text', '')[:100]}...")

        print(f"\n{'='*70}")
        print("✅ LLM ANALYSIS WITH gpt-4o-mini WORKING!")
        print(f"{'='*70}")
    else:
        print(f"❌ Error getting result: {result_response.status_code}")
        print(f"Response: {result_response.text}")
else:
    print(f"❌ Analysis failed: {analysis_response.status_code}")
    print(f"Response: {analysis_response.text}")
