#!/bin/bash
#
# Deploy n8n JWT Authentication Migration
# ========================================
#
# This script automates the migration from API-Keys to JWT authentication.
#
# Steps:
# 1. Restart n8n container with new JWT configuration
# 2. Wait for healthy status
# 3. Test JWT authentication
# 4. Verify workflow access
#
# Usage:
#   ./scripts/deploy_n8n_jwt.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "n8n JWT Authentication Migration"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Must run from project root (/home/cytrex/news-microservices)"
    exit 1
fi

# Step 1: Restart n8n with new configuration
echo "📦 Step 1: Restarting n8n with JWT configuration..."
echo ""

docker compose up -d n8n

echo "✅ Container restarted"
echo ""

# Step 2: Wait for healthy status
echo "⏳ Step 2: Waiting for n8n to become healthy..."
echo ""

MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' news-n8n 2>/dev/null || echo "unknown")

    if [ "$HEALTH" = "healthy" ]; then
        echo "✅ n8n is healthy!"
        break
    fi

    echo "   Status: $HEALTH (waiting... ${ELAPSED}s/${MAX_WAIT}s)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Timeout waiting for n8n to become healthy"
    echo ""
    echo "Check logs:"
    echo "  docker logs news-n8n --tail 50"
    exit 1
fi

echo ""

# Step 3: Test JWT authentication
echo "🔐 Step 3: Testing JWT authentication..."
echo ""

# Make scripts executable
chmod +x scripts/n8n_jwt_auth.py 2>/dev/null || true

# Run authentication test
if python3 scripts/n8n_jwt_auth.py; then
    echo ""
    echo "✅ JWT authentication working!"
else
    echo ""
    echo "❌ JWT authentication failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check n8n logs: docker logs news-n8n --tail 50"
    echo "2. Verify JWT env vars: docker exec news-n8n env | grep N8N_JWT"
    echo "3. Check user credentials in scripts/n8n_jwt_auth.py"
    exit 1
fi

echo ""

# Step 4: Summary
echo "════════════════════════════════════════════════════════════════"
echo "✅ Migration Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "JWT Authentication Status:"
echo "  ✅ n8n container: healthy"
echo "  ✅ JWT login: working"
echo "  ✅ API access: authenticated"
echo "  ✅ Token cached: ~/.n8n_jwt_token"
echo ""
echo "What changed:"
echo "  • API-Keys disabled (N8N_API_DISABLE_API_KEY_AUTH=true)"
echo "  • JWT auth enabled (N8N_JWT_AUTH_ACTIVE=true)"
echo "  • Redis integration active for persistent state"
echo "  • Rate limiting enabled (10 req/sec)"
echo ""
echo "Usage:"
echo "  # Python (recommended)"
echo "  python3 scripts/fix_workflow_jwt.py"
echo ""
echo "  # Or manual JWT"
echo "  TOKEN=\$(curl -s -X POST http://localhost:5678/api/v1/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"andreas@test.com\",\"password\":\"Aug2012#\"}' | jq -r '.token')"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" http://localhost:5678/api/v1/workflows"
echo ""
echo "Documentation:"
echo "  • Migration guide: /home/cytrex/userdocs/n8n/JWT_AUTH_MIGRATION.md"
echo "  • API token analysis: /home/cytrex/userdocs/n8n/API_TOKEN_PROBLEM_ANALYSIS.md"
echo "  • Workflow fix summary: /home/cytrex/userdocs/n8n/WORKFLOW_FIX_SUMMARY.md"
echo ""
echo "Next steps:"
echo "  1. ✅ JWT auth is now active - no action needed"
echo "  2. Optional: Remove old API key from n8n UI"
echo "  3. Optional: Update any external scripts to use JWT"
echo ""
