#!/usr/bin/env python3
"""Test Content Analysis LLM integration with real article"""
import requests
import json
import time

# Auth
print("=" * 70)
print("  CONTENT ANALYSIS LLM TEST")
print("=" * 70)

# Step 1: Login
print("\n1. Authenticating...")
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "e2e@test.com", "password": "E2ETest123!"}
)
token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"✅ Token: {token[:30]}...")

# Step 2: Get article
print("\n2. Getting article...")
feeds_response = requests.get("http://localhost:8001/api/v1/feeds", headers=headers)
feed_id = feeds_response.json()[0]["id"]
articles_response = requests.get(f"http://localhost:8001/api/v1/feeds/{feed_id}/items?limit=1", headers=headers)
article = articles_response.json()[0]
article_id = article["id"]
content = article.get("content") or article.get("description", "")
print(f"✅ Article ID: {article_id}")
print(f"   Title: {article['title'][:60]}...")
print(f"   Content length: {len(content)} chars")

# Step 3: Trigger analysis
print("\n3. Triggering FULL analysis...")
payload = {
    "article_id": article_id,
    "content": content,
    "analysis_type": "full",
    "use_cache": False,
    "provider": "openai",  # Explicitly use OpenAI
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

    # Step 4: Check result
    print("\n4. Checking analysis result...")
    time.sleep(5)  # Wait for processing

    result_response = requests.get(
        f"http://localhost:8002/api/v1/analyze/{analysis_id}",
        headers=headers
    )

    if result_response.status_code == 200:
        final_result = result_response.json()
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"   Status: {final_result.get('status')}")
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
            print(f"      {summary.get('text', '')[:100]}...")

        # Facts
        if final_result.get("facts"):
            facts = final_result["facts"]
            print(f"\n   ✓  Facts: {len(facts)} extracted")
            for fact in facts[:3]:
                print(f"      - {fact.get('text', '')[:80]}...")

        print(f"\n{'='*70}")
        print("✅ LLM ANALYSIS WORKING!")
        print(f"{'='*70}")
    else:
        print(f"❌ Error getting result: {result_response.text}")
else:
    print(f"❌ Analysis failed: {analysis_response.text}")
