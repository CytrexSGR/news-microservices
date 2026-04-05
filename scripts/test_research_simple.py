#!/usr/bin/env python3
"""Simple test for Research Service UUID integration"""
import requests
import json

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "admin@test.com", "password": "Admin123!"}
)
print(f"Login status: {login_response.status_code}")
token = login_response.json().get("access_token")
print(f"Token: {token[:50] if token else 'None'}...")

# Get feed
feeds_response = requests.get(
    "http://localhost:8001/api/v1/feeds",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"\nFeeds status: {feeds_response.status_code}")
feeds = feeds_response.json()
feed_id = feeds[0]["id"] if feeds else None
print(f"Feed ID (UUID): {feed_id}")

# Create research task
research_response = requests.post(
    "http://localhost:8003/api/v1/research/",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={
        "query": "What are the latest developments in AI?",
        "feed_id": feed_id
    }
)
print(f"\nResearch creation status: {research_response.status_code}")
print(f"Response: {json.dumps(research_response.json(), indent=2)}")
