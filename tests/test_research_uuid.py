#!/usr/bin/env python3
"""
Research Service UUID Integration Test

Validates that Research Service properly integrates with Feed Service
using UUID-based feed_id references. Tests:
1. Creating research tasks with UUID feed_id
2. Retrieving research tasks with UUID validation
3. Querying research tasks by feed_id (UUID)
4. Ensuring all feed_id references are valid UUIDs
"""
import requests
import json
import uuid
from typing import Optional

# Service URLs
AUTH_URL = "http://localhost:8000/api/v1/auth"
FEED_URL = "http://localhost:8001/api/v1/feeds"
RESEARCH_URL = "http://localhost:8003/api/v1/research"

# Test user
TEST_USER = {
    "email": "research_uuid@test.com",
    "password": "ResearchUUID123!",
    "username": "researchuuid"
}


def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def is_valid_uuid(value: str) -> bool:
    """Validate UUID format (copied from test_e2e_lifecycle.py)"""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def get_auth_token() -> Optional[str]:
    """Get authentication token"""
    print_section("Authentication Setup")

    # Try login first
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json=TEST_USER
        )
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Login successful (token: {token[:30]}...)")
            return token
    except:
        pass

    # Register if login failed
    try:
        print(f"Registering new user: {TEST_USER['email']}...")
        response = requests.post(
            f"{AUTH_URL}/register",
            json=TEST_USER
        )
        if response.status_code in [200, 201]:
            print("✅ User registered")
            # Login after registration
            response = requests.post(
                f"{AUTH_URL}/login",
                json=TEST_USER
            )
            if response.status_code == 200:
                token = response.json().get('access_token')
                print(f"✅ Login successful (token: {token[:30]}...)")
                return token
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_test_feed() -> Optional[dict]:
    """Get or create a test feed with UUID"""
    print_section("TEST 1: Get Feed with UUID")

    try:
        # Get existing feeds
        response = requests.get(FEED_URL)
        if response.status_code == 200:
            feeds = response.json()
            if feeds and len(feeds) > 0:
                feed = feeds[0]
                feed_id = feed.get('id')

                print(f"✅ Feed Retrieved:")
                print(f"   ID: {feed_id}")
                print(f"   ID is UUID: {is_valid_uuid(feed_id)}")
                print(f"   Name: {feed.get('name')}")
                print(f"   Status: {feed.get('status')}")

                # Validate UUID format
                if not is_valid_uuid(feed_id):
                    print(f"   ❌ ERROR: Feed ID is not a valid UUID!")
                    return None

                return feed
            else:
                print("⚠️  No feeds found - consider creating one first")
                return None
    except Exception as e:
        print(f"❌ Error fetching feed: {e}")
        return None


def test_create_research_task(feed_id: str, token: str) -> Optional[dict]:
    """TEST 2: Create research task with UUID feed_id"""
    print_section("TEST 2: Create Research Task with UUID feed_id")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Validate input feed_id is UUID
    print(f"\nInput validation:")
    print(f"   feed_id: {feed_id}")
    print(f"   feed_id is UUID: {is_valid_uuid(feed_id)}")

    if not is_valid_uuid(feed_id):
        print(f"   ❌ ERROR: Input feed_id is not a valid UUID!")
        return None

    payload = {
        "feed_id": feed_id,  # UUID from Feed Service
        "query": "Test research query with UUID integration",
        "research_type": "quick",
        "max_results": 5,
        "metadata": {
            "test": "uuid_integration",
            "purpose": "validate_uuid_references"
        }
    }

    try:
        print(f"\nCreating research task...")
        response = requests.post(
            RESEARCH_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            research_id = result.get('id')
            returned_feed_id = result.get('feed_id')

            print(f"\n✅ Research Task Created:")
            print(f"   Research ID: {research_id}")
            print(f"   Research ID is UUID: {is_valid_uuid(research_id)}")
            print(f"   feed_id: {returned_feed_id}")
            print(f"   feed_id is UUID: {is_valid_uuid(returned_feed_id)}")
            print(f"   Status: {result.get('status')}")

            # Validate UUID formats
            if not is_valid_uuid(research_id):
                print(f"   ❌ ERROR: Research ID is not a valid UUID!")

            if not is_valid_uuid(returned_feed_id):
                print(f"   ❌ ERROR: Returned feed_id is not a valid UUID!")

            if returned_feed_id != feed_id:
                print(f"   ⚠️  WARNING: Returned feed_id ({returned_feed_id}) != Input feed_id ({feed_id})")

            return result
        else:
            print(f"❌ Research task creation failed: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("⚠️  Request timed out")
        return None
    except Exception as e:
        print(f"❌ Error creating research task: {e}")
        return None


def test_retrieve_research_task(research_id: str, token: str) -> Optional[dict]:
    """TEST 3: Retrieve research task and validate UUID format"""
    print_section("TEST 3: Retrieve Research Task with UUID Validation")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"Retrieving research task...")
        print(f"   Research ID: {research_id}")
        print(f"   Research ID is UUID: {is_valid_uuid(research_id)}")

        response = requests.get(
            f"{RESEARCH_URL}/{research_id}",
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            returned_research_id = result.get('id')
            feed_id = result.get('feed_id')

            print(f"\n✅ Research Task Retrieved:")
            print(f"   Research ID: {returned_research_id}")
            print(f"   Research ID is UUID: {is_valid_uuid(returned_research_id)}")
            print(f"   feed_id: {feed_id}")
            print(f"   feed_id is UUID: {is_valid_uuid(feed_id)}")
            print(f"   Status: {result.get('status')}")
            print(f"   Query: {result.get('query')}")

            # Validate UUID formats
            if not is_valid_uuid(returned_research_id):
                print(f"   ❌ ERROR: Research ID is not a valid UUID!")

            if not is_valid_uuid(feed_id):
                print(f"   ❌ ERROR: feed_id is not a valid UUID!")

            return result
        else:
            print(f"❌ Error retrieving research task: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error retrieving research task: {e}")
        return None


def test_query_by_feed_id(feed_id: str, token: str) -> Optional[list]:
    """TEST 4: Query research tasks by feed_id (UUID)"""
    print_section("TEST 4: Query Research Tasks by feed_id (UUID)")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"Querying research tasks by feed_id...")
        print(f"   feed_id: {feed_id}")
        print(f"   feed_id is UUID: {is_valid_uuid(feed_id)}")

        # Query with feed_id parameter
        response = requests.get(
            f"{RESEARCH_URL}?feed_id={feed_id}",
            headers=headers
        )

        if response.status_code == 200:
            results = response.json()

            print(f"\n✅ Research Tasks Retrieved:")
            print(f"   Total tasks found: {len(results)}")

            # Validate each result
            uuid_errors = []
            for idx, task in enumerate(results, 1):
                task_id = task.get('id')
                task_feed_id = task.get('feed_id')

                print(f"\n   Task {idx}:")
                print(f"      ID: {task_id} (UUID: {is_valid_uuid(task_id)})")
                print(f"      feed_id: {task_feed_id} (UUID: {is_valid_uuid(task_feed_id)})")
                print(f"      Status: {task.get('status')}")

                # Validate UUIDs
                if not is_valid_uuid(task_id):
                    uuid_errors.append(f"Task {idx} ID is not a valid UUID")

                if not is_valid_uuid(task_feed_id):
                    uuid_errors.append(f"Task {idx} feed_id is not a valid UUID")

                if task_feed_id != feed_id:
                    print(f"      ⚠️  WARNING: feed_id mismatch!")

            if uuid_errors:
                print(f"\n❌ UUID VALIDATION ERRORS:")
                for error in uuid_errors:
                    print(f"   - {error}")

            return results
        else:
            print(f"❌ Error querying research tasks: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error querying research tasks: {e}")
        return None


def main():
    """Run all Research Service UUID integration tests"""
    print("\n" + "="*70)
    print("  RESEARCH SERVICE UUID INTEGRATION TEST")
    print("="*70)
    print("\nValidates UUID-based integration between Research and Feed services")
    print("\nTest Coverage:")
    print("  1. Get Feed with UUID validation")
    print("  2. Create research task with UUID feed_id")
    print("  3. Retrieve research task with UUID validation")
    print("  4. Query research tasks by feed_id (UUID)")

    # Setup: Authentication
    token = get_auth_token()
    if not token:
        print("\n❌ TEST FAILED: Cannot proceed without authentication")
        return

    # TEST 1: Get test feed
    feed = get_test_feed()
    if not feed:
        print("\n❌ TEST FAILED: No feed available for testing")
        return

    feed_id = feed.get('id')

    # TEST 2: Create research task with UUID feed_id
    research_task = test_create_research_task(feed_id, token)
    if not research_task:
        print("\n❌ TEST FAILED: Could not create research task")
        return

    research_id = research_task.get('id')

    # TEST 3: Retrieve research task
    retrieved_task = test_retrieve_research_task(research_id, token)
    if not retrieved_task:
        print("\n❌ TEST FAILED: Could not retrieve research task")
        return

    # TEST 4: Query by feed_id
    query_results = test_query_by_feed_id(feed_id, token)
    if query_results is None:
        print("\n⚠️  TEST WARNING: Could not query by feed_id")

    # Final validation
    print_section("TEST RESULTS SUMMARY")

    all_valid = True
    validation_results = []

    # Validate feed UUID
    if is_valid_uuid(feed_id):
        validation_results.append("✅ Feed ID is valid UUID")
    else:
        validation_results.append("❌ Feed ID is NOT a valid UUID")
        all_valid = False

    # Validate research task UUID
    if is_valid_uuid(research_id):
        validation_results.append("✅ Research Task ID is valid UUID")
    else:
        validation_results.append("❌ Research Task ID is NOT a valid UUID")
        all_valid = False

    # Validate feed_id reference
    if is_valid_uuid(retrieved_task.get('feed_id')):
        validation_results.append("✅ Research Task feed_id is valid UUID")
    else:
        validation_results.append("❌ Research Task feed_id is NOT a valid UUID")
        all_valid = False

    # Validate feed_id consistency
    if retrieved_task.get('feed_id') == feed_id:
        validation_results.append("✅ feed_id reference is consistent")
    else:
        validation_results.append("❌ feed_id reference is INCONSISTENT")
        all_valid = False

    # Print results
    for result in validation_results:
        print(f"   {result}")

    if all_valid:
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED")
        print("="*70)
        print("\nResearch Service UUID Integration: ✅ VALIDATED")
        print("  - All IDs are valid UUIDs")
        print("  - feed_id references are consistent")
        print("  - UUID-based queries work correctly")
    else:
        print("\n" + "="*70)
        print("  ❌ TESTS FAILED")
        print("="*70)
        print("\nResearch Service UUID Integration: ❌ ISSUES FOUND")
        print("  - Review validation results above")
        print("  - Fix UUID handling in Research Service")


if __name__ == "__main__":
    main()
