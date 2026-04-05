#!/bin/bash
# Agent Progress Monitoring
# Checks if agents have completed their deliverables

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  AGENT PROGRESS MONITORING                                 ║${NC}"
echo -e "${CYAN}║  Checking for agent deliverables...                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_ROOT="/home/cytrex/news-microservices"
cd "$PROJECT_ROOT"

# Track completion
completed=0
total=4

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent 1: Backward-Compatible API Layer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}▶ Agent 1: backend-api-layer-agent${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "services/feed-service/app/services/analysis_loader.py" ]; then
    # Check if file contains unified table query
    if grep -q "public.article_analysis" services/feed-service/app/services/analysis_loader.py; then
        echo -e "  Status: ${GREEN}✓ COMPLETED${NC}"
        echo "  Deliverable: services/feed-service/app/services/analysis_loader.py"

        # Count lines modified
        lines=$(wc -l < services/feed-service/app/services/analysis_loader.py)
        echo "  Lines: $lines"

        # Show key changes
        echo "  Key change detected:"
        grep -A2 "public.article_analysis" services/feed-service/app/services/analysis_loader.py | head -3 | sed 's/^/    /'

        ((completed++))
    else
        echo -e "  Status: ${YELLOW}⚠ IN PROGRESS${NC} (file exists but no unified table query)"
        echo "  File: services/feed-service/app/services/analysis_loader.py"
    fi
else
    echo -e "  Status: ${RED}✗ PENDING${NC} (file not created yet)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent 2: Load Testing Suite
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}▶ Agent 2: load-testing-agent${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "tests/migration/load_test.sh" ]; then
    echo -e "  Status: ${GREEN}✓ COMPLETED${NC}"
    echo "  Deliverable: tests/migration/load_test.sh"

    # Check if executable
    if [ -x "tests/migration/load_test.sh" ]; then
        echo "  Executable: Yes"
    else
        echo "  Executable: No (will fix with chmod +x)"
    fi

    # Count lines
    lines=$(wc -l < tests/migration/load_test.sh)
    echo "  Lines: $lines"

    ((completed++))
else
    echo -e "  Status: ${RED}✗ PENDING${NC} (file not created yet)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent 3: Backfill Execution Wrapper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}▶ Agent 3: database-migration-agent${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "scripts/migration/execute_backfill.sh" ]; then
    echo -e "  Status: ${GREEN}✓ COMPLETED${NC}"
    echo "  Deliverable: scripts/migration/execute_backfill.sh"

    # Check if executable
    if [ -x "scripts/migration/execute_backfill.sh" ]; then
        echo "  Executable: Yes"
    else
        echo "  Executable: No (will fix with chmod +x)"
    fi

    # Count lines
    lines=$(wc -l < scripts/migration/execute_backfill.sh)
    echo "  Lines: $lines"

    ((completed++))
else
    echo -e "  Status: ${RED}✗ PENDING${NC} (file not created yet)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent 4: Deployment Automation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}▶ Agent 4: deployment-coordinator${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

deploy_exists=false
rollback_exists=false
health_exists=false

if [ -f "scripts/migration/deploy.sh" ]; then
    echo -e "  deploy.sh: ${GREEN}✓${NC}"
    deploy_exists=true
else
    echo -e "  deploy.sh: ${RED}✗${NC}"
fi

if [ -f "scripts/migration/rollback.sh" ]; then
    echo -e "  rollback.sh: ${GREEN}✓${NC}"
    rollback_exists=true
else
    echo -e "  rollback.sh: ${RED}✗${NC}"
fi

if [ -f "scripts/migration/health_check.sh" ]; then
    echo -e "  health_check.sh: ${GREEN}✓${NC}"
    health_exists=true
else
    echo -e "  health_check.sh: ${RED}✗${NC}"
fi

if [ "$deploy_exists" = true ] && [ "$rollback_exists" = true ] && [ "$health_exists" = true ]; then
    echo -e "  Status: ${GREEN}✓ COMPLETED${NC} (all 3 scripts present)"
    ((completed++))
elif [ "$deploy_exists" = true ] || [ "$rollback_exists" = true ] || [ "$health_exists" = true ]; then
    echo -e "  Status: ${YELLOW}⚠ IN PROGRESS${NC} (partial completion)"
else
    echo -e "  Status: ${RED}✗ PENDING${NC} (no files created yet)"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

progress=$((completed * 100 / total))

if [ $completed -eq $total ]; then
    echo -e "${GREEN}✅ ALL AGENTS COMPLETED${NC} ($completed/$total)"
    echo ""
    echo "Ready to proceed to Phase 2 (Execution)!"
    echo ""
    echo "Next steps:"
    echo "  1. Review agent deliverables"
    echo "  2. Run: chmod +x scripts/migration/*.sh tests/migration/*.sh"
    echo "  3. Continue with migration runbook (Phase 2)"
    exit 0
elif [ $completed -gt 0 ]; then
    echo -e "${YELLOW}⚠ AGENTS IN PROGRESS${NC} ($completed/$total completed, $progress%)"
    echo ""
    echo "Wait a few more minutes and re-run this script:"
    echo "  ./scripts/migration/monitor_agents.sh"
    exit 1
else
    echo -e "${RED}✗ AGENTS NOT STARTED${NC} ($completed/$total completed)"
    echo ""
    echo "Possible reasons:"
    echo "  1. Agents need more time (wait 5-10 minutes)"
    echo "  2. Agent tasks may have failed"
    echo "  3. MCP swarm coordination issue"
    echo ""
    echo "Recommended action:"
    echo "  - Wait 5-10 minutes"
    echo "  - Re-run: ./scripts/migration/monitor_agents.sh"
    echo "  - If still no progress after 30min: Switch to manual implementation"
    exit 1
fi
