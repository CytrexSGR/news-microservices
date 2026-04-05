#!/usr/bin/env python3
import requests
import json

# Create new admin user
register_data = {
    "username": "cytrex",
    "email": "cytrex@admin.com",
    "password": "Cytrex123!",
    "full_name": "Cytrex Admin"
}

print("Creating admin user...")
response = requests.post(
    "http://localhost:8100/api/v1/auth/register",
    json=register_data,
    timeout=5
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}\n")

# Login to get token
print("Logging in...")
login_data = {
    "username": "cytrex",
    "password": "Cytrex123!"
}

response = requests.post(
    "http://localhost:8100/api/v1/auth/login",
    json=login_data,
    timeout=5
)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    print(f"Token: {token[:50]}...\n")

    # Test authenticated access
    print("Testing feed access...")
    headers = {"Authorization": f"Bearer {token}"}
    feeds_response = requests.get(
        "http://localhost:8101/api/v1/feeds",
        headers=headers,
        timeout=5
    )
    print(f"Status: {feeds_response.status_code}")

    if feeds_response.status_code == 200:
        feeds = feeds_response.json()
        print(f"\n✅ SUCCESS! Found {len(feeds)} feeds")
        print("\nTop 5 Feeds:")
        for feed in feeds[:5]:
            print(f"  - {feed['name']}: {feed['total_items']} items")
    else:
        print(f"Error: {feeds_response.text}")
else:
    print(f"Login failed: {response.text}")
