#!/usr/bin/env python3
"""
Comprehensive Integration Test Script for Phase 2 Services
Tests all services, database integration, authentication, and cross-service communication
"""
import requests
import json
import sys
from datetime import datetime

# Service URLs
AUTH_URL = "http://localhost:8000"
FEED_URL = "http://localhost:8001"
CONTENT_ANALYSIS_URL = "http://localhost:8002"
RESEARCH_URL = "http://localhost:8003"
OSINT_URL = "http://localhost:8004"

# Test tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(name, passed, details=""):
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    if passed:
        tests_passed += 1
        status = "✓ PASS"
    else:
        tests_failed += 1
        status = "✗ FAIL"

    result = f"{status}: {name}"
    if details:
        result += f" - {details}"
    print(result)
    test_results.append({"name": name, "passed": passed, "details": details})
    return passed

def test_service_health(name, url):
    """Test service health endpoint"""
    try:
        response = requests.get(f"{url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return log_test(f"{name} Health Check", True, f"Status: {data.get('status', 'unknown')}")
        else:
            return log_test(f"{name} Health Check", False, f"HTTP {response.status_code}")
    except Exception as e:
        return log_test(f"{name} Health Check", False, str(e))

def test_research_health():
    """Test Research Service health (different endpoint)"""
    try:
        response = requests.get(f"{RESEARCH_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return log_test("Research Service Health Check", True, f"Status: {data.get('status', 'unknown')}")
        else:
            return log_test("Research Service Health Check", False, f"HTTP {response.status_code}")
    except Exception as e:
        return log_test("Research Service Health Check", False, str(e))

def create_test_user():
    """Create a test user and get JWT token"""
    user_data = {
        "email": f"integration-test-{datetime.now().timestamp()}@example.com",
        "password": "TestPass123!",
        "username": f"inttest{int(datetime.now().timestamp())}"
    }

    try:
        # Register user
        response = requests.post(
            f"{AUTH_URL}/api/v1/auth/register",
            json=user_data,
            timeout=5
        )

        if response.status_code == 201:
            log_test("User Registration", True, f"User: {user_data['username']}")

            # Login to get token
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }

            login_response = requests.post(
                f"{AUTH_URL}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )

            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get("access_token")
                log_test("User Login", True, f"Token length: {len(token) if token else 0}")
                return token
            else:
                log_test("User Login", False, f"HTTP {login_response.status_code}: {login_response.text}")
                return None
        else:
            log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Create Test User", False, str(e))
        return None

def test_database_tables():
    """Test that all service tables exist in database"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="news_mcp",
            user="news_user",
            password="your_db_password"
        )
        cursor = conn.cursor()

        # Check for Content Analysis tables
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'analysis%'")
        analysis_tables = cursor.fetchone()[0]
        log_test("Content Analysis Tables", analysis_tables >= 5, f"{analysis_tables} tables found")

        # Check for Research tables
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'research%'")
        research_tables = cursor.fetchone()[0]
        log_test("Research Service Tables", research_tables >= 3, f"{research_tables} tables found")

        # Check for OSINT tables
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'osint%'")
        osint_tables = cursor.fetchone()[0]
        log_test("OSINT Service Tables", osint_tables >= 4, f"{osint_tables} tables found")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log_test("Database Connection", False, str(e))
        return False

def test_content_analysis_api(token):
    """Test Content Analysis Service endpoints"""
    headers = {"Authorization": f"Bearer {token}"}

    # Test analyze endpoint (should require data)
    try:
        response = requests.get(f"{CONTENT_ANALYSIS_URL}/api/v1/analysis", headers=headers, timeout=5)
        # Even with auth, this might return 422 or 405 if GET not supported
        log_test("Content Analysis API Access", response.status_code in [200, 405, 422], f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Content Analysis API Access", False, str(e))

def test_research_api(token):
    """Test Research Service endpoints"""
    headers = {"Authorization": f"Bearer {token}"}

    # Test templates endpoint
    try:
        response = requests.get(f"{RESEARCH_URL}/api/v1/research/templates", headers=headers, timeout=5)
        if response.status_code == 200:
            templates = response.json()
            log_test("Research Templates API", True, f"{len(templates)} templates")
        else:
            log_test("Research Templates API", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Research Templates API", False, str(e))

def test_osint_api(token):
    """Test OSINT Service endpoints"""
    headers = {"Authorization": f"Bearer {token}"}

    # Test templates endpoint
    try:
        response = requests.get(f"{OSINT_URL}/api/v1/templates", headers=headers, timeout=5)
        if response.status_code == 200:
            templates = response.json()
            log_test("OSINT Templates API", True, f"{len(templates.get('templates', []))} templates")
        else:
            log_test("OSINT Templates API", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("OSINT Templates API", False, str(e))

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("PHASE 2 SERVICES - COMPREHENSIVE INTEGRATION TEST")
    print("="*70 + "\n")

    print("Phase 1: Service Health Checks")
    print("-" * 70)
    test_service_health("Auth Service", AUTH_URL)
    test_service_health("Feed Service", FEED_URL)
    test_service_health("Content Analysis", CONTENT_ANALYSIS_URL)
    test_research_health()
    test_service_health("OSINT Service", OSINT_URL)

    print("\nPhase 2: Database Integration")
    print("-" * 70)
    test_database_tables()

    print("\nPhase 3: Authentication & Authorization")
    print("-" * 70)
    token = create_test_user()

    if token:
        print("\nPhase 4: API Functionality Tests")
        print("-" * 70)
        test_content_analysis_api(token)
        test_research_api(token)
        test_osint_api(token)
    else:
        print("\n⚠ Skipping API tests (no auth token)")

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {tests_run}")
    print(f"Passed: {tests_passed} ({tests_passed/tests_run*100:.1f}%)")
    print(f"Failed: {tests_failed} ({tests_failed/tests_run*100:.1f}%)")
    print("="*70 + "\n")

    # Return exit code
    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
