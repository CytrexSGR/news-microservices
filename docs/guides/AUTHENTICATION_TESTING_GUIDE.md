# Authentication Testing Guide

**Status:** Production Ready
**Last Updated:** 2025-11-24
**Services:** auth-service, content-analysis-v3-api

## Overview

This guide covers comprehensive testing procedures for the authentication system across all services.

## Prerequisites

```bash
# Ensure all services are running
docker compose up -d auth-service content-analysis-v3-api redis postgres

# Wait for services to be healthy
docker compose ps
```

## 1. Auth Service Testing

### 1.1 Basic Login Flow

```bash
# Login with test user
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.access_token')

echo "Access Token: $TOKEN"

# Expected response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }
```

### 1.2 Token Validation

```bash
# Use token to access protected endpoint
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Expected: User profile data
# {
#   "id": 1,
#   "username": "andreas",
#   "email": "andreas@test.com",
#   "role": "admin"
# }
```

### 1.3 Token Refresh

```bash
# Get refresh token
REFRESH_TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.refresh_token')

# Use refresh token to get new access token
NEW_TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }" | jq -r '.access_token')

echo "New Access Token: $NEW_TOKEN"
```

### 1.4 Logout

```bash
# Logout (blacklists token)
curl -X POST http://localhost:8100/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Try to use blacklisted token (should fail)
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Expected: 401 Unauthorized
```

## 2. Secrets Manager Testing

### 2.1 Check Secrets Manager Status

```bash
# Check if Secrets Manager is initialized
docker logs news-auth-service 2>&1 | grep "Secrets Manager"

# Expected:
# INFO: Secrets Manager initialized with provider: local
# INFO: JWT secret loaded from Secrets Manager
```

### 2.2 Test JWT Key Rotation

```bash
# Get admin token
ADMIN_TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.access_token')

# Check rotation status
curl http://localhost:8100/api/v1/admin/rotation-status \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected:
# {
#   "should_rotate": false,
#   "last_rotation": "2025-11-24T10:30:00",
#   "rotation_interval_days": 30,
#   "secrets_provider": "local"
# }

# Manually rotate key
curl -X POST http://localhost:8100/api/v1/admin/rotate-jwt-key \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected:
# {
#   "success": true,
#   "message": "JWT key rotated successfully",
#   "rotated_at": "2025-11-24T15:45:00"
# }

# Verify old token still works (grace period)
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: User profile (old token still valid)
```

### 2.3 Test Grace Period

```bash
# After rotation, both old and new tokens should work

# Old token (signed with previous key)
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get new token (signed with current key)
NEW_TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.access_token')

# New token (signed with current key)
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $NEW_TOKEN"

# Both should return 200 OK
```

## 3. Redis Persistence Testing

### 3.1 Verify AOF Configuration

```bash
# Check Redis AOF settings
docker exec redis redis-cli -a redis_secret_2024 CONFIG GET appendonly
# Expected: appendonly yes

docker exec redis redis-cli -a redis_secret_2024 CONFIG GET appendfsync
# Expected: appendfsync everysec

docker exec redis redis-cli -a redis_secret_2024 CONFIG GET save
# Expected: save 900 1 300 10 60 10000
```

### 3.2 Test Data Persistence

```bash
# Write test data
docker exec redis redis-cli -a redis_secret_2024 SET test_auth_key "test_value_$(date +%s)"

# Verify data written
docker exec redis redis-cli -a redis_secret_2024 GET test_auth_key

# Check AOF file exists
docker exec redis ls -lh /data/appendonlydir/

# Restart Redis
docker compose restart redis

# Wait for Redis to come back up
sleep 5

# Verify data survived restart
docker exec redis redis-cli -a redis_secret_2024 GET test_auth_key

# Expected: Same value as before restart
```

### 3.3 Test Token Blacklist Persistence

```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.access_token')

# Logout (blacklist token)
curl -X POST http://localhost:8100/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Verify token is blacklisted
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: 401 Unauthorized

# Restart Redis
docker compose restart redis
sleep 5

# Verify token still blacklisted after restart
curl http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: 401 Unauthorized (blacklist persisted)
```

## 4. Content-Analysis-V3 Authentication Testing

### 4.1 Test Protected Endpoints

```bash
# Get fresh token
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "andreas",
    "password": "Aug2012#"
  }' | jq -r '.access_token')

# Test /analyze endpoint without auth (should fail)
curl -X POST http://localhost:8117/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Test Article",
    "url": "https://example.com/test",
    "content": "Test content for authentication testing.",
    "run_tier2": false
  }'

# Expected: 401 Unauthorized

# Test /analyze endpoint with auth (should succeed)
curl -X POST http://localhost:8117/api/v1/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Test Article",
    "url": "https://example.com/test",
    "content": "Test content for authentication testing.",
    "run_tier2": false
  }'

# Expected: 200 OK with analysis response
```

### 4.2 Test Optional Authentication

```bash
# Status endpoint without token (should work but limited info)
curl http://localhost:8117/api/v1/status/550e8400-e29b-41d4-a716-446655440000

# Expected: 200 OK with basic status

# Status endpoint with token (should work with full info)
curl http://localhost:8117/api/v1/status/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with full status
```

### 4.3 Test Results Endpoints

```bash
# All results endpoints require authentication

# Get complete results without auth (should fail)
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000

# Expected: 401 Unauthorized

# Get complete results with auth (should succeed)
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with results

# Get Tier0 results with auth
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000/tier0 \
  -H "Authorization: Bearer $TOKEN"

# Get Tier1 results with auth
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000/tier1 \
  -H "Authorization: Bearer $TOKEN"

# Get Tier2 results with auth
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000/tier2 \
  -H "Authorization: Bearer $TOKEN"
```

### 4.4 Test Public Endpoints

```bash
# Health endpoint (no auth required)
curl http://localhost:8117/health

# Expected: 200 OK

# Root endpoint (no auth required)
curl http://localhost:8117/

# Expected: 200 OK with service info
```

## 5. Integration Testing

### 5.1 Full Pipeline Test

```bash
#!/bin/bash
set -e

echo "=== Full Authentication Pipeline Test ==="

# 1. Login
echo "1. Getting access token..."
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}' | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ FAILED: Could not get access token"
    exit 1
fi
echo "✅ SUCCESS: Got access token"

# 2. Submit article for analysis
echo "2. Submitting article for analysis..."
ARTICLE_ID="550e8400-e29b-41d4-a716-$(date +%s)"
RESPONSE=$(curl -s -X POST http://localhost:8117/api/v1/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"article_id\": \"$ARTICLE_ID\",
    \"title\": \"Federal Reserve Raises Interest Rates\",
    \"url\": \"https://example.com/fed-rates\",
    \"content\": \"The Federal Reserve announced today a 0.25% interest rate increase to combat inflation...\",
    \"run_tier2\": false
  }")

STATUS=$(echo $RESPONSE | jq -r '.status')
if [ "$STATUS" != "processing" ]; then
    echo "❌ FAILED: Article submission failed"
    echo "Response: $RESPONSE"
    exit 1
fi
echo "✅ SUCCESS: Article submitted for analysis"

# 3. Wait for analysis to complete
echo "3. Waiting for analysis to complete (10 seconds)..."
sleep 10

# 4. Get analysis results
echo "4. Getting analysis results..."
RESULTS=$(curl -s http://localhost:8117/api/v1/results/$ARTICLE_ID \
  -H "Authorization: Bearer $TOKEN")

TIER0_COMPLETE=$(echo $RESULTS | jq -r '.tier0 != null')
if [ "$TIER0_COMPLETE" != "true" ]; then
    echo "❌ FAILED: Analysis not complete"
    echo "Results: $RESULTS"
    exit 1
fi
echo "✅ SUCCESS: Got analysis results"

# 5. Test logout
echo "5. Testing logout..."
curl -s -X POST http://localhost:8100/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN" > /dev/null

# 6. Verify token is blacklisted
echo "6. Verifying token is blacklisted..."
BLACKLIST_TEST=$(curl -s http://localhost:8100/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN")

if echo "$BLACKLIST_TEST" | grep -q "detail"; then
    echo "✅ SUCCESS: Token correctly blacklisted"
else
    echo "❌ FAILED: Token not blacklisted"
    exit 1
fi

echo ""
echo "=== All Tests Passed ✅ ==="
```

### 5.2 Performance Test

```bash
#!/bin/bash

echo "=== Authentication Performance Test ==="

# Get token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}' | jq -r '.access_token')

# Test 100 authenticated requests
echo "Testing 100 authenticated requests..."
START=$(date +%s.%N)

for i in {1..100}; do
    curl -s http://localhost:8117/api/v1/status/550e8400-e29b-41d4-a716-446655440000 \
      -H "Authorization: Bearer $TOKEN" > /dev/null
done

END=$(date +%s.%N)
DURATION=$(echo "$END - $START" | bc)
AVG=$(echo "$DURATION / 100" | bc -l)

echo "Total time: ${DURATION}s"
echo "Average per request: ${AVG}s"
echo "Expected: < 0.005s per request"

if (( $(echo "$AVG < 0.005" | bc -l) )); then
    echo "✅ PASS: Performance within acceptable range"
else
    echo "⚠️  WARNING: Performance slower than expected"
fi
```

## 6. Error Scenarios Testing

### 6.1 Invalid Token

```bash
# Test with malformed token
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer invalid.token.here"

# Expected: 401 Unauthorized
# {"detail": "Could not validate credentials"}
```

### 6.2 Expired Token

```bash
# This requires waiting for token to expire (30 minutes)
# Or manually create expired token for testing

# Use expired token
curl http://localhost:8117/api/v1/results/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $EXPIRED_TOKEN"

# Expected: 401 Unauthorized
# {"detail": "Could not validate credentials: Signature has expired"}
```

### 6.3 Missing Authorization Header

```bash
# Test without Authorization header
curl http://localhost:8117/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: 403 Forbidden
# {"detail": "Not authenticated"}
```

### 6.4 Wrong Secret Key

```bash
# Simulate secret key mismatch by using token from different service

# Expected: 401 Unauthorized
# {"detail": "Could not validate credentials: Signature verification failed"}
```

## 7. Troubleshooting Common Issues

### Issue: "Not authenticated" even with token

**Diagnosis:**
```bash
# Check token format
echo "Authorization: Bearer $TOKEN"

# Verify token is not empty
echo "Token length: ${#TOKEN}"

# Remove any whitespace/newlines
TOKEN=$(echo $TOKEN | tr -d '\n\r')
```

**Solutions:**
1. Ensure Bearer prefix is included
2. Check for extra spaces or newlines in token
3. Verify token was successfully retrieved from login

### Issue: "Signature verification failed"

**Diagnosis:**
```bash
# Check auth-service JWT secret
docker exec news-auth-service env | grep JWT_SECRET_KEY

# Check content-analysis-v3 JWT secret
docker exec news-content-analysis-v3-api env | grep JWT_SECRET_KEY

# They must match!
```

**Solutions:**
1. Ensure JWT_SECRET_KEY matches across services
2. Restart services after updating .env files
3. Clear Redis cache if needed

### Issue: Shared auth module not found

**Diagnosis:**
```bash
# Check if shared volume is mounted
docker exec news-content-analysis-v3-api ls -la /app/shared/auth/

# Check PYTHONPATH
docker exec news-content-analysis-v3-api env | grep PYTHONPATH
```

**Solutions:**
1. Verify docker-compose.yml has shared volume mount
2. Ensure PYTHONPATH includes /app/shared
3. Restart container after changes

### Issue: Redis data not persisting

**Diagnosis:**
```bash
# Check AOF configuration
docker exec redis redis-cli -a redis_secret_2024 CONFIG GET appendonly

# Check AOF file exists
docker exec redis ls -lh /data/appendonlydir/

# Check disk space
docker exec redis df -h /data
```

**Solutions:**
1. Verify AOF is enabled (appendonly yes)
2. Check disk space is available
3. Verify Redis volume is mounted correctly

## 8. Automated Test Suite

Create `/scripts/test_authentication.sh`:

```bash
#!/bin/bash
set -e

FAILURES=0

run_test() {
    TEST_NAME=$1
    TEST_COMMAND=$2

    echo -n "Testing $TEST_NAME... "
    if eval "$TEST_COMMAND" > /dev/null 2>&1; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
        FAILURES=$((FAILURES + 1))
    fi
}

echo "=== Authentication Test Suite ==="
echo ""

# Test 1: Login
run_test "Login" "curl -s -f -X POST http://localhost:8100/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"andreas\",\"password\":\"Aug2012#\"}' | jq -e '.access_token'"

# Get token for subsequent tests
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"andreas","password":"Aug2012#"}' | jq -r '.access_token')

# Test 2: Protected endpoint with auth
run_test "Protected endpoint with auth" "curl -s -f http://localhost:8100/api/v1/users/me -H 'Authorization: Bearer $TOKEN'"

# Test 3: Protected endpoint without auth (should fail)
run_test "Protected endpoint without auth (should fail)" "! curl -s -f http://localhost:8100/api/v1/users/me"

# Test 4: Content-Analysis-V3 with auth
run_test "Content-Analysis-V3 with auth" "curl -s -f -X POST http://localhost:8117/api/v1/analyze -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"article_id\":\"550e8400-e29b-41d4-a716-446655440000\",\"title\":\"Test\",\"url\":\"https://example.com\",\"content\":\"Test content\",\"run_tier2\":false}'"

# Test 5: Content-Analysis-V3 without auth (should fail)
run_test "Content-Analysis-V3 without auth (should fail)" "! curl -s -f -X POST http://localhost:8117/api/v1/analyze -H 'Content-Type: application/json' -d '{\"article_id\":\"550e8400-e29b-41d4-a716-446655440000\",\"title\":\"Test\",\"url\":\"https://example.com\",\"content\":\"Test content\"}'"

# Test 6: Public health endpoint
run_test "Public health endpoint" "curl -s -f http://localhost:8117/health"

# Test 7: Redis persistence
run_test "Redis persistence" "docker exec redis redis-cli -a redis_secret_2024 CONFIG GET appendonly | grep -q yes"

# Test 8: Secrets Manager initialization
run_test "Secrets Manager initialization" "docker logs news-auth-service 2>&1 | grep -q 'Secrets Manager initialized'"

echo ""
echo "=== Test Results ==="
if [ $FAILURES -eq 0 ]; then
    echo "✅ All tests passed"
    exit 0
else
    echo "❌ $FAILURES test(s) failed"
    exit 1
fi
```

Make executable:
```bash
chmod +x /scripts/test_authentication.sh
```

Run tests:
```bash
./scripts/test_authentication.sh
```

## 9. Continuous Monitoring

### 9.1 Check Auth Service Health

```bash
# Health check
curl http://localhost:8100/health

# Secrets Manager status
docker logs news-auth-service 2>&1 | grep "Secrets Manager" | tail -5

# Active sessions count
docker exec redis redis-cli -a redis_secret_2024 DBSIZE
```

### 9.2 Monitor Token Usage

```bash
# Count blacklisted tokens
docker exec redis redis-cli -a redis_secret_2024 KEYS "blacklist:*" | wc -l

# Check rotation status
curl http://localhost:8100/api/v1/admin/rotation-status \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 9.3 Performance Metrics

```bash
# Average response time (last 100 requests)
docker logs news-content-analysis-v3-api 2>&1 | \
  grep "POST /api/v1/analyze" | \
  tail -100 | \
  awk '{print $NF}' | \
  awk '{s+=$1}END{print s/NR "ms"}'
```

## 10. Production Deployment Checklist

- [ ] Change default JWT_SECRET_KEY to strong random value (min 64 chars)
- [ ] Configure AWS Secrets Manager or HashiCorp Vault (not local provider)
- [ ] Enable automatic JWT key rotation (JWT_ROTATION_ENABLED=true)
- [ ] Set up monitoring for rotation failures
- [ ] Configure CORS origins appropriately
- [ ] Enable HTTPS in production
- [ ] Set up rate limiting on authentication endpoints
- [ ] Configure Redis persistence backups
- [ ] Test token blacklist persistence across Redis restarts
- [ ] Verify Secrets Manager failover behavior
- [ ] Document secret backup/recovery procedures
- [ ] Set up alerts for failed authentication attempts
- [ ] Test grace period behavior during key rotation

## References

- [Auth Service Secrets Management](../services/auth-service-secrets-management.md)
- [Content-Analysis-V3 Authentication](../services/content-analysis-v3-authentication.md)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Last Updated:** 2025-11-24
**Maintainer:** Backend Team
**Related Docs:**
- [Auth Service README](/services/auth-service/README.md)
- [Content-Analysis-V3 README](/services/content-analysis-v3/README.md)
- [API Authentication Guide](../guides/api-authentication.md)
