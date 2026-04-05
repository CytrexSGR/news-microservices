#!/bin/bash
# Smoke Tests for News Microservices
# Tests critical user flows across all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Base URLs
AUTH_URL="http://localhost:8000"
FEED_URL="http://localhost:8001"
CONTENT_URL="http://localhost:8002"
RESEARCH_URL="http://localhost:8003"
OSINT_URL="http://localhost:8004"
NOTIFICATION_URL="http://localhost:8005"
SEARCH_URL="http://localhost:8006"
ANALYTICS_URL="http://localhost:8007"

# Test data
TEST_USER="smoketest@example.com"
TEST_PASSWORD="TestPassword123!"
ACCESS_TOKEN=""

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

# Header
echo "=================================================="
echo "  News Microservices Smoke Tests"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# 1. Auth Service Tests
log_test "Testing Auth Service..."
echo ""

# Register user
log_test "1.1 Register test user"
REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\",\"username\":\"smoketest\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token\|already exists\|already registered"; then
    log_success "User registration successful or user already exists"

    # Try to login
    log_test "1.2 Login test user"
    LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_URL/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$TEST_USER&password=$TEST_PASSWORD")

    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        log_success "User login successful (token obtained)"
    else
        log_error "User login failed"
        echo "Response: $LOGIN_RESPONSE"
    fi
else
    log_error "User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

# Get user profile
if [ -n "$ACCESS_TOKEN" ]; then
    log_test "1.3 Get user profile"
    PROFILE_RESPONSE=$(curl -s -X GET "$AUTH_URL/api/v1/users/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$PROFILE_RESPONSE" | grep -q "email\|username"; then
        log_success "User profile retrieved successfully"
    else
        log_error "Failed to retrieve user profile"
    fi
fi

echo ""

# 2. Feed Service Tests
log_test "Testing Feed Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "2.1 Create test feed"
    FEED_RESPONSE=$(curl -s -X POST "$FEED_URL/api/v1/feeds" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"url":"https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml","name":"Test Feed","category":"technology"}')

    if echo "$FEED_RESPONSE" | grep -q "id\|already exists"; then
        FEED_ID=$(echo "$FEED_RESPONSE" | grep -o '"id":"[^"]*"' | head -n1 | cut -d'"' -f4)
        log_success "Feed created successfully or already exists"

        # Get feed details
        if [ -n "$FEED_ID" ]; then
            log_test "2.2 Get feed details"
            FEED_DETAILS=$(curl -s -X GET "$FEED_URL/api/v1/feeds/$FEED_ID" \
                -H "Authorization: Bearer $ACCESS_TOKEN")

            if echo "$FEED_DETAILS" | grep -q "id\|url"; then
                log_success "Feed details retrieved successfully"
            else
                log_error "Failed to retrieve feed details"
            fi
        fi

        # Trigger feed fetch
        if [ -n "$FEED_ID" ]; then
            log_test "2.3 Trigger feed fetch"
            FETCH_RESPONSE=$(curl -s -X POST "$FEED_URL/api/v1/feeds/$FEED_ID/fetch" \
                -H "Authorization: Bearer $ACCESS_TOKEN")

            if echo "$FETCH_RESPONSE" | grep -q "task_id\|articles\|success"; then
                log_success "Feed fetch triggered successfully"
            else
                log_error "Feed fetch failed"
            fi
        fi
    else
        log_error "Feed creation failed"
        echo "Response: $FEED_RESPONSE"
    fi
else
    log_error "Skipping feed tests (no access token)"
fi

echo ""

# 3. Content Analysis Service Tests
log_test "Testing Content Analysis Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "3.1 Analyze test content"
    ANALYSIS_RESPONSE=$(curl -s -X POST "$CONTENT_URL/api/v1/analyze" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"text":"This is a test article about technology and innovation.","article_id":"test-001"}')

    if echo "$ANALYSIS_RESPONSE" | grep -q "sentiment\|entities\|task_id"; then
        log_success "Content analysis triggered successfully"
    else
        log_error "Content analysis failed"
    fi

    # Test sentiment analysis
    log_test "3.2 Sentiment analysis"
    SENTIMENT_RESPONSE=$(curl -s -X POST "$CONTENT_URL/api/v1/sentiment" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"text":"This is a positive and exciting development in technology."}')

    if echo "$SENTIMENT_RESPONSE" | grep -q "sentiment\|score\|positive\|negative"; then
        log_success "Sentiment analysis completed successfully"
    else
        log_error "Sentiment analysis failed"
    fi
else
    log_error "Skipping content analysis tests (no access token)"
fi

echo ""

# 4. Research Service Tests
log_test "Testing Research Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "4.1 Create research query"
    RESEARCH_RESPONSE=$(curl -s -X POST "$RESEARCH_URL/api/v1/research" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query":"What are the latest developments in AI technology?","max_results":5}')

    if echo "$RESEARCH_RESPONSE" | grep -q "research_id\|task_id\|id"; then
        RESEARCH_ID=$(echo "$RESEARCH_RESPONSE" | grep -o '"research_id":"[^"]*"\|"id":"[^"]*"' | head -n1 | cut -d'"' -f4)
        log_success "Research query created successfully"

        # Get research status
        if [ -n "$RESEARCH_ID" ]; then
            log_test "4.2 Get research status"
            sleep 2  # Wait for processing
            STATUS_RESPONSE=$(curl -s -X GET "$RESEARCH_URL/api/v1/research/$RESEARCH_ID" \
                -H "Authorization: Bearer $ACCESS_TOKEN")

            if echo "$STATUS_RESPONSE" | grep -q "status\|results\|query"; then
                log_success "Research status retrieved successfully"
            else
                log_error "Failed to retrieve research status"
            fi
        fi
    else
        log_error "Research query creation failed"
    fi
else
    log_error "Skipping research tests (no access token)"
fi

echo ""

# 5. OSINT Service Tests
log_test "Testing OSINT Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "5.1 Get OSINT templates"
    TEMPLATES_RESPONSE=$(curl -s -X GET "$OSINT_URL/api/v1/templates" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$TEMPLATES_RESPONSE" | grep -q "templates\|id\|name"; then
        log_success "OSINT templates retrieved successfully"

        # Create OSINT instance
        log_test "5.2 Create OSINT instance"
        INSTANCE_RESPONSE=$(curl -s -X POST "$OSINT_URL/api/v1/instances" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name":"Test OSINT","template_id":"social_media_monitor","config":{"keywords":["technology","AI"]}}')

        if echo "$INSTANCE_RESPONSE" | grep -q "instance_id\|id"; then
            log_success "OSINT instance created successfully"
        else
            log_error "OSINT instance creation failed"
        fi
    else
        log_error "Failed to retrieve OSINT templates"
    fi
else
    log_error "Skipping OSINT tests (no access token)"
fi

echo ""

# 6. Notification Service Tests
log_test "Testing Notification Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "6.1 Send test notification"
    NOTIFICATION_RESPONSE=$(curl -s -X POST "$NOTIFICATION_URL/api/v1/notifications" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"type":"email","recipient":"smoketest@example.com","subject":"Test Notification","body":"This is a test notification"}')

    if echo "$NOTIFICATION_RESPONSE" | grep -q "notification_id\|task_id\|id\|success"; then
        log_success "Test notification sent successfully"
    else
        log_error "Test notification failed"
    fi

    # Get notification preferences
    log_test "6.2 Get notification preferences"
    PREFS_RESPONSE=$(curl -s -X GET "$NOTIFICATION_URL/api/v1/preferences" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$PREFS_RESPONSE" | grep -q "preferences\|email\|channels"; then
        log_success "Notification preferences retrieved successfully"
    else
        log_error "Failed to retrieve notification preferences"
    fi
else
    log_error "Skipping notification tests (no access token)"
fi

echo ""

# 7. Search Service Tests
log_test "Testing Search Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "7.1 Search articles"
    SEARCH_RESPONSE=$(curl -s -X GET "$SEARCH_URL/api/v1/search?q=technology&limit=10" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$SEARCH_RESPONSE" | grep -q "results\|articles\|total\|hits"; then
        log_success "Search executed successfully"
    else
        log_error "Search failed"
    fi

    # Test advanced search
    log_test "7.2 Advanced search with filters"
    ADVANCED_SEARCH=$(curl -s -X POST "$SEARCH_URL/api/v1/search/advanced" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query":"AI technology","filters":{"category":"technology"},"limit":5}')

    if echo "$ADVANCED_SEARCH" | grep -q "results\|articles\|total"; then
        log_success "Advanced search executed successfully"
    else
        log_error "Advanced search failed"
    fi
else
    log_error "Skipping search tests (no access token)"
fi

echo ""

# 8. Analytics Service Tests
log_test "Testing Analytics Service..."
echo ""

if [ -n "$ACCESS_TOKEN" ]; then
    log_test "8.1 Get user analytics"
    ANALYTICS_RESPONSE=$(curl -s -X GET "$ANALYTICS_URL/api/v1/analytics/user" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$ANALYTICS_RESPONSE" | grep -q "analytics\|stats\|metrics\|total"; then
        log_success "User analytics retrieved successfully"
    else
        log_error "Failed to retrieve user analytics"
    fi

    # Get system metrics
    log_test "8.2 Get system metrics"
    METRICS_RESPONSE=$(curl -s -X GET "$ANALYTICS_URL/api/v1/analytics/system" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$METRICS_RESPONSE" | grep -q "metrics\|system\|stats"; then
        log_success "System metrics retrieved successfully"
    else
        log_error "Failed to retrieve system metrics"
    fi
else
    log_error "Skipping analytics tests (no access token)"
fi

echo ""

# Final Summary
echo "=================================================="
echo "  Smoke Test Summary"
echo "=================================================="
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ Some smoke tests FAILED${NC}"
    exit 1
fi
